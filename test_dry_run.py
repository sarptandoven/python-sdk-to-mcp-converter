"""tests for dry-run functionality."""
from dry_run import DryRunInterceptor


def test_interception():
    """test that dangerous calls are intercepted."""
    interceptor = DryRunInterceptor(enabled=True)
    
    assert interceptor.should_intercept("os.remove", is_dangerous=True) == True
    assert interceptor.should_intercept("os.getcwd", is_dangerous=False) == False


def test_disabled():
    """test that disabled interceptor doesn't intercept."""
    interceptor = DryRunInterceptor(enabled=False)
    
    assert interceptor.should_intercept("os.remove", is_dangerous=True) == False


def test_intercept_records():
    """test that interceptions are recorded."""
    interceptor = DryRunInterceptor(enabled=True)
    
    def dummy_func(x, y):
        return x + y
    
    result = interceptor.intercept("test.func", dummy_func, {"x": 1, "y": 2})
    
    assert result["dry_run"] == True
    assert "would have called test.func" in result["message"]
    
    intercepted = interceptor.get_intercepted()
    assert len(intercepted) == 1
    assert intercepted[0]["tool"] == "test.func"


def test_clear():
    """test clearing intercepted calls."""
    interceptor = DryRunInterceptor(enabled=True)
    
    def dummy_func():
        pass
    
    interceptor.intercept("test.func", dummy_func, {})
    assert len(interceptor.get_intercepted()) == 1
    
    interceptor.clear()
    assert len(interceptor.get_intercepted()) == 0


if __name__ == "__main__":
    test_interception()
    test_disabled()
    test_intercept_records()
    test_clear()
    print("all dry-run tests passed")

