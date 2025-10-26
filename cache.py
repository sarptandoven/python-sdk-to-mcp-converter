"""caching layer for sdk calls."""
import time
import hashlib
import json
from functools import wraps


class SimpleCache:
    """simple in-memory cache with ttl."""
    
    def __init__(self, default_ttl=300):
        self.cache = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def _make_key(self, func_name, args, kwargs):
        """generate cache key from function call."""
        key_data = {
            "func": func_name,
            "args": str(args),
            "kwargs": str(sorted(kwargs.items()))
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key):
        """get value from cache."""
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # check if expired
        if time.time() > entry["expires_at"]:
            del self.cache[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return entry["value"]
    
    def set(self, key, value, ttl=None):
        """set value in cache."""
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time()
        }
    
    def clear(self):
        """clear all cache entries."""
        self.cache = {}
        self.hits = 0
        self.misses = 0
    
    def stats(self):
        """get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 3)
        }


def cacheable(cache_instance, ttl=None):
    """decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # generate cache key
            key = cache_instance._make_key(func.__name__, args, kwargs)
            
            # try cache first
            cached = cache_instance.get(key)
            if cached is not None:
                return cached
            
            # execute and cache
            result = func(*args, **kwargs)
            cache_instance.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator

