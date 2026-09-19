import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// /api proxies to the FastAPI stub (api/main.py) in dev.
// The fetch layer falls back to bundled mocks if the API is down,
// so the frontend never blocks on the pipeline.
export default defineConfig({
  worker: { format: 'es' },
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
