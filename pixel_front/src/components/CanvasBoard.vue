<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed, inject } from 'vue';
import ws from '../utils/ws.js';

// 画布配置
const props = defineProps({
  width: { type: Number, default: 1000 },
  height: { type: Number, default: 1000 },
  pixelSize: { type: Number, default: 1 },
  selectedColor: { type: String, required: true },
});

const cooldownEventBus = inject('cooldownEventBus')
const isCoolingDown = ref(false);
const emit = defineEmits(['pixel-placed']);
const containerRef = ref(null); // 新增：容器引用
// 响应式状态（translate 以"像素"为单位）
const canvasRef = ref(null);
const ctx = ref(null);

const isDragging = ref(false);
const scale = ref(1);               // 缩放比例，>= 1
const translateX = ref(0);          // 平移（px）
const translateY = ref(0);          // 平移（px）
const lastX = ref(0);
const lastY = ref(0);
const dragStartX = ref(0); // 新增：记录拖动开始时的X坐标
const dragStartY = ref(0); // 新增：记录拖动开始时的Y坐标
const dragThreshold = 5; // 拖动阈值，单位为像素
const isDraggingForPlacement = ref(false); // 新增：用于判断是否为放置像素的拖动

const dragScaleX = ref(1); // 新增：拖拽时的水平比例修正
const dragScaleY = ref(1); // 新增：拖拽时的垂直比例修正

// 悬停像素指示
const hoverPixelX = ref(-1);
const hoverPixelY = ref(-1);

// 一些便捷尺寸
const baseCanvasWidth = computed(() => props.width * props.pixelSize);
const baseCanvasHeight = computed(() => props.height * props.pixelSize);

// 容器样式：容器大小 = 基础画布大小（最小显示尺寸）
// 注意：border 宽度必须保持 2px，与 getLocalPosInContainer 中的 clientLeft 计算一致
const canvasContainerStyle = computed(() => ({
  width: `${baseCanvasWidth.value}px`,
  height: `${baseCanvasHeight.value}px`,
  backgroundColor: '#fff',
  border: '2px solid var(--border, #e2e8f0)',
  borderRadius: 'var(--radius, 10px)',
  boxShadow: '0 4px 12px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.06)',
  display: 'inline-block',
  flexShrink: 0,
  position: 'relative',
  overflow: 'hidden'
}));

