<script setup>
import { ref, onMounted } from 'vue';

// 颜色选择器属性
const props = defineProps({
  modelValue: { type: String, required: true }
});

// 颜色选择器事件
const emit = defineEmits(['update:modelValue']);

// 色盘canvas引用
const colorPickerCanvas = ref(null);
// 颜色输入框引用
const colorInput = ref(null);

// 常用颜色
const commonColors = ref([
  '#9AC8E2', '#DB7D74', '#B8A6D9', '#E799B0', '#576690', '#FFFFFF'
]);

// 组件挂载后绘制色盘
onMounted(() => {
  drawColorPicker(colorPickerCanvas.value);
});

// 选择颜色
function selectColor(color) {
  emit('update:modelValue', color);
}

// 处理颜色输入
function handleColorInput(event) {
  const color = event.target.value;
  // 验证颜色格式是否正确
  if (isValidColor(color) || color === '' || (color.startsWith('#') && color.length < 7)) {
    // 只有在颜色有效、为空或者以#开头但长度小于7（正在输入中）时才更新
    emit('update:modelValue', color);
  } else {
    // 如果颜色无效，则清空选择
    emit('update:modelValue', '');
  }
}

// 验证颜色格式是否正确
function isValidColor(color) {
  if (!color) return false;
  
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = color;
  
  // 如果颜色有效，fillStyle会保持原值或转换为标准格式
  // 如果颜色无效，fillStyle会变成默认值（通常是#000000）
  return ctx.fillStyle !== '#000000' || 
         color === '#000000' || 
         color.toLowerCase() === 'black' ||
         color === '#000' ||
         color === 'rgb(0, 0, 0)';
}

// 处理色盘点击事件
function handleColorPickerClick(event) {
  const canvas = colorPickerCanvas.value;
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  
  const ctx = canvas.getContext('2d');
  const imageData = ctx.getImageData(x, y, 1, 1);
  const [r, g, b] = imageData.data;
  const hexColor = `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`.toUpperCase();
  
  selectColor(hexColor);
}

// 启用吸管工具
async function activateEyedropper() {
  if (!('EyeDropper' in window)) {
    alert('您的浏览器不支持吸管工具。请使用支持EyeDropper API的浏览器，如Chrome 95+。');
    return;
  }

  try {
    const eyeDropper = new EyeDropper();
    const result = await eyeDropper.open();
    selectColor(result.sRGBHex);
  } catch (error) {
    // 用户取消操作或其他错误
    console.log('吸管工具操作被取消或出现错误:', error);
  }
}

// 绘制渐变色盘
function drawColorPicker(canvas) {
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  canvas.width = 200;
  canvas.height = 150;
  
  // 创建水平渐变 (彩虹色)
  const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
  gradient.addColorStop(0, 'red');
  gradient.addColorStop(0.16, 'orange');
  gradient.addColorStop(0.33, 'yellow');
  gradient.addColorStop(0.5, 'green');
  gradient.addColorStop(0.66, 'blue');
  gradient.addColorStop(0.83, 'indigo');
  gradient.addColorStop(1, 'violet');
  
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  // 创建垂直渐变 (白色到黑色) 覆盖在彩虹色上
  const verticalGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  verticalGradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
  verticalGradient.addColorStop(0.5, 'rgba(255, 255, 255, 0)');
  verticalGradient.addColorStop(0.5, 'rgba(0, 0, 0, 0)');
  verticalGradient.addColorStop(1, 'rgba(0, 0, 0, 1)');
  
  ctx.fillStyle = verticalGradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
}
</script>

<template>
  <div class="color-picker">
    <h3>颜色选择器</h3>
    
    <!-- 渐变色盘 -->
    <div class="color-picker-section">
      <h4>色盘</h4>
      <canvas 
        ref="colorPickerCanvas"
        class="color-picker-canvas"
        @click="handleColorPickerClick"
      ></canvas>
    </div>
    
    <!-- 常用颜色 -->
    <div class="common-colors-section">
      <h4>常用颜色</h4>
      <div class="common-colors">
        <div 
          v-for="color in commonColors" 
          :key="color"
          class="color-option common-color"
          :class="{ selected: modelValue === color }"
          :style="{ backgroundColor: color }"
          @click="selectColor(color)"
        ></div>
      </div>
    </div>
    
    <!-- 颜色输入框 -->
    <div class="color-input-section">
      <h4>自定义颜色</h4>
      <div class="color-input-container">
        <input 
          ref="colorInput"
          type="text" 
          :value="modelValue" 
          @input="handleColorInput"
          placeholder="#RRGGBB 或颜色名称"
          class="color-input"
        />
        <button 
          @click="activateEyedropper" 
          class="eyedropper-btn"
          title="吸管工具"
        >
          🎯
        </button>
      </div>
    </div>
    
    <div class="selected-color">
      当前选择: 
      <span class="color-preview" :style="{ backgroundColor: modelValue }"></span>
      {{ modelValue }}
    </div>
  </div>
</template>

<style scoped>
.color-picker {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.color-picker h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.color-picker h4 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  font-weight: 600;
}

.color-picker-section {
  margin-bottom: 15px;
}

.color-picker-canvas {
  width: 200px;
  height: 150px;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
}

.common-colors-section {
  margin-bottom: 15px;
}

.common-colors {
  display: flex;
  gap: 8px;
}

.color-option {
  width: 30px;
  height: 30px;
  border: 2px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.color-option:hover {
  border-color: #333;
}

.color-option.selected {
  border-color: #333;
  box-shadow: 0 0 0 2px white, 0 0 0 4px #333;
}

.common-color {
  width: 40px;
  height: 40px;
  border-radius: 6px;
}

.color-input-section {
  margin-bottom: 15px;
}

.color-input-container {
  display: flex;
  gap: 5px;
}

.color-input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-family: monospace;
}

.eyedropper-btn {
  width: 40px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background-color: #f0f0f0;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.eyedropper-btn:hover {
  background-color: #e0e0e0;
}

.selected-color {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-preview {
  width: 20px;
  height: 20px;
  border: 1px solid #ccc;
  display: inline-block;
}
</style>