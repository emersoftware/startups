/**
 * OG por startup: SVG → PNG (1200x630).
 * estrellita + "Chile, Startups" · nombre · timeline con SOLO los puntos
 * (mismo color-map y rango de eje que el sitio).
 *
 * El texto se convierte a PATHS vectoriales con opentype.js en el BUILD, así el PNG
 * no depende de que resvg matchee/cargue ninguna font en runtime: local == prod por
 * construcción. (resvg matcheaba mal "Rubik" en el CI y caía a una font monospace.)
 *
 * Se prerenderiza desde el endpoint src/pages/og/[slug].png.ts (build-time, no en el worker).
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

type Ev = { type: string; date: string };

const tval = (d: string) => { const [y, m] = d.split("-").map(Number); return y + (m - 0.5) / 12; };

// Mismo EV map que App.astro (fill / borde para los puntos vacíos sobre blanco).
const EV: Record<string, { fill: string; stroke?: string; dash?: boolean }> = {
  fundacion:   { fill: "#1a1916" },
  capital:     { fill: ACCENT },
  pivot:       { fill: "#ffffff", stroke: "#b5760f" },
  adquisicion: { fill: "#2f7d4f" },
  cierre:      { fill: "#c0492f" },
  inactivo:    { fill: "#ffffff", stroke: "#a8a39a", dash: true },
};

// Rubik estática (instancias 400/500) leída del árbol fuente; opentype la usa para
// sacar los contornos de glifos. cwd = web/ en `astro build` y en el CI.
const load = (f: string) => {
  const b = readFileSync(join(process.cwd(), "src/lib", f));
  return opentype.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength));
};
const RUBIK = { 400: load("Rubik-Regular.ttf"), 500: load("Rubik-Medium.ttf") };

// Texto → contornos. Cada glifo se saca en origen (0,0) y se posiciona con
// transform="translate" (lo aplica resvg). Pasar el pen fraccionario a opentype
// gatilla un bug de toPathData que emite NaN en glifos con curvas y rompe el path.
// tracking = letter-spacing en px (negativo aprieta).
function text(str: string, x: number, baseY: number, size: number, weight: 400 | 500, fill: string, tracking = 0) {
  const font = RUBIK[weight];
  const scale = size / font.unitsPerEm;
  let pen = x;
  const parts: string[] = [];
  for (const ch of str) {
    const g = font.charToGlyph(ch);
    const d = g.getPath(0, 0, size).toPathData(2);
    if (d) parts.push(`<path transform="translate(${pen.toFixed(2)} ${baseY})" d="${d}"/>`);
    pen += g.advanceWidth * scale + tracking;
  }
  return `<g fill="${fill}">${parts.join("")}</g>`;
}

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

function buildSvg(name: string, events: Ev[], start: number, end: number) {
  const xOf = (d: string) => LANE_L + ((tval(d) - start) / (end - start)) * (LANE_R - LANE_L);
  const n = name.length;
  const nameSize = n <= 11 ? 96 : n <= 16 ? 80 : n <= 22 ? 64 : 52;
  const axis = `<line x1="${LANE_L}" y1="${LANE_Y}" x2="${LANE_R}" y2="${LANE_Y}" stroke="#eceae4" stroke-width="2"/>`;
  const dots = events.map((e) => dot(xOf(e.date), e.type)).join("");

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="#ffffff"/>
  <g transform="translate(${PADX},66)">
    <rect width="40" height="40" rx="11" fill="${ACCENT}"/>
    <path transform="translate(8,8)" d="M12 2l2.94 6.34L22 9.27l-5 4.73 1.18 6.99L12 17.77 5.82 21l1.18-6.99-5-4.73 7.06-.93z" fill="#ffffff"/>
    ${text("Chile, Startups", 56, 28, 27, 500, "#1a1916", -0.3)}
  </g>
  ${text(name, PADX, 318, nameSize, 500, "#1a1916", -1.2)}
  ${axis}
  ${dots}
  ${text("startups.emersoftware.cl", PADX, 566, 22, 400, "#bdbab2", -0.2)}
</svg>`;
}

export function ogPng(name: string, events: Ev[], range: { start: number; end: number }): Buffer {
  // El SVG ya trae el texto como paths → resvg solo rasteriza vectores, sin fonts.
  const resvg = new Resvg(buildSvg(name, events, range.start, range.end), {
    fitTo: { mode: "width", value: W },
  });
  return resvg.render().asPng();
}
