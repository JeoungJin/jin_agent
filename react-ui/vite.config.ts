import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // 같은 출처로 요청되어 HttpOnly 쿠키가 그대로 오가고 CORS 설정이 필요 없다
    proxy: { '/api': 'http://localhost:8000' },
  },
  test: { environment: 'node' },
})
