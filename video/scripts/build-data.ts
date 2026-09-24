// Genera src/data.ts desde el HTML publicado de https://startups.emersoftware.cl/
// (no desde web/src/data/timeline.json, que en este checkout es una versión anterior).
//   curl -sL https://startups.emersoftware.cl/ -o scripts/site-home.html
//   bun scripts/build-data.ts
const FETCHED = "2026-09-23";
const EXCLUDE = ["Fiscoclic", "Plutto", "Pulso Escolar", "Pipoll"];
const PICK = ["Cardda", "Fintoc", "Milla", "Konstruedu", "Strade", "Examedi", "Watermelon Tools", "Bemmbo", "Perhaps"];

const html = await Bun.file(new URL("./site-home.html", import.meta.url)).text();
const unesc = (s: string) =>
  s.replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">");

type Ev = { left: number; label: string; title: string; date: string; fill: string; border: string };
const rows = html.split('<div class="startup"').slice(1).map((b) => {
  const name = unesc(b.match(/data-name="([^"]*)"/)![1]);
  const alias = b.match(/También conocida como: ([^"]*)"/)?.[1];
  const events: Ev[] = [...b.matchAll(
    /left:([\d.\-]+)%;width:0;z-index:2"[^>]*>\s*<div class="evdot evdot-hit" data-tl="([^"]*)" data-ti="([^"]*)" data-dl="([^"]*)"[^>]*?style="[^"]*background:([^;]+);border:([^;]+);/g,
  )].map((m) => ({ left: +(+m[1]).toFixed(3), label: unesc(m[2]), title: unesc(m[3]), date: m[4], fill: m[5], border: m[6] }));
  return { name, alias: alias ? unesc(alias) : undefined, events };
});
const pool = rows.filter((r) => !EXCLUDE.some((x) => r.name === x || r.alias?.includes(x)));
const picked = PICK.map((n) => pool.find((r) => r.name === n)!);
const rest = pool.filter((r) => !PICK.includes(r.name));
const ticks = [...html.matchAll(/left:([\d.]+)%;transform:translateX\([^)]*\);font-size:10px;color:#bdbab2"><span class="yr-full">(\d{4})/g)]
  .map((m) => ({ year: +m[2], left: +(+m[1]).toFixed(3) }));

const out = `// Generado por scripts/build-data.ts desde https://startups.emersoftware.cl/ (${FETCHED}).
// ${rows.length} filas publicadas; se excluyen ${EXCLUDE.join(", ")}.
// \`left\` es la posición publicada del hito en el eje (0–100 %, rango 2018–2027).
export type Ev = { left: number; label: string; title: string; date: string; fill: string; border: string };
export type Row = { name: string; alias?: string; events: Ev[] };
export const PUBLISHED_COUNT = ${rows.length};
export const TICKS = ${JSON.stringify(ticks)};
export const ROWS: Row[] = ${JSON.stringify(picked, null, 1)};
// Filas sin nombre que sugieren el resto del conjunto.
export const MORE: Row[] = ${JSON.stringify(rest.slice(0, 40), null, 0)};
`;
await Bun.write(new URL("../src/data.ts", import.meta.url), out);
console.log(rows.length, picked.map((r) => `${r.name}:${r.events.length}`).join(" "), rest.length);
