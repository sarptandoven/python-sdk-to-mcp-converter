"""main mcp server."""
import importlib
import sys
import inspect
import os
from mcp_protocol import read_request, send_response, handle_tools_list, handle_tools_call
from reflection import discover_methods
from schema_gen import signature_to_schema
from auth import inject_auth
from safety import redact_secrets


class MCPServer:
    """simple mcp server for python sdks."""
    
    def __init__(self, sdk_modules, allow_dangerous=False):
        """initialize with list of sdk module names to load."""
        self.tools = []
        self.tool_registry = {}
        self.allow_dangerous = allow_dangerous
        
        for module_name in sdk_modules:
            try:
                module = importlib.import_module(module_name)
                methods = discover_methods(module, module_name, allow_dangerous)
                
                for method in methods:
                    tool = {
                        "name": method["name"],
                        "description": method.get("docstring", ""),
                        "schema": signature_to_schema(method["signature"]),
                        "metadata": {
                            "is_dangerous": method.get("is_dangerous", False),
                            "has_pagination": method.get("has_pagination", False)
                        }
                    }
                    self.tools.append(tool)
                    self.tool_registry[method["name"]] = method["callable"]
                
                print(f"loaded {len(methods)} methods from {module_name}", file=sys.stderr)
            except Exception as e:
                print(f"error loading {module_name}: {e}", file=sys.stderr)
    
    def execute_tool(self, tool_name, arguments):
        """execute a tool with safety checks."""
        if tool_name not in self.tool_registry:
            raise ValueError(f"tool not found: {tool_name}")
        
        # inject auth if needed
        sdk_name = tool_name.split(".")[0]
        arguments = inject_auth(sdk_name, arguments)
        
        # execute
        try:
            result = self.tool_registry[tool_name](**arguments)
            
            # redact secrets from result
            result = redact_secrets(result)
            
            return result
        except Exception as e:
            # better error messages
            raise Exception(f"execution failed: {str(e)}")
    
    def run(self):
        """run the mcp server on stdio."""
        print("mcp server started", file=sys.stderr)
        print(f"loaded {len(self.tools)} tools", file=sys.stderr)
        
        while True:
            request = read_request()
            if not request:
                break
            
            method = request.get("method")
            params = request.get("params", {})
            req_id = request.get("id")
            
            try:
                if method == "tools/list":
                    response = handle_tools_list(self.tools)
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = self.execute_tool(tool_name, arguments)
                    response = {
                        "jsonrpc": "2.0",
                        "result": {
                            "content": [{"type": "text", "text": str(result)}]
                        }
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": "method not found"}
                    }
                
                response["id"] = req_id
                send_response(response)
            
            except Exception as e:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(e)}
                }
                send_response(response)


if __name__ == "__main__":
    from config import load_config
    
    config = load_config()
    print(f"starting with config: {config}", file=sys.stderr)
    
    server = MCPServer(config.sdks, config.allow_dangerous)
    server.run()
