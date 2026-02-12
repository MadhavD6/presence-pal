import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    allowedHosts: [".trycloudflare.com"], // Allow all Cloudflare tunnel subdomains
    hmr: {
      // clientPort: 443, // Use HTTPS port for HMR over tunnel (Enable if using Cloudflare only)
    },
    watch: {
      ignored: ["**/venv/**", "**/.venv/**", "**/node_modules/**", "**/thumbnails/**", "**/backend/**", "**/.git/**"],
    },
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
