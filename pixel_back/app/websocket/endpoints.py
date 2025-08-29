from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.redis_store.canvas import CanvasStore
from app.schemas.events import PixelUpdateEvent
from app.utils.logger import logger
import app.deps as deps
from redis import asyncio as aioredis
import json
import time
from app.services.canvas_service import CanvasService
from app.websocket.manager import ConnectionManager

# Create connection manager for this module
manager = ConnectionManager()

router = APIRouter()


@router.websocket("/ws/canvas")
async def canvas_websocket(websocket: WebSocket):
    """WebSocket endpoint for canvas updates."""
    # 初始化Redis连接用于pub/sub
    await manager.init_redis()
    connection_id = await manager.connect(websocket)
    
    # Get Redis connection from pool
    redis = aioredis.Redis(connection_pool=deps.redis_pool)
    canvas_store = CanvasStore(redis)
    
    try:
        # Send initial canvas state (no initialization needed now)

        # canvas_data = await canvas_store.get_canvas()
        #
        # await manager.send_personal_message(
        #     json.dumps({"type": "initial_canvas", "data": canvas_data}),
        #     websocket
        # )
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message["type"] == "pixel_update":
                # Process pixel update
                event = PixelUpdateEvent(**message["data"])
                log_id = None

                # 更新redis并记录日志到数据库
                async with deps.get_db_session() as db_session:
                    canvas_service = CanvasService(canvas_store, db_session)
                    log_id = await canvas_service.process_pixel_update(event)
                    await deps.increment_pixel_logs_counter()
                    # 检查是否需要创建快照
                    if await deps.async_should_create_snapshot():
                        await deps.reset_pixel_logs_counter()
                        snapshot = await canvas_service.create_snapshot(log_id)
                # 发送更新并记录执行时间
                start_time = time.time()
                await manager.broadcast(json.dumps({"type": "pixel_update", "data": message["data"]}))
                elapsed_time = time.time() - start_time
                logger.info(f"Broadcast message took {elapsed_time:.4f} seconds")
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id=connection_id)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id=connection_id)
    finally:
        # Close Redis connection (returns it to the pool)
        await redis.close()