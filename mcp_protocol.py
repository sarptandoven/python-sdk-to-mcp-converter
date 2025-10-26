"""simple mcp protocol implementation over stdio."""
import json
import sys


def send_response(response):
    """send json response to stdout."""
    print(json.dumps(response), flush=True)


def read_request():
    """read json request from stdin."""
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line.strip())


def handle_tools_list(tools):
    """handle tools/list request."""
    return {
        "jsonrpc": "2.0",
        "result": {
            "tools": [
                {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "inputSchema": tool.get("schema", {})
                }
                for tool in tools
            ]
        }
    }


def handle_tools_call(tool_name, arguments, tool_registry):
    """handle tools/call request."""
    if tool_name not in tool_registry:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": f"tool not found: {tool_name}"
            }
        }
    
    try:
        result = tool_registry[tool_name](**arguments)
        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [{"type": "text", "text": str(result)}]
            }
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }

