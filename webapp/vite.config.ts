import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: { output: { manualChunks: { react: ["react", "react-dom", "react-router-dom"], vendor: ["framer-motion", "zustand", "lucide-react"] } } },
  },
  define: {
    "import.meta.env.VITE_API_BASE": JSON.stringify(process.env.VITE_API_BASE || ""),
  },
  server: {
    allowedHosts: ['goliath'],
    port: 10992,
    strictPort: true,
    host: true,
    proxy: {
      "/api": { target: "http://127.0.0.1:10993", changeOrigin: true },
      "/mcp": { target: "http://127.0.0.1:10993", changeOrigin: true },
      "/docs": { target: "http://127.0.0.1:10993", changeOrigin: true },
      "/openapi.json": { target: "http://127.0.0.1:10993", changeOrigin: true },
      "/redoc": { target: "http://127.0.0.1:10993", changeOrigin: true },
    },
  },
});

