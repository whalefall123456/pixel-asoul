<script setup>
import { ref, onMounted } from 'vue';
import CanvasBoard from './components/CanvasBoard.vue';
import ColorPicker from './components/ColorPicker.vue';
import CooldownTimer from './components/CooldownTimer.vue';
import ws from './utils/ws.js';

// 状态管理
const selectedColor = ref('#FF0000');
const canvasBoard = ref(null);

// 连接到WebSocket服务器
onMounted(() => {
  // 初始化WebSocket连接
  // 在生产环境中，使用相对路径连接到当前域的WebSocket服务
  const wsUrl = window.location.protocol === 'https:' 
    ? `wss://${window.location.host}/ws/canvas` 
    : `ws://${window.location.host}/ws/canvas`;
  ws.connect(wsUrl);
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
    <h1 class="title">多人在线像素画布</h1>
    
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
            <li>可以随时放置像素</li>
            <li>与其他用户实时协作创作</li>
            <li>鼠标滚轮缩放画布</li>
            <li>按住鼠标拖拽移动画布</li>
          </ul>
          <p class="mock-mode-notice">
            <strong>提示:</strong> 点击吸管工具可吸取画布上的颜色，部分浏览器可能不支持。
          </p>
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
  min-width: 1600px; /* 确保应用程序有最小宽度 */
}

.title {
  text-align: center;
  margin-bottom: 30px;
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

/* 响应式设计 - 保持水平布局，但在极小屏幕上调整 */
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

/* 添加媒体查询，确保在小屏幕上也能正常显示 */
@media (max-width: 768px) {
  .canvas-panel {
    overflow-x: auto;
  }
}
</style>