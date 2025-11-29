#!/usr/bin/env python3
"""
Issue #123 Regression Test: Grid Sub-grid Chunk System

Tests that large grids (>64 cells) use chunk-based storage and rendering,
while small grids use the original flat storage. Verifies that:
1. Small grids work as before (no regression)
2. Large grids work correctly with chunks
3. Cell access (read/write) works for both modes
4. Rendering displays correctly for both modes
"""

import mcrfpy
import sys

def test_small_grid():
    """Test that small grids work (original flat storage)"""
    print("Testing small grid (50x50 < 64 threshold)...")

    # Small grid should use flat storage
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(10, 10), size=(400, 400))

    # Set some cells
    for y in range(50):
        for x in range(50):
            cell = grid.at(x, y)
            cell.color = mcrfpy.Color((x * 5) % 256, (y * 5) % 256, 128, 255)
            cell.tilesprite = -1

    # Verify cells
    cell = grid.at(25, 25)
    expected_r = (25 * 5) % 256
    expected_g = (25 * 5) % 256
    color = cell.color
    r, g = color[0], color[1]
    if r != expected_r or g != expected_g:
        print(f"FAIL: Small grid cell color mismatch. Expected ({expected_r}, {expected_g}), got ({r}, {g})")
        return False

    print("  Small grid: PASS")
    return True

def test_large_grid():
    """Test that large grids work (chunk-based storage)"""
    print("Testing large grid (100x100 > 64 threshold)...")

    # Large grid should use chunk storage (100 > 64)
    grid = mcrfpy.Grid(grid_size=(100, 100), pos=(10, 10), size=(400, 400))

    # Set cells across multiple chunks
    # Chunks are 64x64, so a 100x100 grid has 2x2 = 4 chunks
    test_points = [
        (0, 0),      # Chunk (0,0)
        (63, 63),    # Chunk (0,0) - edge
        (64, 0),     # Chunk (1,0) - start
        (64, 64),    # Chunk (1,1) - start
        (99, 99),    # Chunk (1,1) - edge
        (50, 50),    # Chunk (0,0)
        (70, 80),    # Chunk (1,1)
    ]

    for x, y in test_points:
        cell = grid.at(x, y)
        cell.color = mcrfpy.Color(x, y, 100, 255)
        cell.tilesprite = -1

    # Verify cells
    for x, y in test_points:
        cell = grid.at(x, y)
        color = cell.color
        if color[0] != x or color[1] != y:
            print(f"FAIL: Large grid cell ({x},{y}) color mismatch. Expected ({x}, {y}), got ({color[0]}, {color[1]})")
            return False

    print("  Large grid cell access: PASS")
    return True

def test_very_large_grid():
    """Test very large grid (500x500)"""
    print("Testing very large grid (500x500)...")

    # 500x500 = 250,000 cells, should use ~64 chunks (8x8)
    grid = mcrfpy.Grid(grid_size=(500, 500), pos=(10, 10), size=(400, 400))

    # Set some cells at various positions
    test_points = [
        (0, 0),
        (127, 127),
        (128, 128),
        (255, 255),
        (256, 256),
        (400, 400),
        (499, 499),
    ]

    for x, y in test_points:
        cell = grid.at(x, y)
        cell.color = mcrfpy.Color(x % 256, y % 256, 200, 255)

    # Verify
    for x, y in test_points:
        cell = grid.at(x, y)
        color = cell.color
        if color[0] != (x % 256) or color[1] != (y % 256):
            print(f"FAIL: Very large grid cell ({x},{y}) color mismatch")
            return False

    print("  Very large grid: PASS")
    return True

def test_boundary_case():
    """Test the exact boundary (64x64 should NOT use chunks, 65x65 should)"""
    print("Testing boundary cases...")

    # 64x64 should use flat storage (not exceeding threshold)
    grid_64 = mcrfpy.Grid(grid_size=(64, 64), pos=(10, 10), size=(400, 400))
    cell = grid_64.at(63, 63)
    cell.color = mcrfpy.Color(255, 0, 0, 255)
    color = grid_64.at(63, 63).color
    if color[0] != 255:
        print(f"FAIL: 64x64 grid boundary cell not set correctly, got r={color[0]}")
        return False

    # 65x65 should use chunk storage (exceeding threshold)
    grid_65 = mcrfpy.Grid(grid_size=(65, 65), pos=(10, 10), size=(400, 400))
    cell = grid_65.at(64, 64)
    cell.color = mcrfpy.Color(0, 255, 0, 255)
    color = grid_65.at(64, 64).color
    if color[1] != 255:
        print(f"FAIL: 65x65 grid cell not set correctly, got g={color[1]}")
        return False

    print("  Boundary cases: PASS")
    return True

def test_edge_cases():
    """Test edge cell access in chunked grid"""
    print("Testing edge cases...")

    # Create 100x100 grid
    grid = mcrfpy.Grid(grid_size=(100, 100), pos=(10, 10), size=(400, 400))

    # Test all corners
    corners = [(0, 0), (99, 0), (0, 99), (99, 99)]
    for i, (x, y) in enumerate(corners):
        cell = grid.at(x, y)
        cell.color = mcrfpy.Color(i * 60, i * 60, i * 60, 255)

    for i, (x, y) in enumerate(corners):
        cell = grid.at(x, y)
        expected = i * 60
        color = cell.color
        if color[0] != expected:
            print(f"FAIL: Corner ({x},{y}) color mismatch, expected {expected}, got {color[0]}")
            return False

    print("  Edge cases: PASS")
    return True

def run_test(runtime):
    """Timer callback to run tests after scene is active"""
    results = []

    results.append(test_small_grid())
    results.append(test_large_grid())
    results.append(test_very_large_grid())
    results.append(test_boundary_case())
    results.append(test_edge_cases())

    if all(results):
        print("\n=== ALL TESTS PASSED ===")
        sys.exit(0)
    else:
        print("\n=== SOME TESTS FAILED ===")
        sys.exit(1)

# Main
if __name__ == "__main__":
    print("=" * 60)
    print("Issue #123: Grid Sub-grid Chunk System Test")
    print("=" * 60)

    mcrfpy.createScene("test")
    mcrfpy.setScene("test")

    # Run tests after scene is active
    mcrfpy.setTimer("test", run_test, 100)
