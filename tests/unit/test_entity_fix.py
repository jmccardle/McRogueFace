#!/usr/bin/env python3
"""
Test Entity Animation Fix
=========================

This test demonstrates the issue and proposes a fix.
The problem: UIEntity::setProperty updates sprite position incorrectly.
"""

import mcrfpy
import sys

print("Entity Animation Fix Test")
print("========================")
print()
print("ISSUE: When animating entity x/y properties, the sprite position")
print("is being set to grid coordinates instead of pixel coordinates.")
print()
print("In UIEntity::setProperty (lines 562 & 568):")
print("  sprite.setPosition(sf::Vector2f(position.x, position.y));")
print()
print("This should be removed because UIGrid::render() calculates")
print("the correct pixel position based on grid coordinates, zoom, etc.")
print()
print("FIX: Comment out or remove the sprite.setPosition calls in")
print("UIEntity::setProperty for 'x' and 'y' properties.")
print()

# Create scene to demonstrate
mcrfpy.createScene("fix_demo")

# Create grid
grid = mcrfpy.Grid(grid_x=15, grid_y=10)
grid.fill_color = mcrfpy.Color(20, 20, 30)

# Add color layer for cell coloring
color_layer = grid.add_layer("color", z_index=-1)

# Make floor
for y in range(10):
    for x in range(15):
        cell = grid.at(x, y)
        cell.walkable = True
        cell.transparent = True
        color_layer.set(x, y, mcrfpy.Color(100, 100, 120))

# Create entity
entity = mcrfpy.Entity((2, 2), grid=grid)
entity.sprite_index = 64  # @

# UI
ui = mcrfpy.sceneUI("fix_demo")
ui.append(grid)
grid.position = (100, 150)
grid.size = (450, 300)

# Info displays
title = mcrfpy.Caption(pos=(250, 20), text="Entity Animation Issue Demo")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

pos_info = mcrfpy.Caption(pos=(100, 50), text="")
pos_info.fill_color = mcrfpy.Color(255, 255, 100)
ui.append(pos_info)

sprite_info = mcrfpy.Caption(pos=(100, 70), text="")
sprite_info.fill_color = mcrfpy.Color(255, 100, 100)
ui.append(sprite_info)

status = mcrfpy.Caption(pos=(100, 100), text="Press SPACE to animate entity")
status.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(status)

# Update display
def update_display(dt):
    pos_info.text = f"Entity Grid Position: ({entity.x:.2f}, {entity.y:.2f})"
    # We can't access sprite position from Python, but in C++ it would show
    # the issue: sprite position would be (2, 2) instead of pixel coords
    sprite_info.text = "Sprite position is incorrectly set to grid coords (see C++ code)"

# Test animation
def test_animation():
    """Animate entity to show the issue"""
    print("\nAnimating entity from (2,2) to (10,5)")
    
    # This animation will cause the sprite to appear at wrong position
    # because setProperty sets sprite.position to (10, 5) instead of
    # letting the grid calculate pixel position
    anim_x = mcrfpy.Animation("x", 10.0, 2.0, "easeInOut")
    anim_y = mcrfpy.Animation("y", 5.0, 2.0, "easeInOut")
    
    anim_x.start(entity)
    anim_y.start(entity)
    
    status.text = "Animating... Entity may appear at wrong position!"

# Input handler
def handle_input(key, state):
    if state != "start":
        return
    
    key = key.lower()
    
    if key == "q":
        sys.exit(0)
    elif key == "space":
        test_animation()
    elif key == "r":
        entity.x = 2
        entity.y = 2
        status.text = "Reset entity to (2,2)"

# Setup
mcrfpy.setScene("fix_demo")
mcrfpy.keypressScene(handle_input)
mcrfpy.setTimer("update", update_display, 100)

print("Ready to demonstrate the issue.")
print()
print("The fix is to remove these lines from UIEntity::setProperty:")
print("  Line 562: sprite.setPosition(sf::Vector2f(position.x, position.y));")
print("  Line 568: sprite.setPosition(sf::Vector2f(position.x, position.y));")
print()
print("Controls:")
print("  SPACE - Animate entity (will show incorrect behavior)")
print("  R - Reset position")
print("  Q - Quit")