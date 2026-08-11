#!/usr/bin/env python3
"""Baja los datos de GameTracker de todos los servidores del TSV y genera
un unico datos/todos.json con detalle, jugadores online y top 10 por servidor.
Corre en GitHub Actions cada 10 minutos (ver .github/workflows/datos.yml)."""
import html
import json
import os
import re
import sys
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(AQUI, "servers.tsv")
SALIDA = os.path.join(os.path.dirname(AQUI), "datos")
UA = "Mozilla/5.0 (X11; Linux x86_64) ArgentinaCS-web/1.0"


def limpiar(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def campo_id(pagina, el_id):
    m = re.search(r'id="%s"[^>]*>(.*?)</' % re.escape(el_id), pagina, re.S)
    return limpiar(m.group(1)) if m else None


def filas_tabla(fragmento):
    filas = []
    for tr in re.findall(r"<tr>(.*?)</tr>", fragmento, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 4 or 'col_h' in tr:
            continue
        filas.append({
            "nombre": limpiar(tds[1]),
            "score": limpiar(tds[2]),
            "tiempo": limpiar(tds[3]),
        })
    return filas


def parsear(pagina):
    d = {}
    d["estado"] = "online" if re.search(r"Status:.{0,120}?Alive", pagina, re.S) else "offline"
    d["jugadores"] = campo_id(pagina, "HTML_num_players")
    d["max"] = campo_id(pagina, "HTML_max_players")
    d["promedio"] = campo_id(pagina, "HTML_avg_players")
    d["mapa"] = campo_id(pagina, "HTML_curr_map")
    d["escaneado"] = campo_id(pagina, "last_scanned")

    m = re.search(r'id="HTML_map_ss_img"[^>]*src="([^"]+)"', pagina)
    if m:
        src = m.group(1)
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = "https://www.gametracker.com" + src
        d["mapaImg"] = src

    m = re.search(r"Game Server Rank:\s*(?:<[^>]*>\s*)*([\d,]+)(?:st|nd|rd|th)\s*\(([^)]*)\)", pagina, re.S)
    if m:
        d["rank"] = m.group(1)
        d["percentil"] = limpiar(m.group(2)).replace("Percentile", "percentil")

    m = re.search(r'id="HTML_online_players"(.*?)(?:<div class="blocknew blocknew666">|$)', pagina, re.S)
    d["online"] = filas_tabla(m.group(1)) if m else []

    i = pagina.find("TOP 10")
    if i >= 0:
        frag = pagina[i:i + 12000]
        m = re.search(r"<table.*?</table>", frag, re.S)
        if m and "not tracked" not in m.group(0):
            d["top10"] = filas_tabla(m.group(0))
        else:
            d["top10"] = None
    else:
        d["top10"] = None
    return d


def main():
    servidores = []
    with open(TSV, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            nombre, ip = linea.split("\t")[:2]
            servidores.append((nombre, ip))

    todos = {"actualizado": int(time.time()), "servidores": {}}
    errores = 0
    for nombre, ip in servidores:
        url = "https://www.gametracker.com/server_info/%s/" % ip
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                pagina = r.read().decode("utf-8", "replace")
            if "SERVER DETAILS" not in pagina:
                raise ValueError("pagina sin contenido esperado")
            datos = parsear(pagina)
            datos["nombre"] = nombre
            todos["servidores"][ip] = datos
        except Exception as e:  # noqa: BLE001 - un servidor caido no corta el resto
            print("ERROR %s (%s): %s" % (nombre, ip, e))
            errores += 1
        time.sleep(1.2)

    os.makedirs(SALIDA, exist_ok=True)
    with open(os.path.join(SALIDA, "todos.json"), "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, separators=(",", ":"))
    print("OK: %d servidores, %d errores" % (len(todos["servidores"]), errores))
    # si no se pudo bajar NINGUNO, fallar para no pisar datos buenos con vacio
    if not todos["servidores"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
