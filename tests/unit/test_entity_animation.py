#!/usr/bin/env python3
"""
Test Entity Animation
====================

Isolated test for entity position animation.
No perspective, just basic movement in a square pattern.

Headless: mcrfpy.step(dt) is the only clock, so the waypoint sequence is driven
explicitly instead of by keyboard input + a free-running game loop (#350/#341).
"""

import mcrfpy
import sys

failures = []

def check(condition, message):
    if not condition:
        print(f"FAIL: {message}")
        failures.append(message)
    return condition

# Create scene
test_anim = mcrfpy.Scene("test_anim")

# Create simple grid
grid = mcrfpy.Grid(grid_size=(15, 15), pos=(100, 100), size=(450, 450))
grid.fill_color = mcrfpy.Color(20, 20, 30)

# Add a color layer for cell coloring (GridPoint.color is gone; use a ColorLayer)
color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
grid.grid_data.add_layer(color_layer)

# Initialize all cells as walkable floors
for y in range(15):
    for x in range(15):
        cell = grid.at(x, y)
        cell.walkable = True
        cell.transparent = True
        color_layer.set((x, y), mcrfpy.Color(100, 100, 120))

# Mark the path we'll follow with different color
path_cells = [(5,5), (6,5), (7,5), (8,5), (9,5), (10,5),
              (10,6), (10,7), (10,8), (10,9), (10,10),
              (9,10), (8,10), (7,10), (6,10), (5,10),
              (5,9), (5,8), (5,7), (5,6)]

for x, y in path_cells:
    color_layer.set((x, y), mcrfpy.Color(120, 120, 150))

# Create entity at start position
entity = mcrfpy.Entity(grid_pos=(5, 5))
entity.sprite_index = 64  # @
grid.entities.append(entity)

# UI setup
ui = test_anim.children
ui.append(grid)

# Title
title = mcrfpy.Caption(pos=(200, 20), text="Entity Animation Test - Square Path")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Status display
status = mcrfpy.Caption(pos=(100, 50), text="Animating square path")
status.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(status)

# Position display
pos_display = mcrfpy.Caption(pos=(100, 70),
                             text=f"Entity Position: ({entity.draw_pos.x:.2f}, {entity.draw_pos.y:.2f})")
pos_display.fill_color = mcrfpy.Color(255, 255, 100)
ui.append(pos_display)

# Animation info
anim_info = mcrfpy.Caption(pos=(400, 70), text="Animation: Not started")
anim_info.fill_color = mcrfpy.Color(100, 255, 255)
ui.append(anim_info)

# Animation state
waypoints = [(5,5), (10,5), (10,10), (5,10), (5,5)]
completed = []   # (property, final_value) tuples from animation callbacks

def on_anim_done(target, prop, value):
    """Animation completion callback: (target, property, final_value)"""
    completed.append((prop, value))

def animate_to_waypoint(index):
    """Animate the entity's draw position to waypoints[index]."""
    target_x, target_y = waypoints[index]
    duration = 2.0

    print(f"Animating from ({entity.draw_pos.x}, {entity.draw_pos.y}) to ({target_x}, {target_y})")
    status.text = f"Moving to waypoint {index + 1}/{len(waypoints)}: ({target_x}, {target_y})"
    anim_info.text = f"Animation: Active (target: {target_x}, {target_y})"

    # 'draw_x'/'draw_y' are the tile-space draw coordinates ('x'/'y' are aliases).
    # mcrfpy.Animation is no longer exported; animations are created via .animate().
    entity.animate("draw_x", float(target_x), duration, mcrfpy.Easing.LINEAR,
                   callback=on_anim_done)
    entity.animate("draw_y", float(target_y), duration, mcrfpy.Easing.LINEAR,
                   callback=on_anim_done)
    return duration

def step_seconds(seconds, dt=0.1):
    """Advance the headless clock; the engine never advances time on its own."""
    for _ in range(int(round(seconds / dt))):
        mcrfpy.step(dt)

