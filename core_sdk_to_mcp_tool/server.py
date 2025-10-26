"""main mcp server with full integration."""
import importlib
import sys
import time
from mcp_protocol import read_request, send_response, handle_tools_list
from reflection import discover_methods
from schema_gen import signature_to_schema
from auth import AuthManager
from safety import redact_secrets
from executor import Executor
from pagination import detect_pagination, handle_paginated_call, collect_all_pages
from cache import SimpleCache
from rate_limit import RateLimiter, RateLimitExceeded
from logger import get_logger
from metrics import get_metrics
from validation import validate_tool_name, validate_arguments, validate_json_rpc_request, ValidationError
from filters import ToolFilter
from dry_run import DryRunInterceptor


class MCPServer:
    """mcp server for python sdks with full feature set."""
    
    def __init__(self, config):
        """initialize server with configuration."""
        self.config = config
        self.logger = get_logger()
        self.metrics = get_metrics()
        self.tools = []
        self.tool_registry = {}
        self.auth_manager = AuthManager()
        
        # initialize filtering
        self.tool_filter = ToolFilter(
            allowlist=config.tool_allowlist,
            denylist=config.tool_denylist
        )
        
        # initialize dry-run
        self.dry_run_interceptor = DryRunInterceptor(enabled=config.dry_run)
        if config.dry_run:
            self.logger.info("dry-run mode enabled")
        
        # initialize caching if enabled
        self.cache = None
        if config.__dict__.get("enable_cache", False):
            cache_ttl = config.__dict__.get("cache_ttl", 300)
            self.cache = SimpleCache(default_ttl=cache_ttl)
            self.logger.info("cache enabled", ttl=cache_ttl)
        
        # initialize rate limiting if enabled
        self.rate_limiter = None
        if config.__dict__.get("enable_rate_limit", False):
            max_calls = config.__dict__.get("rate_limit_calls", 100)
            time_window = config.__dict__.get("rate_limit_window", 60)
            self.rate_limiter = RateLimiter(max_calls, time_window)
            self.logger.info("rate limiting enabled", max_calls=max_calls, window=time_window)
        
        self.executor = Executor(config, self.cache, self.rate_limiter)
        
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
                    # check if tool should be included based on filters
                    if not self.tool_filter.should_include(method["name"]):
                        continue
                    
                    # check auth
                    has_auth = self.auth_manager.check_auth(module_name)
                    
                    # generate schema
                    use_llm = self.config.__dict__.get("use_llm", False)
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
                            "has_auth": has_auth,
                            "sdk": module_name
                        }
                    }
                    
                    self.tools.append(tool)
                    self.tool_registry[method["name"]] = {
                        "callable": method["callable"],
                        "pagination": pagination_info,
                        "is_dangerous": method.get("is_dangerous", False)
                    }
                
                self.logger.info(f"loaded sdk", name=module_name, methods=len(methods))
                
                if not has_auth:
                    self.logger.warn(f"no auth for sdk", name=module_name)
            
            except ModuleNotFoundError:
                self.logger.error(f"module not found", name=module_name)
            except Exception as e:
                self.logger.error(f"failed to load sdk", name=module_name, error=str(e))
    
    def execute_tool(self, tool_name, arguments, use_cache=True):
        """execute a tool with full safety and reliability."""
        if tool_name not in self.tool_registry:
            raise ValueError(f"tool not found: {tool_name}")
        
        tool_info = self.tool_registry[tool_name]
        callable_obj = tool_info["callable"]
        pagination_info = tool_info["pagination"]
        is_dangerous = tool_info.get("is_dangerous", False)
        
        # check for dry-run interception
        if self.dry_run_interceptor.should_intercept(tool_name, is_dangerous):
            result = self.dry_run_interceptor.intercept(tool_name, callable_obj, arguments)
            return {
                "result": result,
                "cached": False,
                "duration_ms": 0,
                "dry_run": True
            }
        
        # inject auth
        sdk_name = tool_name.split(".")[0]
        arguments = self.auth_manager.inject_auth(sdk_name, arguments)
        
        # execute
        start_time = time.time()
        if pagination_info["has_pagination"]:
            # choose pagination strategy
            if self.config.collect_all_pages:
                result = collect_all_pages(
                    callable_obj,
                    arguments,
                    pagination_info,
                    self.config.max_pagination_items
                )
            else:
                result = handle_paginated_call(
                    callable_obj,
                    arguments,
                    pagination_info,
                    self.config.max_pagination_items
                )
            duration_ms = (time.time() - start_time) * 1000
            exec_result = {"success": True, "result": result, "cached": False, "duration_ms": duration_ms}
        else:
            exec_result = self.executor.execute(
                tool_name,
                callable_obj,
                arguments,
                use_cache
            )
        
        if not exec_result["success"]:
            raise Exception(exec_result["error"]["message"])
        
        result = exec_result["result"]
        
        # redact secrets
        if self.config.redact_secrets:
            result = redact_secrets(result)
        
        return {
            "result": result,
            "cached": exec_result.get("cached", False),
            "duration_ms": exec_result.get("duration_ms", 0)
        }
    
    def handle_request(self, request):
        """handle a single mcp request."""
        start_time = time.time()
        
        # validate request format
        try:
            validate_json_rpc_request(request)
        except ValidationError as e:
            self.metrics.increment("validation_errors")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32600, "message": f"invalid request: {e}"}
            }
        
        method = request.get("method")
        params = request.get("params", {})
        req_id = request.get("id")
        
        self.logger.request(method, params)
        self.metrics.increment(f"requests.{method}")
        
        try:
            if method == "tools/list":
                response = handle_tools_list(self.tools)
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # validate tool name
                try:
                    validate_tool_name(tool_name)
                except ValidationError as e:
                    self.metrics.increment("invalid_tool_names")
                    raise ValueError(str(e))
                
                exec_info = self.execute_tool(tool_name, arguments)
                
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{"type": "text", "text": str(exec_info["result"])}],
                        "metadata": {
                            "cached": exec_info["cached"],
                            "duration_ms": exec_info["duration_ms"]
                        }
                    }
                }
            
            elif method == "server/info":
                executor_stats = self.executor.get_stats()
                all_metrics = self.metrics.get_all_stats()
                
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "name": "python-sdk-mcp-converter",
                        "version": "1.0.0",
                        "tools_count": len(self.tools),
                        "sdks": list(set(t["metadata"]["sdk"] for t in self.tools)),
                        "features": {
                            "caching": self.cache is not None,
                            "rate_limiting": self.rate_limiter is not None,
                            "llm_schemas": self.config.__dict__.get("use_llm", False),
                            "validation": True,
                            "metrics": True
                        },
                        "stats": {
                            "executor": executor_stats,
                            "metrics": all_metrics
                        }
                    }
                }
            
            elif method == "cache/clear":
                if self.cache:
                    self.cache.clear()
                    response = {
                        "jsonrpc": "2.0",
                        "result": {"message": "cache cleared"}
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32600, "message": "caching not enabled"}
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
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.response(method, duration_ms, "error" not in response)
            
            # track metrics
            self.metrics.record_time(f"request_duration.{method}", duration_ms)
            if "error" not in response:
                self.metrics.increment("successful_requests")
            
            return response
        
        except RateLimitExceeded as e:
            self.logger.warn("rate limit exceeded", method=method)
            self.metrics.increment("rate_limit_exceeded")
            self.metrics.increment("failed_requests")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": 429,
                    "message": str(e)
                }
            }
        
        except Exception as e:
            self.logger.error("request failed", method=method, error=str(e))
            self.metrics.increment("failed_requests")
            self.metrics.increment(f"errors.{type(e).__name__}")
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
        self.logger.info("server started", 
                        config=str(self.config),
                        tools=len(self.tools),
                        sdks=len(self.config.sdks))
        
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
