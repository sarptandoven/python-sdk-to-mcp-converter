# quick test to verify different sdks load different tool counts

import asyncio
import os

if 'OPENAI_API_KEY' not in os.environ:
    print("ERROR: OPENAI_API_KEY not set. Please export it:")
    print("  export OPENAI_API_KEY='your-key-here'")
    import sys
    sys.exit(1)

from agent import OpenAIMCPAgent

async def test_sdk_loading():
    """test that different sdks load different tool counts"""
    
    print("testing sdk loading with different sdks...\n")
    
    sdks_to_test = [
        ("os", "expected ~39 tools"),
        ("json", "expected ~2 tools"),
        ("pathlib", "expected ~many tools"),
    ]
    
    for sdk_name, description in sdks_to_test:
        try:
            print(f"loading {sdk_name} ({description})...")
            agent = OpenAIMCPAgent(sdk_name, os.environ['OPENAI_API_KEY'])
            await agent.initialize()
            tool_count = len(agent.tools)
            print(f"[OK] {sdk_name}: loaded {tool_count} tools")
            
            # show first 3 tools
            if tool_count > 0:
                print(f"  sample tools:")
                for tool in agent.tools[:3]:
                    print(f"    - {tool['function']['name']}")
            
            await agent.cleanup()
            print()
            
        except Exception as e:
            print(f"[FAIL] {sdk_name}: error - {str(e)}\n")
    
    print("\nif tool counts are different, the backend is working correctly!")

if __name__ == '__main__':
    asyncio.run(test_sdk_loading())

