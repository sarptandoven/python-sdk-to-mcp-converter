"""execution engine with retries, timeouts, and error handling."""
import time
import asyncio
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
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    # check if error is retryable
                    if not _is_retryable(e):
                        raise
                    
                    # wait before retry
                    if attempt < max_retries - 1:
                        wait_time = backoff ** attempt
                        time.sleep(wait_time)
            
            raise last_error
        return wrapper
    return decorator


def with_timeout(seconds=30):
    """decorator to add timeout."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # simple timeout implementation
            # todo: use proper threading for sync functions
            try:
                if asyncio.iscoroutinefunction(func):
                    return asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
                else:
                    # for now, just call directly
                    # proper timeout would need threading
                    return func(*args, **kwargs)
            except asyncio.TimeoutError:
                raise ExecutionError("TIMEOUT", f"execution exceeded {seconds}s")
        return wrapper
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
    
    def __init__(self, config):
        self.config = config
        self.call_count = 0
    
    @with_timeout(seconds=30)
    @with_retry(max_retries=3)
    def execute(self, callable_obj, kwargs):
        """execute with retry and timeout."""
        self.call_count += 1
        
        start = time.time()
        try:
            result = callable_obj(**kwargs)
            duration = time.time() - start
            
            return {
                "success": True,
                "result": result,
                "duration_ms": duration * 1000
            }
        except Exception as e:
            duration = time.time() - start
            
            return {
                "success": False,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e)
                },
                "duration_ms": duration * 1000
            }
    
    def get_stats(self):
        """get execution statistics."""
        return {
            "total_calls": self.call_count
        }

