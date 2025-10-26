"""tests for executor."""
from executor import Executor, ExecutionError
from config import Config


def test_successful_execution():
    """test successful execution."""
    config = Config()
    executor = Executor(config, cache=None, rate_limiter=None)
    
    def sample_func(x, y):
        return x + y
    
    result = executor.execute("test_func", sample_func, {"x": 1, "y": 2}, use_cache=False)
    
    assert result["success"] == True
    assert result["result"] == 3
    assert "duration_ms" in result


def test_execution_error():
    """test error handling."""
    config = Config()
    executor = Executor(config, cache=None, rate_limiter=None)
    
    def failing_func():
        raise ValueError("test error")
    
    result = executor.execute("test_func", failing_func, {}, use_cache=False)
    
    assert result["success"] == False
    assert "error" in result
    assert result["error"]["type"] == "ValueError"


def test_execution_stats():
    """test stats tracking."""
    config = Config()
    executor = Executor(config, cache=None, rate_limiter=None)
    
    def sample_func():
        return "ok"
    
    executor.execute("test_func", sample_func, {}, use_cache=False)
    executor.execute("test_func", sample_func, {}, use_cache=False)
    
    stats = executor.get_stats()
    assert stats["total_calls"] == 2


def test_execution_with_cache():
    """test execution with caching."""
    from cache import SimpleCache
    
    config = Config()
    cache = SimpleCache(default_ttl=10)
    executor = Executor(config, cache, rate_limiter=None)
    
    call_count = 0
    
    def sample_func():
        nonlocal call_count
        call_count += 1
        return "result"
    
    # first call should execute
    result1 = executor.execute("test_func", sample_func, {}, use_cache=True)
    assert result1["success"] == True
    assert result1["cached"] == False
    assert call_count == 1
    
    # second call should be cached
    result2 = executor.execute("test_func", sample_func, {}, use_cache=True)
    assert result2["success"] == True
    assert result2["cached"] == True
    assert call_count == 1  # should not have increased


if __name__ == "__main__":
    test_successful_execution()
    test_execution_error()
    test_execution_stats()
    test_execution_with_cache()
    print("all tests passed")
