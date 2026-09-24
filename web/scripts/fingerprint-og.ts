/** Give social crawlers a new image URL when the rendered PNG changes.
 * Called by Astro's build hook, or against a verified copy of a deployed build.
 * Retains the original URLs for existing links and cached cards.
 */
import { createHash } from "node:crypto";
import { readdir, readFile, writeFile } from "node:fs/promises";
import { resolve, join, extname } from "node:path";

export async function fingerprintOg(directory: string) {
  const root = resolve(directory);
  const entries = await readdir(root, { recursive: true, withFileTypes: true });
  let pages = 0;
  const images = new Set<string>();
  for (const entry of entries) {
    if (!entry.isFile() || extname(entry.name) !== ".html") continue;
    const path = join(entry.parentPath, entry.name);
    const html = await readFile(path, "utf8");
    const tags = [
      ...html.matchAll(
        /<meta\s+(?:property="og:image"|name="twitter:image")\s+content="([^"]+)"[^>]*>/g,
      ),
    ];
    let updated = html;
    for (const match of tags) {
      const url = new URL(match[1]);
      if (
        url.hostname !== "startups.emersoftware.cl" ||
        !/^\/og(?:\/[^/]+)?(?:\.[a-f0-9]{16})?\.png$/.test(url.pathname)
      )
        throw new Error(`Unexpected image URL: ${url}`);
      const source = join(root, url.pathname);
      const png = await readFile(source);
      const hash = createHash("sha256").update(png).digest("hex").slice(0, 16);
      const pathname = url.pathname
        .replace(/\.[a-f0-9]{16}\.png$/, ".png")
        .replace(/\.png$/, `.${hash}.png`);
      await writeFile(join(root, pathname), png);
      images.add(pathname);
      url.pathname = pathname;
      url.search = "";
      updated = updated.replace(match[0], match[0].replace(match[1], url.href));
    }
    if (updated !== html) {
      await writeFile(path, updated);
      pages++;
    }
  }
  return { pages, images: images.size };
}

if (import.meta.main) {
  console.log(JSON.stringify(await fingerprintOg(process.argv[2] ?? "dist")));
}
