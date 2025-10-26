"""dry-run interceptor for safe testing."""
import inspect


class DryRunInterceptor:
    """intercepts dangerous calls and returns mock results."""
    
    def __init__(self, enabled=False):
        self.enabled = enabled
        self.intercepted_calls = []
    
    def should_intercept(self, tool_name, is_dangerous):
        """check if call should be intercepted."""
        return self.enabled and is_dangerous
    
    def intercept(self, tool_name, callable_obj, kwargs):
        """intercept call and return mock result."""
        # record the call
        self.intercepted_calls.append({
            "tool": tool_name,
            "arguments": kwargs,
            "signature": str(inspect.signature(callable_obj))
        })
        
        # return mock result
        return {
            "dry_run": True,
            "message": f"would have called {tool_name}",
            "arguments": kwargs,
            "note": "this was a dry run, no actual operation performed"
        }
    
    def get_intercepted(self):
        """get list of intercepted calls."""
        return self.intercepted_calls
    
    def clear(self):
        """clear intercepted calls history."""
        self.intercepted_calls = []

