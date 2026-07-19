# A手像素画板 - 多人在线协作像素艺术平台

> 灵感来源于 Reddit [r/place](https://www.reddit.com/r/place/) 的实时协作像素画板，让多名用户在同一块画布上同时创作像素艺术作品。

线上演示：<https://pixel-asoul.club/>

## ✨ 功能特性

- 🎨 **实时协作绘画** - 多用户同时在画布上放置像素，通过 WebSocket 实时同步
- 🌈 **颜色选择器** - 预设调色板、渐变取色、十六进制输入，并支持浏览器 EyeDropper 取色 API
- 🔍 **画布缩放与平移** - 鼠标滚轮缩放、拖拽移动、一键重置视图
- ⏱️ **频率限制与冷却** - 滑动窗口限流（默认 10 秒内 20 次），触发后进入冷却倒计时
- 📊 **实时统计** - 在线人数、累计访问人次、累计放置像素数实时展示
- 📱 **移动端适配** - 全屏画布、底部工具栏、准星模式、触控缩放与拖拽
- 🔍 **SEO 优化** - 完整的 meta 信息、Open Graph / Twitter Card、语义化 H1
- 🔄 **自动重连** - WebSocket 断线后自动重连（最多 5 次）

## 🛠️ 技术栈

| 层 | 技术 |
| --- | --- |
| 前端框架 | Vue 3 (Composition API) |
| 构建工具 | Vite 7 |
| 渲染 | HTML5 Canvas |
| 通信 | WebSocket |
| 后端框架 | FastAPI |
| 实时通信 | WebSocket + Redis Pub/Sub |
| 热数据缓存 | Redis（画布状态、计数器、限流） |
| 持久化 | PostgreSQL（像素日志、快照元数据） |
| 图像处理 | Pillow + NumPy |

## 🏗️ 架构概览

```
┌──────────────┐   WebSocket (/ws/canvas)   ┌────────────────────────────┐
│  Vue 3 前端   │ ◄─────────────────────────► │       FastAPI 后端          │
│  (Canvas渲染)  │                            │                            │
└──────────────┘   GET /api/v1/snapshots/*   │  ┌──────────────────────┐  │
                                              │  │  ConnectionManager    │  │
                                              │  │  (跨进程 Pub/Sub 扇出) │  │
                                              │  └──────────────────────┘  │
                                              │  ┌──────────────────────┐  │
                                              │  │  RateLimiter (滑动窗口)│  │
                                              │  └──────────────────────┘  │
                                              │  ┌──────────────────────┐  │
                                              │  │  CanvasService        │  │
                                              │  │  Redis 画布 + PG 日志  │  │
                                              │  └──────────────────────┘  │
                                              └───────────┬─────┬──────────┘
                                                          │     │
                                            ┌─────────────▼─┐ ┌─▼──────────┐
                                            │     Redis     │ │ PostgreSQL │
                                            │ 画布/计数器/锁 │ │ 日志/快照   │
                                            └───────────────┘ └────────────┘
```

### 像素放置数据流

1. 客户端通过 `/ws/canvas` 发送 `pixel_update` 消息
2. `RateLimiter` 滑动窗口校验每连接请求频率
3. `PixelUpdateEvent` 校验（`app/schemas/events.py`）
4. `CanvasService.process_pixel_update` 更新 Redis 热画布，并向 PostgreSQL 写入 `PixelLog` 持久化
5. 累加 `pixel_logs_since_last_snapshot` 计数器，达到阈值（默认 250）时触发后台快照任务
6. 通过 Redis Pub/Sub 频道 `canvas_updates` 广播给所有连接，并同步最新统计

### 画布与快照

- **画布存储**：Redis 列表 `canvas`，扁平索引 `y * CANVAS_WIDTH + x`，元素为 `#RRGGBB` 字符串
- **快照**：PNG + JSON 文件存于 `pixel_back/app/snapshots/`，元数据记录在 `canvas_snapshots` 表；计数器达阈值或定时（默认 300s）触发
- **启动恢复**：加载最新快照 PNG/JSON，重放 `id > last_log_id` 的像素日志，分块（每 1000 条）回填 Redis 画布；通过 Redis 锁 `canvas_initialization_lock` 防止多 worker 并发初始化

## 📁 项目结构

```
pixel-asoul/
├── pixel_front/              # Vue 3 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── CanvasBoard.vue      # 画布渲染、缩放/平移、像素放置
│   │   │   ├── ColorPicker.vue      # 颜色选择（调色板/渐变/Hex/EyeDropper）
│   │   │   ├── CooldownTimer.vue    # 冷却倒计时
│   │   │   ├── FloatingToolbar.vue  # 悬浮工具栏
│   │   │   └── MobileToolbar.vue    # 移动端底部工具栏
│   │   ├── utils/ws.js             # WebSocket 单例（自动重连、事件分发）
│   │   └── App.vue
│   └── vite.config.js             # 开发代理到线上后端
│
└── pixel_back/              # FastAPI 后端
    ├── app/
    │   ├── main.py                 # 入口：Redis 连接池 + 画布初始化
    │   ├── config.py               # 环境变量与默认值
    │   ├── deps.py                 # 全局依赖（DB 会话、Redis 池）
    │   ├── api/snapshots.py        # 快照 REST 接口
    │   ├── websocket/
    │   │   ├── endpoints.py        # /ws/canvas 入口与事件分发
    │   │   └── manager.py          # 连接注册 + Redis Pub/Sub 广播
    │   ├── redis_store/
    │   │   ├── canvas.py           # Redis 画布原语
    │   │   └── visit_stats.py      # 访问/统计计数器
    │   ├── db/                     # SQLAlchemy 模型、CRUD、会话
    │   ├── services/
    │   │   ├── canvas_service.py   # 编排：Redis + DB + 文件系统
    │   │   ├── canvas_initializer.py # 启动恢复
    │   │   └── stats_service.py
    │   ├── schemas/events.py       # WebSocket 事件校验
    │   └── snapshots/              # 运行时快照文件（PNG/JSON）
    └── requirements.txt
```

## 🚀 快速开始

前端与后端是两个独立子项目，无 monorepo 工具联动，需分别启动。

### 后端

依赖 Python 3.10+、Redis、PostgreSQL。

```bash
cd pixel_back
pip install -r requirements.txt

# 复制并填写环境变量
cp .env.example .env

# 需在 pixel_back 目录下运行，使 app.main:app 正确解析
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后可访问：

- `GET /health`
- `GET /api/v1/snapshots/latest.png`
- `GET /api/v1/snapshots/latest/dataurl`
- `GET /api/v1/snapshots/update`
- `WebSocket /ws/canvas`

### 前端

依赖 Node.js + npm。

```bash
cd pixel_front
npm install
npm run dev      # http://localhost:8080
npm run build    # 产物输出至 dist/
npm run preview  # 预览生产构建
```

> 开发模式下，`vite.config.js` 会把 `/api` 与 `/ws` 代理到 `https://pixel-asoul.club`（本地后端在生产中通常位于 Nginx 之后）。如需对接本地后端，请修改代理 target。
>
> 生产环境由 Nginx 处理反代，前端运行时根据 `window.location.host` 决定后端地址，无需单独配置 API base URL。

## ⚙️ 配置

后端环境变量与默认值见 `pixel_back/.env.example` 与 `pixel_back/app/config.py`，关键项：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `CANVAS_WIDTH` / `CANVAS_HEIGHT` | `1000` / `1000` | 画布尺寸 |
| `SNAPSHOT_THRESHOLD` | `250` | 触发快照的像素日志阈值 |
| `SNAPSHOT_INTERVAL` | `300` | 定时快照间隔（秒） |
| `SNAPSHOT_DIRECTORY` | `snapshots` | 快照文件目录 |
| `MAX_REQUESTS` | `20` | 限流窗口内最大请求数 |
| `WINDOW_SIZE_SECONDS` | `10` | 限流滑动窗口（秒） |
| `REDIS_*` / `POSTGRES_*` | - | Redis / PostgreSQL 连接信息 |

## 🎯 使用说明

1. **选择颜色** - 在颜色选择器中选取预设色、渐变色或输入十六进制
2. **放置像素** - 点击画布任意位置放置像素
3. **缩放视图** - 鼠标滚轮放大/缩小（移动端双指缩放）
4. **移动画布** - 按住拖拽平移视图
5. **重置视图** - 点击「重置视图」恢复初始视角
6. **冷却等待** - 触发频率限制后，等待冷却倒计时结束

## 📝 注意事项

- 放置像素有频率限制（默认 10 秒内 20 次，约 2 次/秒），触发后进入冷却
- 快照元数据（PostgreSQL）必须与 `pixel_back/app/snapshots/` 下的文件保持一致，删除/重命名文件而不更新数据库会破坏启动恢复
- 建议使用现代浏览器（Chrome、Firefox、Edge 等）

## 📄 License

MIT
