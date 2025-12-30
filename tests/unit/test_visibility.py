#!/usr/bin/env python3
"""
Test Knowledge Stubs 1 Visibility System
========================================

Tests per-entity visibility tracking with perspective rendering.
"""

import mcrfpy
import sys
import time

print("Knowledge Stubs 1 - Visibility System Test")
print("==========================================")

# Create scene and grid
mcrfpy.createScene("visibility_test")
grid = mcrfpy.Grid(grid_x=20, grid_y=15)
grid.fill_color = mcrfpy.Color(20, 20, 30)  # Dark background

# Add a color layer for cell coloring
color_layer = grid.add_layer("color", z_index=-1)

# Initialize grid - all walkable and transparent
print("\nInitializing 20x15 grid...")
for y in range(15):
    for x in range(20):
        cell = grid.at(x, y)
        cell.walkable = True
        cell.transparent = True
        color_layer.set(x, y, mcrfpy.Color(100, 100, 120))  # Floor color

# Create some walls to block vision
print("Adding walls...")
walls = [
    # Vertical wall
    [(10, y) for y in range(3, 12)],
    # Horizontal walls
    [(x, 7) for x in range(5, 10)],
    [(x, 7) for x in range(11, 16)],
    # Corner walls
    [(5, 3), (5, 4), (6, 3)],
    [(15, 3), (15, 4), (14, 3)],
    [(5, 11), (5, 10), (6, 11)],
    [(15, 11), (15, 10), (14, 11)],
]

for wall_group in walls:
    for x, y in wall_group:
        cell = grid.at(x, y)
        cell.walkable = False
        cell.transparent = False
        color_layer.set(x, y, mcrfpy.Color(40, 20, 20))  # Wall color

# Create entities
print("\nCreating entities...")
entities = [
    mcrfpy.Entity((2, 7)),    # Left side
    mcrfpy.Entity((18, 7)),   # Right side
    mcrfpy.Entity((10, 1)),   # Top center (above wall)
]

for i, entity in enumerate(entities):
    entity.sprite_index = 64 + i  # @, A, B
    grid.entities.append(entity)
    print(f"  Entity {i}: position ({entity.x}, {entity.y})")

# Test 1: Check initial gridstate
print("\nTest 1: Initial gridstate")
e0 = entities[0]
print(f"  Entity 0 gridstate length: {len(e0.gridstate)}")
print(f"  Expected: {20 * 15}")

# Test 2: Update visibility for each entity
print("\nTest 2: Updating visibility for each entity")
for i, entity in enumerate(entities):
    entity.update_visibility()
    
    # Count visible/discovered cells
    visible_count = sum(1 for state in entity.gridstate if state.visible)
    discovered_count = sum(1 for state in entity.gridstate if state.discovered)
    print(f"  Entity {i}: {visible_count} visible, {discovered_count} discovered")

# Test 3: Test perspective property
print("\nTest 3: Testing perspective property")
print(f"  Initial perspective: {grid.perspective}")
grid.perspective = 0
print(f"  Set to entity 0: {grid.perspective}")

# Test invalid perspective
try:
    grid.perspective = 10  # Out of range
    print("  ERROR: Should have raised exception for invalid perspective")
except IndexError as e:
    print(f"  ✓ Correctly rejected invalid perspective: {e}")

# Test 4: Visual demonstration
def visual_test(runtime):
    print(f"\nVisual test - cycling perspectives at {runtime}ms")
    
    # Cycle through perspectives
    current = grid.perspective
    if current == -1:
        grid.perspective = 0
        print("  Switched to Entity 0 perspective")
    elif current == 0:
        grid.perspective = 1
        print("  Switched to Entity 1 perspective")
    elif current == 1:
        grid.perspective = 2
        print("  Switched to Entity 2 perspective")
    else:
        grid.perspective = -1
        print("  Switched to omniscient view")
    
    # Take screenshot
    from mcrfpy import automation
    filename = f"visibility_perspective_{grid.perspective}.png"
    automation.screenshot(filename)
    print(f"  Screenshot saved: {filename}")

# Test 5: Movement and visibility update
print("\nTest 5: Movement and visibility update")
entity = entities[0]
print(f"  Entity 0 initial position: ({entity.x}, {entity.y})")

# Move entity
entity.x = 8
entity.y = 7
print(f"  Moved to: ({entity.x}, {entity.y})")

# Update visibility
entity.update_visibility()
visible_count = sum(1 for state in entity.gridstate if state.visible)
print(f"  Visible cells after move: {visible_count}")

# Set up UI
ui = mcrfpy.sceneUI("visibility_test")
ui.append(grid)
grid.position = (50, 50)
grid.size = (600, 450)  # 20*30, 15*30

# Add title
title = mcrfpy.Caption(pos=(200, 10), text="Knowledge Stubs 1 - Visibility Test")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add info
info = mcrfpy.Caption(pos=(50, 520), text="Perspective: -1 (omniscient)")
info.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(info)

# Add legend
legend = mcrfpy.Caption(pos=(50, 540), text="Black=Never seen, Dark gray=Discovered, Normal=Visible")
legend.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend)

# Set scene
mcrfpy.setScene("visibility_test")

# Set timer to cycle perspectives
mcrfpy.setTimer("cycle", visual_test, 2000)  # Every 2 seconds

print("\nTest complete! Visual demo cycling through perspectives...")
print("Perspectives will cycle: Omniscient → Entity 0 → Entity 1 → Entity 2 → Omniscient")

# Quick test to exit after screenshots
def exit_timer(dt):
    print("\nExiting after demo...")
    sys.exit(0)

mcrfpy.setTimer("exit", exit_timer, 10000)  # Exit after 10 seconds