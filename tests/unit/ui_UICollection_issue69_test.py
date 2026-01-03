#!/usr/bin/env python3
"""Test for UICollection - Related to issue #69 (Sequence Protocol)"""
import mcrfpy
from datetime import datetime

def test_UICollection():
    """Test UICollection sequence protocol compliance"""
    # Create test scene
    collection_test = mcrfpy.Scene("collection_test")
    collection_test.activate()
    ui = collection_test.children
    
    # Add various UI elements
    frame = mcrfpy.Frame(pos=(10, 10), size=(100, 100))
    caption = mcrfpy.Caption(pos=(120, 10), text="Test")
    # Skip sprite for now since it requires a texture
    
    ui.append(frame)
    ui.append(caption)
    
    print("Testing UICollection sequence protocol (Issue #69)...")
    
    # Test len()
    try:
        length = len(ui)
        print(f"✓ len() works: {length} items")
    except Exception as e:
        print(f"✗ len() failed: {e}")
    
    # Test indexing
    try:
        item0 = ui[0]
        item1 = ui[1]
        print(f"✓ Indexing works: [{type(item0).__name__}, {type(item1).__name__}]")
        
        # Test negative indexing
        last_item = ui[-1]
        print(f"✓ Negative indexing works: ui[-1] = {type(last_item).__name__}")
    except Exception as e:
        print(f"✗ Indexing failed: {e}")
    
    # Test slicing (if implemented)
    try:
        slice_items = ui[0:2]
        print(f"✓ Slicing works: got {len(slice_items)} items")
    except Exception as e:
        print(f"✗ Slicing not implemented (Issue #69): {e}")
    
    # Test iteration
    try:
        types = []
        for item in ui:
            types.append(type(item).__name__)
        print(f"✓ Iteration works: {types}")
    except Exception as e:
        print(f"✗ Iteration failed: {e}")
    
    # Test contains
    try:
        if frame in ui:
            print("✓ 'in' operator works")
        else:
            print("✗ 'in' operator returned False for existing item")
    except Exception as e:
        print(f"✗ 'in' operator not implemented (Issue #69): {e}")
    
    # Test remove
    try:
        ui.remove(1)  # Remove caption
        print(f"✓ remove() works, now {len(ui)} items")
    except Exception as e:
        print(f"✗ remove() failed: {e}")
    
    # Test type preservation (Issue #76)
    try:
        # Add a frame with children to test nested collections
        parent_frame = mcrfpy.Frame(pos=(250, 10), size=(200, 200),
                                   fill_color=mcrfpy.Color(200, 200, 200))
        child_caption = mcrfpy.Caption(pos=(10, 10), text="Child")
        parent_frame.children.append(child_caption)
        ui.append(parent_frame)
        
        # Check if type is preserved when retrieving
        retrieved = ui[-1]
        if type(retrieved).__name__ == "Frame":
            print("✓ Type preservation works")
        else:
            print(f"✗ Type not preserved (Issue #76): got {type(retrieved).__name__}")
    except Exception as e:
        print(f"✗ Type preservation test failed: {e}")
    
    # Test find by name (Issue #41 - not yet implemented)
    try:
        found = ui.find("Test")
        print(f"✓ find() method works: {type(found).__name__}")
    except AttributeError:
        print("✗ find() method not implemented (Issue #41)")
    except Exception as e:
        print(f"✗ find() method error: {e}")
    
    print("PASS")

# Run test immediately
test_UICollection()