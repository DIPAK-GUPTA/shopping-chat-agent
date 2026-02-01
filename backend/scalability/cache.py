"""
Redis Caching Layer for Scalability
Optional - only used when Redis is enabled
"""
from typing import Optional, Any
import json
from functools import wraps

from config import settings

# Redis client (optional)
redis_client = None

if settings.REDIS_ENABLED and settings.REDIS_URL:
    try:
        import redis
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        print(f"Redis connected: {settings.REDIS_URL}")
    except Exception as e:
        print(f"Redis connection failed: {e}")
        redis_client = None


class CacheService:
    """Caching service with Redis fallback to in-memory"""
    
    def __init__(self):
        self.redis = redis_client
        self._memory_cache: dict = {}
    
    @property
    def is_redis_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis is not None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.redis:
            try:
                value = self.redis.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                print(f"Redis get error: {e}")
        
        return self._memory_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (seconds)"""
        if self.redis:
            try:
                self.redis.setex(key, ttl, json.dumps(value))
                return True
            except Exception as e:
                print(f"Redis set error: {e}")
        
        self._memory_cache[key] = value
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if self.redis:
            try:
                self.redis.delete(key)
                return True
            except Exception as e:
                print(f"Redis delete error: {e}")
        
        self._memory_cache.pop(key, None)
        return True
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern (Redis only)"""
        if self.redis:
            try:
                keys = self.redis.keys(pattern)
                if keys:
                    return self.redis.delete(*keys)
            except Exception as e:
                print(f"Redis clear pattern error: {e}")
        
        return 0
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        return self.get(f"session:{session_id}")
    
    def set_session(self, session_id: str, data: dict, ttl: int = None) -> bool:
        """Set session data"""
        if ttl is None:
            ttl = settings.SESSION_TTL_SECONDS
        return self.set(f"session:{session_id}", data, ttl)
    
    def cache_phone_query(self, query_hash: str, result: Any, ttl: int = 300) -> bool:
        """Cache phone query result (5 min TTL)"""
        return self.set(f"query:{query_hash}", result, ttl)
    
    def get_cached_query(self, query_hash: str) -> Optional[Any]:
        """Get cached query result"""
        return self.get(f"query:{query_hash}")


def cached(prefix: str = "cache", ttl: int = 300):
    """
    Decorator for caching function results
    Only works if Redis is available
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            key_parts = [prefix, func.__name__] + [str(a) for a in args]
            key = ":".join(key_parts)
            
            # Check cache
            cached_result = cache_service.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache_service.set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Global cache service instance
cache_service = CacheService()
