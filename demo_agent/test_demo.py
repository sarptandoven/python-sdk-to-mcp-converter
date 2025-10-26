# test harness for demo components
# validates mcp bridge, agent, and openai integration work

import asyncio
import os
import sys
import json

# ensure openai key is set
if 'OPENAI_API_KEY' not in os.environ:
    print("ERROR: OPENAI_API_KEY not set. Please export it:")
    print("  export OPENAI_API_KEY='your-key-here'")
    sys.exit(1)

from config import Config
from mcp_bridge import MCPBridge
from agent import OpenAIMCPAgent


async def test_mcp_bridge():
    """test mcp bridge can connect to server"""
    print("\n=== testing mcp bridge ===")
    
    try:
        bridge = MCPBridge('os')
        print("[OK] bridge created")
        
        await bridge.start()
        print("[OK] server process started")
        
        # give server time to initialize
        await asyncio.sleep(1)
        
        tools = await bridge.list_tools()
        tool_count = len(tools.get('tools', []))
        print(f"[OK] fetched {tool_count} tools from os module")
        
        # test calling a simple tool
        if tool_count > 0:
            # try calling os.getcwd
            try:
                result = await bridge.call_tool('os.getcwd', {})
                print(f"[OK] called os.getcwd: {result[:50] if isinstance(result, str) else result}")
            except Exception as e:
                print(f"[WARN] tool call failed (expected for some tools): {e}")
        
        await bridge.stop()
        print("[OK] server stopped cleanly")
        
        return True
    except Exception as e:
        print(f"[FAIL] error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent():
    """test agent initialization and tool loading"""
    print("\n=== testing openai agent ===")
    
    try:
        config = Config()
        print("[OK] config loaded")
        
        agent = OpenAIMCPAgent('os', config.openai_api_key)
        print("[OK] agent created")
        
        await agent.initialize()
        print(f"[OK] agent initialized with {len(agent.tools)} tools")
        
        # show first few tools
        print("\nfirst 5 tools discovered:")
        for i, tool in enumerate(agent.tools[:5]):
            name = tool['function']['name']
            desc = tool['function'].get('description', 'no description')[:60]
            print(f"  {i+1}. {name}: {desc}")
        
        # test a simple query (this will make real openai call)
        print("\n=== testing agent query ===")
        print("query: what is my current working directory?")
        
        # track tool calls
        tool_calls_made = []
        
        async def track_tool_call(name, args):
            tool_calls_made.append((name, args))
            print(f"  -> tool call: {name}({args})")
            # return mock object with set_result and set_error methods
            class MockDisplay:
                def set_result(self, r): pass
                def set_error(self, e): pass
            return MockDisplay()
        
        response = await agent.process(
            "what is my current working directory?",
            on_tool_call=track_tool_call
        )
        
        print(f"\nagent response: {response}")
        print(f"tool calls made: {len(tool_calls_made)}")
        for name, args in tool_calls_made:
            print(f"  - {name}: {args}")
        
        await agent.cleanup()
        print("\n[OK] agent test complete")
        
        return True
    except Exception as e:
        print(f"[FAIL] error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """run all tests"""
    print("=" * 60)
    print("MCP SDK AGENT - COMPONENT TEST")
    print("=" * 60)
    
    # test 1: mcp bridge
    bridge_ok = await test_mcp_bridge()
    
    # test 2: agent (includes real openai call)
    if bridge_ok:
        agent_ok = await test_agent()
    else:
        print("\nskipping agent test (bridge failed)")
        agent_ok = False
    
    # summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"mcp bridge: {'[OK] pass' if bridge_ok else '[FAIL] fail'}")
    print(f"openai agent: {'[OK] pass' if agent_ok else '[FAIL] fail'}")
    
    if bridge_ok and agent_ok:
        print("\n[OK] all tests passed!")
        print("\nto run the full interactive ui:")
        print("  export OPENAI_API_KEY='sk-...'")
        print("  python app.py")
    else:
        print("\n[FAIL] some tests failed")
    
    return bridge_ok and agent_ok


if __name__ == '__main__':
    result = asyncio.run(main())
    sys.exit(0 if result else 1)

