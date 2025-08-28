<script setup>
import { onMounted, onBeforeUnmount } from 'vue';
import ws from '../utils/ws.js';

// 冷却时间属性
const props = defineProps({
  initialCooldown: { type: Number, default: 5 } // 默认冷却时间为5秒
});

// 初始化WebSocket监听器
onMounted(() => {
  // 移除对cooldown_update事件的监听
});

// 清理
onBeforeUnmount(() => {
  // 移除事件监听器清理
});
</script>

<template>
  <div class="cooldown-display">
    <h3>冷却时间</h3>
    <div class="cooldown-timer">
      可以随时放置像素
    </div>
  </div>
</template>

<style scoped>
.cooldown-display {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.cooldown-display h3 {
  margin-top: 0;
  margin-bottom: 10px;
}

.cooldown-timer {
  font-size: 18px;
  font-weight: bold;
  min-height: 27px;
  color: #333;
}
</style>