"""tests for rate limiting."""
from rate_limit import RateLimiter
import time


def test_rate_limit_basic():
    """test basic rate limiting."""
    limiter = RateLimiter(max_calls=5, time_window=10)
    
    # first 5 calls should succeed
    for i in range(5):
        assert limiter.check_limit() == True
    
    # 6th call should fail
    assert limiter.check_limit() == False


def test_rate_limit_per_key():
    """test per-key rate limiting."""
    limiter = RateLimiter(max_calls=2, time_window=10)
    
    assert limiter.check_limit("key1") == True
    assert limiter.check_limit("key1") == True
    assert limiter.check_limit("key1") == False
    
    # different key should still work
    assert limiter.check_limit("key2") == True


def test_rate_limit_expiration():
    """test rate limit window expiration."""
    limiter = RateLimiter(max_calls=2, time_window=1)
    
    assert limiter.check_limit() == True
    assert limiter.check_limit() == True
    assert limiter.check_limit() == False
    
    # wait for window to expire
    time.sleep(1.1)
    
    # should work again
    assert limiter.check_limit() == True


def test_get_remaining():
    """test getting remaining calls."""
    limiter = RateLimiter(max_calls=5, time_window=10)
    
    assert limiter.get_remaining() == 5
    
    limiter.check_limit()
    assert limiter.get_remaining() == 4
    
    limiter.check_limit()
    assert limiter.get_remaining() == 3


if __name__ == "__main__":
    test_rate_limit_basic()
    test_rate_limit_per_key()
    test_rate_limit_expiration()
    test_get_remaining()
    print("all rate limit tests passed")

