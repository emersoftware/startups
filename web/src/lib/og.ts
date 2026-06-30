/**
 * OG (1200x630) → PNG. Dos variantes:
 *  - ogPng(name, events, range): por startup (deeplink) — nombre + timeline con SOLO los puntos.
 *  - ogHomePng(): home — titular "Cómo evolucionaron las startups chilenas".
 *
 * El texto se convierte a PATHS vectoriales con opentype.js en el BUILD, así el PNG no
 * depende de que resvg matchee/cargue ninguna font en runtime: local == prod por construcción.
 * (resvg matcheaba mal "Rubik" en el CI y caía a una font monospace.)
 *
 * Se prerenderiza desde endpoints (build-time, no en el worker):
 *  src/pages/og/[slug].png.ts  y  src/pages/og.png.ts
 */
import { Resvg } from "@resvg/resvg-js";
import opentype from "opentype.js";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const W = 1200, H = 630;
const PADX = 80;
const LANE_L = PADX, LANE_R = W - PADX;   // 80 → 1120
const LANE_Y = 486;                        // baseline de los puntos
const ACCENT = "#2f5fe6";
const INK = "#1a1916";

type Ev = { type: string; date: string };

const tval = (d: string) => { const [y, m] = d.split("-").map(Number); return y + (m - 0.5) / 12; };

// Mismo EV map que App.astro (fill / borde para los puntos vacíos sobre blanco).
const EV: Record<string, { fill: string; stroke?: string; dash?: boolean }> = {
  fundacion:   { fill: INK },
  capital:     { fill: ACCENT },
  pivot:       { fill: "#ffffff", stroke: "#b5760f" },
  adquisicion: { fill: "#2f7d4f" },
  cierre:      { fill: "#c0492f" },
  inactivo:    { fill: "#ffffff", stroke: "#a8a39a", dash: true },
};

// Rubik Regular (400) — mismo peso que la plataforma (App.astro: marca y nombres en 400).
// opentype la usa para sacar los contornos de glifos. cwd = web/ en `astro build` y en el CI.
const fontBuf = readFileSync(join(process.cwd(), "src/lib", "Rubik-Regular.ttf"));
const RUBIK = opentype.parse(fontBuf.buffer.slice(fontBuf.byteOffset, fontBuf.byteOffset + fontBuf.byteLength));

// Ancho de avance de un string (para encadenar palabras de distinto color en una línea).
function width(str: string, size: number, tracking = 0) {
  const scale = size / RUBIK.unitsPerEm;
  let w = 0;
  for (const ch of str) w += RUBIK.charToGlyph(ch).advanceWidth * scale + tracking;
  return w - tracking; // sin el tracking sobrante tras el último glifo
}

// Texto → contornos. Cada glifo se saca en origen (0,0) y se posiciona con
// transform="translate" (lo aplica resvg). Pasar el pen fraccionario a opentype
// gatilla un bug de toPathData que emite NaN en glifos con curvas y rompe el path.
// tracking = letter-spacing en px (negativo aprieta).
function text(str: string, x: number, baseY: number, size: number, fill: string, tracking = 0) {
  const scale = size / RUBIK.unitsPerEm;
  let pen = x;
  const parts: string[] = [];
  for (const ch of str) {
    const g = RUBIK.charToGlyph(ch);
    const d = g.getPath(0, 0, size).toPathData(2);
    if (d) parts.push(`<path transform="translate(${pen.toFixed(2)} ${baseY})" d="${d}"/>`);
    pen += g.advanceWidth * scale + tracking;
  }
  return `<g fill="${fill}">${parts.join("")}</g>`;
}

// Marca (estrellita + "Chile, Startups") y footer (url) — comunes a ambas variantes.
const brand = `<g transform="translate(${PADX},66)">
    <rect width="40" height="40" rx="11" fill="${ACCENT}"/>
    <path transform="translate(8,8)" d="M12 2l2.94 6.34L22 9.27l-5 4.73 1.18 6.99L12 17.77 5.82 21l1.18-6.99-5-4.73 7.06-.93z" fill="#ffffff"/>
    ${text("Chile, Startups", 56, 28, 27, INK, -0.3)}
  </g>`;
const footer = text("startups.emersoftware.cl", PADX, 566, 22, "#bdbab2", -0.2);

const frame = (inner: string) => `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="#ffffff"/>
  ${brand}
  ${inner}
  ${footer}
</svg>`;

const png = (svg: string): Buffer => new Resvg(svg, { fitTo: { mode: "width", value: W } }).render().asPng();

// Un punto en x absoluto: anillo blanco (separa solapados, como el box-shadow del sitio) + cuadrado.
function dot(x: number, type: string) {
  const c = EV[type] ?? EV.fundacion;
  const s = 22, r = 7;
  const x0 = x - s / 2, y0 = LANE_Y - s / 2;
  const ring = `<rect x="${(x0 - 4).toFixed(1)}" y="${y0 - 4}" width="${s + 8}" height="${s + 8}" rx="${r + 3}" fill="#ffffff"/>`;
  const stroke = c.stroke
    ? ` stroke="${c.stroke}" stroke-width="2.6"${c.dash ? ` stroke-dasharray="3 2.6"` : ""}`
    : "";
  return ring + `<rect x="${x0.toFixed(1)}" y="${y0}" width="${s}" height="${s}" rx="${r}" fill="${c.fill}"${stroke}/>`;
}

// Deeplink: nombre grande + su timeline (solo puntos).
export function ogPng(name: string, events: Ev[], range: { start: number; end: number }): Buffer {
  const xOf = (d: string) => LANE_L + ((tval(d) - range.start) / (range.end - range.start)) * (LANE_R - LANE_L);
  const n = name.length;
  const nameSize = n <= 11 ? 96 : n <= 16 ? 80 : n <= 22 ? 64 : 52;
  const axis = `<line x1="${LANE_L}" y1="${LANE_Y}" x2="${LANE_R}" y2="${LANE_Y}" stroke="#eceae4" stroke-width="2"/>`;
  const dots = events.map((e) => dot(xOf(e.date), e.type)).join("");
  return png(frame(`${text(name, PADX, 318, nameSize, INK, -1.2)}
  ${axis}
  ${dots}`));
}

// Home: titular en dos líneas, "chilenas" en azul.
export function ogHomePng(): Buffer {
  const SZ = 74, TR = -1.6, Y1 = 312, Y2 = Y1 + 92;
  const line2a = "startups ";
  const headline =
    text("Cómo evolucionaron las", PADX, Y1, SZ, INK, TR) +
    text(line2a, PADX, Y2, SZ, INK, TR) +
    text("chilenas", PADX + width(line2a, SZ, TR), Y2, SZ, ACCENT, TR);
  return png(frame(headline));
}
