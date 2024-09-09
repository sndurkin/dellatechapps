import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  root: '.',
  base: '/static/',
  build: {
    outDir: '../static/',
    rollupOptions: {
      input: {
        storymagic: './storymagic/index.html',
        kitchenbuddy: './kitchenbuddy/index.html',
      },
    },
  },
  server: {
    watch: {
      usePolling: true,
    },
  },
  plugins: [svelte()],
})
