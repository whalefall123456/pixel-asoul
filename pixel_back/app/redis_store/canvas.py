import json
from typing import Optional
from redis import asyncio as aioredis
from app.config import CANVAS_WIDTH, CANVAS_HEIGHT


class CanvasStore:
    """Redis store for canvas operations."""
    
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self.canvas_key = "canvas"
        
    async def initialize_canvas(self):
        """Initialize canvas with default empty state.
        
        Note: This method is now primarily used during application startup.
        For normal WebSocket connections, the canvas should already be initialized.
        """
        # Check if canvas already exists
        exists = await self.redis.exists(self.canvas_key)
        if not exists:
            # Create empty canvas (all pixels are black by default)
            canvas_data = ["#FFFFFF"] * (CANVAS_WIDTH * CANVAS_HEIGHT)
            await self.redis.delete(self.canvas_key)
            # Use pipeline for better performance
            pipe = self.redis.pipeline()
            for i in range(0, len(canvas_data), 1000):
                chunk = canvas_data[i:i+1000]
                pipe.rpush(self.canvas_key, *chunk)
            await pipe.execute()
            
    async def get_pixel(self, x: int, y: int) -> str:
        """Get pixel color at position (x, y)."""
        if not (0 <= x < CANVAS_WIDTH and 0 <= y < CANVAS_HEIGHT):
            raise ValueError("Coordinates out of bounds")
            
        index = y * CANVAS_WIDTH + x
        color = await self.redis.lindex(self.canvas_key, index)
        return color or "#FFFFFF"
        
    async def set_pixel(self, x: int, y: int, color: str) -> bool:
        """Set pixel color at position (x, y)."""
        if not (0 <= x < CANVAS_WIDTH and 0 <= y < CANVAS_HEIGHT):
            raise ValueError("Coordinates out of bounds")
            
        index = y * CANVAS_WIDTH + x
        result = await self.redis.lset(self.canvas_key, index, color)
        return result
        
    async def get_canvas(self) -> list:
        """Get entire canvas data."""
        canvas_data = await self.redis.lrange(self.canvas_key, 0, -1)
        return canvas_data

    """
    取消冷却功能
    """
    # async def set_cooldown(self, user_id: str, timestamp: int) -> bool:
    #     """Set cooldown for user."""
    #     key = f"{self.cooldown_key}:{user_id}"
    #     result = await self.redis.setex(key, 60, timestamp)  # 60 seconds cooldown
    #     return result
    #
    # async def get_cooldown(self, user_id: str) -> Optional[int]:
    #     """Get cooldown timestamp for user."""
    #     key = f"{self.cooldown_key}:{user_id}"
    #     timestamp = await self.redis.get(key)
    #     return int(timestamp) if timestamp else None