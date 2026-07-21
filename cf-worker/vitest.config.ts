import { defineWorkersConfig } from "@cloudflare/vitest-pool-workers/config";

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: "./wrangler.jsonc" },
        miniflare: {
          // Fixture bindings are declared in wrangler.jsonc; tests seed
          // them per-suite (see test/fixtures.ts).
          bindings: { CORS_ORIGINS: "" },
        },
      },
    },
  },
});
