"""generate json schemas from python signatures."""
import inspect


def signature_to_schema(sig):
    """convert python signature to json schema."""
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name in ["self", "cls"]:
            continue
        
        # basic type mapping
        param_type = "string"  # default
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
        
        properties[param_name] = {"type": param_type}
        
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    return {
        "type": "object",
        "properties": properties,
        "required": required
    }

