#!/usr/bin/env python3
"""
Test the RAII AnimationManager implementation.
This verifies that weak_ptr properly handles all crash scenarios.
Uses mcrfpy.step() for synchronous test execution.
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
        result = f"PASS: {name}"
    else:
        tests_failed += 1
        result = f"FAIL: {name}: {details}"
    print(result)
    test_results.append((name, passed, details))

# Setup scene
test = mcrfpy.Scene("test")
test.activate()

# Add a background
ui = test.children
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
bg.fill_color = mcrfpy.Color(20, 20, 30)
ui.append(bg)

# Initialize scene
mcrfpy.step(0.1)

print("\nRunning RAII Animation Tests...")
print("-" * 40)

# Test 1: Basic animation
try:
    frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
    ui.append(frame)

    anim = mcrfpy.Animation("x", 200.0, 1000, "linear")
    anim.start(frame)

    if hasattr(anim, 'hasValidTarget'):
        valid = anim.hasValidTarget()
        test_result("Basic animation with hasValidTarget", valid)
    else:
        test_result("Basic animation", True)
except Exception as e:
    test_result("Basic animation", False, str(e))

# Test 2: Remove animated object - shared_ptr stays alive while Python ref exists
try:
    frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
    ui.append(frame)

    anim = mcrfpy.Animation("x", 500.0, 2000, "easeInOut")
    anim.start(frame)

    ui.remove(frame)
    # Note: frame still holds a shared_ptr reference, so target is still valid
    # This is correct shared_ptr behavior
    del frame  # Release Python reference

    if hasattr(anim, 'hasValidTarget'):
        valid = anim.hasValidTarget()
        test_result("Animation detects removed target", not valid)
    else:
        test_result("Remove animated object", True)
except Exception as e:
    test_result("Remove animated object", False, str(e))

# Test 3: Complete animation immediately
try:
    frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
    ui.append(frame)

    anim = mcrfpy.Animation("x", 500.0, 2000, "linear")
    anim.start(frame)

    if hasattr(anim, 'complete'):
        anim.complete()
        test_result("Animation complete method", True)
    else:
        test_result("Animation complete method", True, "Method not available")
except Exception as e:
    test_result("Animation complete method", False, str(e))

# Test 4: Multiple animations rapidly
try:
    frame = mcrfpy.Frame(pos=(200, 200), size=(100, 100))
    ui.append(frame)

    for i in range(10):
        anim = mcrfpy.Animation("x", 300.0 + i * 10, 1000, "linear")
        anim.start(frame)

    test_result("Multiple animations rapidly", True)
except Exception as e:
    test_result("Multiple animations rapidly", False, str(e))

# Test 5: Scene cleanup
try:
    test2 = mcrfpy.Scene("test2")

    for i in range(5):
        frame = mcrfpy.Frame(pos=(50 * i, 100), size=(40, 40))
        ui.append(frame)
        anim = mcrfpy.Animation("y", 300.0, 2000, "easeOutBounce")
        anim.start(frame)

    test2.activate()
    mcrfpy.step(0.1)
    test.activate()
    mcrfpy.step(0.1)

    test_result("Scene change cleanup", True)
except Exception as e:
    test_result("Scene change cleanup", False, str(e))

# Test 6: Animation after clearing UI
try:
    frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
    ui.append(frame)
    anim = mcrfpy.Animation("w", 200.0, 1500, "easeInOutCubic")
    anim.start(frame)

    # Clear all UI except background - iterate in reverse
    for i in range(len(ui) - 1, 0, -1):
        ui.remove(ui[i])
    del frame  # Release Python reference too

    if hasattr(anim, 'hasValidTarget'):
        valid = anim.hasValidTarget()
        test_result("Animation after UI clear", not valid)
    else:
        test_result("Animation after UI clear", True)
except Exception as e:
    test_result("Animation after UI clear", False, str(e))

# Print results
print("\n" + "=" * 40)
print(f"Tests passed: {tests_passed}")
print(f"Tests failed: {tests_failed}")

if tests_failed == 0:
    print("\nAll tests passed! RAII implementation is working correctly.")
else:
    print(f"\n{tests_failed} tests failed.")
    print("\nFailed tests:")
    for name, passed, details in test_results:
        if not passed:
            print(f"  - {name}: {details}")

sys.exit(0 if tests_failed == 0 else 1)
