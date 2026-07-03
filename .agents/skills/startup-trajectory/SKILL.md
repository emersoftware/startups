---
name: startup-trajectory
description: El método reutilizable para reconstruir la trayectoria real de una startup (pivots, rebrands, cierres) desde el archivo web + heurísticas + websearch y llevarla, ya verificada y en lenguaje de producto, a los datos de un sitio. Sirve para auditar/datar/corregir cómo evolucionó una startup y para traspasar el mismo proceso a OTROS portafolios o ventures (no solo este dataset). Úsalo cuando haya que mapear una trayectoria, auditar si está bien capturada, o agregar un pivot/rebrand/cierre con su fuente.
metadata:
  type: project
  version: "2.0"
---

# Reconstruir la trayectoria de una startup

Objetivo: pasar de "snapshots crudos del archivo web" a "una línea de tiempo de fases
**verificada**, cada evento con `source_url`, escrita en **lenguaje de producto**". Sin inventar.

**Principio rector:** la secuencia de **contenido archivado** de una startup (landing + el
perfil que ella misma mantiene) es, casi literalmente, el registro de fases de su producto.
El método lo hace explícito, lo cruza entre fuentes y lo verifica leyendo el **cuerpo completo**.

Este archivo es el camino limpio y reutilizable. Detalle extendido + casos en `docs/METHODOLOGY.md`.

> **Reutilización (lee esto si lo aplicas a otro venture/portafolio):** el método es agnóstico;
> lo específico de este dataset son los paths/scripts. Para un portafolio nuevo cambia solo
> **dos entradas** y reusa todo lo demás: (1) la **cadena de dominios** de cada startup, y
> (2) el **patrón de URL del "perfil del venture"** que la startup edita (aquí es
> `platan.us/startups/<slug>`; en otro caso será el portfolio page de la aceleradora, el
> directorio del fondo, Crunchbase/LinkedIn company, etc.). Ver "Aplicarlo a otro venture" abajo.

---

## El camino (7 pasos)

### 1. Identidad → cadena de dominios
Punto de partida: `data/identity.json`. Cada startup tiene `slug`, todos sus `names[]`
(actuales, anteriores, codenames) y su cadena de `domains[]` en orden cronológico. Si la
cadena está incompleta, **estírala primero** (websearch + CDX del archivo web) antes de datar
fases. Un nombre/codename distinto del actual ya es señal de rebrand. **Cuidado:** un dominio
puede arrastrar historia de un **dueño anterior** (otra empresa, página estacionada, idioma
ajeno) — eso NO es la startup y no debe entrar como fase.

### 2. Archivar las superficies (archivo web)
Dos superficies de primera mano, ambas mensuales:
- **Landings** de cada era de marca → `data/wayback/<dom>/` (`wayback_archive.py`,
  `wayback_archive_chains.py`). La landing **LIDERA** los cambios de producto.
- **Perfil del venture** (la página que la propia startup mantiene en el directorio del
  acelerador/fondo) → `data/wayback_platanus/<slug>/` (`wayback_archive_platanus.py`). Es señal
  de primera mano pero suele **REZAGAR** la landing.

Cada `manifest.json` guarda por mes: `timestamp`, `wayback_url`, `title`, `description`.
El archivo web rate-limitea fuerte (~10–15 s/dominio): respétalo.

### 3. Detectar fases (heurística — INTERNA, nunca se muestra)
- **Primaria — title timeline:** `title_timeline_audit.py` une landings ∪ perfil, normaliza
  cada título a su *tagline*, comprime meses iguales en **fases** con rango de fechas y
  `wayback_url`, y marca `FLAG` cuando hay más transiciones que pivots ya curados → trayectoria
  sub-capturada. Salidas: `data/title_audit.json`, `data/TITLE_AUDIT.md`. El FLAG es señal de
  **revisar**, no de "curar todo": casi siempre sobre-cuenta (iteración de marketing + ruido de
  dueño anterior).
