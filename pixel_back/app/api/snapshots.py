"""
API endpoints for handling canvas snapshots.
"""

import os
import json
import base64
from fastapi import APIRouter, HTTPException, Response
from app.db.crud import get_latest_snapshot, get_pixel_logs_after_id
from app.deps import get_db_session
from app.config import SNAPSHOT_DIRECTORY
from app.utils.logger import logger
from app.utils.utils import png_to_color_array

router = APIRouter(prefix="/api/v1/snapshots", tags=["snapshots"])


@router.get("/latest.png")
async def get_latest_snapshot_png():
    """
    Get the latest canvas snapshot as a PNG image.
    
    Returns:
        Response: PNG image of the latest canvas snapshot
    """
    async with get_db_session() as db:
        snapshot = await get_latest_snapshot(db)
        
        if not snapshot:
            logger.warning("No snapshot found in database")
            raise HTTPException(status_code=404, detail="No snapshot found")
        
        snapshot_file_path = os.path.join(SNAPSHOT_DIRECTORY, snapshot.data_file_path)
        
        if not os.path.exists(snapshot_file_path):
            logger.warning(f"Snapshot file not found: {snapshot_file_path}")
            raise HTTPException(status_code=404, detail="Snapshot file not found")
        
        _, ext = os.path.splitext(snapshot_file_path)
        if ext.lower() != '.png':
            logger.warning(f"Snapshot file is not a PNG: {snapshot_file_path}")
            raise HTTPException(status_code=400, detail="Snapshot file is not in PNG format")
        
        try:
            with open(snapshot_file_path, 'rb') as f:
                png_bytes = f.read()
        except Exception as e:
            logger.error(f"Error reading PNG file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error reading PNG file: {str(e)}")
        
        logger.info(f"Successfully served snapshot PNG. Snapshot ID: {snapshot.id}")
        return Response(content=png_bytes, media_type="image/png")


@router.get("/latest/dataurl")
async def get_latest_snapshot_dataurl():
    """
    Get the latest canvas snapshot as a data URL (base64 encoded PNG).
    
    Returns:
        dict: Object containing the data URL of the PNG image
    """
    async with get_db_session() as db:
        snapshot = await get_latest_snapshot(db)

        if not snapshot:
            logger.warning("No snapshot found in database")
            raise HTTPException(status_code=404, detail="No snapshot found")
        
        snapshot_file_path = os.path.join(SNAPSHOT_DIRECTORY, snapshot.data_file_path)

        if not os.path.exists(snapshot_file_path):
            logger.warning(f"Snapshot file not found: {snapshot_file_path}")
            raise HTTPException(status_code=404, detail="Snapshot file not found")
        
        _, ext = os.path.splitext(snapshot_file_path)
        if ext.lower() != '.png':
            logger.warning(f"Snapshot file is not a PNG: {snapshot_file_path}")
            raise HTTPException(status_code=400, detail="Snapshot file is not in PNG format")
        
        try:
            with open(snapshot_file_path, 'rb') as f:
                png_bytes = f.read()
                # 将PNG数据转换为base64编码的data URL
                png_base64 = base64.b64encode(png_bytes).decode('utf-8')
                data_url = f"data:image/png;base64,{png_base64}"
        except Exception as e:
            logger.error(f"Error reading or encoding PNG file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error reading or encoding PNG file: {str(e)}")
        
        logger.info(f"Successfully served snapshot as data URL. Snapshot ID: {snapshot.id}")
        return {
            "data_url": data_url
        }


@router.get("/latest")
async def get_latest_snapshot_data():
    """
    Get the latest canvas snapshot as JSON data.
    
    Returns:
        dict: Snapshot information including creation time and data file path
    """
    async with get_db_session() as db:
        snapshot = await get_latest_snapshot(db)
        
        if not snapshot:
            logger.warning("No snapshot found in database")
            raise HTTPException(status_code=404, detail="No snapshot found")
        
        snapshot_file_path = os.path.join(SNAPSHOT_DIRECTORY, snapshot.data_file_path)
        
        if not os.path.exists(snapshot_file_path):
            logger.warning(f"Snapshot file not found: {snapshot_file_path}")
            raise HTTPException(status_code=404, detail="Snapshot file not found")
        
        _, ext = os.path.splitext(snapshot_file_path)
        if ext.lower() == '.png':
            try:
                color_array = png_to_color_array(snapshot_file_path)
            except Exception as e:
                logger.error(f"Error converting PNG to color array: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error converting PNG to color array: {str(e)}")
        else:
            try:
                with open(snapshot_file_path, 'r') as f:
                    color_array = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from snapshot file: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Invalid JSON in snapshot file: {str(e)}")
            except Exception as e:
                logger.error(f"Error reading snapshot file: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error reading snapshot file: {str(e)}")
        
        logger.info(f"Successfully served snapshot data. Snapshot ID: {snapshot.id}")
        return {
            "id": snapshot.id,
            "created_at": snapshot.created_at,
            "last_log_id": snapshot.last_log_id,
            "data": color_array
        }

@router.get("/update")
async def get_update():
    async with get_db_session() as db:
        snapshot = await get_latest_snapshot(db)
        if not snapshot:
            logger.warning("No snapshot found in database")
            raise HTTPException(status_code=404, detail="No snapshot found")
        result = await get_pixel_logs_after_id(db, snapshot.last_log_id if snapshot else 0)
        # 返回上次记录快照之后的数据
        return {
            "last_log_id": snapshot.last_log_id,
            "logs": [
                {
                    "x": log.x,
                    "y": log.y,
                    "color": log.color,
                }
                for log in result
            ]
        }
