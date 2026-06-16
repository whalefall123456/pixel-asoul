<script setup>
defineEmits(['zoom-in', 'zoom-out', 'reset-view', 'toggle-info']);
</script>

<template>
  <div class="floating-toolbar">
    <button class="fab" @click="$emit('zoom-in')" aria-label="放大" title="放大">
      <span class="fab-icon">➕</span>
    </button>
    <button class="fab" @click="$emit('zoom-out')" aria-label="缩小" title="缩小">
      <span class="fab-icon">➖</span>
    </button>
    <button class="fab" @click="$emit('reset-view')" aria-label="重置视图" title="重置视图">
      <span class="fab-icon">↻</span>
    </button>
    <button class="fab" @click="$emit('toggle-info')" aria-label="使用说明" title="使用说明">
      <span class="fab-icon">ℹ️</span>
    </button>
  </div>
</template>

<style scoped>
.floating-toolbar {
  position: fixed;
  top: 60px;
  right: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 150;
}

.fab {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--bg-card, #ffffff);
  box-shadow: var(--shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 18px;
}

.fab:active {
  transform: scale(0.92);
  background: var(--primary-light, #e0e7ff);
}

.fab-icon {
  line-height: 1;
}
</style>
