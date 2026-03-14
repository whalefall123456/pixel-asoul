from typing import Dict
from redis import asyncio as aioredis


class VisitStatsStore:
    """Maintain project-level counters in Redis.

    Counters:
    - current_online_users: current online websocket clients
    - total_visits: cumulative connection visits
    - total_placed_pixels: cumulative placed pixel count
    """

    ONLINE_USERS_KEY = "stats:current_online_users"
    TOTAL_VISITS_KEY = "stats:total_visits"
    TOTAL_PLACED_PIXELS_KEY = "stats:total_placed_pixels"

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def initialize(self, total_visits: int = 0, total_placed_pixels: int = 0) -> None:
        """Initialize counters, using database totals for cumulative fields."""
        total_visits = max(0, int(total_visits))
        total_placed_pixels = max(0, int(total_placed_pixels))

        # Online users should restart from 0 on process startup.
        await self.redis.set(self.ONLINE_USERS_KEY, 0)
        await self.redis.set(self.TOTAL_VISITS_KEY, total_visits)
        await self.redis.set(self.TOTAL_PLACED_PIXELS_KEY, total_placed_pixels)

    async def on_user_connected(self) -> Dict[str, int]:
        """Increase online users and total visits when a client connects."""
        online_users = await self.redis.incr(self.ONLINE_USERS_KEY)
        total_visits = await self.redis.incr(self.TOTAL_VISITS_KEY)
        return {
            "current_online_users": int(online_users),
            "total_visits": int(total_visits),
        }

    async def on_user_disconnected(self) -> int:
        """Decrease online users; clamp to 0 to avoid negative values."""
        online_users = await self.redis.decr(self.ONLINE_USERS_KEY)
        if int(online_users) < 0:
            await self.redis.set(self.ONLINE_USERS_KEY, 0)
            return 0
        return int(online_users)

    async def add_placed_pixels(self, count: int = 1) -> int:
        """Increase total placed pixel count."""
        if count < 0:
            raise ValueError("count must be >= 0")
        total = await self.redis.incrby(self.TOTAL_PLACED_PIXELS_KEY, count)
        return int(total)

    async def get_stats(self) -> Dict[str, int]:
        """Read all counters from Redis."""
        online = await self.redis.get(self.ONLINE_USERS_KEY)
        visits = await self.redis.get(self.TOTAL_VISITS_KEY)
        pixels = await self.redis.get(self.TOTAL_PLACED_PIXELS_KEY)

        return {
            "current_online_users": int(online or 0),
            "total_visits": int(visits or 0),
            "total_placed_pixels": int(pixels or 0),
        }

