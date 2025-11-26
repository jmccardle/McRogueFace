#!/bin/bash
# Manual test for --continue-after-exceptions feature (Issue #133)
#
# This test must be run manually because it verifies exit codes
# rather than test output.

echo "Testing --continue-after-exceptions feature..."
echo

cd "$(dirname "$0")/../../build"

# Test 1: Default behavior - should exit with code 1 on first exception
echo "Test 1: Default behavior (exit on first exception)"
timeout 5 ./mcrogueface --headless --exec ../tests/notes/test_exception_exit.py 2>&1
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE"
if [ $EXIT_CODE -eq 1 ]; then
    echo "[PASS] Exit code is 1 as expected"
else
    echo "[FAIL] Expected exit code 1, got $EXIT_CODE"
    exit 1
fi
echo

# Test 2: --continue-after-exceptions - should keep running until timeout
echo "Test 2: --continue-after-exceptions (continue after exception)"
timeout 1 ./mcrogueface --headless --continue-after-exceptions --exec ../tests/notes/test_exception_exit.py 2>&1 | tail -5
EXIT_CODE=${PIPESTATUS[0]}
echo "Exit code: $EXIT_CODE"
if [ $EXIT_CODE -eq 124 ]; then
    echo "[PASS] Timeout killed it (exit code 124) - continued running as expected"
else
    echo "[FAIL] Expected exit code 124 (timeout), got $EXIT_CODE"
    exit 1
fi
echo

echo "All tests PASSED!"
