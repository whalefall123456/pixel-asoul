from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.redis_store.canvas import CanvasStore
from app.schemas.events import PixelUpdateEvent
from app.utils.logger import logger
import app.deps as deps
from redis import asyncio as aioredis
import json
import time
import asyncio
from app.services.canvas_service import CanvasService, create_snapshot_background
from app.services.stats_service import StatsService
from app.utils.utils import extract_client_ip_from_websocket
from app.websocket.manager import ConnectionManager, RateLimiter
from datetime import datetime
from app.config import MAX_REQUESTS,WINDOW_SIZE_SECONDS,CLEANUP_INTERVAL_MINUTES

# Create connection manager for this module
manager = ConnectionManager()
limiter = RateLimiter(max_requests=MAX_REQUESTS, window_size_seconds=WINDOW_SIZE_SECONDS, cleanup_interval_minutes=CLEANUP_INTERVAL_MINUTES)

router = APIRouter()


@router.websocket("/ws/canvas")
async def canvas_websocket(websocket: WebSocket):
    """WebSocket endpoint for canvas updates."""
    # 初始化Redis连接用于pub/sub
    await manager.init_redis()
    connection_id = await manager.connect(websocket)
    client_ip = extract_client_ip_from_websocket(websocket)
    # Get Redis connection from pool
    redis = aioredis.Redis(connection_pool=deps.redis_pool)
    canvas_store = CanvasStore(redis)
    stats_service = StatsService(redis)

    # Track connection-based counters in Redis
    await manager.broadcast(json.dumps({"type": "visit_stats", "data": await stats_service.handle_connect(client_ip)}))

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            # 检查是否允许发送新请求
            is_allowed = await limiter.is_allowed(connection_id)
            if not is_allowed:
                request_times, _ = limiter.clients[connection_id]
                limit_time = WINDOW_SIZE_SECONDS - int((datetime.now() - request_times[0]).total_seconds())
                await manager.send_personal_message(
                    json.dumps({
                        "type": "limited",
                        "data": {
                            "error_message": "频率过高，请稍后",
                            "limit_time": limit_time
                        }
                    }),
                    websocket
                )
                continue

            if message["type"] == "pixel_update":
                # Process pixel update
                event = PixelUpdateEvent(**message["data"])
                log_id = None

                # 更新redis并记录日志到数据库
                async with deps.get_db_session() as db_session:
                    canvas_service = CanvasService(canvas_store, db_session)
                    log_id = await canvas_service.process_pixel_update(event)
                    stats_data = await stats_service.handle_pixel_placed(1)
                    await deps.increment_pixel_logs_counter()
                    # 检查是否需要创建快照
                    if await deps.async_should_create_snapshot():
                        await deps.reset_pixel_logs_counter()
                        # 使用后台任务创建快照，避免阻塞WebSocket消息处理
                        asyncio.create_task(create_snapshot_background(log_id, canvas_store))
                
                # 发送更新并记录执行时间
                start_time = time.time()
                await manager.broadcast(json.dumps({"type": "pixel_update", "data": message["data"]}))
                await manager.broadcast(json.dumps({"type": "visit_stats", "data": stats_data}))
                elapsed_time = time.time() - start_time
                logger.info(f"Broadcast message took {elapsed_time:.4f} seconds")
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Keep in-memory connection state and online counter in sync.
        manager.disconnect(connection_id=connection_id)
        await manager.broadcast(json.dumps({"type": "visit_stats", "data": await stats_service.handle_disconnect()}))
        # Close Redis connection (returns it to the pool)
        await redis.close()