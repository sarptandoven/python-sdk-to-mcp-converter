"""input validation utilities."""
import re


class ValidationError(Exception):
    """raised when validation fails."""
    pass


def validate_tool_name(name):
    """validate tool name format."""
    if not name:
        raise ValidationError("tool name cannot be empty")
    
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_\.]*$', name):
        raise ValidationError(f"invalid tool name format: {name}")
    
    return True


def validate_arguments(arguments, schema):
    """validate arguments against schema."""
    if not isinstance(arguments, dict):
        raise ValidationError("arguments must be a dictionary")
    
    # check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in arguments:
            raise ValidationError(f"missing required field: {field}")
    
    # basic type checking
    properties = schema.get("properties", {})
    for key, value in arguments.items():
        if key not in properties:
            continue  # allow extra fields
        
        expected_type = properties[key].get("type")
        if expected_type and not _check_type(value, expected_type):
            raise ValidationError(
                f"field '{key}' expected {expected_type}, got {type(value).__name__}"
            )
    
    return True


def _check_type(value, expected_type):
    """check if value matches expected type."""
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None)
    }
    
    expected = type_map.get(expected_type)
    if not expected:
        return True  # unknown type, allow
    
    return isinstance(value, expected)


def sanitize_string(value, max_length=1000):
    """sanitize string input."""
    if not isinstance(value, str):
        value = str(value)
    
    # truncate
    if len(value) > max_length:
        value = value[:max_length]
    
    # remove control characters except newline/tab
    value = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', value)
    
    return value


def validate_json_rpc_request(request):
    """validate json-rpc 2.0 request format."""
    if not isinstance(request, dict):
        raise ValidationError("request must be a json object")
    
    if request.get("jsonrpc") != "2.0":
        raise ValidationError("jsonrpc must be '2.0'")
    
    if "method" not in request:
        raise ValidationError("method is required")
    
    if not isinstance(request["method"], str):
        raise ValidationError("method must be a string")
    
    return True

