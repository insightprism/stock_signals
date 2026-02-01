import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 22265,
    proxy: {
      '/api': {
        target: 'http://localhost:22226',
        changeOrigin: true,
      },
    },
  },
})
