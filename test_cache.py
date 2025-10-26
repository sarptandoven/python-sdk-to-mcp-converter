"""tests for caching functionality."""
from cache import SimpleCache
import time


def test_cache_basic():
    """test basic cache operations."""
    cache = SimpleCache(default_ttl=10)
    
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    assert cache.get("key2") is None


def test_cache_expiration():
    """test cache expiration."""
    cache = SimpleCache(default_ttl=1)
    
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    time.sleep(1.1)
    assert cache.get("key1") is None


def test_cache_stats():
    """test cache statistics."""
    cache = SimpleCache()
    
    cache.set("key1", "value1")
    cache.get("key1")  # hit
    cache.get("key2")  # miss
    
    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["size"] == 1


def test_cache_clear():
    """test cache clearing."""
    cache = SimpleCache()
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    
    assert cache.stats()["size"] == 2
    
    cache.clear()
    assert cache.stats()["size"] == 0


if __name__ == "__main__":
    test_cache_basic()
    test_cache_expiration()
    test_cache_stats()
    test_cache_clear()
    print("all cache tests passed")