- **Secundaria — contenido:** cuando el título es "pelado" (solo la marca), el posicionamiento
  vive en el **cuerpo**. `platanus_profile_changes.py` / `pivot_detect_stitched.py` vectorizan
  el texto visible (TF-IDF coseno) para no quedar ciego a esos casos.

### 4. Juzgar (las reglas)
1. **Fase ≠ cada string de título.** Agrupa la iteración de marketing; cuenta fases con
   significado para el usuario, no rewordings del mismo producto.
2. **El título solo DETECTA; el CUERPO COMPLETO PRUEBA.** Nunca cures desde el hero/título/
   `description`: lee el `visible_text` ENTERO del snapshot (`data/wayback/<dom>/<AAAAMM>.html`).
   **El título miente seguido** y eso fabrica pivots inexistentes (ver "Modos de falla"). Si el
   body no confirma un cambio REAL de producto, NO hay pivot.
3. **Datación: gana la señal más temprana.** La landing lidera, el perfil rezaga; toma el primer
   indicio entre todas las superficies (datar por el perfil puede errar meses).
4. **Título pelado → leer el cuerpo** (caso particular de la regla 2).
5. **La FUNDACIÓN describe el producto ORIGINAL**, nunca el actual. Los cambios van en los pivots.
6. **El tip vivo casi siempre requiere websearch:** la última fase puede post-datar el último
   snapshot o vivir en un dominio nuevo. Confirma el producto actual en el sitio vivo + prensa.
7. **Verificabilidad gana siempre** (ver paso 6).
8. **Rebrand vs pivot.** Cambió nombre/dominio = `rebrand`. Mismo nombre, producto nuevo = `pivot`.

### 5. Websearch del estado vivo y de las fuentes datadas
Confirma el producto actual (sitio vivo + prensa) y consigue una **fuente datada** (URL + fecha)
para cada fase: snapshot, paper, Demo Day, prensa, registro. El relato de un fundador o tercero
es **PISTA, no fuente** — y suele venir con su propia incertidumbre.

### 6. Disciplina de verificabilidad (no negociable)
- Default = "no hubo cambio". Solo se afirma pivot/rebrand/cierre **con evidencia en el body**.
- Cada evento necesita `source_url`. Sin fuente datable → **nota/gap honesto**, nunca fecha inventada.
- Cierre **confirmado** (prensa/fundadores/registro) ≠ **inferido** (solo cayó el dominio): el
  inferido se marca como sospecha (`shutdown_basis` en `identity.json`), no como hecho.
- El display name no se cambia salvo decisión explícita; los nombres viejos quedan como alias buscables.

### 7. Llevarlo a los datos y al sitio
- Pivots/rebrands curados → `CURATED` en `build_pivots_curated.py` (resuelve el `wayback_url`
  exacto; `domain` puede ser `profile:<slug>` para el perfil del venture). Correcciones de
  fundación/capital/cierre → `CORRECTIONS` en `build_timeline.py`, clave `(name, type, date)`.
- Regenerar y construir:
  ```
  cd scraper && uv run python build_pivots_curated.py && uv run python build_timeline.py
  cd ../web && bunx astro build
  ```
- `build_timeline.py` garantiza por construcción que **cada evento lleve `source_url`**. Verifica
  que el conteo "eventos SIN source_url" sea 0.

---

## Cómo se escribe y qué se muestra (reglas de presentación)

