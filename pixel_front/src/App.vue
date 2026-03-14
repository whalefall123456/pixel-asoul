<script setup>
import { ref, onMounted, provide } from 'vue';
import CanvasBoard from './components/CanvasBoard.vue';
import ColorPicker from './components/ColorPicker.vue';
import CooldownTimer from './components/CooldownTimer.vue';
import ws from './utils/ws.js';

// 状态管理
const selectedColor = ref('#FF0000');
const canvasBoard = ref(null);
const cooldownTimer = ref(null);

// 统计信息
const stats = ref({
  onlineCount: 0,        // 当前在线人数
  totalVisits: 0,        // 累计访问人次
  totalPixels: 0         // 累计放置像素块数
});

const cooldownEventBus = {
  listeners: [],
  emit(data) {
    this.listeners.forEach(callback => callback(data))
  },
  on(callback) {
    this.listeners.push(callback)
  },
  off(callback) {
    this.listeners = this.listeners.filter(cb => cb !== callback)
  }
}
provide('cooldownEventBus', cooldownEventBus)

// 连接到WebSocket服务器
onMounted(() => {
  // 初始化WebSocket连接
  // 在生产环境中，使用相对路径连接到当前域的WebSocket服务
  const wsUrl = window.location.protocol === 'https:' 
    ? `wss://${window.location.host}/ws/canvas` 
    : `ws://${window.location.host}/ws/canvas`;
  ws.connect(wsUrl);

  // 监听限制消息
  ws.on('limited', (data) => {
    // 显示提示信息
    alert(data.error_message);
    
    // 通知 CooldownTimer 组件开始倒计时
    if (cooldownTimer.value) {
      cooldownTimer.value.startCooldown(data.limit_time);
    }
  });

  // 监听统计信息更新
  ws.on('stats', (data) => {
    stats.value = {
      onlineCount: data.current_online_users || 0,
      totalVisits: data.total_visits || 0,
      totalPixels: data.total_placed_pixels || 0
    };
  });

})

// 重置画布视图
function resetCanvasView() {
  if (canvasBoard.value) {
    canvasBoard.value.resetView();
  }
}
</script>

<template>
  <div class="app">
    <header>
      <h1 class="title">A手像素画板 - 多人在线像素艺术协作平台</h1>
      <p class="subtitle">与其他创作者一起实时协作，创作独特的像素艺术作品</p>
    </header>
    
    <div class="main-container">
      <!-- 左侧控制面板 -->
      <div class="control-panel">
        <ColorPicker v-model="selectedColor" />
        <CooldownTimer ref="cooldownTimer" />
        <button @click="resetCanvasView" class="reset-view-btn">重置视图</button>
      </div>
      
      <!-- 中间画布区域 -->
      <div class="canvas-panel">
        <CanvasBoard 
          ref="canvasBoard"
          :selected-color="selectedColor"
          @pixel-placed="() => {}"
        />
      </div>
      
      <!-- 右侧面板（可以添加其他功能） -->
      <div class="info-panel">
        <div class="instructions">
          <h3>使用说明</h3>
          <ul>
            <li>在左侧选择颜色</li>
            <li>点击画布放置像素</li>
            <li>鼠标滚轮缩放画布</li>
            <li>按住鼠标拖拽移动画布</li>
            <li>放置频率限制为平均2/s</li>
            <li>与其他用户实时协作创作</li>
          </ul>
          <p class="mock-mode-notice">
            <strong>提示:</strong> 点击吸管工具可吸取画布上的颜色，部分浏览器可能不支持。
          </p>
        </div>
        
        <!-- 统计信息展示 -->
        <div class="stats-panel">
          <h3>数据统计</h3>
          <div class="stat-item">
            <span class="stat-label">👥 在线人数:</span>
            <span class="stat-value">{{ stats.onlineCount }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">👁️ 累计访问:</span>
            <span class="stat-value">{{ stats.totalVisits }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">🎨 放置像素:</span>
            <span class="stat-value">{{ stats.totalPixels }}</span>
          </div>
          
          <!-- 哔哩哔哩视频链接 -->
          <div class="bili-link">
            <img src="./assets/bilibili_play.png" alt="Bilibili" class="bili-icon" />
            <a href="https://www.bilibili.com/video/BV1wscrz3ERL" target="_blank" rel="noopener noreferrer">
              绘画过程可视化
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
#app {
  max-width: 100%;
  margin: 0;
  padding: 0;
  text-align: center;
}

.app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 20px;
  width: 100%;
  /*min-width: 1600px;  确保应用程序有最小宽度 */
}

