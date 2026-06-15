<script setup>
import { inject } from 'vue';

const props = defineProps({
  selectedColor: { type: String, required: true },
  cooldownSeconds: { type: Number, default: 0 },
  isCrosshairMode: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false }
});

const emit = defineEmits(['open-color-picker', 'place-pixel', 'toggle-crosshair']);

const showToast = inject('showToast');

function handlePlace() {
  if (props.cooldownSeconds > 0) {
    showToast?.(`冷却中，请等待 ${props.cooldownSeconds} 秒`, 'warning');
    return;
  }
  if (!props.isCrosshairMode) {
    showToast?.('请开启准星模式以精确放置', 'warning');
    return;
  }
  emit('place-pixel');
}
</script>

<template>
  <div class="mobile-toolbar">
    <!-- 颜色选择器入口 -->
    <button
      class="tool-btn color-btn"
      :style="{ backgroundColor: selectedColor || '#ffffff' }"
      @click="$emit('open-color-picker')"
      aria-label="打开颜色选择器"
    >
      <span class="icon">🎨</span>
    </button>

    <!-- 放置像素主按钮 -->
    <button
      class="place-btn"
      :class="{ cooling: cooldownSeconds > 0, disabled }"
      @click="handlePlace"
    >
      <span class="place-icon">✏️</span>
      <span class="place-text">
        {{ cooldownSeconds > 0 ? `冷却 ${cooldownSeconds}s` : '放置像素' }}
      </span>
    </button>

    <!-- 准星开关 -->
    <button
      class="tool-btn crosshair-btn"
      :class="{ active: isCrosshairMode }"
      @click="$emit('toggle-crosshair')"
      aria-label="切换准星模式"
    >
      <span class="icon">🎯</span>
    </button>
  </div>
</template>

<style scoped>
.mobile-toolbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-top: 1px solid var(--border, #e2e8f0);
  z-index: 200;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.08);
}

.tool-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--border, #e2e8f0);
  background: var(--bg-card, #ffffff);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--shadow, 0 1px 3px rgba(0, 0, 0, 0.1));
}

.tool-btn:active {
  transform: scale(0.95);
}

.color-btn {
  border-color: var(--selected-color, #e2e8f0);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.8), 0 2px 8px rgba(0, 0, 0, 0.15);
}

.icon {
  font-size: 22px;
  line-height: 1;
}

.place-btn {
  flex: 1;
  height: 50px;
  max-width: 240px;
  border: none;
  border-radius: 25px;
  background: linear-gradient(135deg, var(--primary, #6366f1), var(--primary-hover, #4f46e5));
  color: white;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
  transition: all 0.2s ease;
}

.place-btn:active {
  transform: scale(0.98);
}

.place-btn.cooling {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  box-shadow: 0 4px 14px rgba(245, 158, 11, 0.35);
  cursor: not-allowed;
}

.place-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.place-icon {
  font-size: 18px;
}

.crosshair-btn.active {
  border-color: var(--primary, #6366f1);
  background: var(--primary-light, #e0e7ff);
}
</style>