1. **Prosa ORIENTADA A PRODUCTO, no al hero.** Di **qué hace el producto, para quién y qué
   reemplaza** — no el copy de marketing. **Nunca cites el slogan entre comillas** (p. ej. 'tu
   aliado para X', 'IA para todos', 'revoluciona tu Y…'): si lo citas, es que curaste desde el
   hero en vez de leer el body (regla 2). Las analogías comparativas SÍ ('el Duolingo de Z', 'el
   ChatGPT de W') cuando describen el producto, porque no son copy.
2. **No uses la palabra "cheque".** Para la inversión del programa: "inversión inicial / estándar
   (~US$X)".
3. **Oculta la metodología del SITIO.** La heurística (TF-IDF, "variación mes a mes", "Wayback")
   NO se menciona en lo que ve el usuario — va a un **blog de metodología** aparte. En el front:
   - El label del chip de fuente es **`<dominio> · <mes>`** (o `<Venture> · <mes>` para el perfil),
     no "Wayback · …". El chip igual ENLAZA al snapshot como fuente (link `target="_blank"` con ↗).
   - El `basis` (tooltip) va **vacío** en pivots.
   - Nada de "Pivot · Wayback", ni notas de heurística en el pie.
   - La metodología SIGUE viva en esta skill y en `docs/METHODOLOGY.md` (son la semilla del blog),
     solo se oculta del sitio renderizado.

---

## Modos de falla (lecciones caras — revísalas antes de afirmar un pivot)

- **El título mintió → pivot fabricado.** Caso real: el `<title>`/`<meta>` vendía un propósito
  aspiracional ("empodera tu vida") sobre un body que YA era B2B desde el primer snapshot. Curado
  desde el hero = pivot consumer→B2B inexistente. Leer el body lo mató. **Siempre lee el cuerpo.**
- **Buzzword ≠ pivot.** Caso real: el hero cambió a un nuevo eslogan de marketing, pero el body ya
  ofrecía ese mismo posicionamiento un año antes → reposicionamiento, no pivot (regla 1).
- **Ruido de dueño anterior.** Dominios con historia de otra empresa (idioma ajeno, "for sale",
  "create-react-app", placeholders) inflan el FLAG y NO son fases de la startup.
- **El perfil rezaga.** Si dataste por el perfil del venture y no por la landing, probablemente
  erraste la fecha por meses.
- **Sub-captura por defecto.** El sesgo histórico fue anotar ~1 pivot cuando había 3–4 fases, y
  describir la fundación con el producto ACTUAL. El title-timeline existe para atrapar justo eso.

---

## Cierre de calidad (antes de dar por hecho)

Cada fase reconstruida debe tener: (a) una transición en el title timeline, (b) **contenido del
body** del snapshot que la confirme, y (c) para el tip vivo, websearch del estado actual. La que
no cumpla las tres se **marca**, no se afirma. Verificaciones finales:
- `eventos SIN source_url` == 0 (lo imprime `build_timeline.py`).
- En el HTML construido: **0** ocurrencias visibles de "cheque", "Wayback", "TF-IDF", "coseno"
  (`grep -oi … web/dist/index.html | wc -l`).
- Idealmente, un fact-check final cruza cada evento contra su `source_url`.

---

## Aplicarlo a OTRO venture / portafolio (generalización)

El método transfiere; reusa los mismos scripts cambiando dos entradas:

1. **Lista de startups + cadenas de dominio** del nuevo portafolio → poblar `identity.json`
   (slug, names[], domains[] en orden). Misma estructura.
2. **El "perfil del venture"**: identifica la página que la startup mantiene en el directorio del
   acelerador/fondo (el equivalente a `platan.us/startups/<slug>`). Ajusta el patrón de URL en
   `wayback_archive_platanus.py`. Si ese venture no tiene perfil propio, usa el sustituto más
   cercano que la startup edite (Crunchbase, LinkedIn company, el portfolio page del fondo) — sigue
   siendo "señal de primera mano que rezaga".

Luego corre el mismo pipeline: archivar superficies → `title_timeline_audit.py` (FLAG) → curar con
las 8 reglas leyendo el **body** → `build_pivots_curated.py` + `build_timeline.py` → build. Las
**reglas, los modos de falla y las reglas de presentación son universales** — no dependen del venture.

## Orquestación con subagentes (recopilación paralela, juicio centralizado)

El pipeline tiene partes **independientes por startup** (pasos 1 y 5: estirar cadenas de
dominios, websearch del estado vivo) que son lentas y triviales. Delegarlas a subagentes en
paralelo (fan-out, 1 por startup) acelera mucho. Pero el **juicio curatorial — las 8 reglas
del paso 4 — NUNCA se delega**: el orquestador aplica las reglas sobre lo que los subagentes
devuelven. Delegar juicio es justo lo que fabrica pivots inexistentes (ver "Modos de falla").

### Cuándo usar subagentes y cuál tipo

| Paso | ¿Delegar? | Tipo | Por qué |
|------|-----------|------|---------|
| 1. Identidad → dominios | **Sí** | `general-purpose` | Websearch + CDX del archivo web, 1 por startup |
| 2. Archivar superficies | Paraleliza *entre startups*, no entre dominios (el rate-limit del archivo web es global) | `Bash` directo | Es llamar a scripts |
| 3. Detectar fases | No | — | `Bash` corre los scripts |
| 4. Juzgar (8 reglas) | **No** | — | Juicio central del orquestador |
| 5. Websearch vivo + fuentes | **Sí** | `general-purpose` | Gathering puro, 1 por startup |
| 6. Verificabilidad | No | — | Juicio |
| 7. Datos + build | No | — | Edición de `CURATED`/`CORRECTIONS` |

Y dentro del paso 4, cuando hace falta **confirmar un pivot leyendo el cuerpo del snapshot**,
se puede delegar el *hallazgo* (no el juicio) a un subagent `Explore` que grepee el `visible_text`
de `data/wayback/<dom>/<AAAAMM>.html`. El orquestador lee su reporte y decide.

### Regla anti-fabulación (no negociable al delegar)

Un subagent devuelve texto. Si entrega **paráfrasis** en vez de URLs datadas + cita textual del
body + fecha, perdemos verificabilidad — que es justo lo que cuida el paso 6. Todo subagent de
recopilación debe recibir esta consigna explícita en su prompt de lanzamiento:

> Devuelve, por cada fase/cambio que reportes: (a) la **URL datada** (snapshot, paper, prensa),
> (b) una **cita textual corta** del body que lo confirma (entre comillas, en el idioma original),
> (c) la **fecha**. **No resumas ni interpretes** — no digas "pivotearon a B2B"; cita el fragmento
> que lo muestra. Si no encuentras evidencia en el body, di "sin evidencia en el body" — no inventes.

Sin esa consigna, un subagent entusiasta fabrica un pivot.

### Plantilla de lanzamiento (fan-out por startup)

Lanza en un solo mensaje N subagentes (uno por startup) — el padre espera a todos y consolida:

```
Para cada startup S del portafolio, lanza en paralelo:

[general-purpose] "Investiga la startup S (dominios: D1, D2, …). Para cada fase de su
 trayectoria devuelve: URL datada + cita textual del body + fecha. Cubre: fundación, levantamientos
 de capital, pivots de producto, rebrand, adquisición, cierre. Regla anti-fabulación: sin
 evidencia en el body → 'sin evidencia', no inventes. Estado vivo confírmalo en el sitio actual
 + prensa reciente."
```

Tras consolidar, el orquestador aplica las 8 reglas y escribe `CURATED`/`CORRECTIONS`. Los
subagentes no tocan datos ni build.

### Subagentes custom (opcional, upgrade)

Los built-in (`Explore`, `general-purpose`) bastan. Si quieres identidad propia + tools
restringidos (p. ej. un `wayback-gatherer` que solo tenga WebSearch+WebFetch, o un `body-reader`
read-only), eso se crea desde **ZCode → Settings → Subagents (Beta)** (no vía archivo en disco,
a diferencia de las skills). Recetas listas para pegar ahí en `references/subagents-recipes.md`.

## Convención de runtime
Bun para JS/TS, `uv run python` para los scripts del scraper. Los scripts de scraping corren desde `scraper/`.
