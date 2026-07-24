# `data/`: generado por el pipeline (no versionado)

Esta carpeta contiene el dataset y los archivos de Wayback (~276 MB). **No se publica**
en el repo (está en `.gitignore`); se regenera corriendo el pipeline del `scraper/`.

## Qué vive acá (al regenerarlo)

- `identity.json`: por startup: `slug`, `names[]` (actuales/anteriores/codenames), cadena de `domains[]`, estado y `shutdown_basis`.
- `funding.json`, `startups.json`, `platanus.json`, `startupchile*.json`, `founders.csv`: datos crudos y consolidados de las fuentes.
- `wayback/<dominio>/`: capturas mensuales de cada landing (`AAAAMM.html` + `manifest.json` con `timestamp`, `wayback_url`, `title`, `description`).
- `wayback_platanus/<slug>/`: capturas mensuales del perfil del venture (la página que la startup edita).
- `pivots/`: salidas de los detectores de fase.
- `pivots_curated.json`: pivots/rebrands curados (entra a la línea de tiempo del sitio).
- `title_audit.json` / `TITLE_AUDIT.md`: reporte de auditoría de trayectorias.

El destino final es `web/src/data/timeline.json`, que **sí** vive en el repo (es lo que renderiza el sitio).

## Cómo regenerarlo

Ver el README de la raíz. En resumen: poblar identidad + dominios, archivar las superficies
desde Wayback, correr los detectores, curar y construir la línea de tiempo. La metodología
completa está en [`docs/METHODOLOGY.md`](../docs/METHODOLOGY.md).
