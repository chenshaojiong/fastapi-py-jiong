import redis
import json
from typing import Optional, Any
from app.core.config import settings

class RedisClient:
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        try:
            self.client.setex(key, expire, json.dumps(value))
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False

redis_client = RedisClient()