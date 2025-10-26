"""tests for validation utilities."""
from validation import (
    validate_tool_name,
    validate_arguments,
    sanitize_string,
    validate_json_rpc_request,
    ValidationError
)


def test_validate_tool_name():
    """test tool name validation."""
    # valid names
    assert validate_tool_name("os.getcwd") == True
    assert validate_tool_name("kubernetes.CoreV1Api.list_namespace") == True
    
    # invalid names
    try:
        validate_tool_name("")
        assert False, "should raise"
    except ValidationError:
        pass
    
    try:
        validate_tool_name("invalid-name")
        assert False, "should raise"
    except ValidationError:
        pass


def test_validate_arguments():
    """test argument validation."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name"]
    }
    
    # valid
    assert validate_arguments({"name": "test", "age": 25}, schema) == True
    assert validate_arguments({"name": "test"}, schema) == True
    
    # missing required
    try:
        validate_arguments({"age": 25}, schema)
        assert False, "should raise"
    except ValidationError:
        pass
    
    # wrong type
    try:
        validate_arguments({"name": 123}, schema)
        assert False, "should raise"
    except ValidationError:
        pass


def test_sanitize_string():
    """test string sanitization."""
    # normal string
    assert sanitize_string("hello world") == "hello world"
    
    # with control chars
    result = sanitize_string("hello\x00world")
    assert "\x00" not in result
    
    # long string
    long_str = "a" * 2000
    result = sanitize_string(long_str, max_length=100)
    assert len(result) == 100


def test_validate_json_rpc():
    """test json-rpc validation."""
    # valid request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    assert validate_json_rpc_request(request) == True
    
    # missing jsonrpc
    try:
        validate_json_rpc_request({"method": "test"})
        assert False, "should raise"
    except ValidationError:
        pass
    
    # missing method
    try:
        validate_json_rpc_request({"jsonrpc": "2.0"})
        assert False, "should raise"
    except ValidationError:
        pass


if __name__ == "__main__":
    test_validate_tool_name()
    test_validate_arguments()
    test_sanitize_string()
    test_validate_json_rpc()
    print("all validation tests passed")

