<script setup>
import { onMounted, onBeforeUnmount, inject, computed } from 'vue';
import ws from '../utils/ws.js';

import { ref } from 'vue';

const isCoolingDown = ref(false);
const remainingTime = ref(0);
const totalTime = ref(0);
let countdownInterval = null;

const cooldownEventBus = inject('cooldownEventBus')

// 计算进度百分比
const progressPercent = computed(() => {
  if (!isCoolingDown.value || totalTime.value === 0) return 100;
  return Math.max(0, ((totalTime.value - remainingTime.value) / totalTime.value) * 100);
});

// 暴露给父组件的方法
defineExpose({
  startCooldown
});

// 倒计时结束时通知
function onFinish() {
  cooldownEventBus.emit({ type: 'cooldown-end' })
}

function startCooldown(limitTime) {
  isCoolingDown.value = true;
  remainingTime.value = limitTime;
  totalTime.value = limitTime;
  
  clearInterval(countdownInterval);

  countdownInterval = setInterval(() => {
    remainingTime.value--;
    if (remainingTime.value <= 0) {
      clearInterval(countdownInterval);
      isCoolingDown.value = false;
      totalTime.value = 0;
      onFinish();
    }
  }, 1000);
}
</script>

<template>
  <div class="cooldown-card card" :class="{ active: isCoolingDown }">
    <h3 class="card-title">状态</h3>
    <div class="cooldown-body">
      <template v-if="isCoolingDown">
        <div class="cooldown-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <span class="progress-time">{{ remainingTime }}s</span>
        </div>
        <p class="cooldown-text">冷却中，请稍候...</p>
      </template>
      <template v-else>
        <div class="ready-indicator">
          <span class="ready-dot"></span>
          <span class="ready-text">可以放置像素</span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border-light);
  transition: border-color 0.3s ease;
}

.card.active {
  border-color: var(--warning);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light);
}

.cooldown-body {
  min-height: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* 冷却进度条 */
.cooldown-progress {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: var(--border-light);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--warning), #f97316);
  border-radius: 4px;
  transition: width 1s linear;
}

.progress-time {
  font-size: 14px;
  font-weight: 700;
  color: var(--warning);
  min-width: 30px;
  text-align: right;
}

.cooldown-text {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--text-secondary);
}

/* 就绪状态 */
.ready-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ready-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
  animation: pulse 2s ease-in-out infinite;
}

.ready-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
