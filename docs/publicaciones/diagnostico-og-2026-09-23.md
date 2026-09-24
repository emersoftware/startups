# Diagnóstico de las tarjetas de X — 23 de septiembre

## Evidencia

- Las 17 fichas del primer hilo y sus imágenes OG devolvieron HTTP 200. Los HTML publicados incluyen `twitter:card=summary_large_image`, URLs absolutas y dimensiones 1200 × 630.
- Se compararon Cardda, Fintoc y Reversso con User-Agent Twitterbot/1.0: mismo formato de metadatos, PNG RGBA de 1200 × 630, respuestas image/png. Esto por sí solo no prueba acceso desde X.
- El validador oficial, https://cards-dev.x.com/validator, sí estaba disponible en la sesión del usuario. Devolvió `Page fetched successfully`, 21 metatags, `summary_large_image` y `Card loaded successfully` para las fichas revisadas. El validador no muestra la imagen; remite al compositor.
- El compositor mostraba para Cardda una descripción del dataset anterior, diferente al HTML actual: evidencia de caché de una tarjeta antigua. Fintoc ya tenía tarjeta con imagen.
- Tras versionar URLs, validar y reabrir el borrador, aparecieron 14 tarjetas con imagen. Reversso, Brolly y Appio siguieron mostrando tarjetas de texto. Algunas vistas previas no persistieron al reabrir: no se declara el problema resuelto únicamente porque el validador termine bien.
- Se retiró el punto de “Profe.Social” en el texto de Salduu para evitar que X seleccione ese dominio como tarjeta del tweet.

## Corrección del sitio

Se preparó un postproceso `web/scripts/fingerprint-og.ts`: conserva los PNG anteriores, crea alias con SHA-256 del contenido y actualiza únicamente `og:image` y `twitter:image`. Se ejecuta al terminar el build de Astro y es idempotente.

La corrección de producción parte de una copia aislada del build publicado, no del timeline anterior del workspace Miami. Los 167 archivos originales se compararon byte por byte con producción antes del cambio: ninguna diferencia. Se verificó que los únicos cambios en las 82 páginas son las dos URLs de imagen; los datos, scripts, estilos y assets originales permanecen iguales. El resultado se guarda en `.context/og-release/` y la comparación final en `.context/og-live-verification.json`.

El hilo se mantiene sin publicar. Su copia editorial está en `hilo-1-preparado-x.md`; conserva la edición del usuario “Acá va una primera tirada”.

## Despliegue verificado

Versión anterior: `322ba72d-844e-4f29-899b-1d63500de004`. Versión publicada: `4cc76371-11e5-453e-ac39-8ea43f2c90cf`. Los 249 archivos finales coinciden byte por byte con producción. La segunda ejecución del postproceso cambió cero páginas (idempotencia).

Después del despliegue, Reversso y Brolly pasaron de tarjeta de texto a tarjeta con imagen al volver a rastrear la ficha con `?v=og2`. La captura de Reversso está en `.context/og-reversso-corregido.png`.

## Resultado observado al terminar

El borrador guardado conserva 19 tweets, el video de 26 segundos y todos los textos (comparación de los 19 textos ignorando versiones de URL y espacios). Tras una recarga completa de X, 16 de las 17 startups muestran tarjeta con imagen, además de la portada del enlace final. Appio permanece como tarjeta de texto: también falla en un compositor independiente, tanto con la URL versionada como con la canónica, aunque el validador oficial confirma la carga. Su PNG publicado se inspeccionó y es válido. No se da por resuelto ese último caso ni se atribuye una causa exacta sin registros internos de X.

El hilo está guardado y abierto para revisión, sin publicar. El cambio de infraestructura de OG está desplegado; los cambios de código del workspace siguen sin commit.

## Solución visual para Appio en el primer hilo

Ante la persistencia de la tarjeta de texto, se adjuntó el PNG OG publicado de Appio al tweet 17/19, conservando su enlace y su texto. Se agregó descripción accesible y X confirmó «Your draft was saved», con la imagen presente en el borrador. Esto evita el fallo de la tarjeta para este hilo; no se presenta como una reparación de la caché de X. No hubo despliegue ni publicación.
