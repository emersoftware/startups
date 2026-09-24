# Reanudación de auditorías — 23 de septiembre de 2026

Revisión secuencial en una sola sesión (Opus 5.5), sin subagentes. El mismo modelo hizo de ejecutor y de crítico, en pasos separados que releen las fuentes desde disco. Cada `tick-N-critic.json` lo declara en `review_mode`: **no es un crítico independiente**.

Flujo usado: ejecutor → `tools/check.py` (precheck) → crítico con la rúbrica vigente (R1-R48 de `.claude/agents/trajectory-critic.md` y `briefs/_CRITICO.md`) → corrección cuando hubo RETRY → `tools/merge_final.py` con `MERGE_SKIP_CORRECTIONS=1` → `tools/validate_projection.py` (apply_audits sobre una copia del timeline desplegado, sin escribir). No se corrieron `build_pivots_curated.py` ni `build_timeline.py`, ni se desplegó nada.

## Conteo reconciliado

| | |
|---|---|
| Startups investigadas (identity.json) | 82 |
| Con `final.json` PASS | 82 (antes de hoy: 68) |
| PASS con una revisión posterior contraria | 0 (antes: Pulso Escolar) |
| En el sitio público (sin Fiscoclic, excluida por el usuario) | 81 |
| Proyección de los finales sobre el timeline desplegado | 81 de 81 «revisada»; 398 eventos (hoy publicados: 355), todos con fuente |
| Lote de las 40 (QUEUE40.json) | 40/40 PASS |

Casos especiales que no cambian el conteo: **Plutto** tiene final PASS, pero está en reserva editorial por un posible cierre no corroborado: no se declara cerrada. **Fiscoclic** tiene final PASS, pero está fuera del sitio y de los hilos. **Divisso** tiene final PASS en t1 y un pulido t2 sin crítico (no bloquea). Seis startups conservan su `HUMAN_REVIEW.md` histórico junto a un final PASS posterior (repartes, larnu, watermelon-tools, payhaus, fraccional y plutto).

## Las 14 pendientes y Pulso Escolar

«Auditoría del contenido terminada» significa final PASS con la evidencia en disco. «Lista para un hilo de X» exige además copy de tweet revisado contra el final, menciones verificadas hoy y el sitio reconstruido. Ninguna de las 15 cumple eso todavía (ver la última columna).

