from app.redis_store.canvas import CanvasStore
from app.db.crud import create_pixel_log, get_latest_snapshot, create_snapshot
from app.schemas.events import PixelUpdateEvent
from app.utils.logger import logger
from app.config import SNAPSHOT_DIRECTORY, CANVAS_WIDTH, CANVAS_HEIGHT
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json
import os
import time
from app.utils.utils import color_array_to_png


class CanvasService:
    """Service for handling canvas operations."""
    
    def __init__(self, redis_store: CanvasStore, db: AsyncSession):
        self.redis_store = redis_store
        self.db = db
        
    async def process_pixel_update(self, event: PixelUpdateEvent) -> int:
        """Process a pixel update event and return the log entry ID.
        
        Args:
            event: PixelUpdateEvent containing update details
            
        Returns:
            The ID of the created log entry
            
        Raises:
            Exception: If the update process fails
        """
        try:
            # Update Redis
            await self.redis_store.set_pixel(event.x, event.y, event.color)
            
            # Log to database using the provided session
            # Note: Transaction management is handled by the caller
            log_entry = await create_pixel_log(self.db, event)
                
            logger.info(
                f"Pixel updated at ({event.x}, {event.y}) with color {event.color} "
                f"by user {event.user_id}. Log entry ID: {log_entry.id}"
            )
            
            return log_entry.id
            
        except Exception as e:
            logger.error(f"Error processing pixel update: {str(e)}", exc_info=True)
            raise
            
    async def create_snapshot(self, last_log_id: int) -> str:
        """Create a snapshot of the current canvas state as a PNG image."""

        try:
            # Ensure snapshot directory exists
            os.makedirs(SNAPSHOT_DIRECTORY, exist_ok=True)
            # Get canvas data from Redis
            canvas_data = await self.redis_store.get_canvas()
            
            # Create snapshot file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.png"
            filepath = os.path.join(SNAPSHOT_DIRECTORY, filename)

            # Convert color array to PNG and save to file
            color_array_to_png(canvas_data, CANVAS_WIDTH, CANVAS_HEIGHT, filepath)
                
            # Save only the filename to database (not the full path)
            # Use the provided session without explicit commit
            snapshot = await create_snapshot(self.db, last_log_id, filename)
            logger.info(f"Created snapshot: {filepath}")
            return filename

        except Exception as e:
            raise