// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// vite.config.js (solo dev)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/openaq': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
    headers: {
      "Content-Security-Policy": [
        "default-src 'self';",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: ws:;",
        "worker-src 'self' blob:;",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;",
        "font-src 'self' https://fonts.gstatic.com data:;",
        "img-src 'self' data: https://tile.openstreetmap.org https://basemaps.cartocdn.com;",
        "connect-src 'self' ws: https://tile.openstreetmap.org https://basemaps.cartocdn.com;",
      ].join(" "),
    },
  },
});
