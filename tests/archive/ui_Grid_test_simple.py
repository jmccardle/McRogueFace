#!/usr/bin/env python3
"""Simple test for mcrfpy.Grid"""
import mcrfpy

print("Starting Grid test...")

# Create test scene
print("[DEBUG] Creating scene...")
mcrfpy.createScene("grid_test")
print("[DEBUG] Setting scene...")
mcrfpy.setScene("grid_test")
print("[DEBUG] Getting UI...")
ui = mcrfpy.sceneUI("grid_test")
print("[DEBUG] UI retrieved")

# Test grid creation
try:
    # Texture constructor: filename, sprite_width, sprite_height
    # kenney_ice.png is 192x176, so 16x16 would give us 12x11 sprites
    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
    print("[INFO] Texture created successfully")
except Exception as e:
    print(f"[FAIL] Texture creation failed: {e}")
    exit(1)
grid = None

try:
    # Try with just 2 args
    grid = mcrfpy.Grid(20, 15)  # Just grid dimensions
    print("[INFO] Grid created with 2 args")
except Exception as e:
    print(f"[FAIL] 2 args failed: {e}")
    
if not grid:
    try:
        # Try with 3 args  
        grid = mcrfpy.Grid(20, 15, texture)
        print("[INFO] Grid created with 3 args")
    except Exception as e:
        print(f"[FAIL] 3 args failed: {e}")

# If we got here, add to UI
try:
    ui.append(grid)
    print("[PASS] Grid created and added to UI successfully")
except Exception as e:
    print(f"[FAIL] Failed to add Grid to UI: {e}")
    exit(1)

# Test grid properties
try:
    print(f"Grid size: {grid.grid_size}")
    print(f"Position: {grid.position}")
    print(f"Size: {grid.size}")
except Exception as e:
    print(f"[FAIL] Property access failed: {e}")

print("Test complete!")