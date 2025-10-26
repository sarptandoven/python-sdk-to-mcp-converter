"""integration tests for end-to-end functionality."""
import json
from server import MCPServer
from config import Config


def test_tools_list():
    """test tools/list endpoint."""
    config = Config()
    config.sdks = ["os"]  # use stdlib for testing
    
    server = MCPServer(config)
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    response = server.handle_request(request)
    
    assert response["id"] == 1
    assert "result" in response
    assert "tools" in response["result"]
    assert len(response["result"]["tools"]) > 0


def test_tools_call():
    """test tools/call endpoint."""
    config = Config()
    config.sdks = ["os"]
    
    server = MCPServer(config)
    
    # find a safe tool to call
    tools = server.tools
    safe_tool = next((t for t in tools if not t["metadata"]["is_dangerous"]), None)
    
    if safe_tool:
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": safe_tool["name"],
                "arguments": {}
            }
        }
        
        response = server.handle_request(request)
        
        assert response["id"] == 2
        # response could be error or result depending on the tool
        assert "result" in response or "error" in response


def test_server_info():
    """test server/info endpoint."""
    config = Config()
    config.sdks = ["os"]
    
    server = MCPServer(config)
    
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "server/info",
        "params": {}
    }
    
    response = server.handle_request(request)
    
    assert response["id"] == 3
    assert "result" in response
    assert response["result"]["name"] == "python-sdk-mcp-converter"
    assert "tools_count" in response["result"]


def test_unknown_method():
    """test handling of unknown methods."""
    config = Config()
    config.sdks = ["os"]
    
    server = MCPServer(config)
    
    request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "unknown/method",
        "params": {}
    }
    
    response = server.handle_request(request)
    
    assert response["id"] == 4
    assert "error" in response
    assert response["error"]["code"] == -32601


if __name__ == "__main__":
    test_tools_list()
    test_tools_call()
    test_server_info()
    test_unknown_method()
    print("all integration tests passed")

