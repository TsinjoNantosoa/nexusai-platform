import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import { VitePWA } from "vite-plugin-pwa";

const apiProxy = {
  "/api": {
    target: process.env["API_PROXY_TARGET"] ?? "http://127.0.0.1:8000",
    changeOrigin: false,
    secure: false,
  },
};

export default defineConfig({
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
    VitePWA({
      strategies: "generateSW",
      filename: "sw.js",
      registerType: "prompt",
      injectRegister: null,
      devOptions: { enabled: false },
      manifest: false,
      workbox: {
        skipWaiting: false,
        clientsClaim: false,
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
  resolve: { tsconfigPaths: true },
  server: { proxy: apiProxy },
  preview: { proxy: apiProxy },
});