| startup | resultado | correcciones antes del PASS | eventos (proyección) | evidencia principal | pendientes reales | ¿lista para hilo? |
|---|---|---|---|---|---|---|
| Crema | PASS t2 | t1 PASS con 3 PC; t2 aplica los dos corregibles (cota del pivot 2022-12, descarte de la postulación a YC) | 2 → 7: fundación 2021-08, Platanus 2022-2, pivot 2022-12 (cuenta sin fronteras), RevTech 2023-08, Techstars NYC 2024-03, pivot 2025-10 (gestión de proyectos), inactiva 2026-09 | portadas crema.cm 2021-2026; WRAL; comunicado Techstars; whois/DNS del 2026-09-23 | identity.json a «sin señal reciente» | No: no está en dos-hilos.md; sin copy |
| Frust | PASS t2 | t1 RETRY: producto al ingreso sin fuente (frust.co registrado el 2023-11-07); BIG 12 fechada por selección | 1 → 5: Platanus 2023-08, inicio documentado 2024-05, ChileMass 2025-06, Endeavor 2026-04, SUC Ignite 2026-09 | registro de Platanus; portadas frust.co; comunicado de inicio de BIG 12 del 2026-09-17 | captura archivada de la nota de BIG 12 (hoy solo copia viva) | No |
| GOPA | PASS t1 | — | 1 → 3: Platanus 2024-02, inicio documentado 2024-05, pivot 2024-05 (reporte crediticio), inactiva sin fecha | gopa.mx 2024-05; DF y blog de Platanus (mayo 2024); whois.mx del 2026-09-23 | identity.json a «sin señal reciente» | No |
| Grupalia | PASS t2 | t1 RETRY: la fundación usaba el flujo de 2024-10 (asesor, OXXO) | 2 → 4: fundación 2023-11, Platanus 2024-02, seed US$4,8M 2025-09, seed US$7,7M 2026-04 | bundle de creditogrupalia.com; DF; notas propias de las rondas | funding.json (rondas y fechas) | No |
| Kunzapp | PASS t2 | t1 RETRY: «versión inicial» con funciones de 2023-09; BIG 11 fechada por selección | 3 → 7: fundación 2023-01, Platanus 2023-03, pre-seed US$750K 2023-09, Emprelatam 2023-09, Endeavor 2025-04, seed US$2M 2025-08, SUC Ignite 2026-03 | DF MAS; Contxto; La Tercera (inicio BIG 11 del 2026-03-18) | — | No |
| Plenti | PASS t3 | t1 RETRY (fundación por residuo); t2 aplicó 8 instrucciones y quedó en RETRY solo por falta de título en la ronda de amigos y familia | 1 → 5: fundación 2022-05, pivot 2022-07 (billetera en dólares), F&F 2023-05, Platanus 2023-05, seed US$3M 2026-09 | registro mercantil; El Espectador; Forbes | — | No |
| Saludtech | PASS t3 | t1 y t2 RETRY (fechas de programas por inicio de cohorte) | 1 → 7: fundación 2020-04, pivot 2020-05, Imagine G14 2022-06, SUC BIG4 2022-09, Platanus 2022-2, AntofaEmprende 2022-09, ángeles 2023-02 | Imagine, Corfo/T13, AntofaEmprende | — | No |
| Kambia | PASS t3 | t1 RETRY (logo de Babson sin adjudicar y 11 no bloqueantes); t2 halló un producto de 2022 y quedó RETRY por afirmar un abandono sin fuente | 1 → 8: fundación 2022-07 (retiros de efectivo), pivot 2023-02 (crédito por WhatsApp), Platanus 2023-03, StartUp Perú 9G 2023-05, Krealo 2023-10 y 2023-12, pivot 2025-10 (cooperativas), pivot 2026-01 (cobranza) | publicación de LinkedIn del cofundador del 2022-08-30; Startups Latam; Forbes Perú; ProInnóvate; perfiles de Platanus | Babson College = hueco de búsqueda declarado; captura archivada de la publicación de 2022; título de la fase Krealo 2023-12 igual al de 2023-10 | No |
| Movana | PASS t2 | t1 RETRY: atribuía al Demo Day la descripción del perfil | 1 → 2: Platanus 2024-07, inicio documentado 2024-09 | captura de movana.io del 2024-09-29 (fuera del manifest); post del Demo Day del 2024-10-29 | sitio con error TLS el 2026-09-23 (dos verificaciones): re-verificar; pista «Motores Regios» sin resolver | No |
| Nodek | PASS t1 | — | 1 → 4: fundación 2022-01 (mayorista), Platanus 2023-03, pivot 2024-04 (marcas de nicho), inactiva 2026-09 | nodek.co (dominio que faltaba en identity.json); nodekbrands.com; whois | identity.json: agregar nodek.co y pasar a sin señal | No |
| Pullpo | PASS t2 | t1 RETRY: ancla de notes mal atribuida | 1 → 3: fundación 2022-08, Platanus 2023-03, pivot 2023-06 (métricas de desarrollo) | portada 2022-08; chunk JS de la ruta '/' del 2023-03-31 y del 2023-06-28 con su router; El Referente | — | No |
| Sendmage | PASS t1 | — | 2 → 3: Platanus 2023-08, inicio documentado 2023-11, inactiva 2025-11 | sendmage.com 2023-11; post del Demo Day; whois (registro nuevo del 2025-11-07); bio de X del cofundador (2026-09-11) | — | No |
| Teambit | PASS t1 | — | 1 → 2: Platanus 2023-08, inicio documentado 2024-03 | teambit.dev 2024-03; bundle vivo | platanus.json: el CTO salió en 2025 | No |
| Winston | PASS t2 | t1 PASS con 2 PC; t2 los aplica | 1 → 4: fundación 2023-03, Corfo Semilla Expande con UDD Ventures 2023-03, Platanus 2023-03, pivot 2023-12 (coaching humano) | elwinston.io 2023-03 y 2023-12; UDD Ventures (2023-03-16) | — | No |
| Pulso Escolar (pipoll) | PASS t8 (t7 resuelve los RETRY t4-t6) | ampliaciones 2023-06 y 2025-07 eliminadas (R48); Platanus 2022-03 sin monto (R28); consolidación retipada a rebrand 2023-12; live_state anclado; t8 adjudica pulsoescolar.com (espejo y versión en inglés) | 5 → 3: fundación 2021-05, Platanus 2022-03, rebrand 2023-12 | ventures.platan.us 2022-06 y 2023-12; pulsoescolar.cl vivo | el tweet de HILO_X.md narra los pasos eliminados; @titog sin confirmar | No: hay que reescribir su tweet |

