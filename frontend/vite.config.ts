import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base is '/' for local dev / HuggingFace; set VITE_BASE=/descale/ for GitHub Pages
// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE || '/',
})
