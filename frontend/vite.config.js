// frontend/vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// ⚠️ Una sola línea, sin saltos, para que Vite no la rompa.
const CONTENT_SECURITY_POLICY =
  "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; worker-src 'self' blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob: https://tile.openstreetmap.org; connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 ws://localhost:5173 wss://localhost:5173 https://tile.openstreetmap.org https://basemaps.cartocdn.com https://demotiles.maplibre.org https://nominatim.openstreetmap.org;";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
    // 👇 ESTA cabecera es la que realmente usa el navegador en dev
    headers: {
      "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    },
  },
});
