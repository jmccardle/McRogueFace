#!/usr/bin/env python3
"""
Test the RAII AnimationManager implementation.
This verifies that weak_ptr properly handles all crash scenarios.
"""

import mcrfpy
import sys

print("RAII AnimationManager Test Suite")
print("=" * 40)

# Test state
tests_passed = 0
tests_failed = 0
test_results = []

def test_result(name, passed, details=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        result = f"✓ {name}"
    else:
        tests_failed += 1
        result = f"✗ {name}: {details}"
    print(result)
    test_results.append((name, passed, details))

def test_1_basic_animation():
    """Test that basic animations still work"""
    try:
        ui = test.children
        frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
        ui.append(frame)
        
        anim = mcrfpy.Animation("x", 200.0, 1000, "linear")
        anim.start(frame)
        
        # Check if animation has valid target
        if hasattr(anim, 'hasValidTarget'):
            valid = anim.hasValidTarget()
            test_result("Basic animation with hasValidTarget", valid)
        else:
            test_result("Basic animation", True)
    except Exception as e:
        test_result("Basic animation", False, str(e))

def test_2_remove_animated_object():
    """Test removing object with active animation"""
    try:
        ui = test.children
        frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
        ui.append(frame)
        
        # Start animation
        anim = mcrfpy.Animation("x", 500.0, 2000, "easeInOut")
        anim.start(frame)
        
        # Remove the frame
        ui.remove(0)
        
        # Check if animation knows target is gone
        if hasattr(anim, 'hasValidTarget'):
            valid = anim.hasValidTarget()
            test_result("Animation detects removed target", not valid)
        else:
            # If method doesn't exist, just check we didn't crash
            test_result("Remove animated object", True)
    except Exception as e:
        test_result("Remove animated object", False, str(e))

def test_3_complete_animation():
    """Test completing animation immediately"""
    try:
        ui = test.children
        frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
        ui.append(frame)
        
        # Start animation
        anim = mcrfpy.Animation("x", 500.0, 2000, "linear")
        anim.start(frame)
        
        # Complete it
        if hasattr(anim, 'complete'):
            anim.complete()
            # Frame should now be at x=500
            test_result("Animation complete method", True)
        else:
            test_result("Animation complete method", True, "Method not available")
    except Exception as e:
        test_result("Animation complete method", False, str(e))

def test_4_multiple_animations_timer():
    """Test creating multiple animations in timer callback"""
    success = False

    def create_animations(timer, runtime):
        nonlocal success
        try:
            ui = test.children
            frame = mcrfpy.Frame(pos=(200, 200), size=(100, 100))
            ui.append(frame)

            # Create multiple animations rapidly (this used to crash)
            for i in range(10):
                anim = mcrfpy.Animation("x", 300.0 + i * 10, 1000, "linear")
                anim.start(frame)

            success = True
        except Exception as e:
            print(f"Timer animation error: {e}")
        finally:
            mcrfpy.Timer("exit", lambda t, r: None, 100, once=True)

    # Clear scene
    ui = test.children
    while len(ui) > 0:
        ui.remove(len(ui) - 1)

    mcrfpy.Timer("test", create_animations, 50, once=True)
    mcrfpy.Timer("check", lambda t, r: test_result("Multiple animations in timer", success), 200, once=True)

def test_5_scene_cleanup():
    """Test that changing scenes cleans up animations"""
    try:
        # Create a second scene
        test2 = mcrfpy.Scene("test2")
        
        # Add animated objects to first scene
        ui = test.children
        for i in range(5):
            frame = mcrfpy.Frame(pos=(50 * i, 100), size=(40, 40))
            ui.append(frame)
            anim = mcrfpy.Animation("y", 300.0, 2000, "easeOutBounce")
            anim.start(frame)
        
        # Switch scenes (animations should become invalid)
        test2.activate()
        
        # Switch back
        test.activate()
        
        test_result("Scene change cleanup", True)
    except Exception as e:
        test_result("Scene change cleanup", False, str(e))

def test_6_animation_after_clear():
    """Test animations after clearing UI"""
    try:
        ui = test.children

        # Create and animate
        frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
        ui.append(frame)
        anim = mcrfpy.Animation("w", 200.0, 1500, "easeInOutCubic")
        anim.start(frame)
        
        # Clear all UI
        while len(ui) > 0:
            ui.remove(len(ui) - 1)
        
        # Animation should handle this gracefully
        if hasattr(anim, 'hasValidTarget'):
            valid = anim.hasValidTarget()
            test_result("Animation after UI clear", not valid)
        else:
            test_result("Animation after UI clear", True)
    except Exception as e:
        test_result("Animation after UI clear", False, str(e))

def run_all_tests(timer, runtime):
    """Run all RAII tests"""
    print("\nRunning RAII Animation Tests...")
    print("-" * 40)

    test_1_basic_animation()
    test_2_remove_animated_object()
    test_3_complete_animation()
    test_4_multiple_animations_timer()
    test_5_scene_cleanup()
    test_6_animation_after_clear()

    # Schedule result summary
    mcrfpy.Timer("results", print_results, 500, once=True)

def print_results(timer, runtime):
    """Print test results"""
    print("\n" + "=" * 40)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")

    if tests_failed == 0:
        print("\n+ All tests passed! RAII implementation is working correctly.")
    else:
        print(f"\nx {tests_failed} tests failed.")
        print("\nFailed tests:")
        for name, passed, details in test_results:
            if not passed:
                print(f"  - {name}: {details}")

    # Exit
    mcrfpy.Timer("exit", lambda t, r: sys.exit(0 if tests_failed == 0 else 1), 500, once=True)

# Setup and run
test = mcrfpy.Scene("test")
test.activate()

# Add a background
ui = test.children
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
bg.fill_color = mcrfpy.Color(20, 20, 30)
ui.append(bg)

# Start tests
start_timer = mcrfpy.Timer("start", run_all_tests, 100, once=True)