.title {
  text-align: center;
  margin-bottom: 10px;
}

.subtitle {
  text-align: center;
  margin-top: 0;
  margin-bottom: 30px;
  color: #666;
  font-size: 1.1em;
}

.main-container {
  display: flex;
  justify-content: center;
  gap: 20px;
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 20px;
  box-sizing: border-box;
  min-height: 0;
  overflow-x: auto;
  min-width: 1600px; /* 确保容器有最小宽度 */
}

.control-panel {
  width: 250px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex-shrink: 0;
  min-width: 250px; /* 防止面板被压缩 */
}

.canvas-panel {
  flex: 0 0 auto; /* 不收缩，不增长，自动尺寸 */
  display: flex;
  justify-content: center;
  padding: 10px 0;
  align-items: flex-start; /* 使画布在面板中顶部对齐 */
  min-width: min-content; /* 确保容器不会小于内容 */
}

.info-panel {
  width: 250px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex-shrink: 0;
  min-width: 250px; /* 防止面板被压缩 */
}

.instructions {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: left;
  width: 100%;
  box-sizing: border-box;
}

.instructions h3 {
  margin-top: 0;
}

.instructions ul {
  padding-left: 20px;
  margin-bottom: 15px;
}

.instructions li {
  margin-bottom: 8px;
}

.mock-mode-notice {
  background-color: #fff8e1;
  border-left: 4px solid #ffc107;
  padding: 10px;
  margin: 0;
  font-size: 14px;
}

.stats-panel {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: left;
  width: 100%;
  box-sizing: border-box;
  margin-top: 20px;
}

.stats-panel h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #e0e0e0;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  font-size: 14px;
  color: #555;
}

.stat-value {
  font-size: 16px;
  font-weight: bold;
  color: #2c3e50;
}

.bili-link {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e0e0e0;
}

.bili-icon {
  width: 64px;
  height: 64px;
  object-fit: contain;
}

.bili-link a {
  color: #00AEEC;
  text-decoration: none;
  font-size: 20px;
  font-weight: 500;
  transition: color 0.3s;
  display: flex;
  align-items: center;
}

.bili-link a:hover {
  color: #0083b0;
}

.reset-view-btn {
  padding: 10px 15px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
}

.reset-view-btn:hover {
  background-color: #45a049;
}

/* 移动端自动缩放整个应用 */
@media (max-width: 1600px) {
  .app {
    width: 1600px;
    /* 使用负边距来居中缩放后的内容 */
    margin-left: calc(50% - (1600px * (100vw / 1600px) / 2));
    transform-origin: top left;
    transform: scale(calc(100vw / 1600px));
  }
  
  .main-container {
    min-width: 1600px;
  }
  
  .control-panel,
  .info-panel {
    width: 250px;
    min-width: 250px;
  }
}

/* 响应式设计 - 保持水平布局，但在极小屏幕上调整
@media (max-width: 500px) {
  .main-container {
    flex-direction: column;
    align-items: center;
  }
  
  .control-panel,
  .info-panel {
    width: 100%;
    max-width: 700px;
  }
}

添加媒体查询，确保在小屏幕上也能正常显示
@media (max-width: 768px) {
  .canvas-panel {
    overflow-x: auto;
  }
} */
</style>