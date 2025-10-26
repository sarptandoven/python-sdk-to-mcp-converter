"""main mcp server with full integration."""
import importlib
import sys
import inspect
from mcp_protocol import read_request, send_response, handle_tools_list
from reflection import discover_methods
from schema_gen import signature_to_schema
from auth import AuthManager
from safety import redact_secrets
from executor import Executor
from pagination import detect_pagination, handle_paginated_call


class MCPServer:
    """mcp server for python sdks."""
    
    def __init__(self, config):
        """initialize server with configuration."""
        self.config = config
        self.tools = []
        self.tool_registry = {}
        self.auth_manager = AuthManager()
        self.executor = Executor(config)
        
        self._load_sdks()
    
    def _load_sdks(self):
        """load all configured sdks."""
        for module_name in self.config.sdks:
            try:
                module = importlib.import_module(module_name)
                methods = discover_methods(
                    module, 
                    module_name, 
                    self.config.allow_dangerous
                )
                
                for method in methods:
                    # check if auth is available
                    has_auth = self.auth_manager.check_auth(module_name)
                    
                    # generate schema with optional llm enhancement
                    use_llm = bool(self.config.__dict__.get("use_llm", False))
                    schema = signature_to_schema(
                        method["signature"],
                        method.get("docstring"),
                        use_llm
                    )
                    
                    # detect pagination
                    pagination_info = detect_pagination(method["signature"])
                    
                    tool = {
                        "name": method["name"],
                        "description": method.get("docstring", ""),
                        "schema": schema,
                        "metadata": {
                            "is_dangerous": method.get("is_dangerous", False),
                            "has_pagination": pagination_info["has_pagination"],
                            "has_auth": has_auth
                        }
                    }
                    
                    self.tools.append(tool)
                    self.tool_registry[method["name"]] = {
                        "callable": method["callable"],
                        "pagination": pagination_info
                    }
                
                print(f"loaded {len(methods)} methods from {module_name}", file=sys.stderr)
                
                if not has_auth:
                    print(f"warning: no auth configured for {module_name}", file=sys.stderr)
            
            except ModuleNotFoundError:
                print(f"error: module {module_name} not found", file=sys.stderr)
            except Exception as e:
                print(f"error loading {module_name}: {e}", file=sys.stderr)
    
    def execute_tool(self, tool_name, arguments):
        """execute a tool with full safety and reliability."""
        if tool_name not in self.tool_registry:
            raise ValueError(f"tool not found: {tool_name}")
        
        tool_info = self.tool_registry[tool_name]
        callable_obj = tool_info["callable"]
        pagination_info = tool_info["pagination"]
        
        # inject auth
        sdk_name = tool_name.split(".")[0]
        arguments = self.auth_manager.inject_auth(sdk_name, arguments)
        
        # execute with pagination handling
        if pagination_info["has_pagination"]:
            result = handle_paginated_call(
                callable_obj,
                arguments,
                pagination_info,
                self.config.max_pagination_items
            )
        else:
            exec_result = self.executor.execute(callable_obj, arguments)
            if not exec_result["success"]:
                raise Exception(exec_result["error"]["message"])
            result = exec_result["result"]
        
        # redact secrets
        if self.config.redact_secrets:
            result = redact_secrets(result)
        
        return result
    
    def handle_request(self, request):
        """handle a single mcp request."""
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
            
            elif method == "server/info":
                # additional endpoint for server info
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "name": "python-sdk-mcp-converter",
                        "version": "0.8.0",
                        "tools_count": len(self.tools),
                        "stats": self.executor.get_stats()
                    }
                }
            
            else:
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"method not found: {method}"
                    }
                }
            
            response["id"] = req_id
            return response
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": str(e),
                    "data": {"type": type(e).__name__}
                }
            }
    
    def run(self):
        """run the server on stdio."""
        print("mcp server started", file=sys.stderr)
        print(f"config: {self.config}", file=sys.stderr)
        print(f"loaded {len(self.tools)} tools from {len(self.config.sdks)} sdks", file=sys.stderr)
        
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
