// vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
    headers: {
      "Content-Security-Policy": [
        "default-src 'self';",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:;",
        "worker-src 'self' blob:;",
        "style-src 'self' 'unsafe-inline';",
        "font-src 'self' data:;",
        "img-src 'self' data: https://tile.openstreetmap.org;",
        // 👇 CLAVE: agregar 'self' (habilita http://localhost:5173)
        "connect-src 'self' http://127.0.0.1:8000 ws://localhost:5173 https://tile.openstreetmap.org;",
      ].join(" "),
    },
  },
});
