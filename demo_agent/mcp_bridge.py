# mcp bridge: communicates with mcp server over stdio
# handles process management and json-rpc protocol

import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path


class MCPBridge:
    """
    bridge to mcp server
    
    spawns server process, sends json-rpc requests over stdin,
    receives responses from stdout
    """
    
    def __init__(self, sdk_name: str):
        self.sdk_name = sdk_name
        self.process = None
        self.reader = None
        self.writer = None
        self.request_id = 0
        
    async def start(self):
        """start mcp server process"""
        # find server.py in parent directory
        server_path = Path(__file__).parent.parent / "server.py"
        
        if not server_path.exists():
            raise FileNotFoundError(
                f"server.py not found at {server_path}\n"
                f"Current directory: {Path.cwd()}\n"
                f"Script directory: {Path(__file__).parent}"
            )
        
        # environment with sdk name
        env = os.environ.copy()
        env["SDKS"] = self.sdk_name
        env["SDK_NAME"] = self.sdk_name  # for compatibility
        
        try:
            # spawn server process using same python interpreter
            self.process = await asyncio.create_subprocess_exec(
                sys.executable,  # use current python interpreter
                str(server_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                limit=10 * 1024 * 1024  # 10MB buffer for very large tool lists (kubernetes has 670+ tools)
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to start MCP server process:\n"
                f"Python: {sys.executable}\n"
                f"Server: {server_path}\n"
                f"Error: {str(e)}"
            ) from e
        
        self.reader = self.process.stdout
        self.writer = self.process.stdin
        
        # wait a moment for server to initialize
        await asyncio.sleep(1.0)  # increased for better stability
        
        # check if process started successfully
        if self.process.returncode is not None:
            stderr = await self.process.stderr.read()
            raise RuntimeError(
                f"MCP server process failed to start\n"
                f"Exit code: {self.process.returncode}\n"
                f"Error: {stderr.decode() if stderr else 'No error output'}"
            )
    
    async def stop(self):
        """stop mcp server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
    
    async def list_tools(self) -> Dict[str, Any]:
        """fetch available tools from server"""
        response = await self._send_request("tools/list", {})
        return response.get("result", {})
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """call a tool via mcp server"""
        response = await self._send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments
            }
        )
        
        # check for errors
        if "error" in response:
            error = response["error"]
            raise Exception(f"{error.get('message', 'unknown error')}")
        
        # extract result
        result = response.get("result", {})
        
        # handle both direct results and wrapped results
        if isinstance(result, dict) and "content" in result:
            # mcp format with content array
            content = result.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", str(result))
        
        return result
    
    async def _send_request(self, method: str, params: Any) -> Dict[str, Any]:
        """send json-rpc request and get response"""
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        
        try:
            # send request
            request_json = json.dumps(request) + "\n"
            self.writer.write(request_json.encode())
            await self.writer.drain()
            
            # read response with timeout
            response_line = await asyncio.wait_for(
                self.reader.readline(),
                timeout=30.0
            )
            
            if not response_line:
                # check stderr for errors
                stderr_data = b""
                try:
                    stderr_data = await asyncio.wait_for(
                        self.process.stderr.read(4096),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    pass
                
                if stderr_data:
                    raise Exception(f"server error: {stderr_data.decode()}")
                raise Exception("no response from server (connection may be closed)")
            
            try:
                response = json.loads(response_line.decode())
            except json.JSONDecodeError as e:
                raise Exception(
                    f"invalid json response from server\n"
                    f"Response: {response_line.decode()[:500]}\n"
                    f"Error: {str(e)}"
                )
            
            return response
            
        except asyncio.TimeoutError:
            raise Exception(
                f"timeout waiting for response from server\n"
                f"Method: {method}\n"
                f"This may indicate the server is hung or the request is too slow"
            )
        except BrokenPipeError:
            raise Exception(
                "server connection lost (broken pipe)\n"
                "The MCP server process may have crashed"
            )


class MCPBridgePool:
    """
    pool of mcp bridges for multiple sdks
    
    allows switching between sdks without restarting
    """
    
    def __init__(self):
        self.bridges: Dict[str, MCPBridge] = {}
    
    async def get_bridge(self, sdk_name: str) -> MCPBridge:
        """get or create bridge for sdk"""
        if sdk_name not in self.bridges:
            bridge = MCPBridge(sdk_name)
            await bridge.start()
            self.bridges[sdk_name] = bridge
        
        return self.bridges[sdk_name]
    
    async def cleanup(self):
        """stop all bridges"""
        for bridge in self.bridges.values():
            await bridge.stop()
        self.bridges.clear()

