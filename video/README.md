# Video de apertura para X

Dos composiciones, 26,5 s, 30 fps, sin voz ni música. Animación editorial nativa: no usa capturas ni simula la interfaz.

- `StartupsXStory`: 1080 × 1920 (9:16) para Reels, TikTok e historias. El contenido queda dentro de la zona segura: libre arriba ~250 px, abajo ~400 px y el carril derecho de botones.
- `StartupsX`: 1080 × 1350 (4:5) para el feed de X.

```sh
bun install
bun run dev          # Remotion Studio
bun run render       # out/startups-x-story.mp4 (9:16, H.264, yuv420p)
bun run render:post  # out/startups-x.mp4 (4:5)
```

Una sola escena continua (`src/StartupsX.tsx`); los tiempos están en el objeto `T`:

- 0–3 s: «Quería saber cómo pivotean las startups en Chile.» y la fila de Cardda se dibuja (escena acelerada: `A_FRAMES`).
- 3–9 s: esa línea se vuelve una serie entre nueve filas con nombre y otras sin nombre que sugieren el resto.
- 9–19 s: zoom a Cardda; el trazo recorre sus etapas (`src/cardda.ts`).
- 19–26,5 s: vuelve al conjunto y cierre con la URL.

Datos: `src/data.ts` se genera con `bun scripts/build-data.ts` desde el HTML publicado de https://startups.emersoftware.cl/ (consultado el 23 de septiembre de 2026, 81 filas), no desde el timeline de este checkout. Las posiciones, fechas y formas de los hitos son las publicadas. Se excluyen Fiscoclic, Plutto y Pulso Escolar.

El resumen de Cardda viene de https://startups.emersoftware.cl/cardda/. Distingue inicio documentado, cambio de nombre, pivot y ampliación. El sitio marca may 2024 como «Pivot», pero su texto lo describe como una expansión; el video conserva el hito publicado y lo rotula «ampliación».

La cifra «más de 80» describe el sitio, no una auditoría completa. Solo existe Rubik Regular en `public/`: no usar pesos mayores a 400.
