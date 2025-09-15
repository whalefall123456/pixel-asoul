import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // host: '0.0.0.0',  // 允许外部设备访问
    // port: 5173       // 端口号，可以按需修改
    // 移除代理配置，因为Nginx会处理API请求代理
  }
})