"""generate json schemas from python signatures with llm enhancement."""
import inspect
import json
import os


def signature_to_schema(sig, docstring=None, use_llm=False):
    """convert python signature to json schema."""
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name in ["self", "cls"]:
            continue
        
        # Skip *args and **kwargs - they can't be in JSON schemas
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            continue  # Skip *args
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            continue  # Skip **kwargs
        
        # improved type mapping
        param_type = _get_json_type(param.annotation)
        prop = {"type": param_type}
        
        # add description from docstring if available
        if docstring:
            desc = _extract_param_description(docstring, param_name)
            if desc:
                prop["description"] = desc
        
        # handle defaults
        if param.default != inspect.Parameter.empty:
            try:
                # test if default is json serializable
                json.dumps(param.default)
                prop["default"] = param.default
            except (TypeError, ValueError):
                # non-serializable default, convert to string
                prop["default"] = str(param.default)
        else:
            required.append(param_name)
        
        properties[param_name] = prop
    
    schema = {
        "type": "object",
        "properties": properties,
        "required": required
    }
    
    # enhance with llm if enabled
    if use_llm and os.getenv("OPENAI_API_KEY"):
        schema = _enhance_schema_with_llm(schema, docstring)
    
    return schema


def _get_json_type(annotation):
    """map python type to json type."""
    if annotation == inspect.Parameter.empty:
        return "string"
    
    type_map = {
        int: "integer",
        float: "number",
        bool: "boolean",
        str: "string",
        list: "array",
        dict: "object"
    }
    
    # handle typing generics
    if hasattr(annotation, "__origin__"):
        origin = annotation.__origin__
        if origin in type_map:
            return type_map[origin]
    
    return type_map.get(annotation, "string")


def _extract_param_description(docstring, param_name):
    """try to extract parameter description from docstring."""
    if not docstring:
        return None
    
    lines = docstring.lower().split("\n")
    for i, line in enumerate(lines):
        if param_name in line and ("param" in line or "arg" in line):
            # extract description after the parameter name
            parts = line.split(":")
            if len(parts) > 1:
                return parts[-1].strip()
    
    return None


def _enhance_schema_with_llm(schema, docstring):
    """use llm to improve schema descriptions."""
    # basic implementation - can be improved
    try:
        import openai
        
        prompt = f"""improve this json schema by adding better descriptions.

schema: {json.dumps(schema)}
docstring: {docstring or 'none'}

return only the improved json schema, keeping the same structure."""
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        improved = json.loads(response.choices[0].message.content)
        return improved
    except Exception as e:
        # fallback to original schema if llm fails
        return schema
