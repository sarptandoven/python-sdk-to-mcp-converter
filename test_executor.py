"""tests for executor."""
from executor import Executor, ExecutionError
from config import Config


def test_successful_execution():
    """test successful execution."""
    config = Config()
    executor = Executor(config)
    
    def sample_func(x, y):
        return x + y
    
    result = executor.execute(sample_func, {"x": 1, "y": 2})
    
    assert result["success"] == True
    assert result["result"] == 3
    assert "duration_ms" in result


def test_execution_error():
    """test error handling."""
    config = Config()
    executor = Executor(config)
    
    def failing_func():
        raise ValueError("test error")
    
    result = executor.execute(failing_func, {})
    
    assert result["success"] == False
    assert "error" in result
    assert result["error"]["type"] == "ValueError"


def test_execution_stats():
    """test stats tracking."""
    config = Config()
    executor = Executor(config)
    
    def sample_func():
        return "ok"
    
    executor.execute(sample_func, {})
    executor.execute(sample_func, {})
    
    stats = executor.get_stats()
    assert stats["total_calls"] == 2


if __name__ == "__main__":
    test_successful_execution()
    test_execution_error()
    test_execution_stats()
    print("all tests passed")

