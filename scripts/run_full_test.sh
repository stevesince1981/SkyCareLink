#!/bin/bash

# SkyCareLink Full Test Suite Runner
# Executes both automated test scripts and provides summary

echo "🚀 SkyCareLink Full Test Suite"
echo "=============================="
echo ""

EXIT_CODE=0

# Run Smoke Tests
echo "📋 Running Smoke Test Suite..."
if bash scripts/smoke.sh; then
    echo -e "\033[0;32m✓ SMOKE TESTS: PASSED\033[0m"
else
    echo -e "\033[0;31m✗ SMOKE TESTS: FAILED\033[0m"
    EXIT_CODE=1
fi

echo ""

# Run Route Health Check
echo "🔍 Running Route Health Check..."
if python scripts/check_routes.py; then
    echo -e "\033[0;32m✓ ROUTE HEALTH: PASSED\033[0m"
else
    echo -e "\033[0;31m✗ ROUTE HEALTH: FAILED\033[0m"
    EXIT_CODE=1
fi

echo ""

# Summary
if [ $EXIT_CODE -eq 0 ]; then
    echo "🎉 ALL AUTOMATED TESTS PASSED"
    echo "✅ System ready for manual testing checklist"
    echo "📋 Next step: Complete tests/e2e_checklist.md"
else
    echo "💥 SOME TESTS FAILED"
    echo "❌ Review failures above before proceeding"
    echo "🛠️  Fix issues and re-run tests"
fi

echo ""
echo "For manual testing: see tests/e2e_checklist.md"
echo "For test documentation: see docs/qa/"

exit $EXIT_CODE