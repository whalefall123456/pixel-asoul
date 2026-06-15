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
  onlineCount: 0,
  totalVisits: 0,
  totalPixels: 0
});

// Toast 通知
const toasts = ref([]);
let toastId = 0;

function showToast(message, type = 'warning', duration = 3000) {
  const id = ++toastId;
  toasts.value.push({ id, message, type });
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id);
  }, duration);
}

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
provide('showToast', showToast)

// 连接到WebSocket服务器
onMounted(() => {
  const wsUrl = window.location.protocol === 'https:' 
    ? `wss://${window.location.host}/ws/canvas` 
    : `ws://${window.location.host}/ws/canvas`;
  ws.connect(wsUrl);

  // 监听限制消息
  ws.on('limited', (data) => {
    showToast(data.error_message || '操作过于频繁，请稍后再试', 'warning');
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
    <!-- Toast 通知 -->
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast-item"
          :class="toast.type"
        >
          <span class="toast-icon">{{ toast.type === 'warning' ? '⚠' : toast.type === 'error' ? '✕' : '✓' }}</span>
          <span class="toast-message">{{ toast.message }}</span>
        </div>
      </TransitionGroup>
    </div>

    <!-- 顶部导航 -->
    <header class="app-header">
      <div class="header-left">
        <div class="logo">
          <span class="logo-icon">🎨</span>
          <div class="logo-text">
            <h1 class="title">A手像素画板</h1>
            <p class="subtitle">多人在线像素艺术协作平台</p>
          </div>
        </div>
      </div>
      <div class="header-right">
        <div class="stats-bar">
          <div class="stat-chip">
            <span class="stat-dot online"></span>
            <span class="stat-num">{{ stats.onlineCount }}</span>
            <span class="stat-label">在线</span>
          </div>
          <div class="stat-chip">
            <span class="stat-dot visits"></span>
            <span class="stat-num">{{ stats.totalVisits }}</span>
            <span class="stat-label">访问</span>
          </div>
          <div class="stat-chip">
            <span class="stat-dot pixels"></span>
            <span class="stat-num">{{ stats.totalPixels }}</span>
            <span class="stat-label">像素</span>
          </div>
        </div>
      </div>
    </header>

    <!-- 主体内容 -->
    <div class="main-container">
      <!-- 左侧工具面板 -->
      <aside class="panel panel-left">
        <ColorPicker v-model="selectedColor" />
        <CooldownTimer ref="cooldownTimer" />
        <button @click="resetCanvasView" class="reset-view-btn">
          <span class="btn-icon">↻</span>
          重置视图
        </button>
      </aside>

      <!-- 中间画布区域 -->
      <main class="canvas-area">
        <CanvasBoard
          ref="canvasBoard"
          :selected-color="selectedColor"
          @pixel-placed="() => {}"
        />
      </main>

      <!-- 右侧信息面板 -->
      <aside class="panel panel-right">
        <div class="card">
          <h3 class="card-title">使用说明</h3>
          <ul class="guide-list">
            <li><span class="guide-key">选色</span> 左侧选择颜色</li>
            <li><span class="guide-key">绘制</span> 点击画布放置像素</li>
            <li><span class="guide-key">缩放</span> 鼠标滚轮缩放</li>
            <li><span class="guide-key">移动</span> 按住鼠标拖拽</li>
            <li><span class="guide-key">限速</span> 放置频率平均 2/s</li>
            <li><span class="guide-key">协作</span> 与其他用户实时创作</li>
          </ul>
          <div class="tip-box">
            点击吸管工具可吸取画布上的颜色，部分浏览器可能不支持。
          </div>
        </div>

        <div class="card bili-card">
          <div class="bili-link">
            <img src="./assets/bilibili_play.png" alt="Bilibili" class="bili-icon" />
            <a href="https://www.bilibili.com/video/BV1wscrz3ERL" target="_blank" rel="noopener noreferrer">
              绘画过程可视化
            </a>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-body);
}

/* ===== Toast 通知 ===== */
.toast-container {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  box-shadow: var(--shadow-lg);
  pointer-events: auto;
  white-space: nowrap;
}

.toast-item.warning {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
}

.toast-item.error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.toast-item.success {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(-12px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ===== 顶部导航 ===== */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.3;
}

.header-right {
  display: flex;
  align-items: center;
}

.stats-bar {
  display: flex;
  gap: 12px;
}

.stat-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-body);
  border-radius: 20px;
  font-size: 13px;
}

.stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.stat-dot.online {
  background: var(--success);
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
}

.stat-dot.visits {
  background: var(--primary);
}

.stat-dot.pixels {
  background: var(--warning);
}

.stat-num {
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  color: var(--text-secondary);
  font-size: 12px;
}

/* ===== 主体布局 ===== */
.main-container {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px 24px;
  max-width: 1800px;
  margin: 0 auto;
  width: 100%;
}

/* ===== 侧边面板 ===== */
.panel {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ===== 画布区域 ===== */
.canvas-area {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-width: 0;
}

/* ===== 卡片通用 ===== */
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border-light);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light);
}

/* ===== 使用说明 ===== */
.guide-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.guide-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.guide-key {
  display: inline-block;
  min-width: 36px;
  padding: 2px 6px;
  background: var(--primary-light);
  color: var(--primary);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  flex-shrink: 0;
}

.tip-box {
  margin-top: 12px;
  padding: 10px;
  background: #fffbeb;
  border: 1px solid #fef3c7;
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: #92400e;
  line-height: 1.5;
}

/* ===== 重置视图按钮 ===== */
.reset-view-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 10px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.reset-view-btn:hover {
  background: var(--primary-light);
  color: var(--primary);
  border-color: var(--primary);
}

.btn-icon {
  font-size: 16px;
}

/* ===== B站链接 ===== */
.bili-card {
  padding: 12px 16px;
}

.bili-link {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bili-icon {
  width: 48px;
  height: 48px;
  object-fit: contain;
  border-radius: var(--radius-sm);
}

.bili-link a {
  color: #00AEEC;
  font-size: 15px;
  font-weight: 600;
  transition: color var(--transition);
}

.bili-link a:hover {
  color: #0083b0;
}

/* ===== 响应式 ===== */
@media (max-width: 1600px) {
  .main-container {
    padding: 12px 16px;
    gap: 12px;
  }
  .panel {
    width: 240px;
  }
}

@media (max-width: 1200px) {
  .app-header {
    flex-direction: column;
    gap: 8px;
    padding: 10px 16px;
  }
  .main-container {
    flex-direction: column;
    align-items: center;
  }
  .panel {
    width: 100%;
    max-width: 700px;
    flex-direction: row;
    flex-wrap: wrap;
  }
  .panel > * {
    flex: 1;
    min-width: 200px;
  }
}
</style>
