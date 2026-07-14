#!/usr/bin/env python3
"""
Enhanced Dijkstra Pathfinding Interactive Demo (headless-driven test)
====================================================================

Interactive visualization with entity pathfinding animations.

Controls (when run with a window):
- Press 1/2/3 to select the first entity
- Press A/B/C to select the second entity
- Space to clear selection
- M to make selected entity move along path
- P to pause/resume animation
- R to reset entity positions
- Q or ESC to quit

Under --headless --exec the same handlers are driven programmatically and the
resulting paths / animation / reset are asserted (see run_checks() at the bottom).
"""

import mcrfpy
import sys

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  PASS: {label}")
    else:
        print(f"  FAIL: {label} {detail}")
        failures.append(label)


# Colors
WALL_COLOR = mcrfpy.Color(60, 30, 30)
FLOOR_COLOR = mcrfpy.Color(200, 200, 220)
PATH_COLOR = mcrfpy.Color(200, 250, 220)
VISITED_COLOR = mcrfpy.Color(180, 230, 200)
ENTITY_COLORS = [
    mcrfpy.Color(255, 100, 100),  # Entity 1 - Red
    mcrfpy.Color(100, 255, 100),  # Entity 2 - Green
    mcrfpy.Color(100, 100, 255),  # Entity 3 - Blue
]

GRID_W = 14
GRID_H = 10

# Global state
grid = None
color_layer = None
entities = []
first_point = None
second_point = None
current_path = []
animating = False
animation_progress = 0.0
animation_speed = 2.0  # cells per second
original_positions = []  # Store original entity positions

# Define the map layout from user's specification
# . = floor, W = wall, E = entity position
map_layout = [
    "..............",  # Row 0
    "..W.....WWWW..",  # Row 1
    "..W.W...W.EW..",  # Row 2  (entity 1 is sealed inside the room)
    "..W.....W..W..",  # Row 3
    "..W...E.WWWW..",  # Row 4
    "E.W...........",  # Row 5
    "..W...........",  # Row 6
    "..W...........",  # Row 7
    "..W.WWW.......",  # Row 8
    "..............",  # Row 9
]


def create_map():
    """Create the interactive map with the layout specified by the user"""
    global grid, color_layer, entities, original_positions

    # Create grid - 14x10 as specified
    grid = mcrfpy.Grid(grid_size=(GRID_W, GRID_H))
    grid.fill_color = mcrfpy.Color(0, 0, 0)

    # Add color layer for cell coloring (GridPoint.color is gone; use a ColorLayer)
    color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
    grid.add_layer(color_layer)

    # Create the map
    entity_positions = []
    for y, row in enumerate(map_layout):
        for x, char in enumerate(row):
            cell = grid.at(x, y)

            if char == 'W':
                # Wall
                cell.walkable = False
                cell.transparent = False
                color_layer.set((x, y), WALL_COLOR)
            else:
                # Floor
                cell.walkable = True
                cell.transparent = True
                color_layer.set((x, y), FLOOR_COLOR)

                if char == 'E':
                    # Entity position
                    entity_positions.append((x, y))

    # Create entities at marked positions
    entities = []
    original_positions = []
    for i, (x, y) in enumerate(entity_positions):
        entity = mcrfpy.Entity(grid_pos=(x, y), grid=grid)
        entity.sprite_index = 49 + i  # '1', '2', '3'
        entities.append(entity)
        original_positions.append((x, y))

    return grid


def clear_path_highlight():
    """Clear any existing path highlighting"""
    global current_path

    # Reset all floor tiles to original color
    for y in range(GRID_H):
        for x in range(GRID_W):
            cell = grid.at(x, y)
            if cell.walkable:
                color_layer.set((x, y), FLOOR_COLOR)

    current_path = []


def highlight_path():
    """Highlight the path between selected entities using entity.path_to()"""
    global current_path

    if first_point is None or second_point is None:
        return

    # Clear previous highlighting
    clear_path_highlight()

    # Get entities
    entity1 = entities[first_point]
    entity2 = entities[second_point]

    # Use the path_to method! (entity.x/.y are PIXELS now; cells are grid_x/grid_y)
    path = entity1.path_to(entity2.grid_x, entity2.grid_y)

    if path:
        current_path = path

        # Highlight the path
        for i, (x, y) in enumerate(path):
            cell = grid.at(x, y)
            if cell.walkable:
                # Use gradient for path visualization
                if i < len(path) - 1:
                    color_layer.set((x, y), PATH_COLOR)
                else:
                    color_layer.set((x, y), VISITED_COLOR)

        # Highlight start and end with entity colors
        color_layer.set((entity1.grid_x, entity1.grid_y), ENTITY_COLORS[first_point])
        color_layer.set((entity2.grid_x, entity2.grid_y), ENTITY_COLORS[second_point])

        # Update info
        info_text.text = f"Path: Entity {first_point+1} to Entity {second_point+1} - {len(path)} steps"
    else:
        info_text.text = f"No path between Entity {first_point+1} and Entity {second_point+1}"
        current_path = []


