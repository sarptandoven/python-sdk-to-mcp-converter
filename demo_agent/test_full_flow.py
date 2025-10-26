#!/usr/bin/env python
"""
comprehensive test of the full frontend-backend interaction
tests the entire flow from SDK loading to query processing
"""

import asyncio
import sys
import os

# ensure openai key is set for full test
if 'OPENAI_API_KEY' not in os.environ:
    print("=" * 70)
    print("FULL FLOW TEST - REQUIRES OPENAI API KEY")
    print("=" * 70)
    print("\nThis test requires an OpenAI API key to test the agent.")
    print("Set it with: export OPENAI_API_KEY='your-key'\n")
    sys.exit(1)

from mcp_bridge import MCPBridge
from agent import OpenAIMCPAgent


async def test_full_flow():
    """test complete workflow"""
    print("=" * 70)
    print("COMPREHENSIVE FRONTEND-BACKEND INTEGRATION TEST")
    print("=" * 70)
    print()
    
    # test 1: bridge initialization
    print("TEST 1: MCP Bridge Initialization")
    print("-" * 70)
    try:
        bridge = MCPBridge('os')
        print(f"[OK] bridge created for SDK: os")
        print(f"[OK] python interpreter: {sys.executable}")
        
        await bridge.start()
        print(f"[OK] server process started")
        
        tools_response = await bridge.list_tools()
        tools = tools_response.get('tools', [])
        print(f"[OK] loaded {len(tools)} tools")
        
        # test a tool call
        result = await bridge.call_tool('os.getcwd', {})
        print(f"[OK] tool call successful: os.getcwd() = {result}")
        
        await bridge.stop()
        print(f"[OK] server stopped cleanly")
        print()
        
    except Exception as e:
        print(f"[FAIL] bridge test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # test 2: agent initialization
    print("TEST 2: OpenAI Agent Initialization")
    print("-" * 70)
    try:
        agent = OpenAIMCPAgent('os', os.environ['OPENAI_API_KEY'])
        print(f"[OK] agent created")
        
        await agent.initialize()
        print(f"[OK] agent initialized with {len(agent.tools)} tools")
        
        # show sample tools
        print(f"\n  sample tools:")
        for tool in agent.tools[:5]:
            name = tool['function']['name']
            desc = tool['function'].get('description', '')[:60]
            print(f"    - {name}: {desc}...")
        
        await agent.cleanup()
        print(f"[OK] agent cleaned up")
        print()
        
    except Exception as e:
        print(f"[FAIL] agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # test 3: end-to-end query
    print("TEST 3: End-to-End Query Processing")
    print("-" * 70)
    try:
        agent = OpenAIMCPAgent('os', os.environ['OPENAI_API_KEY'])
        await agent.initialize()
        print(f"[OK] agent ready")
        
        # track tool calls
        tool_calls_made = []
        
        async def track_tool_call(name, args):
            tool_calls_made.append((name, args))
            print(f"  -> agent calling: {name}({args})")
            
            # mock display object
            class MockDisplay:
                def set_result(self, r): 
                    print(f"  <- result: {str(r)[:100]}")
                def set_error(self, e): 
                    print(f"  [FAIL] error: {e}")
            return MockDisplay()
        
        query = "what is my current working directory?"
        print(f"\nquery: {query}")
        print()
        
        response = await agent.process(query, on_tool_call=track_tool_call)
        
        print(f"\nagent response:")
        print(f"  {response}")
        print()
        print(f"[OK] query processed successfully")
        print(f"[OK] tool calls made: {len(tool_calls_made)}")
        
        await agent.cleanup()
        print()
        
    except Exception as e:
        print(f"[FAIL] end-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # summary
    print("=" * 70)
    print("[OK] ALL TESTS PASSED")
    print("=" * 70)
    print()
    print("the full frontend-backend integration is working correctly!")
    print()
    print("next steps:")
    print("  1. run the UI: python app.py")
    print("  2. click 'load sdk'")
    print("  3. type your query and press enter")
    print("  4. watch the ai agent work!")
    print()
    
    return True


if __name__ == '__main__':
    result = asyncio.run(test_full_flow())
    sys.exit(0 if result else 1)

