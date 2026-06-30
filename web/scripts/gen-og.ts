/**
 * Genera los OG por startup en web/public/og/<slug>.png (1200x630).
 * Diseño: estrellita + "Chile, Startups" arriba · nombre de la startup ·
 * abajo su timeline con SOLO los puntos (mismo color-map y rango que el sitio).
 *
 * Estático: los PNG se commitean y se sirven como assets en Cloudflare.
 * Re-correr tras editar src/data/timeline.json:  bun run scripts/gen-og.ts [slug]
 */
import { Resvg } from "@resvg/resvg-js";
import data from "../src/data/timeline.json";
import { slugify } from "../src/lib/slug";

const FONT = `${import.meta.dir}/fonts/Rubik-var.ttf`;
const OUT = `${import.meta.dir}/../public/og`;

const W = 1200, H = 630;
const PADX = 80;
const LANE_L = PADX, LANE_R = W - PADX;   // 80 → 1120
const LANE_Y = 486;                        // baseline de los puntos
const ACCENT = "#2f5fe6";

const { start, end } = data.meta.range;
const tval = (d: string) => { const [y, m] = d.split("-").map(Number); return y + (m - 0.5) / 12; };
const xOf = (d: string) => LANE_L + ((tval(d) - start) / (end - start)) * (LANE_R - LANE_L);

// Mismo EV map que App.astro (fill / borde para los puntos vacíos sobre blanco).
const EV: Record<string, { fill: string; stroke?: string; dash?: boolean }> = {
  fundacion:   { fill: "#1a1916" },
  capital:     { fill: ACCENT },
  pivot:       { fill: "#ffffff", stroke: "#b5760f" },
  adquisicion: { fill: "#2f7d4f" },
  cierre:      { fill: "#c0492f" },
  inactivo:    { fill: "#ffffff", stroke: "#a8a39a", dash: true },
};

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// Un punto en x,y absolutos: anillo blanco (separa solapados, como el box-shadow del sitio) + cuadrado.
function dot(x: number, y: number, type: string) {
  const c = EV[type] ?? EV.fundacion;
  const s = 22, r = 7;
  const x0 = x - s / 2, y0 = y - s / 2;
  const ring = `<rect x="${(x0 - 4).toFixed(1)}" y="${y0 - 4}" width="${s + 8}" height="${s + 8}" rx="${r + 3}" fill="#ffffff"/>`;
  const stroke = c.stroke
    ? ` stroke="${c.stroke}" stroke-width="2.6"${c.dash ? ` stroke-dasharray="3 2.6"` : ""}`
    : "";
  return ring + `<rect x="${x0.toFixed(1)}" y="${y0}" width="${s}" height="${s}" rx="${r}" fill="${c.fill}"${stroke}/>`;
}

function svg(name: string, events: { type: string; date: string }[]) {
  const n = name.length;
  const nameSize = n <= 11 ? 96 : n <= 16 ? 80 : n <= 22 ? 64 : 52;

  const axis = `<line x1="${LANE_L}" y1="${LANE_Y}" x2="${LANE_R}" y2="${LANE_Y}" stroke="#eceae4" stroke-width="2"/>`;
  const dots = events.map((e) => dot(xOf(e.date), LANE_Y, e.type)).join("");

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="#ffffff"/>

  <g transform="translate(${PADX},66)">
    <rect width="40" height="40" rx="11" fill="${ACCENT}"/>
    <path transform="translate(8,8)" d="M12 2l2.94 6.34L22 9.27l-5 4.73 1.18 6.99L12 17.77 5.82 21l1.18-6.99-5-4.73 7.06-.93z" fill="#ffffff"/>
    <text x="56" y="28" font-family="Rubik" font-weight="400" font-size="27" fill="#1a1916" letter-spacing="-0.3">Chile, Startups</text>
  </g>

  <text x="${PADX}" y="318" font-family="Rubik" font-weight="500" font-size="${nameSize}" fill="#1a1916" letter-spacing="-1.5">${esc(name)}</text>

  ${axis}
  ${dots}

  <text x="${PADX}" y="566" font-family="Rubik" font-weight="400" font-size="22" fill="#bdbab2" letter-spacing="-0.2">startups.emersoftware.cl</text>
</svg>`;
}

const fontData = Buffer.from(await Bun.file(FONT).arrayBuffer());

async function render(name: string, events: any[], slug: string) {
  const resvg = new Resvg(svg(name, events), {
    fitTo: { mode: "width", value: W },
    font: { fontBuffers: [fontData], loadSystemFonts: false, defaultFontFamily: "Rubik" },
  });
  await Bun.write(`${OUT}/${slug}.png`, resvg.render().asPng());
}

const only = process.argv[2]; // opcional: regenerar solo un slug
let count = 0;
for (const s of data.startups as any[]) {
  const slug = slugify(s.name);
  if (!slug || (only && slug !== only)) continue;
  await render(s.name, s.events, slug);
  count++;
}
console.log(`OG generados: ${count} → public/og/`);
