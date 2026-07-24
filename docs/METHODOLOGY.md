# Cómo reconstruir bien la trayectoria de una startup

> Escrito tras descubrir que los 3 casos que el fundador conoce de cerca (Blar, Gokei, Kapso)
> estaban mal o incompletos. Si fallamos en 3/3 conocidos, fallamos en muchos más. Esto
> documenta el método correcto **y** el motor que lo hace reproducible sobre las 82.

## El bug sistémico que teníamos

1. **Un pivot por startup.** La curación previa anotaba ~1 pivot cuando las trayectorias reales
   tienen 3–4 fases. Ejemplo: Blar tenía *un* pivot ("bugs → deuda técnica") cuando en realidad
   recorrió NL2SQL → grafo de código/bugs → deuda técnica → **soporte/onboarding con IA** (este
   último, el actual, no estaba).
2. **La fundación quedó descrita con el producto ACTUAL, no el original.** Las tres fundaciones
   decían lo que la startup es HOY:
   - Blar "self-healing codebases" → en realidad nació como NL2SQL ("ChatGPT para datos financieros").
   - Gokei "reembolsos vía WhatsApp" → nació como app amplia de salud / seguro complementario.
   - Kapso "WhatsApp for developers" → nació como personal training online (fitness + IA).
3. **El rebrand/última fase no se capturaba** cuando ocurría en un dominio nuevo o después del
   último snapshot (Gokei→Skip en getskip.ai; Blar onboarding-agent solo en el sitio vivo).

## El insight: la secuencia de TÍTULOS archivados ya cuenta toda la historia

Ya teníamos, gratis, en cada `manifest.json` el `title` (y `description`) de cada captura mensual.
La **secuencia de títulos** de una landing es prácticamente el registro de fases del producto:

```
blar.io: Repo Retrieval (04-24) → Root Cause of Bugs (07-24) → Technical debt (11-24)
         → Empower Customer Support with AI (10-25) → Revoluciona tu soporte… (12-25)
```

Cada cambio de título normalizado = candidato a cambio de fase. Lo único que faltaba era
**usarlo de forma sistemática** en vez de curar a ojo.

## El motor: `scraper/title_timeline_audit.py`

- Para cada startup une las superficies: **landings** (`data/wayback/<dom>/`) ∪ **perfil Platanus**
  (`data/wayback_platanus/<slug>/`).
- Normaliza cada título a su *tagline* (quita la marca y el chrome de Platanus), comprime meses
  consecutivos iguales en **fases** con rango de fechas y su `wayback_url`.
- Compara nº de transiciones de tagline vs nº de pivots curados. `FLAG` = más transiciones que
  pivots → trayectoria probablemente sub-capturada.
- Salidas: `data/title_audit.json` (estructurado, con `wayback_url` por fase) y `data/TITLE_AUDIT.md`
  (legible para curar). Corrida inicial: **63/82 marcadas.**

**Validación (prueba sobre verdad conocida):** sin alimentarle nada, el motor reprodujo las 4 fases
de Blar (incl. el soporte/onboarding faltante), el angostamiento de Gokei a reembolsos + el rebrand
a Skip, y el destino de Kapso. Eso prueba que el método habría atrapado los 3 errores.

## Las 8 reglas de curación

1. **Fase ≠ cada string de título.** Agrupa la iteración de marketing. "Repo Retrieval" →
   "Tech Stack of your Enterprise" → "Your Entire Tech Stack" es UNA fase (mismo producto, copy
   distinto), no tres. Apunta a fases con significado para el usuario (Blar ≈ 4).
2. **El título SOLO detecta; el CUERPO COMPLETO es la evidencia.** Nunca cures desde el hero,
   el `<title>` ni la `description`: lee el `visible_text` ENTERO del snapshot. Casos reales que
   lo prueban: **Horizon** tenía un `<title>`/`<meta>` viejo ("Empower your life / life purpose")
   sobre un body que ya era B2B ("AI business analyst for companies"): el título mentía y casi
   datamos un pivot consumer→B2B inexistente. **Appio** cambió el hero a "flota de repartidores"
   pero el body ya ofrecía "repartidores ilimitados" un año antes; buzzword, no pivot. Si el body
   no confirma un cambio real de producto, NO hay pivot (regla 1).
