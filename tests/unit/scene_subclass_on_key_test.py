"""Test Scene subclass on_key method callback

Verifies that:
1. Subclass on_key method is called for keyboard events
2. Property assignment (scene.on_key = callable) still works
3. Property assignment on subclass overrides the method
"""
import mcrfpy
from mcrfpy import automation
import sys

# Test state
tests_passed = 0
tests_failed = 0

def test_subclass_method():
    """Test that subclass on_key method receives keyboard events"""
    global tests_passed, tests_failed
    events = []

    class TestScene(mcrfpy.Scene):
        def on_key(self, key, state):
            events.append((key, state))

    ts = TestScene('test_method')
    ts.activate()
    automation.keyDown('a')
    automation.keyUp('a')

    if len(events) >= 2:
        print("PASS: test_subclass_method")
        tests_passed += 1
    else:
        print(f"FAIL: test_subclass_method - got {events}")
        tests_failed += 1

def test_property_handler():
    """Test that property assignment works"""
    global tests_passed, tests_failed
    events = []

    scene = mcrfpy.Scene('test_property')
    scene.on_key = lambda k, s: events.append((k, s))
    scene.activate()
    automation.keyDown('b')
    automation.keyUp('b')

    if len(events) >= 2:
        print("PASS: test_property_handler")
        tests_passed += 1
    else:
        print(f"FAIL: test_property_handler - got {events}")
        tests_failed += 1

def test_property_overrides_method():
    """Test that property assignment on subclass overrides the method"""
    global tests_passed, tests_failed
    method_events = []
    property_events = []

    class TestScene(mcrfpy.Scene):
        def on_key(self, key, state):
            method_events.append((key, state))

    ts = TestScene('test_override')
    ts.activate()
    ts.on_key = lambda k, s: property_events.append((k, s))
    automation.keyDown('c')
    automation.keyUp('c')

    if len(property_events) >= 2 and len(method_events) == 0:
        print("PASS: test_property_overrides_method")
        tests_passed += 1
    else:
        print(f"FAIL: test_property_overrides_method - method={method_events}, property={property_events}")
        tests_failed += 1

# Run tests
test_subclass_method()
test_property_handler()
test_property_overrides_method()

print(f"\nResults: {tests_passed} passed, {tests_failed} failed")
sys.exit(0 if tests_failed == 0 else 1)
