import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// /api 요청은 Spring Boot(8000)로 프록시 → 브라우저는 FastAPI의 존재를 모른다.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:8000' } },
})
