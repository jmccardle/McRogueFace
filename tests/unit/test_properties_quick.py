#!/usr/bin/env python3
"""Quick test of drawable properties"""
import mcrfpy
import sys

def test_properties(timer, runtime):
    timer.stop()
    
    print("\n=== Testing Properties ===")
    
    # Test Frame
    try:
        frame = mcrfpy.Frame(pos=(10, 10), size=(100, 100))
        print(f"Frame visible: {frame.visible}")
        frame.visible = False
        print(f"Frame visible after setting to False: {frame.visible}")
        
        print(f"Frame opacity: {frame.opacity}")
        frame.opacity = 0.5
        print(f"Frame opacity after setting to 0.5: {frame.opacity}")
        
        bounds = frame.get_bounds()
        print(f"Frame bounds: {bounds}")
        
        frame.move(5, 5)
        bounds2 = frame.get_bounds()
        print(f"Frame bounds after move(5,5): {bounds2}")
        
        print("✓ Frame properties work!")
    except Exception as e:
        print(f"✗ Frame failed: {e}")
    
    # Test Entity
    try:
        entity = mcrfpy.Entity()
        print(f"\nEntity visible: {entity.visible}")
        entity.visible = False
        print(f"Entity visible after setting to False: {entity.visible}")
        
        print(f"Entity opacity: {entity.opacity}")
        entity.opacity = 0.7
        print(f"Entity opacity after setting to 0.7: {entity.opacity}")
        
        bounds = entity.get_bounds()
        print(f"Entity bounds: {bounds}")
        
        entity.move(3, 3)
        print(f"Entity position after move(3,3): ({entity.x}, {entity.y})")
        
        print("✓ Entity properties work!")
    except Exception as e:
        print(f"✗ Entity failed: {e}")
    
    sys.exit(0)

test = mcrfpy.Scene("test")
test_properties_timer = mcrfpy.Timer("test_properties", test_properties, 100, once=True)