## Validaciones ejecutadas

- `tools/check.py` reproduce byte a byte 10 prechecks guardados (prueba de la reconstrucción); precheck de cada tick nuevo guardado como `tick-N-precheck.txt`.
- `tools/merge_final.py` probado sobre una copia de `data/` (horizon, lici, wasabil: final.json y curated idénticos).
- `tools/validate_projection.py` después de cada merge: solo cambia la startup mergeada; 0 eventos sin fuente; `audited_count` 81.
- `tools/check_wayback_urls.py`: todas las URL `web.archive.org/web/<ts>/` de los artefactos de hoy tienen respaldo en un manifest, un archivo local o el CDX (antes de los veredictos se corrigieron 4 URL de archivo cuyo timestamp no correspondía al recurso: 3 escritos sin consultar el CDX, en pipoll, pullpo y sendmage, y 1 tomado de otro dominio, en nodek).
- Disponibilidad con UA de navegador y sin UA para cada `live_state`, guardada en `data/wayback_external/<slug>/`.
- `tools/transversal_scan.py`: estado de los problemas transversales (GAPS §36).
- **Build real en un clon APFS del proyecto** (`build_pivots_curated.py` + `build_timeline.py`): 81 startups, 398 eventos, 0 sin fuente; coincide evento por evento con la proyección, y contra el timeline desplegado cambian exactamente las 15 startups. `scraper/test_audited_timeline.py`: 5/5 OK.
- Comparación con el respaldo previo (`.context/backup-2026-09-23/` en Miami): `corrections.json`, `identity.json`, `funding.json` y `web/src/data/timeline.json` quedan byte-idénticos; `curated_trajectories.json` pasa de 106 a 115 entradas (12 agregadas y 3 de pipoll eliminadas).

## Qué falta para llevarlo al sitio y a los hilos

1. **Humano**: correr el build (`build_timeline.py` ya llama a `apply_audits`) sobre el `timeline.json` desplegado, revisar el diff (81 fichas; +43 eventos) y desplegar. La proyección validada es la de `tools/validate_projection.py`.
2. `identity.json`: aplicar las propuestas de `IDENTITY_DEFECTS.md` (estado «sin señal reciente» de crema, gopa y nodek; dominio nodek.co; eras de sendmage). No afecta la proyección, que toma el estado del artefacto.
3. Hilos (`docs/publicaciones/dos-hilos.md` en Miami): ninguna de las 14 está en los borradores. Pulso Escolar vuelve a ser candidata, pero su tweet debe reescribirse con la trayectoria nueva (colegios en 2021 → Pipoll para empresas en Platanus 2022 → Pulso Escolar desde 2023-12) y sin @titog hasta confirmarlo. Para cualquiera de las 15 hay que verificar hoy las menciones de X: las de `CONTACTO_40.md` son del 2026-09-11/14.
4. Pendientes transversales fuera de estas 15 (GAPS §36), que llegan al sitio con el próximo build: ampliaciones publicadas como pivot (§29) en 13 startups; fechas de entrada que difieren del registro (§30) en 21 finales; Start-Up Chile fechado por selección en 9 fases. Cruce con las 34 candidatas de `dos-hilos.md`: §29 afecta a Cardda, Fintoc, Examedi, Toku, Carvuk, Vivvidero, Appio, Sento y ElCeroKm; §30 a Cardda, Cacttus, Brolly, Mercately, TiendaDa, WallState, Carvuk, Morfy, Wayak, Kapso y Calypso; Start-Up Chile a Brolly, eSponsor, Salduu, Reversso, TiendaDa, Flair y Lokal. Los tweets de Calypso y Taxflow hablan de ampliación mientras sus finales publican rebrand y pivot.
