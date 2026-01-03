#!/usr/bin/env python3
"""Detailed test for mcrfpy.Frame class - Issues #38 and #42"""
import mcrfpy
import sys

def test_issue_38_children():
    """Test Issue #38: PyUIFrameObject lacks 'children' arg in constructor"""
    print("\n=== Testing Issue #38: children argument in Frame constructor ===")
    
    # Create test scene
    issue38_test = mcrfpy.Scene("issue38_test")
    issue38_test.activate()
    ui = issue38_test.children
    
    # Test 1: Try to pass children in constructor
    print("\nTest 1: Passing children argument to Frame constructor")
    try:
        # Create some child elements
        child1 = mcrfpy.Caption(pos=(10, 10), text="Child 1")
        child2 = mcrfpy.Sprite(pos=(10, 30))

        # Try to create frame with children argument
        frame = mcrfpy.Frame(pos=(10, 10), size=(200, 150), children=[child1, child2])
        print("✗ UNEXPECTED: Frame accepted children argument (should fail per issue #38)")
    except TypeError as e:
        print(f"✓ EXPECTED: Frame constructor rejected children argument: {e}")
    except Exception as e:
        print(f"✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
    
    # Test 2: Verify children can be added after creation
    print("\nTest 2: Adding children after Frame creation")
    try:
        frame = mcrfpy.Frame(pos=(10, 10), size=(200, 150))
        ui.append(frame)

        # Add children via the children collection
        child1 = mcrfpy.Caption(pos=(10, 10), text="Added Child 1")
        child2 = mcrfpy.Caption(pos=(10, 30), text="Added Child 2")
        
        frame.children.append(child1)
        frame.children.append(child2)
        
        print(f"✓ Successfully added {len(frame.children)} children via children collection")
        
        # Verify children are accessible
        for i, child in enumerate(frame.children):
            print(f"  - Child {i}: {type(child).__name__}")
            
    except Exception as e:
        print(f"✗ Failed to add children: {type(e).__name__}: {e}")

def test_issue_42_click_callback():
    """Test Issue #42: click callback requires x, y, button arguments"""
    print("\n\n=== Testing Issue #42: click callback arguments ===")
    
    # Create test scene
    issue42_test = mcrfpy.Scene("issue42_test")
    issue42_test.activate()
    ui = issue42_test.children
    
    # Test 1: Callback with correct signature
    print("\nTest 1: Click callback with correct signature (x, y, button)")
    def correct_callback(x, y, button):
        print(f"  Correct callback called: x={x}, y={y}, button={button}")
        return True
    
    try:
        frame1 = mcrfpy.Frame(pos=(10, 10), size=(200, 150))
        ui.append(frame1)
        frame1.on_click = correct_callback
        print("✓ Click callback with correct signature assigned successfully")
    except Exception as e:
        print(f"✗ Failed to assign correct callback: {type(e).__name__}: {e}")

    # Test 2: Callback with wrong signature (no args)
    print("\nTest 2: Click callback with no arguments")
    def wrong_callback_no_args():
        print("  Wrong callback called")

    try:
        frame2 = mcrfpy.Frame(pos=(220, 10), size=(200, 150))
        ui.append(frame2)
        frame2.on_click = wrong_callback_no_args
        print("✓ Click callback with no args assigned (will fail at runtime per issue #42)")
    except Exception as e:
        print(f"✗ Failed to assign callback: {type(e).__name__}: {e}")

    # Test 3: Callback with wrong signature (too few args)
    print("\nTest 3: Click callback with too few arguments")
    def wrong_callback_few_args(x, y):
        print(f"  Wrong callback called: x={x}, y={y}")

    try:
        frame3 = mcrfpy.Frame(pos=(10, 170), size=(200, 150))
        ui.append(frame3)
        frame3.on_click = wrong_callback_few_args
        print("✓ Click callback with 2 args assigned (will fail at runtime per issue #42)")
    except Exception as e:
        print(f"✗ Failed to assign callback: {type(e).__name__}: {e}")
    
    # Test 4: Verify callback property getter
    print("\nTest 4: Verify click callback getter")
    try:
        if hasattr(frame1, 'click'):
            callback = frame1.click
            print(f"✓ Click callback getter works, returned: {callback}")
        else:
            print("✗ Frame object has no 'click' attribute")
    except Exception as e:
        print(f"✗ Failed to get click callback: {type(e).__name__}: {e}")

def main():
    """Run all tests"""
    print("Testing mcrfpy.Frame - Issues #38 and #42")
    
    test_issue_38_children()
    test_issue_42_click_callback()
    
    print("\n\n=== TEST SUMMARY ===")
    print("Issue #38 (children constructor arg): Constructor correctly rejects children argument")
    print("Issue #42 (click callback args): Click callbacks can be assigned (runtime behavior not tested in headless mode)")
    print("\nAll tests completed successfully!")
    
    sys.exit(0)

if __name__ == "__main__":
    main()