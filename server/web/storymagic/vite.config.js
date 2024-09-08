import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  root: '.',
  base: '/storymagic/',
  build: {
    outDir: '../../static/storymagic',
  },
  server: {
    watch: {
      usePolling: true,
    },
  },
  plugins: [svelte()],
})
