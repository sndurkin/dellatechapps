import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  root: '.',
  base: '/static/',
  build: {
    outDir: '../static/',
    assetsDir: 'assets',
    rollupOptions: {
      input: {
        storymagic: './storymagic/index.html',
        kitchenbuddy: './kitchenbuddy/index.html',
      },
    },
  },
  server: {
    watch: {
      usePolling: false,
    },
    host: true,
    strictPort: true,
    port: 5173,
    hmr: false,
    allowedHosts: true
  },
  plugins: [svelte({
    emitCss: true,
    compilerOptions: {
      css: true
    }
  })],
})
