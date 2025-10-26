"""rate limiting for api calls."""
import time
from collections import defaultdict


class RateLimiter:
    """simple rate limiter using token bucket algorithm."""
    
    def __init__(self, max_calls=100, time_window=60):
        """
        initialize rate limiter.
        
        max_calls: maximum calls allowed in time window
        time_window: time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = defaultdict(list)
        self.total_blocked = 0
    
    def check_limit(self, key="default"):
        """check if call is allowed under rate limit."""
        now = time.time()
        
        # clean old entries
        self.calls[key] = [t for t in self.calls[key] if now - t < self.time_window]
        
        # check limit
        if len(self.calls[key]) >= self.max_calls:
            self.total_blocked += 1
            return False
        
        # record this call
        self.calls[key].append(now)
        return True
    
    def get_remaining(self, key="default"):
        """get remaining calls for key."""
        now = time.time()
        self.calls[key] = [t for t in self.calls[key] if now - t < self.time_window]
        return max(0, self.max_calls - len(self.calls[key]))
    
    def reset(self, key=None):
        """reset rate limit for key or all keys."""
        if key:
            self.calls[key] = []
        else:
            self.calls = defaultdict(list)
            self.total_blocked = 0
    
    def stats(self):
        """get rate limiter statistics."""
        return {
            "total_blocked": self.total_blocked,
            "tracked_keys": len(self.calls)
        }


class RateLimitExceeded(Exception):
    """raised when rate limit is exceeded."""
    pass

