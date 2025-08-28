from typing import List
import json
from fastapi import WebSocket
import uuid
import asyncio
from redis import asyncio as aioredis
import app.deps as deps


class ConnectionManager:
    """Manages WebSocket connections with Redis pub/sub for multi-worker support."""
    
    def __init__(self):
        # 使用字典存储连接，键为唯一标识符
        self.active_connections: dict = {}
        self.pubsub = None
        self.redis = None
        self.channel_name = "canvas_updates"
        
    async def init_redis(self):
        """Initialize Redis connection and pub/sub for this manager."""
        if self.redis is None:
            # 使用已有的Redis连接池而不是创建新的连接
            self.redis = aioredis.Redis(connection_pool=deps.redis_pool)
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(self.channel_name)
            # Start listening for messages
            asyncio.create_task(self._listen_for_messages())
        
    async def _listen_for_messages(self):
        """Listen for messages from Redis pub/sub and broadcast to local connections."""
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                # Broadcast to local connections only
                # message["data"] is already a string, no need to decode
                await self._local_broadcast(message["data"])
    
    async def connect(self, websocket: WebSocket):
        """Accept a WebSocket connection."""
        await websocket.accept()
        # 为每个连接生成唯一ID
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        # 初始化Redis连接（如果尚未初始化）
        if self.redis is None:
            await self.init_redis()
            
        return connection_id
        
    def disconnect(self, connection_id: str = None, websocket: WebSocket = None):
        """Remove a WebSocket connection."""
        if connection_id and connection_id in self.active_connections:
            del self.active_connections[connection_id]
        elif websocket:
            # 如果通过websocket对象查找
            connections_to_remove = [k for k, v in self.active_connections.items() if v == websocket]
            for conn_id in connections_to_remove:
                del self.active_connections[conn_id]
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        await websocket.send_text(message)
        
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSockets across all workers."""
        # Publish to Redis channel for cross-worker communication
        if self.redis:
            await self.redis.publish(self.channel_name, message)
        else:
            # Fallback to local broadcast if Redis not available
            await self._local_broadcast(message)
            
    async def _local_broadcast(self, message: str):
        """Broadcast a message to local connections only."""
        # 创建当前连接列表的副本，避免在迭代过程中修改字典
        connections_copy = dict(self.active_connections)
        disconnected_connections = []
        
        for connection_id, connection in connections_copy.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                # 记录断开的连接
                disconnected_connections.append(connection_id)
        
        # 移除断开的连接
        for connection_id in disconnected_connections:
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
                
    async def close(self):
        """Close Redis connections."""
        if self.pubsub:
            await self.pubsub.unsubscribe(self.channel_name)
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()