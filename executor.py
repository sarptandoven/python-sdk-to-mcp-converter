"""execution engine with retries, timeouts, caching, and async support."""
import time
import asyncio
import inspect
from functools import wraps


class ExecutionError(Exception):
    """structured execution error."""
    def __init__(self, code, message, details=None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


def with_retry(max_retries=3, backoff=2):
    """decorator to add retry logic."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    if not _is_retryable(e):
                        raise
                    
                    if attempt < max_retries - 1:
                        wait_time = backoff ** attempt
                        await asyncio.sleep(wait_time)
            
            raise last_error
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    if not _is_retryable(e):
                        raise
                    
                    if attempt < max_retries - 1:
                        wait_time = backoff ** attempt
                        time.sleep(wait_time)
            
            raise last_error
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def with_timeout(seconds=30):
    """decorator to add timeout."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise ExecutionError("TIMEOUT", f"execution exceeded {seconds}s")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # for sync functions, just call directly
            # proper timeout would require threading which adds complexity
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def _is_retryable(error):
    """check if error should be retried."""
    error_str = str(error).lower()
    retryable_patterns = [
        "timeout",
        "connection",
        "network",
        "temporarily unavailable",
        "rate limit",
        "too many requests",
        "503",
        "429"
    ]
    
    return any(pattern in error_str for pattern in retryable_patterns)


class Executor:
    """executes tool calls with safety and reliability."""
    
    def __init__(self, config, cache=None, rate_limiter=None):
        self.config = config
        self.cache = cache
        self.rate_limiter = rate_limiter
        self.call_count = 0
        self.error_count = 0
        self.cache_hits = 0
    
    def _check_rate_limit(self, tool_name):
        """check rate limit before execution."""
        if self.rate_limiter:
            if not self.rate_limiter.check_limit(tool_name):
                from rate_limit import RateLimitExceeded
                raise RateLimitExceeded(f"rate limit exceeded for {tool_name}")
    
    def _get_from_cache(self, tool_name, kwargs):
        """try to get result from cache."""
        if not self.cache:
            return None
        
        key = self.cache._make_key(tool_name, (), kwargs)
        result = self.cache.get(key)
        
        if result:
            self.cache_hits += 1
        
        return result
    
    def _save_to_cache(self, tool_name, kwargs, result):
        """save result to cache."""
        if self.cache:
            key = self.cache._make_key(tool_name, (), kwargs)
            self.cache.set(key, result)
    
    async def execute_async(self, callable_obj, kwargs):
        """execute async function with retry and timeout."""
        @with_timeout(seconds=self.config.timeout_seconds)
        @with_retry(max_retries=self.config.max_retries)
        async def _exec():
            return await callable_obj(**kwargs)
        
        return await _exec()
    
    def execute_sync(self, callable_obj, kwargs):
        """execute sync function with retry."""
        @with_retry(max_retries=self.config.max_retries)
        def _exec():
            return callable_obj(**kwargs)
        
        return _exec()
    
    def execute(self, tool_name, callable_obj, kwargs, use_cache=True):
        """execute with all features: cache, rate limit, retry."""
        self.call_count += 1
        
        # check rate limit
        self._check_rate_limit(tool_name)
        
        # try cache first
        if use_cache:
            cached = self._get_from_cache(tool_name, kwargs)
            if cached is not None:
                return {
                    "success": True,
                    "result": cached,
                    "cached": True,
                    "duration_ms": 0
                }
        
        # execute
        start = time.time()
        try:
            if inspect.iscoroutinefunction(callable_obj):
                # run async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.execute_async(callable_obj, kwargs)
                    )
                finally:
                    loop.close()
            else:
                result = self.execute_sync(callable_obj, kwargs)
            
            duration = time.time() - start
            
            # cache successful result
            if use_cache:
                self._save_to_cache(tool_name, kwargs, result)
            
            return {
                "success": True,
                "result": result,
                "cached": False,
                "duration_ms": duration * 1000
            }
        
        except Exception as e:
            self.error_count += 1
            duration = time.time() - start
            
            return {
                "success": False,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "code": getattr(e, "code", "UNKNOWN")
                },
                "duration_ms": duration * 1000
            }
    
    def get_stats(self):
        """get execution statistics."""
        stats = {
            "total_calls": self.call_count,
            "errors": self.error_count,
            "cache_hits": self.cache_hits
        }
        
        if self.cache:
            stats["cache"] = self.cache.stats()
        
        if self.rate_limiter:
            stats["rate_limit"] = self.rate_limiter.stats()
        
        return stats
