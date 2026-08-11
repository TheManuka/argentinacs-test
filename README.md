# Sitio web — Comunidad ArgentinaCS

Sitio estático de la comunidad: servidores de Counter-Strike 1.6 y Minecraft, tienda de merchandising y VIP (en construcción) y redes sociales.

> El nombre de la comunidad se escribe **ArgentinaCS** (sin espacio). Formas permitidas: "ArgentinaCS" o "Comunidad ArgentinaCS", siempre sin la bandera pegada al nombre.

## Archivos

| Archivo | Qué es |
|---|---|
| `index.html` | Página principal: listado de servidores, tienda/VIP, redes |
| `tienda.html` | Tienda (página "en construcción") |
| `vip.html` | Contratar VIP (página "en construcción") |
| `assets/styles.css` | Estilos (paleta negro + azul + dorado del banner oficial) |
| `assets/main.js` | Copiar IP al portapapeles + aviso de confirmación |
| `assets/favicon.svg` | Ícono del sitio (logo blanco sobre fondo oscuro) |
| `assets/fondo.jpg` | Imagen de fondo (soldado CS vs creeper), fija y sutil — comprimida para carga rápida; el original sin comprimir está en `tools/fondo-original.png` |

> **Regla de imágenes:** toda imagen que se sume al sitio (fotos de merchandising, banners propios, etc.) va comprimida — JPEG calidad ~85 para fotos, PNG solo para gráficos con pocos colores, ideal por debajo de ~200 KB. Los originales sin comprimir se guardan en `tools/` (que no se sube al hosting).

## SEO (posicionamiento en buscadores)

El sitio ya incluye: títulos y descripciones optimizados por página, Open Graph + Twitter Cards (vista previa con imagen al compartir el link en WhatsApp/Discord/redes, usa `assets/og.jpg`), datos estructurados JSON-LD (Organization + WebSite con las redes sociales), jerarquía de encabezados correcta, `robots.txt` y `sitemap.xml`.

**⚠️ Paso obligatorio al conseguir el dominio** (las URLs absolutas usan el marcador `https://TU-DOMINIO.com` hasta entonces):

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File "tools/set_domain.ps1" -Domain "https://tudominio.com"
```

Después de publicar con el dominio real:
1. Dar de alta el sitio en [Google Search Console](https://search.google.com/search-console) y enviar `sitemap.xml`.
2. Verificar la vista previa al compartir con [metatags.io](https://metatags.io) o pegando el link en WhatsApp.
3. Usar siempre HTTPS (además de seguridad, Google lo premia en el ranking).

## Cómo publicarlo

No necesita servidor especial ni base de datos: **subí todos los archivos (manteniendo la carpeta `assets/`) a cualquier hosting** y listo. Funciona en cualquier dominio sin tocar nada, porque todas las rutas son relativas.

Recomendado: usar HTTPS (el botón de copiar IP funciona mejor en sitios seguros).

## Jugadores en vivo

- **CS 1.6:** cada tarjeta muestra el banner dinámico de **GameTracker** (jugadores conectados + mapa). Se actualiza solo (GameTracker recrawlea cada pocos minutos y la página lo refresca cada 5). Al tocar el banner se abre la página de estadísticas completas del servidor en GameTracker. Si algún servidor no aparece, hay que agregarlo (gratis) en gametracker.com → "Add server".
- **Minecraft:** el contador 🟢 X/Y usa la API pública de mcsrvstat.us y se refresca cada 2 minutos.

## Cómo funcionan los botones

- **▶ Jugar (CS 1.6):** abre `steam://connect/IP:PUERTO` → Steam inicia Counter-Strike 1.6 conectado a ese servidor. Si el jugador no usa Steam, puede copiar la IP y usar `connect IP:PUERTO` en la consola del juego.
- **▶ Agregar y jugar (Minecraft Bedrock):** abre `minecraft://?addExternalServer=...` → agrega el servidor automáticamente en Bedrock (celu/tablet/Windows).
- **Minecraft Java:** no existe un enlace estándar que abra el juego, por eso el botón copia la IP para pegarla en Multijugador → Agregar servidor.
- **Copiar IP:** cualquier IP se copia tocándola (o con el botón ⧉).

## Para editar servidores

La forma fácil (recomendada): editá `tools/servers.tsv` (una línea por servidor: `Nombre<TAB>IP:PUERTO`; las líneas que empiezan con `#` son los títulos de grupo) y después corré:

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File "tools/update_servers.ps1"
```

Eso regenera todo el listado de `index.html` automáticamente, con banners de GameTracker incluidos. La carpeta `tools/` no hace falta subirla al hosting.

A mano: cada servidor es un bloque `<article class="server-card ...">` en `index.html`; si lo editás directo, actualizá la IP **en los 4 lugares**: texto visible, `data-copy`, `href` del botón Jugar y las 2 URLs de GameTracker.
