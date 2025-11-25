"""
Caching layer for Amadeus Hotels API responses.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Union
from threading import Lock
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    data: Any
    timestamp: float
    ttl: int
    
    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        return time.time() - self.timestamp > self.ttl


class ThreadSafeCache:
    """Thread-safe cache implementation with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._access_times: Dict[str, float] = {}
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        # Create a deterministic key from the arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if entry.is_expired():
                # Remove expired entry
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                return None
            
            # Update access time for LRU
            self._access_times[key] = time.time()
            return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache."""
        with self._lock:
            # Remove expired entries first
            self._cleanup_expired()
            
            # If cache is full, remove least recently used entry
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            # Set the new entry
            entry_ttl = ttl if ttl is not None else self.default_ttl
            self._cache[key] = CacheEntry(
                data=value,
                timestamp=time.time(),
                ttl=entry_ttl
            )
            self._access_times[key] = time.time()
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries from the cache."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]
    
    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._access_times:
            return
        
        # Find the least recently used key
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        del self._cache[lru_key]
        del self._access_times[lru_key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def size(self) -> int:
        """Get the current cache size."""
        with self._lock:
            return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'default_ttl': self.default_ttl,
                'hit_rate': getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1)
            }


class AmadeusCache:
    """Cache wrapper for Amadeus API responses."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache = ThreadSafeCache(max_size=max_size, default_ttl=default_ttl)
        self._hit_count = 0
        self._miss_count = 0
    
    def _get_cache_key(self, method: str, *args, **kwargs) -> str:
        """Generate a cache key for API method calls."""
        # Create a deterministic key from method name and arguments
        key_data = {
            'method': method,
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get_or_set(
        self,
        method: str,
        callable_func,
        *args,
        ttl: Optional[int] = None,
        **kwargs
    ) -> Any:
        """Get from cache or call function and cache result."""
        cache_key = self._get_cache_key(method, *args, **kwargs)
        
        # Try to get from cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            self._hit_count += 1
            logger.debug(f"Cache hit for {method}")
            return cached_result
        
        # Cache miss - call the function
        self._miss_count += 1
        logger.debug(f"Cache miss for {method}")
        
        try:
            # Call the actual function
            if asyncio.iscoroutinefunction(callable_func):
                result = await callable_func(*args, **kwargs)
            else:
                result = callable_func(*args, **kwargs)
            
            # Cache the result
            self.cache.set(cache_key, result, ttl=ttl)
            return result
            
        except Exception as e:
            logger.error(f"Error calling {method}: {e}")
            raise
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern."""
        # This is a simple implementation - in production you might want
        # to use a more sophisticated pattern matching
        with self.cache._lock:
            keys_to_remove = [
                key for key in self.cache._cache.keys()
                if pattern in key
            ]
            for key in keys_to_remove:
                del self.cache._cache[key]
                if key in self.cache._access_times:
                    del self.cache._access_times[key]
            return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self._hit_count = 0
        self._miss_count = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / max(total_requests, 1)
        
        stats = self.cache.stats()
        stats.update({
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'total_requests': total_requests,
            'hit_rate': hit_rate
        })
        return stats






