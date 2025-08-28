from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PixelUpdateEvent(BaseModel):
    """Model for pixel update events."""
    x: int
    y: int
    color: str
    user_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class CanvasSnapshot(BaseModel):
    """Model for canvas snapshot metadata."""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    last_log_id: Optional[int] = None
    data_file_path: str