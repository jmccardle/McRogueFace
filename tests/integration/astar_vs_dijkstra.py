#!/usr/bin/env python3
"""
A* vs Dijkstra Visual Comparison
=================================

Shows the difference between A* (single target) and Dijkstra (multi-target).
"""

import mcrfpy
import sys

# Colors
WALL_COLOR = mcrfpy.Color(40, 20, 20)
FLOOR_COLOR = mcrfpy.Color(60, 60, 80)
ASTAR_COLOR = mcrfpy.Color(0, 255, 0)      # Green for A*
DIJKSTRA_COLOR = mcrfpy.Color(0, 150, 255) # Blue for Dijkstra
START_COLOR = mcrfpy.Color(255, 100, 100)  # Red for start
END_COLOR = mcrfpy.Color(255, 255, 100)    # Yellow for end

# Global state
grid = None
color_layer = None
mode = "ASTAR"
start_pos = (5, 10)
end_pos = (27, 10)  # Changed from 25 to 27 to avoid the wall

def create_map():
    """Create a map with obstacles to show pathfinding differences"""
    global grid, color_layer

    pathfinding_comparison = mcrfpy.Scene("pathfinding_comparison")

    # Create grid
    grid = mcrfpy.Grid(grid_w=30, grid_h=20)
    grid.fill_color = mcrfpy.Color(0, 0, 0)

    # Add color layer for cell coloring
    color_layer = grid.add_layer("color", z_index=-1)

    # Initialize all as floor
    for y in range(20):
        for x in range(30):
            grid.at(x, y).walkable = True
            color_layer.set(x, y, FLOOR_COLOR)

    # Create obstacles that make A* and Dijkstra differ
    obstacles = [
        # Vertical wall with gaps
        [(15, y) for y in range(3, 17) if y not in [8, 12]],
        # Horizontal walls
        [(x, 5) for x in range(10, 20)],
        [(x, 15) for x in range(10, 20)],
        # Maze-like structure
        [(x, 10) for x in range(20, 25)],
        [(25, y) for y in range(5, 15)],
    ]

    for obstacle_group in obstacles:
        for x, y in obstacle_group:
            grid.at(x, y).walkable = False
            color_layer.set(x, y, WALL_COLOR)

    # Mark start and end
    color_layer.set(start_pos[0], start_pos[1], START_COLOR)
    color_layer.set(end_pos[0], end_pos[1], END_COLOR)

def clear_paths():
    """Clear path highlighting"""
    for y in range(20):
        for x in range(30):
            cell = grid.at(x, y)
            if cell.walkable:
                color_layer.set(x, y, FLOOR_COLOR)

    # Restore start and end colors
    color_layer.set(start_pos[0], start_pos[1], START_COLOR)
    color_layer.set(end_pos[0], end_pos[1], END_COLOR)

def show_astar():
    """Show A* path"""
    clear_paths()

    # Compute A* path
    path = grid.compute_astar_path(start_pos[0], start_pos[1], end_pos[0], end_pos[1])

    # Color the path
    for i, (x, y) in enumerate(path):
        if (x, y) != start_pos and (x, y) != end_pos:
            color_layer.set(x, y, ASTAR_COLOR)

    status_text.text = f"A* Path: {len(path)} steps (optimized for single target)"
    status_text.fill_color = ASTAR_COLOR

