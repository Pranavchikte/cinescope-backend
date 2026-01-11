import redis
import json
from typing import Optional, Any
from app.core.config import settings

class CacheService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    def get(self, key: str) -> Optional[Any]:
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        self.redis_client.setex(key, ttl, json.dumps(value))
    
    def delete(self, key: str):
        self.redis_client.delete(key)

cache_service = CacheService()