import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    // Playwright owns e2e/; vitest owns everything colocated with source.
    include: ["src/**/*.test.{ts,tsx}"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      // `server-only` throws on import outside a react-server bundle — that is how it
      // makes a client import of server code a build error. Under Vitest that throw would
      // fire before any assertion, so it resolves to a stub which explains itself.
      "server-only": path.resolve(__dirname, "./src/shared/test/server-only-stub.ts"),
    },
  },
});
