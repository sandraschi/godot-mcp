import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 10992,
    strictPort: true,
    host: true,
    proxy: {
      "/api": { target: "http://127.0.0.1:10993", changeOrigin: true },
      "/docs": { target: "http://127.0.0.1:10993", changeOrigin: true },
      "/openapi.json": { target: "http://127.0.0.1:10993", changeOrigin: true },
      "/redoc": { target: "http://127.0.0.1:10993", changeOrigin: true },
    },
  },
});
