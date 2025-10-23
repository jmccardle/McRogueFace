#!/bin/bash
# Run all tests and check for failures

TESTS=(
    "test_click_init.py"
    "test_drawable_base.py" 
    "test_frame_children.py"
    "test_sprite_texture_swap.py"
    "test_timer_object.py"
    "test_timer_object_fixed.py"
)

echo "Running all tests..."
echo "===================="

failed=0
passed=0

for test in "${TESTS[@]}"; do
    echo -n "Running $test... "
    if timeout 5 ./mcrogueface --headless --exec ../tests/$test > /tmp/test_output.txt 2>&1; then
        if grep -q "FAIL\|✗" /tmp/test_output.txt; then
            echo "FAILED"
            echo "Output:"
            cat /tmp/test_output.txt | grep -E "✗|FAIL|Error|error" | head -10
            ((failed++))
        else
            echo "PASSED"
            ((passed++))
        fi
    else
        echo "TIMEOUT/CRASH"
        ((failed++))
    fi
done

echo "===================="
echo "Total: $((passed + failed)) tests"
echo "Passed: $passed"
echo "Failed: $failed"

exit $failed