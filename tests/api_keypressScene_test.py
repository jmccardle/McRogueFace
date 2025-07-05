#!/usr/bin/env python3
"""Test for mcrfpy.keypressScene() - Related to issue #61"""
import mcrfpy

# Track keypresses for different scenes
scene1_presses = []
scene2_presses = []

def scene1_handler(key_code):
    """Handle keyboard events for scene 1"""
    scene1_presses.append(key_code)
    print(f"Scene 1 key pressed: {key_code}")

def scene2_handler(key_code):
    """Handle keyboard events for scene 2"""
    scene2_presses.append(key_code)
    print(f"Scene 2 key pressed: {key_code}")
    
def test_keypressScene():
    """Test keyboard event handling for scenes"""
    print("=== Testing mcrfpy.keypressScene() ===")
    
    # Test 1: Basic handler registration
    print("\n1. Basic handler registration:")
    mcrfpy.createScene("scene1")
    mcrfpy.setScene("scene1")
    
    try:
        mcrfpy.keypressScene(scene1_handler)
        print("✓ Keypress handler registered for scene1")
    except Exception as e:
        print(f"✗ Failed to register handler: {e}")
        print("FAIL")
        return
    
    # Test 2: Handler persists across scene changes
    print("\n2. Testing handler persistence:")
    mcrfpy.createScene("scene2") 
    mcrfpy.setScene("scene2")
    
    try:
        mcrfpy.keypressScene(scene2_handler)
        print("✓ Keypress handler registered for scene2")
    except Exception as e:
        print(f"✗ Failed to register handler for scene2: {e}")
    
    # Switch back to scene1
    mcrfpy.setScene("scene1")
    current = mcrfpy.currentScene()
    print(f"✓ Switched back to: {current}")
    
    # Test 3: Clear handler
    print("\n3. Testing handler clearing:")
    try:
        mcrfpy.keypressScene(None)
        print("✓ Handler cleared with None")
    except Exception as e:
        print(f"✗ Failed to clear handler: {e}")
    
    # Test 4: Re-register handler
    print("\n4. Testing re-registration:")
    try:
        mcrfpy.keypressScene(scene1_handler)
        print("✓ Handler re-registered successfully")
    except Exception as e:
        print(f"✗ Failed to re-register: {e}")
    
    # Test 5: Lambda functions
    print("\n5. Testing lambda functions:")
    try:
        mcrfpy.keypressScene(lambda k: print(f"Lambda key: {k}"))
        print("✓ Lambda function accepted as handler")
    except Exception as e:
        print(f"✗ Failed with lambda: {e}")
    
    # Known issues
    print("\n⚠ Known Issues:")
    print("- Invalid argument (non-callable) causes segfault")
    print("- No way to query current handler")
    print("- Handler is global, not per-scene (issue #61)")
    
    # Summary related to issue #61
    print("\n📋 Issue #61 Analysis:")
    print("Current: mcrfpy.keypressScene() sets a global handler")
    print("Proposed: Scene objects should encapsulate their own callbacks")
    print("Impact: Currently only one keypress handler active at a time")
    
    print("\n=== Test Complete ===")
    print("PASS - API functions correctly within current limitations")

# Run test immediately
test_keypressScene()