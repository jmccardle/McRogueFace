#!/usr/bin/env python3
"""
Test Animation Property Locking (#120)
Verifies that multiple animations on the same property are handled correctly.
"""

import mcrfpy
import sys

print("Animation Property Locking Test Suite (#120)")
print("=" * 50)

# Test state
tests_passed = 0
tests_failed = 0
test_results = []

def test_result(name, passed, details=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        result = f"PASS: {name}"
    else:
        tests_failed += 1
        result = f"FAIL: {name}: {details}"
    print(result)
    test_results.append((name, passed, details))


def test_1_replace_mode_default():
    """Test that REPLACE mode is the default and works correctly"""
    try:
        ui = mcrfpy.sceneUI("test")
        frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
        ui.append(frame)

        # Start first animation
        anim1 = mcrfpy.Animation("x", 500.0, 2.0, "linear")
        anim1.start(frame)  # Default is replace mode

        # Immediately start second animation on same property
        anim2 = mcrfpy.Animation("x", 200.0, 1.0, "linear")
        anim2.start(frame)  # Should replace anim1

        # anim1 should have been completed (jumped to final value)
        # and anim2 should now be active
        # The frame should be at x=500 (anim1's final value) then animating to 200

        # If we got here without error, replace worked
        test_result("Replace mode (default)", True)
    except Exception as e:
        test_result("Replace mode (default)", False, str(e))


def test_2_replace_mode_explicit():
    """Test explicit REPLACE mode"""
    try:
        ui = mcrfpy.sceneUI("test")
        frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
        ui.append(frame)

        anim1 = mcrfpy.Animation("x", 500.0, 2.0, "linear")
        anim1.start(frame, conflict_mode="replace")

        anim2 = mcrfpy.Animation("x", 200.0, 1.0, "linear")
        anim2.start(frame, conflict_mode="replace")

        test_result("Replace mode (explicit)", True)
    except Exception as e:
        test_result("Replace mode (explicit)", False, str(e))


def test_3_queue_mode():
    """Test QUEUE mode - animation should be queued"""
    try:
        ui = mcrfpy.sceneUI("test")
        frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
        ui.append(frame)

        # Start first animation (short duration for test)
        anim1 = mcrfpy.Animation("y", 300.0, 0.5, "linear")
        anim1.start(frame)

        # Queue second animation
        anim2 = mcrfpy.Animation("y", 100.0, 0.5, "linear")
        anim2.start(frame, conflict_mode="queue")

        # Both should be accepted without error
        # anim2 will start after anim1 completes
        test_result("Queue mode", True)
    except Exception as e:
        test_result("Queue mode", False, str(e))


def test_4_error_mode():
    """Test ERROR mode - should raise RuntimeError"""
    try:
        ui = mcrfpy.sceneUI("test")
        frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
        ui.append(frame)

        anim1 = mcrfpy.Animation("w", 200.0, 2.0, "linear")
        anim1.start(frame)

        # Try to start second animation with error mode
        anim2 = mcrfpy.Animation("w", 300.0, 1.0, "linear")
        try:
            anim2.start(frame, conflict_mode="error")
            test_result("Error mode", False, "Expected RuntimeError but none was raised")
        except RuntimeError as e:
            # This is expected!
            if "conflict" in str(e).lower() or "already" in str(e).lower():
                test_result("Error mode", True)
            else:
                test_result("Error mode", False, f"Wrong error message: {e}")
    except Exception as e:
        test_result("Error mode", False, str(e))


def test_5_invalid_conflict_mode():
    """Test that invalid conflict_mode raises ValueError"""
    try:
        ui = mcrfpy.sceneUI("test")
        frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
        ui.append(frame)

        anim = mcrfpy.Animation("h", 200.0, 1.0, "linear")
        try:
            anim.start(frame, conflict_mode="invalid_mode")
            test_result("Invalid conflict_mode", False, "Expected ValueError but none raised")
        except ValueError as e:
            if "invalid" in str(e).lower():
                test_result("Invalid conflict_mode", True)
            else:
                test_result("Invalid conflict_mode", False, f"Wrong error: {e}")
    except Exception as e:
        test_result("Invalid conflict_mode", False, str(e))


def test_6_different_properties_no_conflict():
    """Test that different properties can animate simultaneously"""
    try:
        ui = mcrfpy.sceneUI("test")
        frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
        ui.append(frame)

        # Animate different properties - should not conflict
        anim_x = mcrfpy.Animation("x", 500.0, 1.0, "linear")
        anim_y = mcrfpy.Animation("y", 500.0, 1.0, "linear")
        anim_w = mcrfpy.Animation("w", 200.0, 1.0, "linear")

        anim_x.start(frame, conflict_mode="error")
        anim_y.start(frame, conflict_mode="error")
        anim_w.start(frame, conflict_mode="error")

        # All should succeed without error since they're different properties
        test_result("Different properties no conflict", True)
    except RuntimeError as e:
        test_result("Different properties no conflict", False, f"Unexpected conflict: {e}")
    except Exception as e:
        test_result("Different properties no conflict", False, str(e))


def test_7_different_targets_no_conflict():
    """Test that same property on different targets doesn't conflict"""
    try:
        ui = mcrfpy.sceneUI("test")
        frame1 = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
        frame2 = mcrfpy.Frame(pos=(200, 200), size=(100, 100))
        ui.append(frame1)
        ui.append(frame2)

        # Same property, different targets - should not conflict
        anim1 = mcrfpy.Animation("x", 500.0, 1.0, "linear")
        anim2 = mcrfpy.Animation("x", 600.0, 1.0, "linear")

        anim1.start(frame1, conflict_mode="error")
        anim2.start(frame2, conflict_mode="error")

        test_result("Different targets no conflict", True)
    except RuntimeError as e:
        test_result("Different targets no conflict", False, f"Unexpected conflict: {e}")
    except Exception as e:
        test_result("Different targets no conflict", False, str(e))


def test_8_replace_completes_old():
    """Test that REPLACE mode completes the old animation's value"""
    try:
        ui = mcrfpy.sceneUI("test")
        frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
        ui.append(frame)

        # Start animation to move x to 500
        anim1 = mcrfpy.Animation("x", 500.0, 10.0, "linear")  # Long duration
        anim1.start(frame)

        # Immediately replace - should complete anim1 (jump to 500)
        anim2 = mcrfpy.Animation("x", 200.0, 1.0, "linear")
        anim2.start(frame, conflict_mode="replace")

        # Frame should now be at x=500 (anim1's final) and animating to 200
        # Due to immediate completion, x should equal 500 right now
        if frame.x == 500.0:
            test_result("Replace completes old animation", True)
        else:
            test_result("Replace completes old animation", False,
                       f"Expected x=500, got x={frame.x}")
    except Exception as e:
        test_result("Replace completes old animation", False, str(e))


def run_all_tests(runtime):
    """Run all property locking tests"""
    print("\nRunning Animation Property Locking Tests...")
    print("-" * 50)

    test_1_replace_mode_default()
    test_2_replace_mode_explicit()
    test_3_queue_mode()
    test_4_error_mode()
    test_5_invalid_conflict_mode()
    test_6_different_properties_no_conflict()
    test_7_different_targets_no_conflict()
    test_8_replace_completes_old()

    # Print results
    print("\n" + "=" * 50)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")

    if tests_failed == 0:
        print("\nAll tests passed!")
    else:
        print(f"\n{tests_failed} tests failed:")
        for name, passed, details in test_results:
            if not passed:
                print(f"  - {name}: {details}")

    # Exit with appropriate code
    sys.exit(0 if tests_failed == 0 else 1)


# Setup and run
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Start tests after a brief delay to allow scene to initialize
mcrfpy.setTimer("start", run_all_tests, 100)
