import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    global: 'globalThis',
  },
  optimizeDeps: {
    esbuildOptions: {
      define: {
        global: 'globalThis',
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return

          if (id.includes('plotly.js')) return 'plotly'
          if (id.includes('react-plotly.js')) return 'plotly-react'
          if (id.includes('@tanstack/react-query')) return 'react-query'
          if (id.includes('react-router-dom')) return 'router'
          if (id.includes('lucide-react')) return 'icons'
          if (id.includes('react-dom')) return 'react-dom'
          if (id.includes('react')) return 'react'

          return 'vendor'
        },
      },
    },
  },
  server: {
    port: 5173,
    allowedHosts: ['.ngrok-free.dev'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