def test_immediate_position():
    """Test setting position directly (no animation)."""
    # #295: grid_pos (logical cell) is DECOUPLED from draw_pos (visual position).
    # Setting one does not move the other; they are assigned independently.
    entity.grid_pos = (7, 7)
    check(tuple(entity.cell_pos) == (7, 7),
          f"direct grid_pos set: expected cell (7,7), got {tuple(entity.cell_pos)}")
    check((entity.draw_pos.x, entity.draw_pos.y) == (5.0, 5.0),
          f"grid_pos is decoupled from draw_pos; draw_pos should be unchanged at "
          f"(5,5), got {entity.draw_pos}")

    entity.draw_pos = (7.0, 7.0)
    check((entity.draw_pos.x, entity.draw_pos.y) == (7.0, 7.0),
          f"direct draw_pos set: expected (7.0, 7.0), got {entity.draw_pos}")

    # Animation to a new x, driven by explicit steps
    entity.animate("draw_x", 9.0, 1.0, mcrfpy.Easing.LINEAR)
    step_seconds(0.5)
    mid_x = entity.draw_pos.x
    check(7.0 < mid_x < 9.0,
          f"linear animation should be mid-flight at t=0.5s, draw_x={mid_x}")
    step_seconds(0.6)
    check(abs(entity.draw_pos.x - 9.0) < 0.01,
          f"animation should land on draw_x=9.0, got {entity.draw_pos.x}")

print("Entity Animation Test")
print("====================")
print("This test animates an entity in a square pattern:")
print("(5,5) -> (10,5) -> (10,10) -> (5,10) -> (5,5)")
print()

test_anim.activate()
grid.perspective = None  # omniscient view (perspective takes an Entity or None now)

# --- Direct position assignment ---------------------------------------------
test_immediate_position()

# --- Square-path waypoint animation -----------------------------------------
entity.grid_pos = (5, 5)
entity.draw_pos = (5.0, 5.0)   # decoupled from grid_pos; reset both
completed.clear()

for i, (wx, wy) in enumerate(waypoints):
    start = (entity.draw_pos.x, entity.draw_pos.y)
    duration = animate_to_waypoint(i)

    # Halfway through: entity must be strictly between start and target on any
    # axis that actually changes (proves interpolation, not a snap).
    step_seconds(duration / 2)
    half = (entity.draw_pos.x, entity.draw_pos.y)
    for axis, s, t, h in (("x", start[0], wx, half[0]), ("y", start[1], wy, half[1])):
        if s != t:
            check(min(s, t) < h < max(s, t),
                  f"waypoint {i}: draw_{axis} should be interpolating between "
                  f"{s} and {t} at half-time, got {h}")

    # Finish the segment (plus a little slack for the final step)
    step_seconds(duration / 2 + 0.2)
    end = entity.draw_pos
    check(abs(end.x - wx) < 0.01 and abs(end.y - wy) < 0.01,
          f"waypoint {i}: expected draw_pos ({wx}, {wy}), got ({end.x}, {end.y})")

    pos_display.text = f"Entity Position: ({end.x:.2f}, {end.y:.2f})"

anim_info.text = "Animation: Complete"

# Each waypoint fires two completion callbacks (draw_x and draw_y)
check(len(completed) == 2 * len(waypoints),
      f"expected {2 * len(waypoints)} animation callbacks, got {len(completed)}")

# The entity ends where it started -- a closed square
check(abs(entity.draw_pos.x - 5.0) < 0.01 and abs(entity.draw_pos.y - 5.0) < 0.01,
      f"square path should end at (5, 5), got {entity.draw_pos}")

# Animating draw_pos does not move the entity's logical cell (#313 contract:
# draw_pos is the visual position, cell_pos/grid_pos is the authoritative cell).
check(tuple(entity.cell_pos) == (5, 5),
      f"logical cell should still be (5,5), got {tuple(entity.cell_pos)}")

if failures:
    print(f"\n{len(failures)} check(s) failed")
    sys.exit(1)

print("\nPASS")
sys.exit(0)
