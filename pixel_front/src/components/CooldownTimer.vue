<script setup>
import { onMounted, onBeforeUnmount, inject } from 'vue';
import ws from '../utils/ws.js';

import { ref } from 'vue';

const isCoolingDown = ref(false);
const remainingTime = ref(0);
let countdownInterval = null;

const cooldownEventBus = inject('cooldownEventBus')

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
  
  clearInterval(countdownInterval);

  countdownInterval = setInterval(() => {
    remainingTime.value--;
    if (remainingTime.value <= 0) {
      clearInterval(countdownInterval);
      isCoolingDown.value = false;
      // 倒计时结束通知其他组件
      onFinish();
    }
  }, 1000);
}

</script>

<template>
  <div class="cooldown-display">
    <h3>冷却时间</h3>
    <div class="cooldown-timer">
      {{ isCoolingDown ? `${remainingTime}秒后可以放置像素` : '可以随时放置像素' }}
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