#!/usr/bin/env python3
"""Sincroniza la tienda de Minecraft: lee el catalogo de la planilla y actualiza
(1) el catalogo del sitio web y (2) el menu /compras del servidor por SFTP.

Corre una vez por dia desde GitHub Actions. Si no hay cambios, no toca nada.
Ver tools/README-tienda.md para la explicacion completa.
"""
import csv
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGINA = os.path.join(RAIZ, "servidor-minecraft-survival.html")
META = os.path.join(RAIZ, "tools", "tienda_meta.json")

CSV_URL = os.environ.get("TIENDA_CSV_URL", "")
SFTP_HOST = os.environ.get("MC_SFTP_HOST", "45.235.98.41")
SFTP_PORT = os.environ.get("MC_SFTP_PORT", "8822")
SFTP_USER = os.environ.get("MC_SFTP_USER", "")
SFTP_PASS = os.environ.get("MC_SFTP_PASS", "")
BASE_REMOTA = "/45.235.98.41_25565/plugins/ConditionalEvents/events"
RUTA_EVENTOS = BASE_REMOTA + "/more_events.yml"
WEBHOOK_MAKE = "https://hook.us2.make.com/yl7yr7n5kayca9g7rmmn80oh6tyq1uus"

cambios = []
avisos = []


def bajar_catalogo():
    """Lee la planilla publicada como CSV y devuelve [(codigo, titulo, precio)]."""
    with urllib.request.urlopen(CSV_URL, timeout=60) as r:
        texto = r.read().decode("utf-8", "replace")
    productos = []
    for fila in csv.reader(io.StringIO(texto)):
        if len(fila) < 3:
            continue
        codigo, titulo, precio = fila[0].strip(), fila[1].strip(), fila[2].strip()
        if not codigo or codigo.lower() == "product_code" or not titulo:
            continue
        limpio = precio.replace(",", "").replace(".", "")
        if not limpio.isdigit():
            continue
        productos.append((codigo, titulo, int(limpio)))
    return productos


def miles(n):
    return "{:,}".format(n).replace(",", ".")


def agrupar(productos, meta):
    grupos = {s["id"]: [] for s in meta["secciones"]}
    for codigo, titulo, precio in productos:
        info = meta["productos"].get(codigo)
        if info is None:
            avisos.append("Producto nuevo sin descripcion en tienda_meta.json: %s (%s)" % (codigo, titulo))
            info = {"seccion": "otros", "juego_nombre": titulo, "web_nombre": titulo}
        grupos.setdefault(info["seccion"], []).append((codigo, titulo, precio, info))
    return grupos


def esc_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def html_catalogo(grupos, meta):
    out = ['      <div class="catalogo">']
    secciones_con_items = [s for s in meta["secciones"] if grupos.get(s["id"])]
    for i, sec in enumerate(secciones_con_items):
        out.append('        <div class="cat-grupo">')
        out.append("          <h3>%s</h3>" % esc_html(sec["web"]))
        out.append('          <ul class="cat-lista">')
        for _codigo, titulo, precio, info in grupos[sec["id"]]:
            nombre = esc_html(info.get("web_nombre", titulo))
            detalle = info.get("web_detalle", "")
            texto = "<strong>%s</strong>" % nombre
            if detalle:
                texto += " — %s" % esc_html(detalle)
            out.append('            <li><span>%s</span><span class="cat-precio">$%s</span></li>'
                       % (texto, miles(precio)))
        out.append("          </ul>")
        out.append("        </div>")
        if i < len(secciones_con_items) - 1:
            out.append("")
    out.append("      </div>")
    return "\n".join(out) + "\n"


def actualizar_sitio(grupos, meta):
    with open(PAGINA, encoding="utf-8") as f:
        html = f.read()
    nuevo = html_catalogo(grupos, meta)
    patron = re.compile(r'      <div class="catalogo">.*?\n      </div>\n', re.S)
    if not patron.search(html):
        raise RuntimeError("No se encontro el bloque del catalogo en la pagina del servidor")
    salida = patron.sub(lambda _m: nuevo, html, count=1)
    if salida == html:
        return False
    with open(PAGINA, "w", encoding="utf-8", newline="") as f:
        f.write(salida)
    cambios.append("catalogo del sitio web")
    return True


def link_compra(codigo):
    return '%s?player=%%player%%&product=%s' % (WEBHOOK_MAKE, codigo)


