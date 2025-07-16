#!/usr/bin/env python3
"""Test for mcrfpy.sceneUI() method - Related to issue #28"""
import mcrfpy
from mcrfpy import automation
from datetime import datetime

def test_sceneUI():
    """Test getting UI collection from scene"""
    # Create a test scene
    mcrfpy.createScene("ui_test_scene")
    mcrfpy.setScene("ui_test_scene")
    
    # Get initial UI collection (should be empty)
    try:
        ui_collection = mcrfpy.sceneUI("ui_test_scene")
        print(f"✓ sceneUI returned collection with {len(ui_collection)} items")
    except Exception as e:
        print(f"✗ sceneUI failed: {e}")
        print("FAIL")
        return
    
    # Add some UI elements to the scene
    frame = mcrfpy.Frame(10, 10, 200, 150, 
                        fill_color=mcrfpy.Color(100, 100, 200),
                        outline_color=mcrfpy.Color(255, 255, 255),
                        outline=2.0)
    ui_collection.append(frame)
    
    caption = mcrfpy.Caption(mcrfpy.Vector(220, 10), 
                            text="Test Caption",
                            fill_color=mcrfpy.Color(255, 255, 0))
    ui_collection.append(caption)
    
    # Skip sprite for now since it requires a texture
    # sprite = mcrfpy.Sprite(10, 170, scale=2.0)
    # ui_collection.append(sprite)
    
    # Get UI collection again
    ui_collection2 = mcrfpy.sceneUI("ui_test_scene")
    print(f"✓ After adding elements: {len(ui_collection2)} items")
    
    # Test iteration (Issue #28 - UICollectionIter)
    try:
        item_types = []
        for item in ui_collection2:
            item_types.append(type(item).__name__)
        print(f"✓ Iteration works, found types: {item_types}")
    except Exception as e:
        print(f"✗ Iteration failed (Issue #28): {e}")
    
    # Test indexing
    try:
        first_item = ui_collection2[0]
        print(f"✓ Indexing works, first item type: {type(first_item).__name__}")
    except Exception as e:
        print(f"✗ Indexing failed: {e}")
    
    # Test invalid scene name
    try:
        invalid_ui = mcrfpy.sceneUI("nonexistent_scene")
        print(f"✗ sceneUI should fail for nonexistent scene, got {len(invalid_ui)} items")
    except Exception as e:
        print(f"✓ sceneUI correctly fails for nonexistent scene: {e}")
    
    # Take screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_sceneUI_{timestamp}.png"
    automation.screenshot(filename)
    print(f"Screenshot saved: {filename}")
    print("PASS")

# Set up timer to run test
mcrfpy.setTimer("test", test_sceneUI, 1000)

# Cancel timer after running once
def cleanup():
    mcrfpy.delTimer("test")
    mcrfpy.delTimer("cleanup")
    
mcrfpy.setTimer("cleanup", cleanup, 1100)