from fastapi import WebSocket
import uuid
from redis import asyncio as aioredis
import app.deps as deps
import asyncio
from collections import deque
from datetime import datetime, timedelta


class ConnectionManager:
    """Manages WebSocket connections with Redis pub/sub for multi-worker support."""
    
    def __init__(self):
        # 使用字典存储连接，键为唯一标识符
        self.active_connections: dict = {}
        self.pubsub = None
        self.redis = None
        self.channel_name = "canvas_updates"
        
    async def init_redis(self):
        """初始化redis连接，并订阅"""
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


class RateLimiter:
    """
    滑动窗口频率限制器，自动清理非活跃客户端
    """

    def __init__(self, max_requests: int, window_size_seconds: int, cleanup_interval_minutes: int = 5):
        """
        初始化频率限制器
        :param max_requests: 在时间窗口内允许的最大请求数
        :param window_size_seconds: 时间窗口大小（秒）
        :param cleanup_interval_minutes: 清理非活跃客户端的时间间隔（分钟）
        """
        self.max_requests = max_requests
        self.window_size = timedelta(seconds=window_size_seconds)
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self.clients = {}  # 存储每个客户端的请求时间队列和最后活跃时间
        self._last_cleanup = datetime.now()

    def _cleanup_inactive_clients(self):
        """
        清理超过一定时间未活动的客户端记录
        """
        now = datetime.now()
        inactive_threshold = now - (self.window_size + timedelta(minutes=1))  # 宽松阈值

        # 找出需要移除的客户端ID
        to_remove = []
        for client_id, (request_times, last_active) in self.clients.items():
            if last_active < inactive_threshold:
                to_remove.append(client_id)

        # 移除非活跃客户端记录
        for client_id in to_remove:
            del self.clients[client_id]

    async def is_allowed(self, client_id: str) -> bool:
        """
        检查客户端是否允许发送新请求
        :param client_id: 客户端唯一标识符
        :return: 如果允许则返回True，否则返回False
        """
        now = datetime.now()

        # 定期清理非活跃客户端
        if now - self._last_cleanup > self.cleanup_interval:
            self._cleanup_inactive_clients()
            self._last_cleanup = now

        if client_id not in self.clients:
            self.clients[client_id] = (deque(), now)

        request_times, _ = self.clients[client_id]
        # 更新最后活跃时间
        self.clients[client_id] = (request_times, now)

        # 移除超出时间窗口的旧请求记录
        while request_times and now - request_times[0] > self.window_size:
            request_times.popleft()

        # 检查是否超出限制
        if len(request_times) >= self.max_requests:
            return False

        # 记录当前请求时间
        request_times.append(now)
        return True


