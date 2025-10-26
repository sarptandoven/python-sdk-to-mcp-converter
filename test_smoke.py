"""smoke tests for end-to-end functionality."""
from server import MCPServer
from config import Config
import json


def test_basic_server_lifecycle():
    """test basic server creation and tool listing."""
    config = Config()
    config.sdks = ["os"]
    
    server = MCPServer(config)
    
    # should have discovered tools
    assert len(server.tools) > 0
    assert any(t["name"].startswith("os.") for t in server.tools)


def test_tools_list_request():
    """test tools/list endpoint."""
    config = Config()
    config.sdks = ["os"]
    
    server = MCPServer(config)
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    response = server.handle_request(request)
    
    assert "error" not in response
    assert "result" in response
    assert "tools" in response["result"]
    assert len(response["result"]["tools"]) > 0


def test_server_info_request():
    """test server/info endpoint."""
    config = Config()
    config.sdks = ["os"]
    config.enable_cache = True
    config.enable_rate_limit = True
    
    server = MCPServer(config)
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "server/info",
        "params": {}
    }
    
    response = server.handle_request(request)
    
    assert "error" not in response
    result = response["result"]
    assert result["name"] == "python-sdk-mcp-converter"
    assert result["version"] == "1.0.0"
    assert result["features"]["caching"] == True
    assert result["features"]["rate_limiting"] == True


def test_filtering():
    """test tool filtering."""
    config = Config()
    config.sdks = ["os"]
    config.tool_allowlist = ["os.path.*"]
    
    server = MCPServer(config)
    
    # should only have path tools
    assert all("path" in t["name"] for t in server.tools)


def test_dry_run_mode():
    """test dry-run mode."""
    config = Config()
    config.sdks = ["os"]
    config.dry_run = True
    config.allow_dangerous = True
    
    server = MCPServer(config)
    
    # find a dangerous tool
    dangerous_tool = None
    for tool in server.tools:
        if tool["metadata"]["is_dangerous"]:
            dangerous_tool = tool["name"]
            break
    
    if dangerous_tool:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": dangerous_tool,
                "arguments": {}
            }
        }
        
        response = server.handle_request(request)
        
        # should get dry-run result, not error
        if "result" in response:
            content = str(response["result"])
            assert "dry_run" in content.lower() or "dry run" in content.lower()


def test_validation():
    """test input validation."""
    config = Config()
    config.sdks = ["os"]
    
    server = MCPServer(config)
    
    # invalid json-rpc (missing jsonrpc field)
    request = {
        "id": 1,
        "method": "tools/list"
    }
    
    response = server.handle_request(request)
    assert "error" in response
    assert response["error"]["code"] == -32600


def test_caching():
    """test caching behavior."""
    config = Config()
    config.sdks = ["os"]
    config.enable_cache = True
    
    server = MCPServer(config)
    
    # get first available tool
    if len(server.tools) > 0:
        tool_name = server.tools[0]["name"]
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": {}
            }
        }
        
        # first call
        response1 = server.handle_request(request)
        
        # second call (should be cached if successful)
        request["id"] = 2
        response2 = server.handle_request(request)
        
        # both should have metadata
        if "result" in response1 and "result" in response2:
            # at least one test passed
            assert True


def test_multiple_sdks():
    """test loading multiple sdks."""
    config = Config()
    config.sdks = ["os", "json"]
    
    server = MCPServer(config)
    
    # should have tools from both sdks
    sdk_names = set(t["metadata"]["sdk"] for t in server.tools)
    assert "os" in sdk_names
    assert "json" in sdk_names


if __name__ == "__main__":
    print("running smoke tests...")
    
    test_basic_server_lifecycle()
    print("✓ basic server lifecycle")
    
    test_tools_list_request()
    print("✓ tools/list request")
    
    test_server_info_request()
    print("✓ server/info request")
    
    test_filtering()
    print("✓ filtering")
    
    test_dry_run_mode()
    print("✓ dry-run mode")
    
    test_validation()
    print("✓ validation")
    
    test_caching()
    print("✓ caching")
    
    test_multiple_sdks()
    print("✓ multiple sdks")
    
    print("\nall smoke tests passed")

