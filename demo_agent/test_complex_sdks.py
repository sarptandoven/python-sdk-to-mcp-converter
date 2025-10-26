#!/usr/bin/env python
"""
test complex SDK loading (kubernetes, github, boto3, azure, stripe)
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_sdk_discovery(sdk_name):
    """test if SDK methods can be discovered"""
    print(f"\n{'='*60}")
    print(f"Testing: {sdk_name}")
    print('='*60)
    
    try:
        # Import the module
        import importlib
        module = importlib.import_module(sdk_name)
        print(f"[OK] module imported successfully")
        
        # Try discovery
        from reflection import discover_methods
        methods = discover_methods(module, sdk_name, allow_dangerous=True)
        
        print(f"[OK] discovered {len(methods)} methods")
        
        if methods:
            print(f"\nfirst 10 methods:")
            for i, method in enumerate(methods[:10]):
                print(f"  {i+1}. {method['name']}")
            
            if len(methods) > 10:
                print(f"  ... and {len(methods) - 10} more")
        else:
            print("\n[WARN] no methods discovered - this SDK may need:")
            print("  - special configuration")
            print("  - client instantiation")
            print("  - credentials")
        
        return len(methods) > 0
        
    except ModuleNotFoundError:
        print(f"[FAIL] module not installed")
        print(f"  install with: pip install {sdk_name}")
        return False
    except Exception as e:
        print(f"[FAIL] error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """test all complex SDKs"""
    print("="*60)
    print("COMPLEX SDK DISCOVERY TEST")
    print("="*60)
    
    sdks_to_test = [
        ("os", "baseline - should always work"),
        ("json", "baseline - should always work"),
        ("kubernetes", "complex - needs config"),
        ("github", "complex - needs token"),
        ("boto3", "complex - needs credentials"),
        ("azure.mgmt.compute", "complex - needs credentials"),
        ("stripe", "complex - needs API key"),
    ]
    
    results = {}
    for sdk_name, description in sdks_to_test:
        result = test_sdk_discovery(sdk_name)
        results[sdk_name] = result
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for sdk_name, _ in sdks_to_test:
        status = "[OK] working" if results[sdk_name] else "[FAIL] not working"
        print(f"{sdk_name:25} {status}")
    
    print("\n" + "="*60)
    working = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"result: {working}/{total} SDKs successfully discovered methods")
    print("="*60)
    
    return working > 0


if __name__ == '__main__':
    result = main()
    sys.exit(0 if result else 1)

