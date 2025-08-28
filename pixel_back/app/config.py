import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "password")
REDIS_POOL_SIZE = int(os.getenv("REDIS_POOL_SIZE", 20))

# PostgreSQL configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "databaseName")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Canvas configuration
CANVAS_WIDTH = int(os.getenv("CANVAS_WIDTH", 1000))
CANVAS_HEIGHT = int(os.getenv("CANVAS_HEIGHT", 1000))
PIXEL_LIMIT_PER_USER = int(os.getenv("PIXEL_LIMIT_PER_USER", 1))  # pixels per user
# COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", 60))  # seconds between placing pixels

# Snapshot configuration
SNAPSHOT_INTERVAL = int(os.getenv("SNAPSHOT_INTERVAL", 300))  # seconds between snapshots
SNAPSHOT_DIRECTORY = os.getenv("SNAPSHOT_DIRECTORY", "snapshots")  # directory to store snapshot files
SNAPSHOT_THRESHOLD = int(os.getenv("SNAPSHOT_THRESHOLD", 250))