def animate_movement(dt):
    """Animate entity movement along path"""
    global animation_progress, animating, current_path

    if not animating or not current_path or first_point is None:
        return

    entity = entities[first_point]

    # Update animation progress
    animation_progress += animation_speed * dt

    # Calculate current position along path
    path_index = int(animation_progress)

    if path_index >= len(current_path):
        # Animation complete
        animating = False
        animation_progress = 0.0
        # Snap to final position (grid_pos = logical cell, draw_pos = visual)
        if current_path:
            final_x, final_y = current_path[-1]
            entity.grid_pos = (final_x, final_y)
            entity.draw_pos = (float(final_x), float(final_y))
        return

    # Interpolate between path points
    if path_index < len(current_path) - 1:
        curr_x, curr_y = current_path[path_index]
        next_x, next_y = current_path[path_index + 1]

        # Calculate interpolation factor
        t = animation_progress - path_index

        # Smooth interpolation (draw_pos is the fractional render position)
        entity.draw_pos = (curr_x + (next_x - curr_x) * t,
                           curr_y + (next_y - curr_y) * t)
        entity.grid_pos = (curr_x, curr_y)
    else:
        # At last point
        entity.grid_pos = current_path[path_index]
        entity.draw_pos = (float(current_path[path_index][0]),
                           float(current_path[path_index][1]))


def handle_keypress(key, action):
    """Handle keyboard input (#184: handlers receive Key and InputState enums)"""
    global first_point, second_point, animating, animation_progress

    if action != mcrfpy.InputState.PRESSED:
        return

    # Number keys for first entity
    if key in (mcrfpy.Key.NUM_1, mcrfpy.Key.NUM_2, mcrfpy.Key.NUM_3):
        first_point = {mcrfpy.Key.NUM_1: 0, mcrfpy.Key.NUM_2: 1, mcrfpy.Key.NUM_3: 2}[key]
        status_text.text = f"First: Entity {first_point+1} | Second: {f'Entity {second_point+1}' if second_point is not None else '?'}"
        highlight_path()

    # Letter keys for second entity
    elif key in (mcrfpy.Key.A, mcrfpy.Key.B, mcrfpy.Key.C):
        second_point = {mcrfpy.Key.A: 0, mcrfpy.Key.B: 1, mcrfpy.Key.C: 2}[key]
        status_text.text = f"First: {f'Entity {first_point+1}' if first_point is not None else '?'} | Second: Entity {second_point+1}"
        highlight_path()

    # Movement control
    elif key == mcrfpy.Key.M:
        if current_path and first_point is not None:
            animating = True
            animation_progress = 0.0
            control_text.text = "Animation: MOVING (press P to pause)"

    # Pause/Resume
    elif key == mcrfpy.Key.P:
        animating = not animating
        control_text.text = f"Animation: {'MOVING' if animating else 'PAUSED'} (press P to {'pause' if animating else 'resume'})"

    # Reset positions
    elif key == mcrfpy.Key.R:
        animating = False
        animation_progress = 0.0
        for i, entity in enumerate(entities):
            entity.grid_pos = original_positions[i]
            entity.draw_pos = (float(original_positions[i][0]),
                               float(original_positions[i][1]))
        control_text.text = "Entities reset to original positions"
        highlight_path()  # Re-highlight path after reset

    # Clear selection
    elif key == mcrfpy.Key.SPACE:
        first_point = None
        second_point = None
        animating = False
        animation_progress = 0.0
        clear_path_highlight()
        status_text.text = "Press 1/2/3 for first entity, A/B/C for second"
        info_text.text = "Space to clear, Q to quit"
        control_text.text = "Press M to move, P to pause, R to reset"

    # Quit
    elif key in (mcrfpy.Key.Q, mcrfpy.Key.ESCAPE):
        print("\nExiting enhanced Dijkstra demo...")
        sys.exit(0 if not failures else 1)


# Timer callback for animation. Callback is (timer, runtime_ms) -- runtime is
# cumulative, so derive the frame delta ourselves.
last_runtime_ms = 0.0
timer_ticks = 0


def update_animation(timer, runtime_ms):
    """Update animation state"""
    global last_runtime_ms, timer_ticks
    dt_ms = runtime_ms - last_runtime_ms
    last_runtime_ms = runtime_ms
    timer_ticks += 1
    animate_movement(dt_ms / 1000.0)  # Convert ms to seconds


# Create the visualization
print("Enhanced Dijkstra Pathfinding Demo")
print("==================================")
print("Controls:")
print("  1/2/3 - Select first entity")
print("  A/B/C - Select second entity")
print("  M     - Move first entity along path")
print("  P     - Pause/Resume animation")
print("  R     - Reset entity positions")
print("  Space - Clear selection")
print("  Q/ESC - Quit")

dijkstra_enhanced = mcrfpy.Scene("dijkstra_enhanced")

# Create map
grid = create_map()

# Set up UI
ui = dijkstra_enhanced.children
ui.append(grid)

# Scale and position grid for better visibility
grid.size = (560, 400)  # 14*40, 10*40
grid.pos = (120, 60)

