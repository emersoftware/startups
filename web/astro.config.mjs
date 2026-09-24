import { defineConfig } from 'astro/config';
import { fileURLToPath } from 'node:url';
import { fingerprintOg } from './scripts/fingerprint-og.ts';

export default defineConfig({
  site: 'https://startups.emersoftware.cl',
  integrations: [{
    name: 'versioned-social-images',
    hooks: {
      'astro:build:done': async ({ dir, logger }) => {
        const result = await fingerprintOg(fileURLToPath(dir));
        logger.info(`${result.pages} pages linked to ${result.images} versioned OG images`);
      },
    },
  }],
});
