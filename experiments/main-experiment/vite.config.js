import { defineConfig } from "vite";
import { copyFileSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";

function githubPagesRoutes() {
  let outDir = "dist";

  return {
    name: "github-pages-routes",
    configResolved(config) {
      outDir = config.build.outDir;
    },
    closeBundle() {
      const indexPath = resolve(outDir, "index.html");

      copyFileSync(indexPath, resolve(outDir, "404.html"));

      for (const itemRoute of ["photo", "package"]) {
        const itemRouteDir = resolve(outDir, itemRoute);
        mkdirSync(itemRouteDir, { recursive: true });
        copyFileSync(indexPath, resolve(itemRouteDir, "index.html"));
      }
    },
  };
}

export default defineConfig({
  base: "/manage-fail/main-experiment/",
  plugins: [githubPagesRoutes()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