# Add title
title = mcrfpy.Caption(pos=(250, 10), text="Enhanced Dijkstra Pathfinding")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add status text
status_text = mcrfpy.Caption(pos=(120, 480), text="Press 1/2/3 for first entity, A/B/C for second")
status_text.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(status_text)

# Add info text
info_text = mcrfpy.Caption(pos=(120, 500), text="Space to clear, Q to quit")
info_text.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(info_text)

# Add control text
control_text = mcrfpy.Caption(pos=(120, 520), text="Press M to move, P to pause, R to reset")
control_text.fill_color = mcrfpy.Color(150, 200, 150)
ui.append(control_text)

# Add legend
legend1 = mcrfpy.Caption(pos=(120, 560), text="Entities: 1=Red 2=Green 3=Blue")
legend1.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend1)

legend2 = mcrfpy.Caption(pos=(120, 580), text="Colors: Dark=Wall Light=Floor Cyan=Path")
legend2.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend2)

# Mark entity positions with colored indicators
for i, entity in enumerate(entities):
    marker = mcrfpy.Caption(pos=(120 + entity.grid_x * 40 + 15, 60 + entity.grid_y * 40 + 10),
                            text=str(i+1))
    marker.fill_color = ENTITY_COLORS[i]
    marker.outline = 1
    marker.outline_color = mcrfpy.Color(0, 0, 0)
    ui.append(marker)

# Set up input handling
dijkstra_enhanced.on_key = handle_keypress

# Set up animation timer (60 FPS)
animation_timer = mcrfpy.Timer("animation", update_animation, 16)

# Show the scene
dijkstra_enhanced.activate()

print("\nVisualization ready!")
print("Entities are at:")
for i, entity in enumerate(entities):
    print(f"  Entity {i+1}: ({entity.grid_x}, {entity.grid_y})")


def press(key):
    """Simulate a key press through the scene's real handler"""
    handle_keypress(key, mcrfpy.InputState.PRESSED)


def run_checks():
    """Headless driver: exercise the same code paths the keyboard drives."""
    print("\n1. Map construction")
    check("three entities placed at 'E' markers", len(entities) == 3,
          f"got {len(entities)}")
    check("entity positions match layout",
          original_positions == [(10, 2), (6, 4), (0, 5)],
          f"got {original_positions}")
    check("walls are not walkable", not grid.at(2, 1).walkable)
    check("floors are walkable", grid.at(0, 0).walkable)
    # grid.layer(name) returns a wrapper around the same layer (not the same PyObject)
    check("color layer attached", grid.layer("color").name == "color")

    print("\n2. path_to() between entity 2 and entity 3 (reachable around the wall)")
    press(mcrfpy.Key.NUM_2)   # first = entity 2 @ (6,4)
    press(mcrfpy.Key.C)      # second = entity 3 @ (0,5)
    check("path found", len(current_path) > 0, "path_to returned empty")
    if current_path:
        check("path ends at entity 3", tuple(current_path[-1]) == (0, 5),
              f"got {current_path[-1]}")
        walkable = all(grid.at(x, y).walkable for x, y in current_path)
        check("every path cell is walkable", walkable)
        contiguous = all(
            max(abs(current_path[i+1][0] - current_path[i][0]),
                abs(current_path[i+1][1] - current_path[i][1])) == 1
            for i in range(len(current_path) - 1))
        check("path steps are contiguous", contiguous)
        check("info caption reports the path", "Path:" in info_text.text,
              info_text.text)

    print("\n3. path_to() into the sealed room (entity 1) has no solution")
    saved_path = list(current_path)
    press(mcrfpy.Key.A)      # second = entity 1 @ (10,2), walled in
    check("no path reported", len(current_path) == 0,
          f"got {len(current_path)} steps")
    check("info caption reports no path", "No path" in info_text.text,
          info_text.text)

    print("\n4. M drives the entity along the path (timer + step())")
    press(mcrfpy.Key.C)      # back to the reachable target
    check("path restored", current_path == saved_path)
    press(mcrfpy.Key.M)
    check("animating flag set", animating is True)

    # mcrfpy.step() is the headless clock; the 16ms timer fires once per step.
    for _ in range(400):
        mcrfpy.step(0.05)
        if not animating:
            break
    check("animation timer fired", timer_ticks > 0, f"ticks={timer_ticks}")
    check("animation completed", animating is False)
    entity2 = entities[1]
    check("entity 2 arrived at entity 3's cell",
          (entity2.grid_x, entity2.grid_y) == (0, 5),
          f"got ({entity2.grid_x}, {entity2.grid_y})")

    print("\n5. R resets entities to their original positions")
    press(mcrfpy.Key.R)
    positions = [(e.grid_x, e.grid_y) for e in entities]
    check("positions restored", positions == original_positions,
          f"got {positions}")

    print("\n6. Space clears the selection and the highlight")
    press(mcrfpy.Key.SPACE)
    check("selection cleared",
          first_point is None and second_point is None and current_path == [])


run_checks()

if failures:
    print(f"\nFAIL: {len(failures)} check(s) failed: {failures}")
    sys.exit(1)
print("\nPASS")
sys.exit(0)