def lineas_menu(grupos, meta):
    """Genera las lineas del evento /compras en formato ConditionalEvents."""
    sep = "        - 'message: <dark_gray><strikethrough>──────────────────────────'"
    boton_largo = ('        - \'message: <click:open_url:"%s"><aqua><underlined>'
                   'Comprar con MercadoPago</underlined></aqua></click>\'')
    boton_linea = ('        - \'message: <click:open_url:"%s">%s'
                   ' <aqua><underlined>[Comprar]</underlined></aqua></click>\'')

    L = [sep, "        - 'message: <gold><bold>           ✦ TIENDA ✦'", sep]

    for codigo, _t, precio, info in grupos.get("vip", []):
        L.append("        - 'message: <gold><bold>★ %s <white>─ <green>$%s'"
                 % (info["juego_nombre"], miles(precio)))
        for extra in info.get("juego_lineas", []):
            L.append("        - 'message: <gray>  %s'" % extra)
        L.append(boton_largo % link_compra(codigo))
        L.append("        - 'message: '")

    for sec_id in ("piedras", "spawners", "packs", "otros"):
        items = grupos.get(sec_id, [])
        if not items:
            continue
        titulo = next(s["juego"] for s in meta["secciones"] if s["id"] == sec_id)
        L.append(sep)
        L.append("        - 'message: <white><bold>  %s'" % titulo)
        L.append(sep)
        for codigo, _t, precio, info in items:
            det = info.get("juego_detalle", "")
            det_txt = " <dark_gray>(%s)" % det if det else ""
            etiqueta = "<gray> %s%s <white>─ <green>$%s" % (info["juego_nombre"], det_txt, miles(precio))
            if sec_id == "piedras":
                L.append("        - 'message: %s'" % etiqueta)
                L.append(boton_largo % link_compra(codigo))
                L.append("        - 'message: '")
            else:
                L.append(boton_linea % (link_compra(codigo), etiqueta))
        if sec_id == "spawners":
            L.append("        - 'message: '")
    L.append(sep)
    return "\n".join(L) + "\n"


def sftp(cfg, *args, timeout=180):
    subprocess.run(["curl", "-sk", "-K", cfg] + list(args), check=True, timeout=timeout)


def actualizar_servidor(grupos, meta):
    """Reemplaza SOLO las lineas del evento compras, cuidando los bytes del resto."""
    tmp = tempfile.mkdtemp()
    local = os.path.join(tmp, "more_events.yml")
    cfg = os.path.join(tmp, "cfg")
    with open(cfg, "w") as f:
        f.write('user = "%s:%s"\n' % (SFTP_USER, SFTP_PASS))
    url = "sftp://%s:%s%s" % (SFTP_HOST, SFTP_PORT, RUTA_EVENTOS)

    sftp(cfg, url, "-o", local)
    with open(local, "rb") as f:
        crudo = f.read()
    original = len(crudo)
    if original < 100000:
        raise RuntimeError("El archivo del servidor bajo incompleto (%d bytes)" % original)

    texto = crudo.decode("utf-8")
    inicio = texto.find("  compras:\n")
    if inicio < 0:
        raise RuntimeError("No se encontro el evento compras en el servidor")
    marca = "      default:\n"
    pos_default = texto.find(marca, inicio)
    if pos_default < 0:
        raise RuntimeError("Estructura inesperada del evento compras")
    cuerpo_desde = pos_default + len(marca)
    fin = texto.find("\n\n", cuerpo_desde)
    if fin < 0:
        raise RuntimeError("No se encontro el final del evento compras")

    bloque = "        - 'cancel_event: true'\n" + lineas_menu(grupos, meta)
    nuevo_texto = texto[:cuerpo_desde] + bloque + texto[fin + 1:]
    if nuevo_texto == texto:
        return False

    # Validaciones antes de tocar el servidor en vivo
    import yaml
    yaml.safe_load(nuevo_texto)
    for imprescindible in ("acsregen_endcities:", "type: player_command", "  vip_list:", "  compras:", "  ps_cleanup_world:"):
        if imprescindible not in nuevo_texto:
            raise RuntimeError("Falta '%s' en el archivo generado: se aborta" % imprescindible)
    nuevos_bytes = nuevo_texto.encode("utf-8")
    if abs(len(nuevos_bytes) - original) > original * 0.15:
        raise RuntimeError("El archivo cambio demasiado (%d -> %d bytes): se aborta" % (original, len(nuevos_bytes)))

    sello = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    respaldo = os.path.join(tmp, "backup.yml")
    with open(respaldo, "wb") as f:
        f.write(crudo)
    sftp(cfg, "-T", respaldo, "sftp://%s:%s%s/backup-more_events-%s.yml.bak"
         % (SFTP_HOST, SFTP_PORT, BASE_REMOTA, sello))

    salida = os.path.join(tmp, "nuevo.yml")
    with open(salida, "wb") as f:
        f.write(nuevos_bytes)
    sftp(cfg, "-T", salida, url)

    verif = os.path.join(tmp, "verif.yml")
    sftp(cfg, url, "-o", verif)
    with open(verif, "rb") as f:
        if f.read() != nuevos_bytes:
            raise RuntimeError("La verificacion posterior a la subida no coincide")

    cambios.append("menu /compras del servidor")
    return True


def main():
    if not CSV_URL:
        print("Falta la direccion de la planilla (TIENDA_CSV_URL): no se hace nada.")
        return 0
    with open(META, encoding="utf-8") as f:
        meta = json.load(f)

    productos = bajar_catalogo()
    print("Productos leidos de la planilla: %d" % len(productos))
    if len(productos) < 5:
        print("Muy pocos productos: la planilla puede estar mal publicada. Se aborta sin tocar nada.")
        return 1

    grupos = agrupar(productos, meta)
    actualizar_sitio(grupos, meta)
    if SFTP_USER and SFTP_PASS:
        actualizar_servidor(grupos, meta)
    else:
        avisos.append("Sin credenciales SFTP: no se actualizo el menu del servidor")

    for a in avisos:
        print("AVISO: " + a)
    if cambios:
        print("CAMBIOS::" + ", ".join(cambios))
    else:
        print("Sin cambios: la tienda ya estaba al dia.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
