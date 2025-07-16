#!/usr/bin/env python3
"""Debug the astar_vs_dijkstra demo issue"""

import mcrfpy
import sys

# Same setup as the demo
start_pos = (5, 10)
end_pos = (25, 10)

print("Debugging A* vs Dijkstra demo...")
print(f"Start: {start_pos}, End: {end_pos}")

# Create scene and grid
mcrfpy.createScene("debug")
grid = mcrfpy.Grid(grid_x=30, grid_y=20)

# Initialize all as floor
print("\nInitializing 30x20 grid...")
for y in range(20):
    for x in range(30):
        grid.at(x, y).walkable = True

# Test path before obstacles
print("\nTest 1: Path with no obstacles")
path1 = grid.compute_astar_path(start_pos[0], start_pos[1], end_pos[0], end_pos[1])
print(f"  Path: {path1[:5]}...{path1[-3:] if len(path1) > 5 else ''}")
print(f"  Length: {len(path1)}")

# Add obstacles from the demo
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

print("\nAdding obstacles...")
wall_count = 0
for obstacle_group in obstacles:
    for x, y in obstacle_group:
        grid.at(x, y).walkable = False
        wall_count += 1
        if wall_count <= 5:
            print(f"  Wall at ({x}, {y})")

print(f"  Total walls added: {wall_count}")

# Check specific cells
print(f"\nChecking key positions:")
print(f"  Start ({start_pos[0]}, {start_pos[1]}): walkable={grid.at(start_pos[0], start_pos[1]).walkable}")
print(f"  End ({end_pos[0]}, {end_pos[1]}): walkable={grid.at(end_pos[0], end_pos[1]).walkable}")

# Check if path is blocked
print(f"\nChecking horizontal line at y=10:")
blocked_x = []
for x in range(30):
    if not grid.at(x, 10).walkable:
        blocked_x.append(x)

print(f"  Blocked x positions: {blocked_x}")

# Test path with obstacles
print("\nTest 2: Path with obstacles")
path2 = grid.compute_astar_path(start_pos[0], start_pos[1], end_pos[0], end_pos[1])
print(f"  Path: {path2}")
print(f"  Length: {len(path2)}")

# Check if there's any path at all
if not path2:
    print("\n  No path found! Checking why...")
    
    # Check if we can reach the vertical wall gap
    print("\n  Testing path to wall gap at (15, 8):")
    path_to_gap = grid.compute_astar_path(start_pos[0], start_pos[1], 15, 8)
    print(f"    Path to gap: {path_to_gap}")
    
    # Check from gap to end
    print("\n  Testing path from gap (15, 8) to end:")
    path_from_gap = grid.compute_astar_path(15, 8, end_pos[0], end_pos[1])
    print(f"    Path from gap: {path_from_gap}")

# Check walls more carefully
print("\nDetailed wall analysis:")
print("  Walls at x=25 (blocking end?):")
for y in range(5, 15):
    print(f"    ({25}, {y}): walkable={grid.at(25, y).walkable}")

def timer_cb(dt):
    sys.exit(0)

ui = mcrfpy.sceneUI("debug")
ui.append(grid)
mcrfpy.setScene("debug")
mcrfpy.setTimer("exit", timer_cb, 100)