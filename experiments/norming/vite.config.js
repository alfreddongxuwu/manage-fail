import { defineConfig } from "vite";

export default defineConfig({
  base: "/manage-fail/norming/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
