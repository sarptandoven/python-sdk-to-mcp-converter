"""minimal mcp server."""
import importlib
import sys
from mcp_protocol import read_request, send_response, handle_tools_list
from reflection import discover_methods
from schema_gen import signature_to_schema
from auth import AuthManager
from safety import redact_secrets
from executor import Executor


class MCPServer:
    """minimal mcp server for python sdks."""
    
    def __init__(self, config):
        self.config = config
        self.tools = []
        self.tool_registry = {}
        self.auth_manager = AuthManager()
        self.executor = Executor(config)
        self._load_sdks()
    
    def _load_sdks(self):
        """load configured sdks."""
        for module_name in self.config.sdks:
            try:
                module = importlib.import_module(module_name)
                methods = discover_methods(module, module_name, self.config.allow_dangerous)
                
                for method in methods:
                    schema = signature_to_schema(method["signature"], method.get("docstring"))
                    
                    tool = {
                        "name": method["name"],
                        "description": method.get("docstring", ""),
                        "schema": schema
                    }
                    
                    self.tools.append(tool)
                    self.tool_registry[method["name"]] = method["callable"]
                
                print(f"[OK] loaded {module_name}: {len(methods)} methods", file=sys.stderr)
            
            except Exception as e:
                print(f"[FAIL] {module_name}: {e}", file=sys.stderr)
    
    def execute_tool(self, tool_name, arguments):
        """execute a tool."""
        if tool_name not in self.tool_registry:
            raise ValueError(f"tool not found: {tool_name}")
        
        callable_obj = self.tool_registry[tool_name]
        
        # inject auth
        sdk_name = tool_name.split(".")[0]
        arguments = self.auth_manager.inject_auth(sdk_name, arguments)
        
        # execute
        result = self.executor.execute(callable_obj, arguments)
        
        # redact secrets
        if self.config.redact_secrets:
            result = redact_secrets(result)
        
        return result
    
    def handle_request(self, request):
        """handle mcp request."""
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
                    "error": {"code": -32601, "message": f"method not found: {method}"}
                }
            
            response["id"] = req_id
            return response
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)}
            }
    
    def run(self):
        """run server on stdio."""
        print(f"[OK] server started: {len(self.tools)} tools from {len(self.config.sdks)} sdks", file=sys.stderr)
        
        while True:
            request = read_request()
            if not request:
                break
            
            response = self.handle_request(request)
            send_response(response)


if __name__ == "__main__":
    from config import load_config
    
    config = load_config()
    server = MCPServer(config)
    server.run()
