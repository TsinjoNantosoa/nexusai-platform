// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - TanStack devtools (dev-only, first), tanstackStart, viteReact, tailwindcss, tsConfigPaths,
//     nitro (build-only using cloudflare as a default target), VITE_* env injection, @ path alias,
//     React/TanStack dedupe, error logger plugins, and sandbox detection (port/host/strictPort).
// Never set ssr.external or resolve.external: the Worker has no runtime module resolution, so
// the build fails. Never add compression (compressPublicAssets, vite-plugin-compression):
// hosting already compresses at the edge.
// You can pass additional config via defineConfig({ vite: { ... }, etc... }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  vite: {
    plugins: [
      VitePWA({
        strategies: "generateSW",
        filename: "sw.js",
        registerType: "autoUpdate",
        injectRegister: null,
        devOptions: { enabled: false },
        manifest: false,
        workbox: {
          globPatterns: ["**/*.{js,css,woff2}", "icons/*.png", "offline.html"],
          runtimeCaching: [
            {
              urlPattern: ({ url, request, sameOrigin }) =>
                sameOrigin && request.mode === "navigate" && url.pathname === "/",
              handler: "NetworkFirst",
              options: {
                cacheName: "nexusai-public-pages",
                precacheFallback: { fallbackURL: "/offline.html" },
                networkTimeoutSeconds: 5,
                cacheableResponse: { statuses: [200] },
                expiration: { maxEntries: 1, maxAgeSeconds: 86400 },
              },
            },
          ],
        },
      }),
    ],
  },
  tanstackStart: {
    // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
    // nitro/vite builds from this
    server: { entry: "server" },
  },
});
