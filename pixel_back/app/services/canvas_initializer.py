from app.redis_store.canvas import CanvasStore
from app.deps import get_db_session
from app.db.crud import get_latest_snapshot, get_pixel_logs_after_id
from app.config import SNAPSHOT_DIRECTORY, CANVAS_WIDTH
from redis import asyncio as aioredis
import json
import os
from app.utils.logger import logger
from app.utils.utils import png_to_color_array


async def initialize_canvas_at_startup():
    """
    Initialize canvas at application startup.
    This function handles canvas initialization including:
    1. Checking for existing canvas data in Redis
    2. Loading from database snapshots if available
    3. Creating a new canvas if none exists
    """
    logger.info("Starting canvas initialization...")
    
    # Get Redis connection from pool
    # Import redis_pool inside function to get the latest value
    from app.deps import redis_pool

    redis = aioredis.Redis(connection_pool=redis_pool)
    canvas_store = CanvasStore(redis)
    
    try:
        # Check if canvas already exists in Redis
        exists = await redis.exists(canvas_store.canvas_key)
        if not exists:
            logger.info("No existing canvas found in Redis. Checking for snapshots...")
            
            # Check for existing snapshots in database
            async with get_db_session() as db:
                latest_snapshot = await get_latest_snapshot(db)
                
                if latest_snapshot and os.path.exists(os.path.join(SNAPSHOT_DIRECTORY, latest_snapshot.data_file_path)):
                    # Load canvas from snapshot
                    full_path = os.path.join(SNAPSHOT_DIRECTORY, latest_snapshot.data_file_path)
                    logger.info(f"Loading canvas from snapshot: {full_path}")
                    try:
                        # Check file extension to determine how to load the snapshot
                        _, ext = os.path.splitext(full_path)
                        if ext.lower() == '.png':
                            # Load from PNG file
                            canvas_data = png_to_color_array(full_path)
                        else:
                            # Load from JSON file (fallback for old snapshots)
                            with open(full_path, 'r') as f:
                                canvas_data = json.load(f)
                            
                        # 使用get_pixel_logs_after_id函数获取快照之后记录的数据，更新canvas_data
                        logs = await get_pixel_logs_after_id(db, latest_snapshot.last_log_id)
                        for log in logs:
                            index = log.y * CANVAS_WIDTH + log.x  # 计算像素在画布中的索引位置
                            canvas_data[index] = log.color
                        
                        # Save to Redis
                        await redis.delete(canvas_store.canvas_key)
                        pipe = redis.pipeline()
                        for i in range(0, len(canvas_data), 1000):
                            chunk = canvas_data[i:i+1000]
                            pipe.rpush(canvas_store.canvas_key, *chunk)
                        await pipe.execute()
                        logger.info("Canvas loaded from snapshot successfully")
                    except Exception as e:
                        logger.error(f"Failed to load canvas from snapshot: {e}")
                        # Fall back to creating a new canvas
                        await canvas_store.initialize_canvas()
                else:
                    # Create a new canvas
                    logger.info("No snapshots found. Creating a new canvas.")
                    await canvas_store.initialize_canvas()
        else:
            logger.info("Canvas already exists in Redis. Skipping initialization.")
            
    except Exception as e:
        logger.error(f"Error during canvas initialization: {e}")
        raise
    finally:
        # Close Redis connection (returns it to the pool)
        await redis.close()
        
    logger.info("Canvas initialization completed.")