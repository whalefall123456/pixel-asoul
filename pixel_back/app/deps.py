from redis import asyncio as aioredis
from redis.asyncio import ConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, REDIS_POOL_SIZE, DATABASE_URL,SNAPSHOT_THRESHOLD
from app.db.session import async_session
from app.db.crud import get_latest_snapshot, get_pixel_logs_after_id
from app.db.models import PixelLog
from sqlalchemy.future import select
from sqlalchemy import func
from contextlib import asynccontextmanager

# Global Redis connection pool
redis_pool = None

# Global variable to track number of pixel logs since last snapshot
pixel_logs_since_last_snapshot = 0


def create_redis_pool():
    """Create a global Redis connection pool."""
    global redis_pool
    if redis_pool is None:
        redis_pool = ConnectionPool.from_url(
            f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
            password=REDIS_PASSWORD,
            encoding="utf-8",
            decode_responses=True,
            max_connections=REDIS_POOL_SIZE
        )
        print(f"redis connected to {REDIS_HOST}")
    return redis_pool


@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """提供一个带自动事务管理的数据库会话上下文管理器。
    
    使用此函数时，数据库操作将在事务中执行，并在成功时自动提交，
    在发生异常时自动回滚。
    
    用法示例:
    async with get_db_session() as db_session:
        # 执行数据库操作
        db_session.add(some_object)
        # 事务将自动提交或回滚
    """
    session = async_session()
    try:
        async with session.begin():
            yield session
        # 事务在此处自动提交
    except Exception:
        # 事务在此处自动回滚
        raise
    finally:
        await session.close()


async def initialize_pixel_logs_counter(db: AsyncSession) -> int:
    """Initialize the pixel logs counter by counting logs since the last snapshot.
    
    Returns:
        The number of pixel logs since the last snapshot.
    """
    global pixel_logs_since_last_snapshot
    
    # Get the latest snapshot
    latest_snapshot = await get_latest_snapshot(db)
    result = await get_pixel_logs_after_id(db, latest_snapshot.last_log_id if latest_snapshot else 0)
    pixel_logs_since_last_snapshot = len(result)
    
    return pixel_logs_since_last_snapshot


def increment_pixel_logs_counter():
    """Increment the pixel logs counter by 1."""
    global pixel_logs_since_last_snapshot
    pixel_logs_since_last_snapshot += 1


def get_pixel_logs_count():
    """Get the current pixel logs count since last snapshot."""
    global pixel_logs_since_last_snapshot
    return pixel_logs_since_last_snapshot


def should_create_snapshot(threshold: int = SNAPSHOT_THRESHOLD) -> bool:
    """Check if a snapshot should be created based on the pixel logs count.
    
    Args:
        threshold: The number of logs that triggers a snapshot creation.
        
    Returns:
        True if a snapshot should be created, False otherwise.
    """
    return get_pixel_logs_count() >= threshold


def reset_pixel_logs_counter():
    """Reset the pixel logs counter to 0 after creating a snapshot."""
    global pixel_logs_since_last_snapshot
    pixel_logs_since_last_snapshot = 0