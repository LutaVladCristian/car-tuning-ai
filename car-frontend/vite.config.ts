import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Read env vars from the repo root .env instead of car-frontend/.env
  envDir: '..',
})
