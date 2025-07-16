#!/usr/bin/env python3
"""
Test for keypressScene() validation - should reject non-callable arguments
"""

def test_keypress_validation(timer_name):
    """Test that keypressScene validates its argument is callable"""
    import mcrfpy
    import sys
    
    print("Testing keypressScene() validation...")
    
    # Create test scene
    mcrfpy.createScene("test")
    mcrfpy.setScene("test")
    
    # Test 1: Valid callable (function)
    def key_handler(key, action):
        print(f"Key pressed: {key}, action: {action}")
    
    try:
        mcrfpy.keypressScene(key_handler)
        print("✓ Accepted valid function as key handler")
    except Exception as e:
        print(f"✗ Rejected valid function: {e}")
        raise
    
    # Test 2: Valid callable (lambda)
    try:
        mcrfpy.keypressScene(lambda k, a: None)
        print("✓ Accepted valid lambda as key handler")
    except Exception as e:
        print(f"✗ Rejected valid lambda: {e}")
        raise
    
    # Test 3: Invalid - string
    try:
        mcrfpy.keypressScene("not callable")
        print("✗ Should have rejected string as key handler")
    except TypeError as e:
        print(f"✓ Correctly rejected string: {e}")
    except Exception as e:
        print(f"✗ Wrong exception type for string: {e}")
        raise
    
    # Test 4: Invalid - number
    try:
        mcrfpy.keypressScene(42)
        print("✗ Should have rejected number as key handler")
    except TypeError as e:
        print(f"✓ Correctly rejected number: {e}")
    except Exception as e:
        print(f"✗ Wrong exception type for number: {e}")
        raise
    
    # Test 5: Invalid - None
    try:
        mcrfpy.keypressScene(None)
        print("✗ Should have rejected None as key handler")
    except TypeError as e:
        print(f"✓ Correctly rejected None: {e}")
    except Exception as e:
        print(f"✗ Wrong exception type for None: {e}")
        raise
    
    # Test 6: Invalid - dict
    try:
        mcrfpy.keypressScene({"not": "callable"})
        print("✗ Should have rejected dict as key handler")
    except TypeError as e:
        print(f"✓ Correctly rejected dict: {e}")
    except Exception as e:
        print(f"✗ Wrong exception type for dict: {e}")
        raise
    
    # Test 7: Valid callable class instance
    class KeyHandler:
        def __call__(self, key, action):
            print(f"Class handler: {key}, {action}")
    
    try:
        mcrfpy.keypressScene(KeyHandler())
        print("✓ Accepted valid callable class instance")
    except Exception as e:
        print(f"✗ Rejected valid callable class: {e}")
        raise
    
    print("\n✅ keypressScene() validation test PASSED")
    sys.exit(0)

# Execute the test after a short delay
import mcrfpy
mcrfpy.setTimer("test", test_keypress_validation, 100)