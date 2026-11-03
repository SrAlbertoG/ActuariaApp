/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Puerto fijo: debe coincidir con "allowed_origins" del backend (CORS).
  server: { port: 1420, strictPort: true },
  test: { environment: "jsdom", globals: true },
});