"""
Caching Strategy (Story 7.4)

Multi-layer caching with Redis L1 + LRU L2 for 80% hit rate.
Reduces redundant feature extraction and model inference computations.

Cache Hierarchy:
1. L2 (LRU): In-memory, fast, process-local
2. L1 (Redis): Distributed, persistent, shared across instances

Target Performance:
- Cache hit rate: ≥80%
- Hit latency: <5ms (L2) or <10ms (L1)
- Miss latency: 50ms+ (database/computation)
"""

import pickle
import hashlib
import logging
import time
from typing import Any, Optional, Dict
from collections import OrderedDict
from threading import Lock

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache with size limit"""

    def __init__(self, maxsize: int = 1000):
        """
        Initialize LRU cache.

        Args:
            maxsize: Maximum number of entries
        """
        self.cache = OrderedDict()
        self.maxsize = maxsize
        self.lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def set(self, key: str, value: Any):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            if key in self.cache:
                # Update and move to end
                self.cache.move_to_end(key)
            self.cache[key] = value

            # Evict oldest if over capacity
            if len(self.cache) > self.maxsize:
                self.cache.popitem(last=False)  # Remove oldest (first item)

    def clear(self):
        """Clear all entries"""
        with self.lock:
            self.cache.clear()

    def __contains__(self, key: str) -> bool:
        """Check if key exists"""
        with self.lock:
            return key in self.cache

    def __len__(self) -> int:
        """Get cache size"""
        with self.lock:
            return len(self.cache)


class CacheManager:
    """
    Multi-layer cache manager with Redis L1 + LRU L2.

    Features:
    - L1 (Redis): Distributed cache for sharing across instances
    - L2 (LRU): In-memory cache for fastest access
    - Automatic TTL expiration
    - Cache statistics (hit rate, miss rate)
    - Graceful degradation if Redis unavailable
    """

    def __init__(
        self,
        redis_host: Optional[str] = None,
        redis_port: int = 6379,
        max_memory_mb: int = 512
    ):
        """
        Initialize cache manager.

        Args:
            redis_host: Redis host (None to disable Redis)
            redis_port: Redis port (default: 6379)
            max_memory_mb: Max memory for LRU cache in MB
        """
        self.max_memory_mb = max_memory_mb

        # Initialize L2 (LRU) cache
        # Approximate: ~1KB per entry, so 512MB = ~500K entries
        lru_maxsize = (max_memory_mb * 1024) // 2  # Conservative estimate
        self.lru_cache = LRUCache(maxsize=lru_maxsize)

        # Initialize L1 (Redis) cache
        self.redis_client = None
        if redis_host and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    socket_connect_timeout=1,
                    decode_responses=False  # We use binary for pickle
                )
                self.redis_client.ping()
                logger.info(f"Redis L1 cache connected at {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis unavailable: {e}. Using LRU L2 only.")
                self.redis_client = None

        # Statistics
        self.hits = 0
        self.misses = 0
        self.stats_lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (L2 → L1 → None).

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        # Check L2 (LRU) first - fastest
        value = self.lru_cache.get(key)
        if value is not None:
            with self.stats_lock:
                self.hits += 1
            logger.debug(f"Cache hit (L2): {key}")
            return value

        # Check L1 (Redis)
        if self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    value = self._deserialize(cached)
                    # Populate L2 for faster access next time
                    self.lru_cache.set(key, value)
                    with self.stats_lock:
                        self.hits += 1
                    logger.debug(f"Cache hit (L1): {key}")
                    return value
            except Exception as e:
                logger.warning(f"Redis get failed for {key}: {e}")

        # Cache miss
        with self.stats_lock:
            self.misses += 1
        logger.debug(f"Cache miss: {key}")
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set value in both cache layers.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 3600 = 1 hour)
        """
        # Set in L2 (LRU)
        self.lru_cache.set(key, value)

        # Set in L1 (Redis)
        if self.redis_client:
            try:
                serialized = self._serialize(value)
                self.redis_client.setex(key, ttl, serialized)
                logger.debug(f"Cached in L1+L2: {key} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Redis set failed for {key}: {e}")
        else:
            logger.debug(f"Cached in L2 only: {key}")

    def invalidate(self, pattern: str):
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Key pattern (e.g., "features:*")
        """
        # Invalidate L1 (Redis)
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} Redis keys matching {pattern}")
            except Exception as e:
                logger.warning(f"Redis invalidate failed: {e}")

        # Invalidate L2 (LRU) - clear all since we don't have pattern matching
        # In production, you might want more sophisticated L2 invalidation
        self.lru_cache.clear()
        logger.info(f"Cleared L2 cache")

    def clear(self):
        """Clear all cache entries"""
        self.lru_cache.clear()

        if self.redis_client:
            try:
                self.redis_client.flushdb()
                logger.info("Cleared all caches (L1+L2)")
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with hits, misses, hit_rate, etc.
        """
        with self.stats_lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0.0
            miss_rate = self.misses / total if total > 0 else 0.0

            return {
                'hits': self.hits,
                'misses': self.misses,
                'total_requests': total,
                'hit_rate': hit_rate,
                'miss_rate': miss_rate,
                'l2_size': len(self.lru_cache),
                'redis_connected': self.redis_client is not None
            }

    def _serialize(self, value: Any) -> bytes:
        """
        Serialize value for Redis storage.

        Args:
            value: Value to serialize

        Returns:
            Serialized bytes
        """
        return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize value from Redis.

        Args:
            data: Serialized bytes

        Returns:
            Deserialized value
        """
        return pickle.loads(data)

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.redis_client:
            self.redis_client.close()


# Global cache instance (can be used across modules)
_global_cache = None


def get_cache_manager(
    redis_host: Optional[str] = None,
    redis_port: int = 6379,
    max_memory_mb: int = 512
) -> CacheManager:
    """
    Get global cache manager instance.

    Args:
        redis_host: Redis host (None for LRU only)
        redis_port: Redis port
        max_memory_mb: Max memory for LRU

    Returns:
        CacheManager instance
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = CacheManager(
            redis_host=redis_host,
            redis_port=redis_port,
            max_memory_mb=max_memory_mb
        )

    return _global_cache


# Decorator for automatic caching
def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator to automatically cache function results.

    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key

    Example:
        @cached(ttl=300, key_prefix="features")
        def extract_features(bse_code: str, date: str):
            # Expensive computation
            return features
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__] if key_prefix else [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)

            # Get cache manager
            cache = get_cache_manager()

            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator
