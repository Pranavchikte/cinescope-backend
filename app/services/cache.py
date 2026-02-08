import redis
import json
import logging
from typing import Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        # Create connection pool (reuse connections)
        self.pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20
        )
        self.redis_client = redis.Redis(connection_pool=self.pool)
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached data"""
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key '{key}': {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set cached data with TTL"""
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Cache set error for key '{key}': {e}")
    
    def delete(self, key: str):
        """Delete cached data"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error for key '{key}': {e}")
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern (e.g., 'user_genres:*')"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache delete pattern error for pattern '{pattern}': {e}")

cache_service = CacheService()