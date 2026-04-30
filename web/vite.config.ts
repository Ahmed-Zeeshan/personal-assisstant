import { defineConfig } from 'vite';

export default defineConfig({
  base: './',                     // produces relative paths so file:// loading works
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'es2022',
    cssCodeSplit: false,          // single CSS file simplifies packaging
    rollupOptions: {
      output: { inlineDynamicImports: true }
    }
  }
});
