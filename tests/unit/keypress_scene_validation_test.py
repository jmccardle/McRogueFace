#!/usr/bin/env python3
"""
Test for keypressScene() validation - should reject non-callable arguments
"""

def test_keypress_validation(timer, runtime):
    """Test that keypressScene validates its argument is callable"""
    import mcrfpy
    import sys
    
    print("Testing keypressScene() validation...")
    
    # Create test scene
    test = mcrfpy.Scene("test")
    test.activate()
    
    # Test 1: Valid callable (function)
    def key_handler(key, action):
        print(f"Key pressed: {key}, action: {action}")
    
    try:
        test.on_key = key_handler
        print("OK: Accepted valid function as key handler")
    except Exception as e:
        print(f"FAIL: Rejected valid function: {e}")
        raise
    
    # Test 2: Valid callable (lambda)
    try:
        test.on_key = lambda k, a: None
        print("OK: Accepted valid lambda as key handler")
    except Exception as e:
        print(f"FAIL: Rejected valid lambda: {e}")
        raise
    
    # Test 3: Invalid - string
    try:
        test.on_key = "not callable"
        print("FAIL: Should have rejected string as key handler")
    except TypeError as e:
        print(f"OK: Correctly rejected string: {e}")
    except Exception as e:
        print(f"FAIL: Wrong exception type for string: {e}")
        raise
    
    # Test 4: Invalid - number
    try:
        test.on_key = 42
        print("FAIL: Should have rejected number as key handler")
    except TypeError as e:
        print(f"OK: Correctly rejected number: {e}")
    except Exception as e:
        print(f"FAIL: Wrong exception type for number: {e}")
        raise
    
    # Test 5: None clears the callback (valid)
    try:
        test.on_key = None
        assert test.on_key is None, "on_key should be None after clearing"
        print("OK: Accepted None to clear key handler")
    except Exception as e:
        print(f"FAIL: Rejected None: {e}")
        raise
    
    # Test 6: Invalid - dict
    try:
        test.on_key = {"not": "callable"}
        print("FAIL: Should have rejected dict as key handler")
    except TypeError as e:
        print(f"OK: Correctly rejected dict: {e}")
    except Exception as e:
        print(f"FAIL: Wrong exception type for dict: {e}")
        raise
    
    # Test 7: Valid callable class instance
    class KeyHandler:
        def __call__(self, key, action):
            print(f"Class handler: {key}, {action}")
    
    try:
        test.on_key = KeyHandler()
        print("OK: Accepted valid callable class instance")
    except Exception as e:
        print(f"FAIL: Rejected valid callable class: {e}")
        raise
    
    print("\nPASS: keypressScene() validation test PASSED")
    sys.exit(0)

# Execute the test after a short delay
import mcrfpy
test_timer = mcrfpy.Timer("test", test_keypress_validation, 100, once=True)

# In headless mode, timers only fire via step()
for _ in range(3):
    mcrfpy.step(0.05)