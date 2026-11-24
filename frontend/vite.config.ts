import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // No Docker com Windows, alterações nas pastas montadas não disparam eventos de arquivo;
    // o polling faz o Vite perceber as edições sem precisar reiniciar o container.
    watch: { usePolling: true, interval: 300 },
  },
})
