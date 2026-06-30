// OG por startup: /og/<slug>.png. Se prerenderiza en el build (uno por startup),
// queda como asset estático en dist/og/. Sin PNGs commiteados, sin native code en runtime.
import type { APIRoute } from "astro";
import data from "../../data/timeline.json";
import { slugify } from "../../lib/slug";
import { ogPng } from "../../lib/og";

export function getStaticPaths() {
  const seen = new Set<string>();
  return (data.startups as any[])
    .map((s) => ({ s, slug: slugify(s.name) }))
    .filter(({ slug }) => slug && !seen.has(slug) && seen.add(slug))
    .map(({ s, slug }) => ({ params: { slug }, props: { name: s.name, events: s.events } }));
}

export const GET: APIRoute = ({ props }) => {
  const png = ogPng(props.name, props.events, data.meta.range);
  return new Response(new Uint8Array(png), {
    headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=31536000, immutable" },
  });
};
