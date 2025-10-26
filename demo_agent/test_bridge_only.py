#!/usr/bin/env python
"""
test mcp bridge without requiring openai api key
verifies the backend is working correctly
"""

import asyncio
import sys
from mcp_bridge import MCPBridge


async def test_bridge():
    """test mcp bridge functionality"""
    print("=" * 60)
    print("MCP BRIDGE TEST (NO OPENAI API KEY REQUIRED)")
    print("=" * 60)
    
    # test with os module (no external dependencies)
    print("\n1. testing with 'os' module...")
    bridge = MCPBridge('os')
    
    try:
        print("   - starting server process...")
        await bridge.start()
        await asyncio.sleep(0.5)
        
        print("   - fetching tools list...")
        tools_response = await bridge.list_tools()
        tools = tools_response.get('tools', [])
        print(f"   [OK] loaded {len(tools)} tools")
        
        # show sample tools
        print("\n   sample tools:")
        for i, tool in enumerate(tools[:10]):
            print(f"     {i+1}. {tool['name']}")
        
        # test calling a few tools
        print("\n2. testing tool calls...")
        
        # test getcwd
        print("   - calling os.getcwd()...")
        result = await bridge.call_tool('os.getcwd', {})
        print(f"   [OK] result: {result}")
        
        # test cpu_count
        print("   - calling os.cpu_count()...")
        result = await bridge.call_tool('os.cpu_count', {})
        print(f"   [OK] result: {result} cpu cores")
        
        # test getenv
        print("   - calling os.getenv('HOME')...")
        result = await bridge.call_tool('os.getenv', {'key': 'HOME'})
        print(f"   [OK] result: {result}")
        
        print("\n3. stopping server...")
        await bridge.stop()
        print("   [OK] server stopped cleanly")
        
        print("\n" + "=" * 60)
        print("[OK] ALL TESTS PASSED")
        print("=" * 60)
        print("\nthe backend is working correctly!")
        print("to use the full UI with openai agent:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("  python app.py")
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        await bridge.stop()
        return False


if __name__ == '__main__':
    result = asyncio.run(test_bridge())
    sys.exit(0 if result else 1)

