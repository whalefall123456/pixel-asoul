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

// 预设颜色 - 分组排列
const presetColors = [
  // 基础色
  '#FFFFFF', '#C0C0C0', '#808080', '#000000',
  // 红色系
  '#FF0000', '#CC0000', '#990000', '#660000',
  // 橙色系
  '#FF8800', '#CC6600', '#994400', '#663300',
  // 黄色系
  '#FFFF00', '#CCCC00', '#999900', '#666600',
  // 绿色系
  '#00FF00', '#00CC00', '#009900', '#006600',
  // 青色系
  '#00FFFF', '#00CCCC', '#009999', '#006666',
  // 蓝色系
  '#0000FF', '#0000CC', '#000099', '#000066',
  // 紫色系
  '#8800FF', '#6600CC', '#440099', '#330066',
  // 粉色系
  '#FF00FF', '#CC00CC', '#990099', '#660066',
  // 皮肤色
  '#FFDAB9', '#F5DEB3', '#D2B48C', '#8B4513',
  // ASOUL 相关色
  '#9AC8E2', '#DB7D74', '#B8A6D9', '#E799B0', '#576690',
];

// 选择颜色
function selectColor(color) {
  emit('update:modelValue', color);
}

// 处理颜色输入
function handleColorInput(event) {
  const color = event.target.value;
  if (isValidColor(color) || color === '' || (color.startsWith('#') && color.length < 7)) {
    emit('update:modelValue', color);
  } else {
    emit('update:modelValue', '');
  }
}

// 验证颜色格式是否正确
function isValidColor(color) {
  if (!color) return false;
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = color;
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
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const x = (event.clientX - rect.left) * scaleX;
  const y = (event.clientY - rect.top) * scaleY;
  
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
    console.log('吸管工具操作被取消或出现错误:', error);
  }
}

// 绘制渐变色盘
function drawColorPicker(canvas) {
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  canvas.width = 220;
  canvas.height = 140;
  
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

// 组件挂载后绘制色盘
onMounted(() => {
  drawColorPicker(colorPickerCanvas.value);
});
</script>

<template>
  <div class="color-picker card">
    <h3 class="card-title">颜色选择器</h3>
    
    <!-- 渐变色盘 -->
    <div class="section">
      <canvas 
        ref="colorPickerCanvas"
        class="color-picker-canvas"
        @click="handleColorPickerClick"
      ></canvas>
    </div>
    
    <!-- 预设颜色 -->
    <div class="section">
      <div class="preset-grid">
        <div 
          v-for="color in presetColors" 
          :key="color"
          class="preset-color"
          :class="{ selected: modelValue === color }"
          :style="{ backgroundColor: color }"
          :title="color"
          @click="selectColor(color)"
        ></div>
      </div>
    </div>
    
    <!-- 颜色输入框 -->
    <div class="section">
      <div class="color-input-row">
        <div class="color-preview" :style="{ backgroundColor: modelValue || '#ffffff' }"></div>
        <input 
          ref="colorInput"
          type="text" 
          :value="modelValue" 
          @input="handleColorInput"
          placeholder="#RRGGBB"
          class="color-input"
        />
        <button 
          @click="activateEyedropper" 
          class="eyedropper-btn"
          title="吸管工具"
        >
          💉
        </button>
      </div>
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
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light);
}

.section {
  margin-bottom: 12px;
}

.section:last-child {
  margin-bottom: 0;
}

/* 色盘 */
.color-picker-canvas {
  width: 100%;
  height: 100px;
  border-radius: var(--radius-sm);
  cursor: crosshair;
  border: 1px solid var(--border);
  display: block;
}

/* 预设颜色网格 */
.preset-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 4px;
}

.preset-color {
  aspect-ratio: 1;
  border-radius: 4px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all var(--transition);
  position: relative;
}

.preset-color:hover {
  transform: scale(1.15);
  z-index: 1;
  border-color: var(--text-secondary);
}

.preset-color.selected {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-light);
  transform: scale(1.1);
  z-index: 1;
}

/* 颜色输入行 */
.color-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-preview {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--border);
  flex-shrink: 0;
  transition: border-color var(--transition);
}

.color-input {
  flex: 1;
  min-width: 0;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 13px;
  color: var(--text-primary);
  background: var(--bg-card);
  transition: border-color var(--transition);
  outline: none;
}

.color-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.eyedropper-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition);
  flex-shrink: 0;
}

.eyedropper-btn:hover {
  background: var(--primary-light);
  border-color: var(--primary);
}
</style>
