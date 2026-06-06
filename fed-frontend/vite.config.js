import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Determine the API URL based on environment
// In Koyeb, this will be set via Environment Variables
// In local dev, it defaults to localhost:8000
const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler', {}]],
      },
    })
  ],
  server: {
    port: 5173,
    // Only use proxy in local development mode
    proxy: {
      '/api': {
        target: apiBaseUrl,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  // Optional: If you use absolute paths in your React code (e.g., /api/...)
  // ensure they resolve correctly in the build
  base: '/', 
})





{/*
// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler', {}]],
      },
    })
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})



import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})*/}
