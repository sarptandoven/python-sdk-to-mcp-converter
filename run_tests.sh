#!/bin/bash

# comprehensive test runner for python sdk to mcp converter

echo "running all tests..."
echo ""

failed=0

# unit tests
echo "=== unit tests ==="
for test in test_reflection test_safety test_executor test_cache test_rate_limit test_validation test_filters test_dry_run; do
    echo -n "  $test... "
    if python ${test}.py > /dev/null 2>&1; then
        echo "✓"
    else
        echo "✗"
        failed=$((failed + 1))
    fi
done

# integration test
echo ""
echo "=== integration tests ==="
echo -n "  test_integration... "
if python test_integration.py > /dev/null 2>&1; then
    echo "✓"
else
    echo "✗"
    failed=$((failed + 1))
fi

# smoke tests
echo ""
echo "=== smoke tests ==="
echo -n "  test_smoke... "
if python test_smoke.py > /dev/null 2>&1; then
    echo "✓"
else
    echo "✗"
    failed=$((failed + 1))
fi

# summary
echo ""
echo "=== summary ==="
if [ $failed -eq 0 ]; then
    echo "all tests passed! ✓"
    exit 0
else
    echo "$failed test(s) failed ✗"
    exit 1
fi

