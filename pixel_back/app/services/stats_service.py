from typing import Dict
from redis import asyncio as aioredis
import app.deps as deps
from app.deps import get_db_session, initialize_pixel_logs_counter
from app.db.crud import get_visit_log_count, get_pixel_log_count, create_visit_log
from app.redis_store.visit_stats import VisitStatsStore


class StatsService:
    """Business service for visit and canvas counters."""

    def __init__(self, redis: aioredis.Redis):
        self.stats_store = VisitStatsStore(redis)

    @classmethod
    async def initialize_startup_counters(cls) -> None:
        """Load totals from DB and seed Redis stats counters at startup."""
        visit_logs_count = 0
        pixel_logs_count = 0

        async with get_db_session() as db:
            await initialize_pixel_logs_counter(db)
            visit_logs_count = await get_visit_log_count(db)
            pixel_logs_count = await get_pixel_log_count(db)

        redis = aioredis.Redis(connection_pool=deps.redis_pool)
        try:
            service = cls(redis)
            await service.initialize_from_totals(
                total_visits=visit_logs_count,
                total_placed_pixels=pixel_logs_count,
            )
        finally:
            await redis.close()

    async def initialize_from_totals(self, total_visits: int, total_placed_pixels: int) -> None:
        """Seed Redis counters using totals loaded from database."""
        await self.stats_store.initialize(
            total_visits=total_visits,
            total_placed_pixels=total_placed_pixels,
        )

    async def handle_connect(self, ip: str | None) -> Dict[str, int]:
        """Record visit log in DB, then update Redis counters."""
        # 防御性兜底，避免空值插入
        safe_ip = (ip or "").strip() or "unknown"

        # 按项目约定：事务作用域在 get_db_session 外层管理
        async with deps.get_db_session() as db_session:
            await create_visit_log(db_session, safe_ip)

        # DB 成功后再更新 Redis 统计
        await self.stats_store.on_user_connected()
        return await self.stats_store.get_stats()

    async def handle_disconnect(self) -> Dict[str, int]:
        """Update counters for a disconnected client and return current stats."""
        await self.stats_store.on_user_disconnected()
        return await self.stats_store.get_stats()

    async def handle_pixel_placed(self, count: int = 1) -> Dict[str, int]:
        """Increase placed pixel counter and return current stats."""
        await self.stats_store.add_placed_pixels(count)
        return await self.stats_store.get_stats()

    async def get_stats(self) -> Dict[str, int]:
        """Return current stats."""
        return await self.stats_store.get_stats()

