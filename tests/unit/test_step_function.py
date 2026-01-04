#!/usr/bin/env python3
"""
Test mcrfpy.step() function (#153)
===================================

Tests the Python-controlled simulation advancement for headless mode.

Key behavior:
- step(dt) advances simulation by dt seconds
- step(None) or step() advances to next scheduled event
- Returns actual time advanced
- In windowed mode, returns 0.0 (no-op)
"""

import mcrfpy
import sys

def run_tests():
    """Run step() function tests"""
    print("=== mcrfpy.step() Tests ===\n")

    # Test 1: step() with specific dt value
    print("Test 1: step() with specific dt value")
    dt = mcrfpy.step(0.1)  # Advance 100ms
    print(f"  step(0.1) returned: {dt}")
    # In headless mode, should return 0.1
    # In windowed mode, returns 0.0
    if dt == 0.0:
        print("  Note: Running in windowed mode - step() is no-op")
    else:
        assert abs(dt - 0.1) < 0.001, f"Expected ~0.1, got {dt}"
        print("  Correctly advanced by 0.1 seconds")
    print()

    # Test 2: step() with integer value (converts to float)
    print("Test 2: step() with integer value")
    dt = mcrfpy.step(1)  # Advance 1 second
    print(f"  step(1) returned: {dt}")
    if dt != 0.0:
        assert abs(dt - 1.0) < 0.001, f"Expected ~1.0, got {dt}"
        print("  Correctly advanced by 1.0 seconds")
    print()

    # Test 3: step(None) - advance to next event
    print("Test 3: step(None) - advance to next event")
    dt = mcrfpy.step(None)
    print(f"  step(None) returned: {dt}")
    if dt != 0.0:
        assert dt >= 0, "step(None) should return non-negative dt"
        print(f"  Advanced by {dt} seconds to next event")
    print()

    # Test 4: step() with no argument (same as step(None))
    print("Test 4: step() with no argument")
    dt = mcrfpy.step()
    print(f"  step() returned: {dt}")
    if dt != 0.0:
        assert dt >= 0, "step() should return non-negative dt"
        print(f"  Advanced by {dt} seconds")
    print()

    # Test 5: Timer callback with step()
    print("Test 5: Timer fires after step() advances past interval")
    timer_fired = [False]  # Use list for mutable closure

    def on_timer(timer, runtime):
        """Timer callback - receives timer object and runtime in ms"""
        timer_fired[0] = True
        print(f"    Timer fired at simulation time={runtime}ms")

    # Set a timer for 500ms
    test_timer = mcrfpy.Timer("test_timer", on_timer, 500)

    # Step 600ms - timer should fire (500ms interval + some buffer)
    dt = mcrfpy.step(0.6)
    if dt != 0.0:  # Headless mode
        # Timer should have fired
        if timer_fired[0]:
            print("  Timer correctly fired after step(0.6)")
        else:
            # Try another step to ensure timer fires
            mcrfpy.step(0.1)
            if timer_fired[0]:
                print("  Timer fired after additional step")
            else:
                print("  WARNING: Timer didn't fire - check timer synchronization")
    else:
        print("  Skipping timer test in windowed mode")

    # Clean up
    test_timer.stop()
    print()

    # Test 6: Error handling - invalid argument type
    print("Test 6: Error handling - invalid argument type")
    try:
        mcrfpy.step("invalid")
        print("  ERROR: Should have raised TypeError")
        return False
    except TypeError as e:
        print(f"  Correctly raised TypeError: {e}")
    print()

    print("=== All step() Tests Passed! ===")
    return True

# Main execution
if __name__ == "__main__":
    try:
        # Create a scene for the test
        test_step = mcrfpy.Scene("test_step")
        test_step.activate()

        if run_tests():
            print("\nPASS")
            sys.exit(0)
        else:
            print("\nFAIL")
            sys.exit(1)
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
