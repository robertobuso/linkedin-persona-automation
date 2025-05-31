// vite.config.ts - CORRECTED AND RECOMMENDED
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import nativePath from 'node:path' // Import native Node.js path module explicitly
import { fileURLToPath } from 'node:url' // Import native Node.js url module explicitly
import tailwindcss from '@tailwindcss/vite'

// Define __dirname for ES Modules using native Node.js modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = nativePath.dirname(__filename);

export default defineConfig({
  plugins: [
    react(),
    tailwindcss({
      // Explicitly point to your Tailwind config file
      config: nativePath.resolve(__dirname, 'tailwind.config.js')
    }),
  ],
  resolve: {
    alias: {
      // Alias for your application code if you import '@/'
      '@': nativePath.resolve(__dirname, './src'),

      // If you specifically need 'path-browserify' for your *frontend browser code*
      // (i.e., code in your src/ directory imports 'path'), keep this alias.
      // If not, or if it was an attempt to fix __dirname, it might not be needed here.
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