"""Redis caching layer with in-memory fallback for Windows dev."""

import json
import logging
from typing import Any, Optional
from config import get_settings

logger = logging.getLogger(__name__)

# In-memory cache fallback
_memory_cache: dict[str, str] = {}
_redis_client = None


def _get_redis():
    """Get Redis client, returns None if unavailable."""
    global _redis_client
    settings = get_settings()
    if not settings.REDIS_ENABLED:
        return None
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            _redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Redis unavailable, using in-memory cache: {e}")
            _redis_client = None
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache."""
    client = _get_redis()
    try:
        if client:
            val = client.get(key)
        else:
            val = _memory_cache.get(key)
        if val:
            return json.loads(val)
    except Exception as e:
        logger.error(f"Cache get error: {e}")
    return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set a value in cache with TTL in seconds."""
    client = _get_redis()
    try:
        serialized = json.dumps(value, default=str)
        if client:
            client.setex(key, ttl, serialized)
        else:
            _memory_cache[key] = serialized
    except Exception as e:
        logger.error(f"Cache set error: {e}")


def cache_delete(key: str) -> None:
    """Delete a key from cache."""
    client = _get_redis()
    try:
        if client:
            client.delete(key)
        else:
            _memory_cache.pop(key, None)
    except Exception as e:
        logger.error(f"Cache delete error: {e}")


def cache_clear() -> None:
    """Clear all cache."""
    client = _get_redis()
    try:
        if client:
            client.flushdb()
        else:
            _memory_cache.clear()
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
