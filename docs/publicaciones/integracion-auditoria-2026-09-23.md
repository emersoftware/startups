# Integración de la auditoría terminada — 23 de septiembre de 2026

## Resultado local

82 finales PASS; 81 fichas públicas porque Fiscoclic sigue excluida. La revisión secuencial de Opus hizo de ejecutor y crítico en pasos separados: no se presenta como auditoría con crítico independiente. Fuente: `data/audit/REANUDACION_2026-09-23.md`.

Se copió el dataset a Miami y se incorporaron los archivos de proyección y agrupación mensual que ya usaba el proyecto original. No se editaron archivos en `/Users/emersoftware/Documents/projects/startups`. No se localizaron ADRs aceptados en los directorios de documentación revisados.

Se ejecutaron `build_pivots_curated.py`, `build_timeline.py`, las cinco pruebas de `test_audited_timeline.py` y `bun run build` en `web/`. Resultado: 81 fichas, 398 eventos, 0 sin fuente; Astro genera 83 páginas (81 fichas, portada y 404), y el postproceso versiona 82 imágenes OG. `git diff --check` pasa. Se inspeccionó Pulso Escolar en el navegador: tiene sus tres eventos y fuentes; las ampliaciones retiradas ya no son hitos. Captura: `.context/audit-integration/pulso-escolar-build.png`.

Comparación contra el timeline publicado antes de la integración: 355 → 398 eventos, **+43**, exactamente 15 trayectorias modificadas. El diff de Git es más amplio porque Miami partía de un commit anterior al sitio publicado: incluye la integración previa del proyector y la agrupación por mes. No confundir ambas bases.

| Ficha | Antes | Después |
|---|---:|---:|
| Saludtech | 1 | 7 |
| Pulso Escolar | 5 | 3 |
| Crema | 2 | 7 |
| Nodek | 1 | 4 |
| Plenti | 1 | 5 |
| Kambia | 1 | 8 |
| Pullpo | 1 | 3 |
| Kunzapp | 3 | 7 |
| Winston | 1 | 4 |
| Sendmage | 2 | 3 |
| Teambit | 1 | 2 |
| Frust | 1 | 5 |
| Grupalia | 2 | 4 |
| GOPA | 1 | 3 |
| Movana | 1 | 2 |

Los +43 son eventos de las fichas, no necesariamente 43 puntos adicionales: eventos del mismo mes se agrupan en un solo punto, conservando todas sus fuentes.

## Identidad

`python3 scraper/apply_identity_audit.py` aplica las propuestas de estado a la copia de `data/identity.json` de Miami. Es idempotente. El dataset está gitignorado; el script deja el cambio reproducible.

- Crema, GOPA, Nodek: `shutdown` / `inferred`, que el sitio presenta como «Sin señal», nunca como cierre confirmado.
- Manifest/Bloocks: cambia `shutdown_basis` de confirmed a inferred.
- Telaio/Lummy: inactividad inferida; se retira lummy.ai (empresa ajena), se agrega kapibara.cl.
- Trutix: shutdown / confirmed, con anuncio del CEO.
- SignatureAPI: active; Superposition Labs coexiste, no acredita un pivot.
- Sendmage: conserva shutdown / inferred y se registran las eras ajenas del dominio.
- Nodek: se agrega nodek.co como primer dominio, distinguiendo el redirect de 2021-12 del primer cuerpo de 2022-01.

No se aplicaron automáticamente todos los defectos históricos de dominios, financiación o fechas de IDENTITY_DEFECTS.md: este paso cubre los estados y las correcciones de dominio indicadas arriba. Los finales PASS no fueron reescritos.

## Revisión editorial transversal

La auditoría finalizó, pero su propio cierre conserva pendientes de consistencia entre generaciones de la rúbrica. El build reproduce fielmente los finales, no resuelve por sí mismo esos pendientes.

| Caso | Lectura del final | Decisión de copy |
|---|---|---|
| Cardda | 2024-05 se describe como expansión de gestión de gastos | Requiere adjudicar cambio de núcleo vs ampliación; primer hilo congelado |
| Fintoc | 2022-05 mantiene API, pero dice que deja de ser negocio principal | No basta buscar «suma» para eliminarlo; primer hilo congelado |
| Examedi | 2023-01 suma telemedicina al domicilio | Ampliación; primer hilo congelado |
| Toku | 2026-03 agrega agentes a pagos | Ampliación; el tweet existente no cuenta ese paso y queda intacto |
| Carvuk | 2023-03 agrega seguro y conserva servicios sueltos | Ampliación; primer hilo congelado |
| Vivvidero | 2022-08 suma obra gris; 2024-08 retira compra de usados | Distinguir adición de cambio de foco; primer hilo congelado |
| Appio/fudata | 2022-09 Fudata coexiste con Appio | No era reemplazo de Appio; primer hilo congelado |
| Sento | 2025-03 mismo núcleo, más canales | Segundo hilo dice ampliación de cobertura |
| ElCeroKm | 2025-03 agrega compra online; vía previa continúa | Segundo hilo distingue adición de compra y asesoría posterior |
| Calypso | Final rebrand por dominio calypso.day → calypso.ms; nombre igual | Segundo hilo narra cambio de dominio, sin inventar nombre nuevo |
| Taxflow | Final pivot: equipo cambia foco a Houston; Taxflow sigue disponible | Segundo hilo narra cambio de foco y coexistencia |

Quedan por adjudicar en los artefactos/proyección las ampliaciones marcadas como pivots, las 21 discrepancias de fechas de ingreso y las 9 fases Start-Up Chile fechadas por selección, documentadas en GAPS §36. No se desplegó este build.

## Hilos y menciones

Por instrucción del usuario: **tres hilos, 17 + 17 + 15 startups**; 19, 19 y 17 tweets contando apertura y cierre. `dos-hilos.md` conserva el nombre histórico, pero contiene los tres. El primero es una copia exacta del compositor, incluida su edición inicial y versiones de URL; no se modificó el borrador de X. Pulso Escolar va al tercero, sin @titog y sin narrar los dos hitos retirados. El tercero no incorpora menciones heredadas sin revisión.

Codex abrió los 49 perfiles propuestos en hilos 1/2 y guardó observaciones públicas en `.context/audit-integration/x-profiles-2026-09-23.json`. Esto verifica acceso y contenido de perfil, pero no sustituye una adjudicación independiente del vínculo de cada cuenta. Algunas bios no lo explicitan. Rigo conserva el vínculo a Fireflux y X en https://github.com/rigobcastro; Gabriel Aramburu identifica Calypso en https://garamburu.com. Ian Lee se presenta con Nexor; su relación con Examedi es histórica, no cargo actual.

El usuario pidió revisión independiente por Claude. Se inició una sesión de Claude Opus en segundo plano, con encargo de lectura y cobertura de las 49 startups, incluyendo búsqueda de menciones para el tercer hilo. Prompt: `.context/claude-x-review/PROMPT.md`; sesión `252484ac-4def-4bb4-9316-95504b6db655`. No debe editar el primer hilo, publicar, contactar personas ni conectar servicios. Resultado aún pendiente.

Nada de esta integración fue publicado en X; hilos 2 y 3 siguen en Markdown. La corrección anterior de caché OG sí estaba desplegada antes de este trabajo y es independiente de este nuevo build.
