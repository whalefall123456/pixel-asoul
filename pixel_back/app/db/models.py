from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone, timedelta

Base = declarative_base()

BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    """Return timezone-aware current datetime in Asia/Shanghai (UTC+8)."""
    return datetime.now(BEIJING_TZ)


class PixelLog(Base):
    """Model for pixel placement logs."""
    __tablename__ = "pixel_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True)
    x = Column(Integer)
    y = Column(Integer)
    color = Column(String)
    created_at = Column(DateTime(timezone=True), default=beijing_now)


class VisitLog(Base):
    """Model for visit logs."""
    __tablename__ = "visit_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    ip = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), default=beijing_now)


class CanvasSnapshot(Base):
    """Model for canvas snapshots."""
    __tablename__ = "canvas_snapshots"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=beijing_now)
    last_log_id = Column(BigInteger)
    data_file_path = Column(String)