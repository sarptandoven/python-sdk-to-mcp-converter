"""execution with retry logic."""
import time
import asyncio
import inspect
from functools import wraps


def with_retry(max_retries=3):
    """decorator for retry logic."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    if not any(x in error_str for x in ['timeout', 'connection', 'temporary']):
                        raise
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
            raise last_error
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    if not any(x in error_str for x in ['timeout', 'connection', 'temporary']):
                        raise
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
            raise last_error
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


class Executor:
    """executes sdk methods with retry."""
    
    def __init__(self, config):
        self.config = config
        self.max_retries = getattr(config, 'max_retries', 3)
        self.timeout = getattr(config, 'timeout_seconds', 30)
    
    def execute(self, callable_obj, arguments):
        """execute callable with retry."""
        if inspect.iscoroutinefunction(callable_obj):
            return asyncio.run(self._execute_async(callable_obj, arguments))
        else:
            return self._execute_sync(callable_obj, arguments)
    
    def _execute_sync(self, callable_obj, arguments):
        """execute sync callable with retry."""
        @with_retry(self.max_retries)
        def wrapped():
            return callable_obj(**arguments)
        
        return wrapped()
    
    async def _execute_async(self, callable_obj, arguments):
        """execute async callable with retry."""
        @with_retry(self.max_retries)
        async def wrapped():
            return await callable_obj(**arguments)
        
        return await wrapped()
