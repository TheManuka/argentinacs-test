# Robot de la tienda de Minecraft

Revisa **una vez por día** si cambiaron los productos o los precios en la planilla
y actualiza solo lo que haga falta. Corre en los servidores de GitHub, así que
funciona con la computadora apagada.

## Qué hace, en orden

1. Lee el catálogo de la planilla (código, título y precio de cada producto).
2. Actualiza el **catálogo del sitio web** (la lista de la página de Minecraft), con el precio de cada producto.
3. Actualiza el **precio del VIP de Minecraft** en `vip.html` (la página de contratar VIP).
4. Actualiza el **menú `/compras` del servidor** por SFTP, con precios nuevos.
5. Si cambió algo del sitio, hace **push a `main`**.

Si no cambió nada, no toca absolutamente nada y termina sin hacer ruido.

**Horario:** 04:20 de Argentina, justo antes del reinicio diario del servidor
(04:59). Así el menú nuevo se carga solo cuando el servidor reinicia — no hace
falta que nadie ejecute `/ce reload`.

## Archivos

| Archivo | Para qué |
|---|---|
| `.github/workflows/tienda.yml` | El horario y los permisos |
| `tools/sync_tienda.py` | Toda la lógica |
| `tools/tienda_meta.json` | Cómo se presenta cada producto (grupo, nombre y descripción) |

> ⚠️ **No editar a mano** el bloque `<div class="catalogo">` de `servidor-minecraft-survival.html`
> ni el precio marcado con `data-precio="vip"` en `vip.html`: los reescribe el robot en cada corrida.

## Qué hay que configurar (una sola vez)

En el repositorio: **Settings → Secrets and variables → Actions → New secret**

| Nombre | Valor |
|---|---|
| `TIENDA_CSV_URL` | La dirección CSV de la hoja *Minecraft sv1* de la planilla |
| `MC_SFTP_USER` | Usuario del SFTP del servidor de Minecraft |
| `MC_SFTP_PASS` | Contraseña del SFTP |

Para obtener `TIENDA_CSV_URL`: en la planilla, **Archivo → Compartir → Publicar
en la web** → elegir la hoja *Minecraft sv1* → formato **CSV** → Publicar.
El documento sigue siendo privado; solo esa hoja queda accesible por esa dirección.

**Sin esos datos el robot no hace nada** (termina avisando y no toca ni el sitio
ni el servidor), así que es seguro dejarlo instalado antes de configurarlo.

## Cuando agregues un producto nuevo

El robot lo publica igual, en un grupo llamado "Otros", y deja un aviso en el
registro de ejecución. Para que salga en su grupo correcto y con su descripción,
hay que sumarlo a `tools/tienda_meta.json`.

## Cuidados que ya tiene

Antes de tocar el servidor, el robot verifica que:

- la planilla haya devuelto al menos 5 productos (si devuelve menos, aborta: puede
  estar mal publicada);
- el archivo del servidor haya bajado completo;
- el archivo resultante sea un YAML válido;
- sigan estando los otros eventos del servidor (los del End, la limpieza de
  protecciones, el menú `/vip`);
- el tamaño no cambie más de un 15%.

Además **guarda una copia de respaldo** del archivo original en el servidor
(`backup-more_events-FECHA.yml.bak`) y, después de subir, **vuelve a descargarlo
para confirmar** que quedó exactamente como debía. Si algo no cierra, no sube nada.
