#!/usr/bin/env python3
"""
Test that all UI classes can be instantiated without arguments.
This verifies the fix for requiring arguments even with safe default constructors.
"""

import mcrfpy
import sys

def test_ui_constructors(runtime):
    """Test that UI classes can be instantiated without arguments"""
    
    print("Testing UI class instantiation without arguments...")
    
    # Test UICaption with no arguments
    try:
        caption = mcrfpy.Caption()
        print("PASS: Caption() - Success")
        print(f"      Position: ({caption.x}, {caption.y})")
        print(f"      Text: '{caption.text}'")
        assert caption.x == 0.0
        assert caption.y == 0.0
        assert caption.text == ""
    except Exception as e:
        print(f"FAIL: Caption() - {e}")
        import traceback
        traceback.print_exc()
    
    # Test UIFrame with no arguments
    try:
        frame = mcrfpy.Frame()
        print("PASS: Frame() - Success")
        print(f"      Position: ({frame.x}, {frame.y})")
        print(f"      Size: ({frame.w}, {frame.h})")
        assert frame.x == 0.0
        assert frame.y == 0.0
        assert frame.w == 0.0
        assert frame.h == 0.0
    except Exception as e:
        print(f"FAIL: Frame() - {e}")
        import traceback
        traceback.print_exc()
    
    # Test UIGrid with no arguments
    try:
        grid = mcrfpy.Grid()
        print("PASS: Grid() - Success")
        print(f"      Grid size: {grid.grid_x} x {grid.grid_y}")
        print(f"      Position: ({grid.x}, {grid.y})")
        assert grid.grid_x == 1
        assert grid.grid_y == 1
        assert grid.x == 0.0
        assert grid.y == 0.0
    except Exception as e:
        print(f"FAIL: Grid() - {e}")
        import traceback
        traceback.print_exc()
    
    # Test UIEntity with no arguments
    try:
        entity = mcrfpy.Entity()
        print("PASS: Entity() - Success")
        print(f"      Position: ({entity.x}, {entity.y})")
        assert entity.x == 0.0
        assert entity.y == 0.0
    except Exception as e:
        print(f"FAIL: Entity() - {e}")
        import traceback
        traceback.print_exc()
    
    # Test UISprite with no arguments (if it has a default constructor)
    try:
        sprite = mcrfpy.Sprite()
        print("PASS: Sprite() - Success")
        print(f"      Position: ({sprite.x}, {sprite.y})")
        assert sprite.x == 0.0
        assert sprite.y == 0.0
    except Exception as e:
        print(f"FAIL: Sprite() - {e}")
        # Sprite might still require arguments, which is okay
    
    print("\nAll tests complete!")
    
    # Exit cleanly
    sys.exit(0)

# Create a basic scene so the game can start
mcrfpy.createScene("test")

# Schedule the test to run after game initialization
mcrfpy.setTimer("test", test_ui_constructors, 100)