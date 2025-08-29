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
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.utils.utils import color_array_to_png
import traceback


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
            
    async def _save_snapshot_image(self, canvas_data: list) -> str:
        """Save snapshot image in a thread pool to avoid blocking the event loop."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            # Run the blocking image creation in a separate thread
            filepath = await loop.run_in_executor(
                executor, 
                self._create_and_save_image,
                canvas_data
            )
            return filepath
    
    def _create_and_save_image(self, canvas_data: list) -> str:
        """Create and save image in a separate thread."""
        # Ensure snapshot directory exists
        os.makedirs(SNAPSHOT_DIRECTORY, exist_ok=True)
        
        # Create snapshot file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{timestamp}.png"
        filepath = os.path.join(SNAPSHOT_DIRECTORY, filename)

        # Convert color array to PNG and save to file
        color_array_to_png(canvas_data, CANVAS_WIDTH, CANVAS_HEIGHT, filepath)
        return filepath
    
    async def create_snapshot(self, last_log_id: int) -> str:
        """Create a snapshot of the current canvas state as a PNG image."""
        start_time = time.time()
        try:
            logger.info("Starting snapshot creation process")
            
            # Get canvas data from Redis directly (no need to use thread pool for async operation)
            redis_start_time = time.time()
            canvas_data = await self.redis_store.get_canvas()
            redis_time = time.time() - redis_start_time
            logger.info(f"Retrieved canvas data from Redis in {redis_time:.2f} seconds")
            
            # Save image in a separate thread to avoid blocking the event loop
            image_start_time = time.time()
            filepath = await self._save_snapshot_image(canvas_data)
            image_time = time.time() - image_start_time
            logger.info(f"Saved snapshot image in {image_time:.2f} seconds")
                
            # Save only the filename to database (not the full path)
            # Use the provided session without explicit commit
            db_start_time = time.time()
            snapshot = await create_snapshot(self.db, last_log_id, os.path.basename(filepath))
            db_time = time.time() - db_start_time
            logger.info(f"Saved snapshot metadata to database in {db_time:.2f} seconds")
            
            total_time = time.time() - start_time
            logger.info(f"Created snapshot: {filepath} in {total_time:.2f} seconds")
            return os.path.basename(filepath)

        except Exception as e:
            logger.error(f"Error creating snapshot: {str(e)}", exc_info=True)
            raise