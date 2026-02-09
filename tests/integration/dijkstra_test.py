#!/usr/bin/env python3
"""
Dijkstra Pathfinding Test - Headless
====================================

Tests all Dijkstra functionality and generates a screenshot.
"""

import mcrfpy
from mcrfpy import automation
import sys

def create_test_map():
    """Create a test map with obstacles"""
    dijkstra_test = mcrfpy.Scene("dijkstra_test")
    
    # Create grid
    grid = mcrfpy.Grid(grid_w=20, grid_h=12)
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    
    # Initialize all cells as walkable floor
    for y in range(12):
        for x in range(20):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
            grid.at(x, y).color = mcrfpy.Color(200, 200, 220)
    
    # Add walls to create interesting paths
    walls = [
        # Vertical wall in the middle
        (10, 1), (10, 2), (10, 3), (10, 4), (10, 5), (10, 6), (10, 7), (10, 8),
        # Horizontal walls
        (2, 6), (3, 6), (4, 6), (5, 6), (6, 6),
        (14, 6), (15, 6), (16, 6), (17, 6),
        # Some scattered obstacles
        (5, 2), (15, 2), (5, 9), (15, 9)
    ]
    
    for x, y in walls:
        grid.at(x, y).walkable = False
        grid.at(x, y).color = mcrfpy.Color(60, 30, 30)
    
    # Place test entities
    entities = []
    positions = [(2, 2), (17, 2), (9, 10)]
    colors = [
        mcrfpy.Color(255, 100, 100),  # Red
        mcrfpy.Color(100, 255, 100),  # Green
        mcrfpy.Color(100, 100, 255)   # Blue
    ]
    
    for i, (x, y) in enumerate(positions):
        entity = mcrfpy.Entity(x, y)
        entity.sprite_index = 49 + i  # '1', '2', '3'
        grid.entities.append(entity)
        entities.append(entity)
        # Mark entity positions
        grid.at(x, y).color = colors[i]
    
    return grid, entities

def test_dijkstra(grid, entities):
    """Test Dijkstra pathfinding between all entity pairs"""
    results = []
    
    for i in range(len(entities)):
        for j in range(len(entities)):
            if i != j:
                # Compute Dijkstra from entity i
                e1 = entities[i]
                e2 = entities[j]
                grid.compute_dijkstra(int(e1.x), int(e1.y))
                
                # Get distance and path to entity j
                distance = grid.get_dijkstra_distance(int(e2.x), int(e2.y))
                path = grid.get_dijkstra_path(int(e2.x), int(e2.y))
                
                if path:
                    results.append(f"Path {i+1}→{j+1}: {len(path)} steps, {distance:.1f} units")
                    
                    # Color one interesting path
                    if i == 0 and j == 2:  # Path from 1 to 3
                        for x, y in path[1:-1]:  # Skip endpoints
                            if grid.at(x, y).walkable:
                                grid.at(x, y).color = mcrfpy.Color(200, 250, 220)
                else:
                    results.append(f"Path {i+1}→{j+1}: No path found!")
    
    return results

def run_test(timer, runtime):
    """Timer callback to run tests and take screenshot"""
    # Run pathfinding tests
    results = test_dijkstra(grid, entities)

    # Update display with results
    y_pos = 380
    for result in results:
        caption = mcrfpy.Caption(result, 50, y_pos)
        caption.fill_color = mcrfpy.Color(200, 200, 200)
        ui.append(caption)
        y_pos += 20

    # Take screenshot (one-shot timer)
    screenshot_timer = mcrfpy.Timer("screenshot", lambda t, rt: take_screenshot(), 500, once=True)

def take_screenshot():
    """Take screenshot and exit"""
    try:
        automation.screenshot("dijkstra_test.png")
        print("Screenshot saved: dijkstra_test.png")
    except Exception as e:
        print(f"Screenshot failed: {e}")
    
    # Exit
    sys.exit(0)

# Create test map
print("Creating Dijkstra pathfinding test...")
grid, entities = create_test_map()

# Set up UI
ui = dijkstra_test.children
ui.append(grid)

# Position and scale grid
grid.position = (50, 50)
grid.size = (500, 300)

# Add title
title = mcrfpy.Caption(pos=(200, 10), text="Dijkstra Pathfinding Test")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Add legend
legend = mcrfpy.Caption(pos=(50, 360), text="Red=Entity1  Green=Entity2  Blue=Entity3  Cyan=Path 1→3")
legend.fill_color = mcrfpy.Color(180, 180, 180)
ui.append(legend)

# Set scene
dijkstra_test.activate()

# Run test after scene loads (one-shot timer)
test_timer = mcrfpy.Timer("test", run_test, 100, once=True)

print("Running Dijkstra tests...")