3. **Datación: gana la señal más temprana; la landing LIDERA, el perfil REZAGA.** Kapso: el perfil
   decía "strength training" hasta ago-2025 mientras kapso.ai ya decía "WhatsApp" en mar-2025. Datar
   por el perfil habría errado el pivot por ~10 meses. Toma el primer indicio entre todas las superficies.
4. **Título "pelado" (solo marca) esconde el posicionamiento en el CUERPO.** El perfil de Kapso era
   "Platanus | Kapso" sin slogan; el "personal training" estaba en el body. Si el título no tiene
   tagline, lee el texto visible / `description` (o usa `platanus_profile_changes.py`, que vectoriza
   el cuerpo completo). El motor de títulos por sí solo es ciego a esto.
5. **La FUNDACIÓN describe el producto ORIGINAL** (evidencia más temprana: primer snapshot, paper,
   Demo Day, prensa de lanzamiento), nunca el actual. Los cambios van en los pivots.
6. **La última fase (el "tip" vivo) casi siempre requiere websearch.** Puede post-datar el último
   snapshot o vivir en un dominio nuevo. Confirma el producto actual en el sitio vivo + prensa
   (Blar = agente de onboarding dentro del producto; Gokei = Skip "atiéndete ahora, paga después").
7. **Verificabilidad gana siempre.** El relato del fundador es una PISTA, no una fuente, y suele venir
   con su propia incertidumbre. Cada fase necesita `source_url` (snapshot, paper o prensa con fecha).
   Si una época no tiene fuente datable (p.ej. el pitch 2023 pre-snapshots de Gokei), **se deja como
   nota/gap honesto, no se inventa una fecha.**
8. **Rebrand vs pivot.** Cambio de nombre/dominio = `rebrand` (chip apunta al snapshot del nuevo brand).
   Mismo nombre, producto nuevo = `pivot`. El display name se mantiene salvo decisión explícita
   (Gokei sigue como display aunque hoy sea Skip; Skip queda como alias buscable).

## Lenguaje de la prosa y qué se muestra en el sitio

- **Orientada a producto, no al hero.** La prosa dice qué hace el producto, para quién y qué
  reemplaza. **Nunca** cites el slogan de marketing entre comillas ('your ally in mastering
  technical debt', 'AI for the people', 'Revoluciona tu soporte…'): si lo estás citando, es que
  curaste desde el hero en vez de leer el body (regla 2). Nombres/analogías reales sí ('Duolingo
  para programar', 'ChatGPT para datos financieros') porque describen el producto.
- **Sin "cheque".** Para la inversión del programa usa "inversión inicial / estándar (~US$X)".
- **Oculta la metodología del sitio.** La heurística (TF-IDF, variación mes a mes, "Wayback")
  NO se menciona en lo que ve el usuario: el label del chip es `<dominio> · <mes>` y el `basis`
  (tooltip) va vacío en pivots. La metodología vive en este doc y en la skill (semilla del blog
  de metodología), no en el sitio renderizado. El chip igual ENLAZA al snapshot como fuente.

## Flujo para re-curar el resto

```
cd scraper
uv run python title_timeline_audit.py          # regenera el FLAG report
# Para cada startup marcada: lee data/TITLE_AUDIT.md (fases + wayback_url ya resueltos),
# aplica las 8 reglas, y agrega/edita entradas en build_pivots_curated.py (CURATED) y,
# si la fundación está mal, en CORRECTIONS de build_timeline.py.
uv run python build_pivots_curated.py && uv run python build_timeline.py
cd ../web && bunx astro build
```

Curar = "escribir la prosa de un candidato ya fuenteado" (el `wayback_url` viene en el report),
no redescubrir desde cero. Eso hace tratable las ~60 restantes; conviene hacerlo con un fan-out de
subagentes (lotes de ~6) que aplican las reglas 1–8 con disciplina de verificabilidad y emiten
entradas candidatas, que luego se revisan y mergean.
