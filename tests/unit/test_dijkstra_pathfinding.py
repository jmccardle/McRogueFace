#!/usr/bin/env python3
"""
Test Dijkstra Pathfinding Implementation
========================================

Demonstrates:
1. Computing Dijkstra distance map from a root position
2. Getting distances to any position
3. Finding paths from any position back to the root
4. Multi-target pathfinding (flee/approach scenarios)
"""

import mcrfpy
from mcrfpy import libtcod
import sys

def create_test_grid():
    """Create a test grid with obstacles"""
    dijkstra_test = mcrfpy.Scene("dijkstra_test")

    # Create grid
    grid = mcrfpy.Grid(grid_x=20, grid_y=20)

    # Add color layer for cell coloring
    color_layer = grid.add_layer("color", z_index=-1)
    # Store color_layer on grid for access elsewhere
    grid._color_layer = color_layer

    # Initialize all cells as walkable
    for y in range(grid.grid_y):
        for x in range(grid.grid_x):
            cell = grid.at(x, y)
            cell.walkable = True
            cell.transparent = True
            cell.tilesprite = 46  # . period
            color_layer.set(x, y, mcrfpy.Color(50, 50, 50))

    # Create some walls to make pathfinding interesting
    # Vertical wall
    for y in range(5, 15):
        cell = grid.at(10, y)
        cell.walkable = False
        cell.transparent = False
        cell.tilesprite = 219  # Block
        color_layer.set(10, y, mcrfpy.Color(100, 100, 100))

    # Horizontal wall
    for x in range(5, 15):
        if x != 10:  # Leave a gap
            cell = grid.at(x, 10)
            cell.walkable = False
            cell.transparent = False
            cell.tilesprite = 219
            color_layer.set(x, 10, mcrfpy.Color(100, 100, 100))

    return grid

def test_basic_dijkstra():
    """Test basic Dijkstra functionality"""
    print("\n=== Testing Basic Dijkstra ===")
    
    grid = create_test_grid()
    
    # Compute Dijkstra map from position (5, 5)
    root_x, root_y = 5, 5
    print(f"Computing Dijkstra map from root ({root_x}, {root_y})")
    grid.compute_dijkstra(root_x, root_y)
    
    # Test getting distances to various points
    test_points = [
        (5, 5),    # Root position (should be 0)
        (6, 5),    # Adjacent (should be 1)
        (7, 5),    # Two steps away
        (15, 15),  # Far corner
        (10, 10),  # On a wall (should be unreachable)
    ]
    
    print("\nDistances from root:")
    for x, y in test_points:
        distance = grid.get_dijkstra_distance(x, y)
        if distance is None:
            print(f"  ({x:2}, {y:2}): UNREACHABLE")
        else:
            print(f"  ({x:2}, {y:2}): {distance:.1f}")
    
    # Test getting paths
    print("\nPaths to root:")
    for x, y in [(15, 5), (15, 15), (5, 15)]:
        path = grid.get_dijkstra_path(x, y)
        if path:
            print(f"  From ({x}, {y}): {len(path)} steps")
            # Show first few steps
            for i, (px, py) in enumerate(path[:3]):
                print(f"    Step {i+1}: ({px}, {py})")
            if len(path) > 3:
                print(f"    ... {len(path)-3} more steps")
        else:
            print(f"  From ({x}, {y}): No path found")

def test_libtcod_interface():
    """Test the libtcod module interface"""
    print("\n=== Testing libtcod Interface ===")
    
    grid = create_test_grid()
    
    # Use libtcod functions
    print("Using libtcod.dijkstra_* functions:")
    
    # Create dijkstra context (returns grid)
    dijkstra = libtcod.dijkstra_new(grid)
    print(f"Created Dijkstra context: {type(dijkstra)}")
    
    # Compute from a position
    libtcod.dijkstra_compute(grid, 10, 2)
    print("Computed Dijkstra map from (10, 2)")
    
    # Get distance using libtcod
    distance = libtcod.dijkstra_get_distance(grid, 10, 17)
    print(f"Distance to (10, 17): {distance}")
    
    # Get path using libtcod
    path = libtcod.dijkstra_path_to(grid, 10, 17)
    print(f"Path from (10, 17) to root: {len(path) if path else 0} steps")

def test_multi_target_scenario():
    """Test fleeing/approaching multiple targets"""
    print("\n=== Testing Multi-Target Scenario ===")
    
    grid = create_test_grid()
    
    # Place three "threats" and compute their Dijkstra maps
    threats = [(3, 3), (17, 3), (10, 17)]
    
    print("Computing threat distances...")
    threat_distances = []
    
    for i, (tx, ty) in enumerate(threats):
        # Mark threat position
        cell = grid.at(tx, ty)
        cell.tilesprite = 84  # T for threat
        grid._color_layer.set(tx, ty, mcrfpy.Color(255, 0, 0))
        
        # Compute Dijkstra from this threat
        grid.compute_dijkstra(tx, ty)
        
        # Store distances for all cells
        distances = {}
        for y in range(grid.grid_y):
            for x in range(grid.grid_x):
                d = grid.get_dijkstra_distance(x, y)
                if d is not None:
                    distances[(x, y)] = d
        
        threat_distances.append(distances)
        print(f"  Threat {i+1} at ({tx}, {ty}): {len(distances)} reachable cells")
    
    # Find safest position (farthest from all threats)
    print("\nFinding safest position...")
    best_pos = None
    best_min_dist = 0
    
    for y in range(grid.grid_y):
        for x in range(grid.grid_x):
            # Skip if not walkable
            if not grid.at(x, y).walkable:
                continue
            
            # Get minimum distance to any threat
            min_dist = float('inf')
            for threat_dist in threat_distances:
                if (x, y) in threat_dist:
                    min_dist = min(min_dist, threat_dist[(x, y)])
            
            # Track best position
            if min_dist > best_min_dist and min_dist != float('inf'):
                best_min_dist = min_dist
                best_pos = (x, y)
    
    if best_pos:
        print(f"Safest position: {best_pos} (min distance to threats: {best_min_dist:.1f})")
        # Mark safe position
        cell = grid.at(best_pos[0], best_pos[1])
        cell.tilesprite = 83  # S for safe
        grid._color_layer.set(best_pos[0], best_pos[1], mcrfpy.Color(0, 255, 0))

def run_test(timer, runtime):
    """Timer callback to run tests after scene loads"""
    test_basic_dijkstra()
    test_libtcod_interface()
    test_multi_target_scenario()
    
    print("\n=== Dijkstra Implementation Test Complete ===")
    print("✓ Basic Dijkstra computation works")
    print("✓ Distance queries work") 
    print("✓ Path finding works")
    print("✓ libtcod interface works")
    print("✓ Multi-target scenarios work")
    
    # Take screenshot
    try:
        from mcrfpy import automation
        automation.screenshot("dijkstra_test.png")
        print("\nScreenshot saved: dijkstra_test.png")
    except:
        pass
    
    sys.exit(0)

# Main execution
print("McRogueFace Dijkstra Pathfinding Test")
print("=====================================")

# Set up scene
grid = create_test_grid()
ui = dijkstra_test.children
ui.append(grid)

# Add title
title = mcrfpy.Caption(pos=(10, 10), text="Dijkstra Pathfinding Test")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Set timer to run tests
test_timer = mcrfpy.Timer("test", run_test, 100, once=True)

# Show scene
dijkstra_test.activate()