import redis
import json
from typing import Optional, Any
from backend.core.config import get_settings

settings = get_settings()

class RedisCache:
    def __init__(self):
        self.redis = None
        self.enabled = False
        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=1 # Fast fail
            )
            self.redis.ping()
            self.enabled = True
            print(f"Redis Cache Connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            print(f"Redis Cache Connection Failed: {e}. Running in Fallback Mode (DB Only).")
            self.redis = None
            self.enabled = False

    def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        try:
            val = self.redis.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception as e:
            print(f"Redis Read Error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        if not self.enabled:
            return
        try:
            val_str = json.dumps(value)
            self.redis.setex(key, ttl, val_str)
        except Exception as e:
            print(f"Redis Write Error: {e}")

# Singleton
cache = RedisCache()
