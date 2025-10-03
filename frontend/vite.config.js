// frontend/vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const CSP = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  "worker-src 'self' blob:",
  "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 ws://localhost:5173 wss://localhost:5173 https://tile.openstreetmap.org https://basemaps.cartocdn.com https://demotiles.maplibre.org https://nominatim.openstreetmap.org"
].join("; ");

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
    headers: {
      "Content-Security-Policy": CSP,
    },
  },
});

