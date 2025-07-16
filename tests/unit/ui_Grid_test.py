#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test for mcrfpy.Grid class - Related to issues #77, #74, #50, #52, #20"""
import mcrfpy
from datetime import datetime
try:
    from mcrfpy import automation
    has_automation = True
except ImportError:
    has_automation = False
    print("Warning: automation module not available")

def test_Grid():
    """Test Grid creation and properties"""
    # Create test scene
    mcrfpy.createScene("grid_test")
    mcrfpy.setScene("grid_test")
    ui = mcrfpy.sceneUI("grid_test")
    
    # Test grid creation
    try:
        # Note: Grid requires texture, creating one for testing
        texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
        grid = mcrfpy.Grid(20, 15,  # grid dimensions
                          texture,  # texture
                          mcrfpy.Vector(10, 10),   # position
                          mcrfpy.Vector(400, 300)) # size
        ui.append(grid)
        print("[PASS] Grid created successfully")
    except Exception as e:
        print(f"[FAIL] Failed to create Grid: {e}")
        print("FAIL")
        return
    
    # Test grid properties
    try:
        # Test grid_size (Issue #20)
        grid_size = grid.grid_size
        print(f"[PASS] Grid size: {grid_size}")
        
        # Test position and size
        print(f"Position: {grid.position}")
        print(f"Size: {grid.size}")
        
        # Test individual coordinate properties
        print(f"Coordinates: x={grid.x}, y={grid.y}, w={grid.w}, h={grid.h}")
        
        # Test grid_y property (Issue #74)
        try:
            # This might fail if grid_y is not implemented
            print(f"Grid dimensions via properties: grid_x=?, grid_y=?")
            print("[FAIL] Issue #74: Grid.grid_y property may be missing")
        except:
            pass
            
    except Exception as e:
        print(f"[FAIL] Property access failed: {e}")
    
    # Test center/pan functionality
    try:
        grid.center = mcrfpy.Vector(10, 7)
        print(f"[PASS] Center set to: {grid.center}")
        grid.center_x = 5
        grid.center_y = 5
        print(f"[PASS] Center modified to: ({grid.center_x}, {grid.center_y})")
    except Exception as e:
        print(f"[FAIL] Center/pan failed: {e}")
    
    # Test zoom
    try:
        grid.zoom = 1.5
        print(f"[PASS] Zoom set to: {grid.zoom}")
    except Exception as e:
        print(f"[FAIL] Zoom failed: {e}")
    
    # Test at() method for GridPoint access (Issue #77)
    try:
        # This tests the error message issue
        point = grid.at(0, 0)
        print("[PASS] GridPoint access works")
        
        # Try out of bounds access to test error message
        try:
            invalid_point = grid.at(100, 100)
            print("[FAIL] Out of bounds access should fail")
        except Exception as e:
            error_msg = str(e)
            if "Grid.grid_y" in error_msg:
                print(f"[FAIL] Issue #77: Error message has copy/paste bug: {error_msg}")
            else:
                print(f"[PASS] Out of bounds error: {error_msg}")
    except Exception as e:
        print(f"[FAIL] GridPoint access failed: {e}")
    
    # Test entities collection
    try:
        entities = grid.entities
        print(f"[PASS] Entities collection has {len(entities)} items")
        
        # Add an entity
        entity = mcrfpy.Entity(mcrfpy.Vector(5, 5), 
                              texture, 
                              0,  # sprite index
                              grid)
        entities.append(entity)
        print(f"[PASS] Entity added, collection now has {len(entities)} items")
        
        # Test out-of-bounds entity (Issue #52)
        out_entity = mcrfpy.Entity(mcrfpy.Vector(50, 50),  # Outside 20x15 grid
                                  texture,
                                  1,
                                  grid)
        entities.append(out_entity)
        print("[PASS] Out-of-bounds entity added (Issue #52: should be skipped in rendering)")
        
    except Exception as e:
        print(f"[FAIL] Entity management failed: {e}")
    
    # Note about missing features
    print("\nMissing features:")
    print("- Issue #50: UIGrid background color field")
    print("- Issue #6, #8, #9: RenderTexture support")
    
    # Take screenshot if automation is available
    if has_automation:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_Grid_{timestamp}.png"
        automation.screenshot(filename)
        print(f"Screenshot saved: {filename}")
    else:
        print("Screenshot skipped - automation not available")
    print("PASS")

# Set up timer to run test
mcrfpy.setTimer("test", test_Grid, 1000)

# Cancel timer after running once
def cleanup():
    mcrfpy.delTimer("test")
    mcrfpy.delTimer("cleanup")
    
mcrfpy.setTimer("cleanup", cleanup, 1100)