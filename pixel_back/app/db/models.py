from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class PixelLog(Base):
    """Model for pixel placement logs."""
    __tablename__ = "pixel_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True)
    x = Column(Integer)
    y = Column(Integer)
    color = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class CanvasSnapshot(Base):
    """Model for canvas snapshots."""
    __tablename__ = "canvas_snapshots"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_log_id = Column(BigInteger)
    data_file_path = Column(String)