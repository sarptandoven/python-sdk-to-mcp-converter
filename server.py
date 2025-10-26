"""main mcp server."""
import importlib
import sys
import inspect
from mcp_protocol import read_request, send_response, handle_tools_list, handle_tools_call
from reflection import discover_methods
from schema_gen import signature_to_schema


class MCPServer:
    """simple mcp server for python sdks."""
    
    def __init__(self, sdk_modules):
        """initialize with list of sdk module names to load."""
        self.tools = []
        self.tool_registry = {}
        
        for module_name in sdk_modules:
            try:
                module = importlib.import_module(module_name)
                methods = discover_methods(module, module_name)
                
                for method in methods:
                    tool = {
                        "name": method["name"],
                        "description": inspect.getdoc(method["callable"]) or "",
                        "schema": signature_to_schema(method["signature"])
                    }
                    self.tools.append(tool)
                    self.tool_registry[method["name"]] = method["callable"]
                
                print(f"loaded {len(methods)} methods from {module_name}", file=sys.stderr)
            except Exception as e:
                print(f"error loading {module_name}: {e}", file=sys.stderr)
    
    def run(self):
        """run the mcp server on stdio."""
        print("mcp server started", file=sys.stderr)
        
        while True:
            request = read_request()
            if not request:
                break
            
            method = request.get("method")
            params = request.get("params", {})
            req_id = request.get("id")
            
            if method == "tools/list":
                response = handle_tools_list(self.tools)
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                response = handle_tools_call(tool_name, arguments, self.tool_registry)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": "method not found"}
                }
            
            response["id"] = req_id
            send_response(response)


if __name__ == "__main__":
    # default: load os module for testing
    sdks = ["os"]
    server = MCPServer(sdks)
    server.run()

