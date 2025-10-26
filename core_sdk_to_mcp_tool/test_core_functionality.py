"""comprehensive tests for core sdk-to-mcp functionality."""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

from reflection import discover_methods
from schema_gen import signature_to_schema
from mcp_protocol import handle_tools_list, handle_tools_call
from executor import Executor
from config import Config


def test_method_discovery():
    """test 1: discover methods from python's os module."""
    import os as os_module
    
    methods = discover_methods(os_module, "os", allow_dangerous=False)
    
    assert len(methods) > 0, "should discover at least some methods"
    
    assert any("getcwd" in m["name"] for m in methods), "should find os.getcwd"
    assert any("listdir" in m["name"] for m in methods), "should find os.listdir"
    
    for method in methods:
        assert "name" in method
        assert "callable" in method
        assert "signature" in method
        assert callable(method["callable"])
    
    print(f"[OK] test 1 passed: discovered {len(methods)} methods from os module")
    return True


def test_schema_generation():
    """test 2: generate json schema from python function."""
    def example_function(name: str, age: int = 25, active: bool = True):
        return f"{name} is {age}"
    
    import inspect
    sig = inspect.signature(example_function)
    schema = signature_to_schema(sig)
    
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["age"]["type"] == "integer"
    assert schema["properties"]["age"]["default"] == 25
    assert "name" in schema["required"]
    assert "age" not in schema["required"]
    
    print("[OK] test 2 passed: schema generation works correctly")
    return True


def test_mcp_protocol_tools_list():
    """test 3: test mcp tools/list protocol."""
    tools = [
        {
            "name": "os.getcwd",
            "description": "get current working directory",
            "schema": {"type": "object", "properties": {}, "required": []}
        },
        {
            "name": "os.listdir",
            "description": "list directory contents",
            "schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }
    ]
    
    response = handle_tools_list(tools)
    
    assert response["jsonrpc"] == "2.0"
    assert "result" in response
    assert "tools" in response["result"]
    assert len(response["result"]["tools"]) == 2
    assert response["result"]["tools"][0]["name"] == "os.getcwd"
    assert "inputSchema" in response["result"]["tools"][0]
    
    print("[OK] test 3 passed: mcp tools/list protocol works")
    return True


def test_mcp_protocol_tools_call():
    """test 4: test mcp tools/call protocol."""
    def mock_function(value: int):
        return value * 2
    
    tool_registry = {
        "test.double": mock_function
    }
    
    response = handle_tools_call("test.double", {"value": 5}, tool_registry)
    
    assert response["jsonrpc"] == "2.0"
    assert "result" in response
    assert "content" in response["result"]
    assert response["result"]["content"][0]["type"] == "text"
    assert "10" in response["result"]["content"][0]["text"]
    
    error_response = handle_tools_call("nonexistent", {}, tool_registry)
    assert "error" in error_response
    assert error_response["error"]["code"] == -32601
    
    print("[OK] test 4 passed: mcp tools/call protocol works")
    return True


def test_executor_basic():
    """test 5: test executor with simple function."""
    config = Config()
    config.max_retries = 1
    config.timeout_seconds = 5
    
    executor = Executor(config)
    
    def simple_add(a: int, b: int):
        return a + b
    
    result = executor.execute(simple_add, {"a": 3, "b": 7})
    
    assert result == 10
    
    print("[OK] test 5 passed: executor basic functionality works")
    return True


def test_complex_sdk_discovery():
    """test 6: test discovery with json module (more complex)."""
    import json as json_module
    
    methods = discover_methods(json_module, "json", allow_dangerous=False)
    
    assert len(methods) > 0, "should discover json methods"
    assert any("dumps" in m["name"] for m in methods), "should find json.dumps"
    assert any("loads" in m["name"] for m in methods), "should find json.loads"
    
    for method in methods:
        assert method["signature"] is not None, "all methods should have signatures"
    
    print(f"[OK] test 6 passed: discovered {len(methods)} methods from json module")
    return True


def test_dangerous_method_filtering():
    """test 7: test dangerous method filtering."""
    from safety import is_dangerous
    
    assert is_dangerous("os.remove") == True
    assert is_dangerous("os.delete_file") == True
    assert is_dangerous("database.drop_table") == True
    assert is_dangerous("api.create_user") == True
    
    assert is_dangerous("os.getcwd") == False
    assert is_dangerous("os.listdir") == False
    assert is_dangerous("api.get_user") == False
    
    print("[OK] test 7 passed: dangerous method filtering works")
    return True


def test_end_to_end_simple_sdk():
    """test 8: end-to-end test with pathlib."""
    from pathlib import Path
    import pathlib
    
    methods = discover_methods(pathlib, "pathlib", allow_dangerous=False)
    
    assert len(methods) > 0, "should discover pathlib methods"
    
    path_methods = [m for m in methods if "Path" in m["name"]]
    assert len(path_methods) > 0, "should find Path class methods"
    
    for method in path_methods[:5]:
        schema = signature_to_schema(method["signature"], method.get("docstring"))
        assert schema["type"] == "object"
        assert "properties" in schema
    
    print(f"[OK] test 8 passed: end-to-end pathlib discovery and schema generation")
    return True


def test_executor_with_retry():
    """test 9: test executor retry logic."""
    config = Config()
    config.max_retries = 3
    config.timeout_seconds = 5
    
    executor = Executor(config)
    
    call_count = [0]
    
    def flaky_function():
        call_count[0] += 1
        if call_count[0] < 2:
            raise Exception("timeout error")
        return "success"
    
    result = executor.execute(flaky_function, {})
    
    assert result == "success"
    assert call_count[0] == 2, "should retry once"
    
    print("[OK] test 9 passed: executor retry logic works")
    return True


def run_all_tests():
    """run all core functionality tests."""
    tests = [
        test_method_discovery,
        test_schema_generation,
        test_mcp_protocol_tools_list,
        test_mcp_protocol_tools_call,
        test_executor_basic,
        test_complex_sdk_discovery,
        test_dangerous_method_filtering,
        test_end_to_end_simple_sdk,
        test_executor_with_retry
    ]
    
    print("\n" + "="*70)
    print("RUNNING CORE SDK-TO-MCP FUNCTIONALITY TESTS")
    print("="*70 + "\n")
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