// 注意：CSS transform 从右到左应用；我们使用 translate(...) scale(...)
// => 实际效果是"先 scale，再 translate（单位为像素）"
const canvasTransformStyle = computed(() => ({
  transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value})`,
  transformOrigin: '0 0'
}));




// 计算鼠标样式
const canvasCursor = computed(() => {
  return isCoolingDown.value ? 'not-allowed' : 'pointer';
});

onMounted(async () => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  ctx.value = canvas.getContext('2d');
  ctx.value.imageSmoothingEnabled = false;

  // 物理像素尺寸（绘制坐标系）
  canvas.width = baseCanvasWidth.value;
  canvas.height = baseCanvasHeight.value;


  // 事件
  canvas.addEventListener('click', handleCanvasClick);
  canvas.addEventListener('wheel', handleWheel, { passive: false });
  canvas.addEventListener('mousedown', handleMouseDown);
  canvas.addEventListener('mousemove', handleMouseMove);
  canvas.addEventListener('mouseup', handleMouseUp);
  canvas.addEventListener('mouseleave', handleMouseLeave);

  // WebSocket
  ws.on('pixel_update', handlePixelUpdate);
  ws.on('initial_canvas', drawFullCanvas);

  ws.on('limited', () => {
    isCoolingDown.value = true;
    // console.log('已进入冷却时间');
    // 立即更新游标样式
    if (canvasRef.value) {
      canvasRef.value.style.cursor = 'not-allowed';
    }
  });

  cooldownEventBus.on(handleCooldownEvent)

  // 初始指针
  canvas.style.cursor = 'pointer';
  
  // 获取并绘制最新图片，完成后执行更新
  await fetchAndDrawLatestImage();
  fetchAndDrawUpdate();
});

onBeforeUnmount(() => {
  const canvas = canvasRef.value;
  if (canvas) {
    canvas.removeEventListener('click', handleCanvasClick);
    canvas.removeEventListener('wheel', handleWheel);
    canvas.removeEventListener('mousedown', handleMouseDown);
    canvas.removeEventListener('mousemove', handleMouseMove);
    canvas.removeEventListener('mouseup', handleMouseUp);
    canvas.removeEventListener('mouseleave', handleMouseLeave);
  }
  ws.off('pixel_update', handlePixelUpdate);
  ws.off('initial_canvas', drawFullCanvas);
  cooldownEventBus.off(handleCooldownEvent)
});


// 画布尺寸相关变化时，重设物理像素并重新约束视图
watch(() => [props.pixelSize, props.width, props.height], () => {
  if (!canvasRef.value) return;
  const canvas = canvasRef.value;
  canvas.width = baseCanvasWidth.value;
  canvas.height = baseCanvasHeight.value;
  applyBoundaryConstraints(); // 保证仍不留空白
});




// ============ 缩放（滚轮） ============
function handleWheel(event) {
  event.preventDefault();

  const { x: mx, y: my } = getLocalPosInContainer(event);

  const zoomIntensity = 0.1;
  const factor = event.deltaY < 0 ? (1 + zoomIntensity) : (1 - zoomIntensity);

  let newScale = scale.value * factor;
  newScale = Math.min(40, Math.max(1, newScale));
  if (Math.abs(newScale - 1) < 1e-3) newScale = 1;

  // 以鼠标为锚点：mx = T'x + newScale * cx，其中 cx = (mx - Tx)/scale
  const cx = (mx - translateX.value) / scale.value;
  const cy = (my - translateY.value) / scale.value;

  scale.value = newScale;
  translateX.value = mx - scale.value * cx;
  translateY.value = my - scale.value * cy;

  applyBoundaryConstraints();
}

// ============ 拖拽（像素空间平移） ============
function handleMouseDown(event) {
  isDragging.value = true;
  lastX.value = event.clientX;
  lastY.value = event.clientY;
  dragStartX.value = event.clientX; // 记录拖动开始位置
  dragStartY.value = event.clientY; // 记录拖动开始位置
  isDraggingForPlacement.value = false; // 重置拖动标记

  // === 新增开始：计算拖拽比例 ===
  if (containerRef.value) {
    const el = containerRef.value;
    const rect = el.getBoundingClientRect();
    
    // 减去边框影响（与点击逻辑一致）
    const borderLeft = el.clientLeft || 0;
    const borderRight = borderLeft; // 假设对称
    const borderTop = el.clientTop || 0;
    const borderBottom = borderTop; // 假设对称

    const renderedContentWidth = rect.width - borderLeft - borderRight;
    const renderedContentHeight = rect.height - borderTop - borderBottom;

    // 计算比例：逻辑尺寸 / 实际渲染尺寸
    // 例如：逻辑1000 / 渲染500 = 2.0。意味着鼠标动1px，逻辑上要动2px。
    dragScaleX.value = renderedContentWidth > 0 ? baseCanvasWidth.value / renderedContentWidth : 1;
    dragScaleY.value = renderedContentHeight > 0 ? baseCanvasHeight.value / renderedContentHeight : 1;
  }
  // === 新增结束 ===

  if (canvasRef.value && !isCoolingDown.value) {
    canvasRef.value.style.cursor = 'grabbing';
  }
}

function handleMouseMove(event) {
  // 更新悬停像素位置（无论是否拖拽）
  updateHoverPixel(event);

  if (!isDragging.value) return;

  // 计算物理位移
  const rawDx = event.clientX - lastX.value;
  const rawDy = event.clientY - lastY.value;
  
  // === 修改：乘以比例系数，转换为逻辑位移 ===
  const dx = rawDx * dragScaleX.value;
  const dy = rawDy * dragScaleY.value;
  
  // 更新位置
  translateX.value += dx;
  translateY.value += dy;

  lastX.value = event.clientX;
  lastY.value = event.clientY;

  applyBoundaryConstraints();
}

function handleMouseUp() {
  // 检查鼠标释放位置与初始点击位置的距离
  const deltaX = Math.abs(lastX.value - dragStartX.value);
  const deltaY = Math.abs(lastY.value - dragStartY.value);
  
  // 如果移动距离超过阈值，则认为是拖动
  if (deltaX > dragThreshold || deltaY > dragThreshold) {
    isDraggingForPlacement.value = true;
  }
  
  isDragging.value = false;
  if (canvasRef.value) {
    canvasRef.value.style.cursor = isCoolingDown.value ? 'not-allowed' : 'pointer';
  }
}

// 更新悬停像素位置
function updateHoverPixel(event) {
  const { x: mx, y: my } = getLocalPosInContainer(event);
  const canvasX = (mx - translateX.value) / scale.value;
  const canvasY = (my - translateY.value) / scale.value;
  const px = Math.floor(canvasX / props.pixelSize);
  const py = Math.floor(canvasY / props.pixelSize);

  if (px >= 0 && px < props.width && py >= 0 && py < props.height) {
    hoverPixelX.value = px;
    hoverPixelY.value = py;
  } else {
    hoverPixelX.value = -1;
    hoverPixelY.value = -1;
  }
}

// 悬停高亮样式
const highlightStyle = computed(() => {
  if (hoverPixelX.value < 0 || hoverPixelY.value < 0 || isCoolingDown.value) return null;
  const ps = props.pixelSize;
  const s = scale.value;
  const tx = translateX.value + hoverPixelX.value * ps * s;
  const ty = translateY.value + hoverPixelY.value * ps * s;
  const size = ps * s;
  return {
    transform: `translate(${tx}px, ${ty}px)`,
    width: `${size}px`,
    height: `${size}px`,
  };
});

function handleMouseLeave() {
  handleMouseUp();
  hoverPixelX.value = -1;
  hoverPixelY.value = -1;
}

function handleCanvasClick(event) {
  // 如果是拖动浏览，则不执行像素放置
  if (isDraggingForPlacement.value) {
    isDraggingForPlacement.value = false; // 重置标记
    return;
  }
  //如果在冷却中，则不执行像素放置
  if (isCoolingDown.value) return;

  if (!canvasRef.value) return;

  // 用"容器内容区"的局部坐标（不受 transform 影响，也不包含边框）
  const { x: mx, y: my } = getLocalPosInContainer(event);

  // 反解到画布像素坐标系：container = translate + scale * canvas
  const canvasX = (mx - translateX.value) / scale.value;
  const canvasY = (my - translateY.value) / scale.value;

  const x = Math.floor(canvasX / props.pixelSize);
  const y = Math.floor(canvasY / props.pixelSize);

  if (x >= 0 && x < props.width && y >= 0 && y < props.height) {
    //测试
    console.log(`点击了像素 (${x}, ${y})`);
    ws.send('pixel_place', { x, y, color: props.selectedColor });
    emit('pixel-placed');
  }
}

// ============ 像素绘制 ============
function handlePixelUpdate(data) {
  drawPixel(data.x, data.y, data.color);
}

function drawFullCanvas(canvasData) {
  if (!ctx.value) return;
  ctx.value.clearRect(0, 0, baseCanvasWidth.value, baseCanvasHeight.value);
  for (let y = 0; y < props.height; y++) {
    for (let x = 0; x < props.width; x++) {
      const color = canvasData[y * props.width + x];
      drawPixel(x, y, color);
    }
  }
}


function drawPixel(x, y, color) {
  if (!ctx.value) return;
  ctx.value.fillStyle = color;
  ctx.value.fillRect(
    x * props.pixelSize,
    y * props.pixelSize,
    props.pixelSize,
    props.pixelSize
  );
}

// imageData 是后端返回的 data URL 格式: "data:image/png;base64,..."
// 直接把 PNG 快照绘制到画布上（1000x1000 按 pixelSize 缩放）
function drawPNGImageFromDataURL(imageData) {
  const startTime = performance.now();

  const img = new Image();
  img.src = imageData;

  img.onload = () => {
    if (!ctx.value) return;

    ctx.value.save();
    ctx.value.imageSmoothingEnabled = false;
    ctx.value.drawImage(img, 0, 0, baseCanvasWidth.value, baseCanvasHeight.value);
    ctx.value.restore();

    const endTime = performance.now();
    console.log(`drawPNGImageFromDataURL 运行时长: ${endTime - startTime} 毫秒`);
  };

  img.onerror = (error) => {
    console.error('加载 PNG 图像时出错:', error);
    const endTime = performance.now();
    console.log(`drawPNGImageFromDataURL 运行时长(失败): ${endTime - startTime} 毫秒`);
  };
}

// 从后端获取最新图片数据并绘制到画布
async function fetchAndDrawLatestImage() {
  try {
    const response = await fetch('/api/v1/snapshots/latest/dataurl');
    
    // 检查响应是否成功
    if (!response.ok) {
      console.warn(`获取最新图片失败: ${response.status} ${response.statusText}`);
      return;
    }
    
    // 检查内容类型
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      console.warn('响应不是JSON格式:', contentType);
      return;
    }
    
    const data = await response.json();
    
    // 检查返回的数据是否包含需要的字段
    if (!data.data_url) {
      console.warn('返回的数据缺少data_url字段:', data);
      return;
    }
    
    // 使用返回的data_url数据绘制画布
    drawPNGImageFromDataURL(data.data_url);
    
    return data;
  } catch (error) {
    console.error('获取或绘制最新图片时出错:', error);
  }
}

async function fetchAndDrawUpdate() {
  try {
    const response = await fetch('/api/v1/snapshots/update');
    
    // 检查响应是否成功
    if (!response.ok) {
      console.warn(`获取更新日志失败: ${response.status} ${response.statusText}`);
      return null;
    }
    
    // 检查内容类型
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      console.warn('响应不是JSON格式:', contentType);
      return null;
    }
    
    const data = await response.json();
    
    // 检查返回的数据是否包含需要的字段
    if (!data.logs) {
      console.warn('返回的数据缺少logs字段:', data);
      return null;
    }
    
    // 使用返回的logs数据绘制画布
    drawLogsToCanvas(data.logs);
    
    return data;
  } catch (error) {
    console.error('获取或绘制日志更新时出错:', error);
    return null;
  }
}

// 将后端返回的logs数据绘制到画布上
function drawLogsToCanvas(logs) {
  if (!ctx.value || !logs || !Array.isArray(logs)) return;
  
  // 保存当前上下文状态
  ctx.value.save();
  ctx.value.imageSmoothingEnabled = false;
  
  // 绘制每个日志记录的像素
  logs.forEach(log => {
    // 确保日志数据有效
    if (
      typeof log.x === 'number' && 
      typeof log.y === 'number' && 
      typeof log.color === 'string'
    ) {
      // 检查边界
      if (log.x >= 0 && log.x < props.width && log.y >= 0 && log.y < props.height) {
        drawPixel(log.x, log.y, log.color);
      }
    }
  });
  
  // 恢复上下文状态
  ctx.value.restore();
}

// ============ 边界约束（像素空间） ============
// 规则：不留空白。令基准宽高为 Cw, Ch；缩放后为 Sw, Sh；
// translateX ∈ [Cw - Sw, 0]，translateY ∈ [Ch - Sh, 0]；若 Sw<=Cw 则 translateX=0（最小填满容器）
function applyBoundaryConstraints() {
  const Cw = baseCanvasWidth.value;
  const Ch = baseCanvasHeight.value;
  const Sw = Cw * scale.value;
  const Sh = Ch * scale.value;

  const minTx = Math.min(0, Cw - Sw);
  const maxTx = 0;
  translateX.value = Math.min(maxTx, Math.max(minTx, translateX.value));

  const minTy = Math.min(0, Ch - Sh);
  const maxTy = 0;
  translateY.value = Math.min(maxTy, Math.max(minTy, translateY.value));
}

// 重置视图
function resetView() {
  scale.value = 1;
  translateX.value = 0;
  translateY.value = 0;
  applyBoundaryConstraints();
}

// 获取鼠标位置
function getLocalPosInContainer(event) {
  const el = containerRef.value;
  if (!el) return { x: 0, y: 0 };

  const rect = el.getBoundingClientRect();
  
  // 获取边框宽度（clientLeft 通常等于左边框宽度）
  // 我们假设 CSS 中边框是对称的 (border: 2px solid ...)
  const borderLeft = el.clientLeft || 0;
  const borderTop = el.clientTop || 0;
  const borderRight = borderLeft; // 假设左右边框相等
  const borderBottom = borderTop; // 假设上下边框相等

  // 1. 计算实际用于显示画布的“内容区域”的渲染宽高
  // 也就是：总渲染宽 - 左右边框
  const renderedContentWidth = rect.width - borderLeft - borderRight;
  const renderedContentHeight = rect.height - borderTop - borderBottom;

  // 2. 计算逻辑尺寸与渲染内容尺寸的比例
  // 逻辑宽度 (1000) / 渲染出的内容宽度 (例如 800)
  const scaleX = renderedContentWidth > 0 ? baseCanvasWidth.value / renderedContentWidth : 1;
  const scaleY = renderedContentHeight > 0 ? baseCanvasHeight.value / renderedContentHeight : 1;

  // 3. 计算坐标
  // (鼠标屏幕坐标 - 容器屏幕坐标 - 左边框厚度) * 比例
  const x = (event.clientX - rect.left - borderLeft) * scaleX;
  const y = (event.clientY - rect.top  - borderTop) * scaleY;

  return { x, y };
}

function handleCooldownEvent(event) { 
  if (event.type === 'cooldown-end') {
    // 处理冷却结束逻辑
    isCoolingDown.value = false
    // console.log('冷却结束')
    // 立即更新游标样式
    if (canvasRef.value) {
      canvasRef.value.style.cursor = 'pointer';
    }
  }
}

// 暴露方法
defineExpose({ resetView });
</script>


<template>
  <div :style="canvasContainerStyle" ref="containerRef">
    <canvas 
      ref="canvasRef"
      class="pixel-canvas"
      :style="{ ...canvasTransformStyle, cursor: canvasCursor }"
    ></canvas>
    <div 
      v-if="highlightStyle"
      class="pixel-highlight"
      :style="highlightStyle"
    ></div>
    <div v-if="hoverPixelX >= 0 && hoverPixelY >= 0" class="coord-badge">
      ({{ hoverPixelX }}, {{ hoverPixelY }})
    </div>
  </div>
</template>


<style scoped>
.pixel-canvas {
  display: block;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
  transform-origin: 0 0;
}

.pixel-highlight {
  position: absolute;
  top: 0;
  left: 0;
  background: rgba(99, 102, 241, 0.3);
  border: 1.5px solid rgba(99, 102, 241, 0.8);
  pointer-events: none;
  z-index: 1;
}

.coord-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  padding: 3px 8px;
  background: rgba(30, 41, 59, 0.8);
  color: #fff;
  font-size: 12px;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  border-radius: 4px;
  pointer-events: none;
  z-index: 10;
}
</style>
