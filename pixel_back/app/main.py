"""
Main FastAPI application for the Pixel Canvas project.
This file contains the core application setup, WebSocket handling, and API endpoints.
"""

import uvicorn
from fastapi import FastAPI
from app.websocket.endpoints import router as websocket_router
from app.api.snapshots import router as snapshots_router
from app.config import CANVAS_WIDTH, CANVAS_HEIGHT
from app.deps import create_redis_pool, initialize_pixel_logs_counter, get_db_session
import app.deps as deps
from app.services.canvas_initializer import initialize_canvas_at_startup
import asyncio

# Create FastAPI app
app = FastAPI(
    title="Pixel Canvas API",
    description="A Reddit r/place inspired real-time collaborative pixel canvas",
    version="1.0.0"
)

# Include routers
app.include_router(websocket_router)
app.include_router(snapshots_router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Create Redis connection pool
    create_redis_pool()
    print("Redis connection pool created")
    
    # Initialize pixel logs counter
    async with get_db_session() as db:
        await initialize_pixel_logs_counter(db)
    
    # Initialize canvas
    await initialize_canvas_at_startup()
    print("Canvas initialization completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up application on shutdown."""
    if deps.redis_pool:
        await deps.redis_pool.disconnect()
    print("Redis connection pool disconnected")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Pixel Canvas API",
        "canvas_size": f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)