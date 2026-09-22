import { defineConfig } from "vite";

export default defineConfig({
  base: "/manage-fail/main-experiment/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
