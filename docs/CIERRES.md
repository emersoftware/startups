# Última revisión de cada ficha

Los hitos y el estado auditado siguen en `web/src/data/timeline.json`. La edición
para lectura está en `web/src/data/closings.json`, por slug, y se muestra con
`ClosingSummary.astro` al final del relato cronológico.

- `reviewed_on` conserva la fecha de la auditoría; no es la fecha de edición del texto.
  Si la ficha no registra una fecha, se muestra «Descripción documentada» sin inventarla.
- `summary` explica lo esencial que completa el último hito, en uno o dos párrafos.
- `details` conserva cifras, condiciones e integraciones secundarias. Puede estar vacío
  si la descripción es breve; en ese caso no se muestra el desplegable.
- Cada párrafo incluye sus fuentes. Una observación sin fuente pública se identifica
  con `basis`, sin inventar un enlace.
- Se pueden evitar repeticiones de hechos que ya están visibles en los hitos. No se
  deben perder datos, convertir planes en resultados ni interpretar un dominio caído
  como prueba de cierre. Las cifras comerciales se atribuyen a la empresa.

Al incorporar una ficha o cambiar su fecha de auditoría, hay que revisar también su
cierre. El build falla si falta el cierre o su fecha no coincide con la ficha.

El parentesco de un spin-off y la continuidad de ambas plataformas se conservan en
`lineage`; no se reescriben como un cambio de nombre o el reemplazo de la matriz.

## Build y tarjetas sociales

Ejecutar `bun run build` dentro de `web/`. Además de generar las páginas y las imágenes
OG, calcula una URL con huella de contenido para cada PNG y actualiza `og:image` y
`twitter:image`. El paso está integrado en Astro y también corre al usar `astro build`
directamente. Así, una corrección del gráfico produce una nueva URL de imagen.
Los PNG de `web/dist/` se generan en el build; no se versionan. Deben desplegarse junto
con las páginas del mismo build, incluidos los OG con y sin huella.
