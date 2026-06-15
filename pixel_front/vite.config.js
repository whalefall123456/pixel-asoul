import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',  // 允许外部设备访问
    port: 8080,       // 端口号，可以按需修改
    // 本地开发时代理到线上后端（生产环境由 Nginx 处理）
    proxy: {
      '/api': {
        target: 'https://pixel-asoul.club',
        changeOrigin: true,
        secure: false
      },
      '/ws': {
        target: 'wss://pixel-asoul.club',
        changeOrigin: true,
        secure: false,
        ws: true,
      }
    }
  }
})