"""
Benchmark: Static Grid Performance Test

This benchmark measures McRogueFace's grid rendering performance with a static
100x100 grid. The goal is 60 FPS with minimal CPU usage.

Expected results:
- 60 FPS (16.6ms per frame)
- Grid render time should be <2ms after dirty flag optimization
- Currently will be higher (likely 8-12ms) - this establishes baseline

Usage:
    ./build/mcrogueface --exec tests/benchmark_static_grid.py

Press F3 to toggle performance overlay
Press ESC to exit
"""

import mcrfpy
import sys

# Create the benchmark scene
mcrfpy.createScene("benchmark")
mcrfpy.setScene("benchmark")

# Get scene UI
ui = mcrfpy.sceneUI("benchmark")

# Create a 100x100 grid with default texture
grid = mcrfpy.Grid(
    grid_size=(100, 100),
    pos=(0, 0),
    size=(1024, 768)
)

# Fill grid with varied tile patterns to ensure realistic rendering
for x in range(100):
    for y in range(100):
        cell = grid.at((x, y))
        # Checkerboard pattern with different sprites
        if (x + y) % 2 == 0:
            cell.tilesprite = 0
            cell.color = (50, 50, 50, 255)
        else:
            cell.tilesprite = 1
            cell.color = (70, 70, 70, 255)

        # Add some variation
        if x % 10 == 0 or y % 10 == 0:
            cell.tilesprite = 2
            cell.color = (100, 100, 100, 255)

# Add grid to scene
ui.append(grid)

# Instructions caption
instructions = mcrfpy.Caption(
    text="Static Grid Benchmark (100x100)\n"
         "Press F3 for performance overlay\n"
         "Press ESC to exit\n"
         "Goal: 60 FPS with low grid render time",
    pos=(10, 10),
    fill_color=(255, 255, 0, 255)
)
ui.append(instructions)

# Benchmark info
print("=" * 60)
print("STATIC GRID BENCHMARK")
print("=" * 60)
print("Grid size: 100x100 cells")
print("Expected FPS: 60")
print("Tiles rendered: ~1024 visible cells per frame")
print("")
print("This benchmark establishes baseline grid rendering performance.")
print("After dirty flag optimization, grid render time should drop")
print("significantly for static content.")
print("")
print("Press F3 in-game to see real-time performance metrics.")
print("=" * 60)

# Exit handler
def handle_key(key, state):
    if key == "Escape" and state:
        print("\nBenchmark ended by user")
        sys.exit(0)

mcrfpy.keypressScene(handle_key)

# Run for 10 seconds then provide summary
frame_count = 0
start_time = None

def benchmark_timer(ms):
    global frame_count, start_time

    if start_time is None:
        import time
        start_time = time.time()

    frame_count += 1

    # After 10 seconds, print summary and exit
    import time
    elapsed = time.time() - start_time

    if elapsed >= 10.0:
        print("\n" + "=" * 60)
        print("BENCHMARK COMPLETE")
        print("=" * 60)
        print(f"Frames rendered: {frame_count}")
        print(f"Time elapsed: {elapsed:.2f}s")
        print(f"Average FPS: {frame_count / elapsed:.1f}")
        print("")
        print("Check profiler overlay (F3) for detailed timing breakdown.")
        print("Grid render time is the key metric for optimization.")
        print("=" * 60)
        # Don't exit automatically - let user review with F3
        # sys.exit(0)

# Update every 100ms
mcrfpy.setTimer("benchmark", benchmark_timer, 100)
