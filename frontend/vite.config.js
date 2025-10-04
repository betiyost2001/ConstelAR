// frontend/vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// ⚠️ Una sola línea, sin saltos (evita que Vite inserte \n raros)
const CONTENT_SECURITY_POLICY =
  "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; worker-src 'self' blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob: https://tile.openstreetmap.org; connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 ws://localhost:5173 wss://localhost:5173 https://tile.openstreetmap.org https://basemaps.cartocdn.com https://demotiles.maplibre.org https://nominatim.openstreetmap.org https://wft-geo-db.p.rapidapi.com https://*.rapidapi.com;";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      // Todo lo que empiece con /api -> backend en :8000, quitando /api
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
    headers: {
      "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    },
  },
});
