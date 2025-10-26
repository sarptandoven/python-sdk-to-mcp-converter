"""demo of the mcp server with all features."""
import json
import sys
from io import StringIO
from server import MCPServer
from config import Config


def demo_basic_usage():
    """demonstrate basic server usage."""
    print("\n=== basic usage demo ===")
    
    # create a simple config
    config = Config()
    config.sdks = ["os"]
    config.allow_dangerous = False
    
    server = MCPServer(config)
    
    # list tools
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    response = server.handle_request(request)
    print(f"found {len(response['result']['tools'])} tools")
    print(f"sample tools: {[t['name'] for t in response['result']['tools'][:3]]}")


def demo_caching():
    """demonstrate caching feature."""
    print("\n=== caching demo ===")
    
    config = Config()
    config.sdks = ["os"]
    config.enable_cache = True
    config.cache_ttl = 60
    
    server = MCPServer(config)
    
    # get first available tool
    list_request = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "tools/list",
        "params": {}
    }
    list_response = server.handle_request(list_request)
    tool_name = list_response["result"]["tools"][0]["name"]
    
    # first call
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": {}
        }
    }
    
    response1 = server.handle_request(request)
    cached1 = response1.get("result", {}).get("metadata", {}).get("cached", False)
    duration1 = response1.get("result", {}).get("metadata", {}).get("duration_ms", 0)
    
    print(f"first call: cached={cached1}, duration={duration1:.2f}ms")
    
    # second call (should be cached)
    request["id"] = 2
    response2 = server.handle_request(request)
    cached2 = response2.get("result", {}).get("metadata", {}).get("cached", False)
    duration2 = response2.get("result", {}).get("metadata", {}).get("duration_ms", 0)
    
    print(f"second call: cached={cached2}, duration={duration2:.2f}ms")
    print(f"speedup: {duration1 / max(duration2, 0.001):.1f}x")


def demo_rate_limiting():
    """demonstrate rate limiting."""
    print("\n=== rate limiting demo ===")
    
    config = Config()
    config.sdks = ["os"]
    config.enable_rate_limit = True
    config.rate_limit_calls = 3
    config.rate_limit_window = 60
    
    server = MCPServer(config)
    
    # get first available tool
    list_request = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "tools/list",
        "params": {}
    }
    list_response = server.handle_request(list_request)
    tool_name = list_response["result"]["tools"][0]["name"]
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": {}
        }
    }
    
    # make calls until rate limited
    for i in range(5):
        request["id"] = i + 1
        response = server.handle_request(request)
        
        if "error" in response:
            print(f"call {i+1}: rate limited (error code {response['error']['code']})")
        else:
            print(f"call {i+1}: success")


def demo_metrics():
    """demonstrate metrics collection."""
    print("\n=== metrics demo ===")
    
    config = Config()
    config.sdks = ["os"]
    
    server = MCPServer(config)
    
    # get first available tool
    list_request = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "tools/list",
        "params": {}
    }
    list_response = server.handle_request(list_request)
    tool_name = list_response["result"]["tools"][0]["name"]
    
    # make some calls
    for i in range(3):
        request = {
            "jsonrpc": "2.0",
            "id": i + 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": {}
            }
        }
        server.handle_request(request)
    
    # get server info with metrics
    request = {
        "jsonrpc": "2.0",
        "id": 100,
        "method": "server/info",
        "params": {}
    }
    
    response = server.handle_request(request)
    stats = response["result"]["stats"]
    
    print(f"executor calls: {stats['executor']['total_calls']}")
    print(f"successful requests: {stats['metrics']['counters'].get('successful_requests', 0)}")
    print(f"uptime: {stats['metrics']['uptime_seconds']:.2f}s")


def demo_validation():
    """demonstrate input validation."""
    print("\n=== validation demo ===")
    
    config = Config()
    config.sdks = ["os"]
    
    server = MCPServer(config)
    
    # invalid request (missing jsonrpc)
    request = {
        "id": 1,
        "method": "tools/list"
    }
    
    response = server.handle_request(request)
    if "error" in response:
        print(f"caught invalid request: {response['error']['message']}")
    
    # invalid tool name
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "invalid-tool-name!",
            "arguments": {}
        }
    }
    
    response = server.handle_request(request)
    if "error" in response:
        print(f"caught invalid tool name: {response['error']['message']}")


if __name__ == "__main__":
    print("python sdk to mcp converter - feature demo")
    print("=" * 50)
    
    # suppress logs for cleaner output
    import os as env_os
    env_os.environ["LOG_LEVEL"] = "ERROR"
    
    demo_basic_usage()
    demo_caching()
    demo_rate_limiting()
    demo_metrics()
    demo_validation()
    
    print("\n" + "=" * 50)
    print("demo complete")

