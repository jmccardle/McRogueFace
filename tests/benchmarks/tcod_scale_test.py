#!/usr/bin/env python3
"""
TCOD Scaling Benchmark - Test pathfinding/FOV on large grids

Tests whether TCOD operations scale acceptably on 1000x1000 grids,
to determine if TCOD data needs chunking or can stay as single logical grid.
"""
import mcrfpy
import sys
import time

# Grid sizes to test
SIZES = [(100, 100), (250, 250), (500, 500), (1000, 1000)]
ITERATIONS = 10

def benchmark_grid_size(grid_x, grid_y):
    """Benchmark TCOD operations for a given grid size"""
    results = {}

    # Create scene and grid
    scene_name = f"bench_{grid_x}x{grid_y}"
    mcrfpy.createScene(scene_name)
    ui = mcrfpy.sceneUI(scene_name)

    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)

    # Time grid creation
    t0 = time.perf_counter()
    grid = mcrfpy.Grid(
        pos=(0, 0),
        size=(800, 600),
        grid_size=(grid_x, grid_y),
        texture=texture
    )
    ui.append(grid)
    results['create_ms'] = (time.perf_counter() - t0) * 1000

    # Set up some walkability (maze-like pattern)
    t0 = time.perf_counter()
    for y in range(grid_y):
        for x in range(grid_x):
            cell = grid.at(x, y)
            # Create a simple maze: every 3rd cell is a wall
            cell.walkable = not ((x % 3 == 0) and (y % 3 == 0))
            cell.transparent = cell.walkable
    results['setup_walkability_ms'] = (time.perf_counter() - t0) * 1000

    # Add an entity for FOV perspective
    entity = mcrfpy.Entity(
        grid_pos=(grid_x // 2, grid_y // 2),
        texture=texture,
        sprite_index=64,
        grid=grid
    )

    # Benchmark FOV computation
    fov_times = []
    for i in range(ITERATIONS):
        # Move entity to different positions
        ex, ey = (i * 7) % (grid_x - 20) + 10, (i * 11) % (grid_y - 20) + 10
        t0 = time.perf_counter()
        grid.compute_fov(ex, ey, radius=15)
        fov_times.append((time.perf_counter() - t0) * 1000)
    results['fov_avg_ms'] = sum(fov_times) / len(fov_times)
    results['fov_max_ms'] = max(fov_times)

    # Benchmark A* pathfinding (corner to corner)
    path_times = []
    for i in range(ITERATIONS):
        # Path from near origin to near opposite corner
        x1, y1 = 1, 1
        x2, y2 = grid_x - 2, grid_y - 2
        t0 = time.perf_counter()
        path = grid.compute_astar_path(x1, y1, x2, y2)
        path_times.append((time.perf_counter() - t0) * 1000)
    results['astar_avg_ms'] = sum(path_times) / len(path_times)
    results['astar_max_ms'] = max(path_times)
    results['astar_path_len'] = len(path) if path else 0

    # Benchmark Dijkstra (full map distance calculation)
    dijkstra_times = []
    for i in range(ITERATIONS):
        cx, cy = grid_x // 2, grid_y // 2
        t0 = time.perf_counter()
        grid.compute_dijkstra(cx, cy)
        dijkstra_times.append((time.perf_counter() - t0) * 1000)
    results['dijkstra_avg_ms'] = sum(dijkstra_times) / len(dijkstra_times)
    results['dijkstra_max_ms'] = max(dijkstra_times)

    return results

def main():
    print("=" * 60)
    print("TCOD Scaling Benchmark")
    print("=" * 60)
    print(f"Testing grid sizes: {SIZES}")
    print(f"Iterations per test: {ITERATIONS}")
    print()

    all_results = {}

    for grid_x, grid_y in SIZES:
        print(f"\n--- Grid {grid_x}x{grid_y} ({grid_x * grid_y:,} cells) ---")
        try:
            results = benchmark_grid_size(grid_x, grid_y)
            all_results[f"{grid_x}x{grid_y}"] = results

            print(f"  Creation:     {results['create_ms']:.2f}ms")
            print(f"  Walkability:  {results['setup_walkability_ms']:.2f}ms")
            print(f"  FOV (r=15):   {results['fov_avg_ms']:.3f}ms avg, {results['fov_max_ms']:.3f}ms max")
            print(f"  A* path:      {results['astar_avg_ms']:.2f}ms avg, {results['astar_max_ms']:.2f}ms max (len={results['astar_path_len']})")
            print(f"  Dijkstra:     {results['dijkstra_avg_ms']:.2f}ms avg, {results['dijkstra_max_ms']:.2f}ms max")

        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[f"{grid_x}x{grid_y}"] = {'error': str(e)}

    print("\n" + "=" * 60)
    print("SUMMARY - Per-frame budget analysis (targeting 16ms for 60fps)")
    print("=" * 60)

    for size, results in all_results.items():
        if 'error' in results:
            print(f"  {size}: ERROR")
        else:
            total_logic = results['fov_avg_ms'] + results['astar_avg_ms']
            print(f"  {size}: FOV+A* = {total_logic:.2f}ms ({total_logic/16*100:.0f}% of frame budget)")

    print("\nDone.")
    sys.exit(0)

# Run immediately (no timer needed for this test)
mcrfpy.createScene("init")
mcrfpy.setScene("init")

# Use a timer to let the engine initialize
def run_benchmark(runtime):
    main()

mcrfpy.setTimer("bench", run_benchmark, 100)
