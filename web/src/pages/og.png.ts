// OG del home: /og.png. Se prerenderiza en el build (mismo enfoque que los deeplinks:
// Rubik en paths), reemplaza el binario hecho a mano. Queda como asset estático en dist/.
import type { APIRoute } from "astro";
import { ogHomePng } from "../lib/og";

export const GET: APIRoute = () => {
  const buf = ogHomePng();
  return new Response(new Uint8Array(buf), {
    headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=31536000, immutable" },
  });
};
