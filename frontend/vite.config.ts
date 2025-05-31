import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import nativePath from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url);
const __dirname = nativePath.dirname(__filename);

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // No config needed for v4 - it reads from CSS
  ],
  resolve: {
    alias: {
      '@': nativePath.resolve(__dirname, './src'),
      'path': 'path-browserify',
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})