from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.db.models import PixelLog, CanvasSnapshot, VisitLog
from app.schemas.events import PixelUpdateEvent
from typing import List


async def create_pixel_log(db: AsyncSession, event: PixelUpdateEvent) -> PixelLog:
    """Create a new pixel log entry."""
    db_log = PixelLog(
        user_id=event.user_id,
        x=event.x,
        y=event.y,
        color=event.color
    )
    db.add(db_log)
    await db.flush()  # 刷新以获取ID，但不提交事务
    return db_log


async def create_visit_log(db: AsyncSession, ip: str) -> VisitLog:
    """Create a new visit log entry."""
    visit_log = VisitLog(ip=ip)
    db.add(visit_log)
    await db.flush()  # 刷新以获取ID，但不提交事务
    return visit_log


async def get_pixel_logs_after_id(db: AsyncSession, pixel_log_id: int) -> List[PixelLog]:
    """Get pixel logs with IDs greater than the specified ID."""
    result = await db.execute(
        select(PixelLog)
        .where(PixelLog.id > pixel_log_id)
        .order_by(PixelLog.id)
    )
    return list(result.scalars().all())


async def get_visit_log_count(db: AsyncSession) -> int:
    """Get total number of visit logs."""
    result = await db.execute(select(func.count(VisitLog.id)))
    count = result.scalar()
    return int(count or 0)


async def get_pixel_log_count(db: AsyncSession) -> int:
    """Get total number of pixel logs."""
    result = await db.execute(select(func.count(PixelLog.id)))
    count = result.scalar()
    return int(count or 0)


async def get_latest_snapshot(db: AsyncSession) -> CanvasSnapshot:
    """Get the latest canvas snapshot."""
    try:
        result = await db.execute(
            select(CanvasSnapshot).order_by(CanvasSnapshot.created_at.desc()).limit(1)
        )
        return result.scalars().first()
    except Exception as e:
        # 可以根据实际需求记录日志或进行其他处理
        print(f"Database error occurred: {e}")
        return None


async def create_snapshot(db: AsyncSession, last_log_id: int, file_path: str) -> CanvasSnapshot:
    """Create a new canvas snapshot."""
    snapshot = CanvasSnapshot(
        last_log_id=last_log_id,
        data_file_path=file_path
    )
    db.add(snapshot)
    await db.flush()  # 刷新以获取ID，但不提交事务
    return snapshot