def show_dijkstra():
    """Show Dijkstra exploration"""
    clear_paths()

    # Compute Dijkstra from start
    grid.compute_dijkstra(start_pos[0], start_pos[1])

    # Color cells by distance (showing exploration)
    max_dist = 40.0
    for y in range(20):
        for x in range(30):
            if grid.at(x, y).walkable:
                dist = grid.get_dijkstra_distance(x, y)
                if dist is not None and dist < max_dist:
                    # Color based on distance
                    intensity = int(255 * (1 - dist / max_dist))
                    color_layer.set(x, y, mcrfpy.Color(0, intensity // 2, intensity))

    # Get the actual path
    path = grid.get_dijkstra_path(end_pos[0], end_pos[1])

    # Highlight the actual path more brightly
    for x, y in path:
        if (x, y) != start_pos and (x, y) != end_pos:
            color_layer.set(x, y, DIJKSTRA_COLOR)

    # Restore start and end
    color_layer.set(start_pos[0], start_pos[1], START_COLOR)
    color_layer.set(end_pos[0], end_pos[1], END_COLOR)

    status_text.text = f"Dijkstra: {len(path)} steps (explores all directions)"
    status_text.fill_color = DIJKSTRA_COLOR

def show_both():
    """Show both paths overlaid"""
    clear_paths()

    # Get both paths
    astar_path = grid.compute_astar_path(start_pos[0], start_pos[1], end_pos[0], end_pos[1])
    grid.compute_dijkstra(start_pos[0], start_pos[1])
    dijkstra_path = grid.get_dijkstra_path(end_pos[0], end_pos[1])

    print(astar_path, dijkstra_path)

    # Color Dijkstra path first (blue)
    for x, y in dijkstra_path:
        if (x, y) != start_pos and (x, y) != end_pos:
            color_layer.set(x, y, DIJKSTRA_COLOR)

    # Then A* path (green) - will overwrite shared cells
    for x, y in astar_path:
        if (x, y) != start_pos and (x, y) != end_pos:
            color_layer.set(x, y, ASTAR_COLOR)

    # Mark differences
    different_cells = []
    for cell in dijkstra_path:
        if cell not in astar_path:
            different_cells.append(cell)

    status_text.text = f"Both paths: A*={len(astar_path)} steps, Dijkstra={len(dijkstra_path)} steps"
    if different_cells:
        info_text.text = f"Paths differ at {len(different_cells)} cells"
    else:
        info_text.text = "Paths are identical"

def handle_keypress(key_str, state):
    """Handle keyboard input"""
    global mode
    if state == "end": return
    print(key_str)
    if key_str == "Esc" or key_str == "Q":
        print("\nExiting...")
        sys.exit(0)
    elif key_str == "A" or key_str == "1":
        mode = "ASTAR"
        show_astar()
    elif key_str == "D" or key_str == "2":
        mode = "DIJKSTRA"
        show_dijkstra()
    elif key_str == "B" or key_str == "3":
        mode = "BOTH"
        show_both()
    elif key_str == "Space":
        # Refresh current mode
        if mode == "ASTAR":
            show_astar()
        elif mode == "DIJKSTRA":
            show_dijkstra()
        else:
            show_both()

# Create the demo
print("A* vs Dijkstra Pathfinding Comparison")
print("=====================================")
print("Controls:")
print("  A or 1 - Show A* path (green)")
print("  D or 2 - Show Dijkstra (blue gradient)")
print("  B or 3 - Show both paths")
print("  Q/ESC  - Quit")
print()
print("A* is optimized for single-target pathfinding")
print("Dijkstra explores in all directions (good for multiple targets)")

create_map()

# Set up UI
ui = pathfinding_comparison.children
ui.append(grid)

# Scale and position
grid.size = (600, 400)  # 30*20, 20*20
grid.position = (100, 100)

# Add title
title = mcrfpy.Caption(pos=(250, 20), text="A* vs Dijkstra Pathfinding")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add status
status_text = mcrfpy.Caption(pos=(100, 60), text="Press A for A*, D for Dijkstra, B for Both")
status_text.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(status_text)

# Add info
info_text = mcrfpy.Caption(pos=(100, 520), text="")
info_text.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(info_text)

# Add legend
legend1 = mcrfpy.Caption(pos=(100, 540), text="Red=Start, Yellow=End, Green=A*, Blue=Dijkstra")
legend1.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend1)

legend2 = mcrfpy.Caption(pos=(100, 560), text="Dark=Walls, Light=Floor")
legend2.fill_color = mcrfpy.Color(150, 150, 150)
ui.append(legend2)

# Set scene and input
pathfinding_comparison.activate()
pathfinding_comparison.on_key = handle_keypress

# Show initial A* path
show_astar()

print("\nDemo ready!")
