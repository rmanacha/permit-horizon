// Vite builds the static site into web/dist. No React plugin: esbuild compiles TSX on its own
// (tsconfig "jsx": "react-jsx"), which keeps Babel and its data packages out of the tree
// (decision 79). base "./" makes every URL relative, so the same build works on GitHub Pages
// (/permit-horizon/), under Docker and with `make run` (/).
import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  esbuild: { jsx: 'automatic' },
  build: { outDir: 'dist', emptyOutDir: true, target: 'es2022', sourcemap: false },
  server: { port: 5173, strictPort: true },
  preview: { port: 4173, strictPort: true },
});
