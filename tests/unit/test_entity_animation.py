#!/usr/bin/env python3
"""
Test Entity Animation
====================

Isolated test for entity position animation.
No perspective, just basic movement in a square pattern.
"""

import mcrfpy
import sys

# Create scene
mcrfpy.createScene("test_anim")

# Create simple grid
grid = mcrfpy.Grid(grid_x=15, grid_y=15)
grid.fill_color = mcrfpy.Color(20, 20, 30)

# Add a color layer for cell coloring
color_layer = grid.add_layer("color", z_index=-1)

# Initialize all cells as walkable floors
for y in range(15):
    for x in range(15):
        cell = grid.at(x, y)
        cell.walkable = True
        cell.transparent = True
        color_layer.set(x, y, mcrfpy.Color(100, 100, 120))

# Mark the path we'll follow with different color
path_cells = [(5,5), (6,5), (7,5), (8,5), (9,5), (10,5),
              (10,6), (10,7), (10,8), (10,9), (10,10),
              (9,10), (8,10), (7,10), (6,10), (5,10),
              (5,9), (5,8), (5,7), (5,6)]

for x, y in path_cells:
    color_layer.set(x, y, mcrfpy.Color(120, 120, 150))

# Create entity at start position
entity = mcrfpy.Entity((5, 5), grid=grid)
entity.sprite_index = 64  # @

# UI setup
ui = mcrfpy.sceneUI("test_anim")
ui.append(grid)
grid.position = (100, 100)
grid.size = (450, 450)  # 15 * 30 pixels per cell

# Title
title = mcrfpy.Caption(pos=(200, 20), text="Entity Animation Test - Square Path")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Status display
status = mcrfpy.Caption(pos=(100, 50), text="Press SPACE to start animation | Q to quit")
status.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(status)

# Position display
pos_display = mcrfpy.Caption(pos=(100, 70), text=f"Entity Position: ({entity.x:.2f}, {entity.y:.2f})")
pos_display.fill_color = mcrfpy.Color(255, 255, 100)
ui.append(pos_display)

# Animation info
anim_info = mcrfpy.Caption(pos=(400, 70), text="Animation: Not started")
anim_info.fill_color = mcrfpy.Color(100, 255, 255)
ui.append(anim_info)

# Debug info
debug_info = mcrfpy.Caption(pos=(100, 570), text="Debug: Waiting...")
debug_info.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(debug_info)

# Animation state
current_waypoint = 0
animating = False
waypoints = [(5,5), (10,5), (10,10), (5,10), (5,5)]

def update_position_display(dt):
    """Update position display every 200ms"""
    pos_display.text = f"Entity Position: ({entity.x:.2f}, {entity.y:.2f})"
    
    # Check if entity is at expected position
    if animating and current_waypoint > 0:
        target = waypoints[current_waypoint - 1]
        distance = ((entity.x - target[0])**2 + (entity.y - target[1])**2)**0.5
        debug_info.text = f"Debug: Distance to target {target}: {distance:.3f}"

def animate_to_next_waypoint():
    """Animate to the next waypoint"""
    global current_waypoint, animating
    
    if current_waypoint >= len(waypoints):
        status.text = "Animation complete! Press SPACE to restart"
        anim_info.text = "Animation: Complete"
        animating = False
        current_waypoint = 0
        return
    
    target_x, target_y = waypoints[current_waypoint]
    
    # Log what we're doing
    print(f"Animating from ({entity.x}, {entity.y}) to ({target_x}, {target_y})")
    
    # Update status
    status.text = f"Moving to waypoint {current_waypoint + 1}/{len(waypoints)}: ({target_x}, {target_y})"
    anim_info.text = f"Animation: Active (target: {target_x}, {target_y})"
    
    # Create animations - ensure we're using floats
    duration = 2.0  # 2 seconds per segment
    
    # Try different approaches to see what works
    
    # Approach 1: Direct property animation
    anim_x = mcrfpy.Animation("x", float(target_x), duration, "linear")
    anim_y = mcrfpy.Animation("y", float(target_y), duration, "linear")
    
    # Start animations
    anim_x.start(entity)
    anim_y.start(entity)
    
    # Log animation details
    print(f"Started animations: x to {float(target_x)}, y to {float(target_y)}, duration: {duration}s")
    
    current_waypoint += 1
    
    # Schedule next waypoint
    mcrfpy.setTimer("next_waypoint", lambda dt: animate_to_next_waypoint(), int(duration * 1000 + 100))

def start_animation():
    """Start or restart the animation sequence"""
    global current_waypoint, animating
    
    # Reset entity position
    entity.x = 5
    entity.y = 5
    
    # Reset state
    current_waypoint = 0
    animating = True
    
    print("Starting animation sequence...")
    
    # Start first animation
    animate_to_next_waypoint()

def test_immediate_position():
    """Test setting position directly"""
    print(f"Before: entity at ({entity.x}, {entity.y})")
    entity.x = 7
    entity.y = 7
    print(f"After direct set: entity at ({entity.x}, {entity.y})")
    
    # Try with animation to same position
    anim_x = mcrfpy.Animation("x", 9.0, 1.0, "linear")
    anim_x.start(entity)
    print("Started animation to x=9.0")

# Input handler
def handle_input(key, state):
    if state != "start":
        return
    
    key = key.lower()
    
    if key == "q":
        print("Exiting test...")
        sys.exit(0)
    elif key == "space":
        if not animating:
            start_animation()
        else:
            print("Animation already in progress!")
    elif key == "t":
        # Test immediate position change
        test_immediate_position()
    elif key == "r":
        # Reset position
        entity.x = 5
        entity.y = 5
        print(f"Reset entity to ({entity.x}, {entity.y})")

# Set scene
mcrfpy.setScene("test_anim")
mcrfpy.keypressScene(handle_input)

# Start position update timer
mcrfpy.setTimer("update_pos", update_position_display, 200)

# No perspective (omniscient view)
grid.perspective = -1

print("Entity Animation Test")
print("====================")
print("This test animates an entity in a square pattern:")
print("(5,5) → (10,5) → (10,10) → (5,10) → (5,5)")
print()
print("Controls:")
print("  SPACE - Start animation")
print("  T - Test immediate position change")
print("  R - Reset position to (5,5)")
print("  Q - Quit")
print()
print("The position display updates every 200ms")
print("Watch the console for animation logs")