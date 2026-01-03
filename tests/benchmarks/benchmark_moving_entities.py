"""
Benchmark: Moving Entities Performance Test

This benchmark measures McRogueFace's performance with 50 randomly moving
entities on a 100x100 grid.

Expected results:
- Should maintain 60 FPS
- Entity render time should be <3ms
- Grid render time will be higher due to constant updates (no dirty flag benefit)

Usage:
    ./build/mcrogueface --exec tests/benchmark_moving_entities.py

Press F3 to toggle performance overlay
Press ESC to exit
"""

import mcrfpy
import sys
import random

# Create the benchmark scene
benchmark = mcrfpy.Scene("benchmark")
benchmark.activate()

# Get scene UI
ui = benchmark.children

# Create a 100x100 grid
grid = mcrfpy.Grid(
    grid_size=(100, 100),
    pos=(0, 0),
    size=(1024, 768)
)

# Add color layer for floor pattern
color_layer = grid.add_layer("color", z_index=-1)

# Simple floor pattern
for x in range(100):
    for y in range(100):
        cell = grid.at(x, y)
        cell.tilesprite = 0
        color_layer.set(x, y, mcrfpy.Color(40, 40, 40, 255))

# Create 50 entities with random positions and velocities
entities = []
ENTITY_COUNT = 50

for i in range(ENTITY_COUNT):
    entity = mcrfpy.Entity(
        (random.randint(0, 99), random.randint(0, 99)),
        sprite_index=random.randint(10, 20),  # Use varied sprites
        grid=grid
    )

    # Give each entity a random velocity (stored as Python attributes)
    entity.velocity_x = random.uniform(-0.5, 0.5)
    entity.velocity_y = random.uniform(-0.5, 0.5)

    entities.append(entity)

ui.append(grid)

# Instructions caption
instructions = mcrfpy.Caption(
    text=f"Moving Entities Benchmark ({ENTITY_COUNT} entities)\n"
         "Press F3 for performance overlay\n"
         "Press ESC to exit\n"
         "Goal: 60 FPS with entities moving",
    pos=(10, 10),
    fill_color=(255, 255, 0, 255)
)
ui.append(instructions)

# Benchmark info
print("=" * 60)
print("MOVING ENTITIES BENCHMARK")
print("=" * 60)
print(f"Entity count: {ENTITY_COUNT}")
print("Grid size: 100x100 cells")
print("Expected FPS: 60")
print("")
print("Entities move randomly and bounce off walls.")
print("This tests entity rendering performance and position updates.")
print("")
print("Press F3 in-game to see real-time performance metrics.")
print("=" * 60)

# Exit handler
def handle_key(key, state):
    if key == "Escape" and state:
        print("\nBenchmark ended by user")
        sys.exit(0)

benchmark.on_key = handle_key

# Update entity positions
def update_entities(ms):
    dt = ms / 1000.0  # Convert to seconds

    for entity in entities:
        # Update position
        new_x = entity.x + entity.velocity_x
        new_y = entity.y + entity.velocity_y

        # Bounce off walls
        if new_x < 0 or new_x >= 100:
            entity.velocity_x = -entity.velocity_x
            new_x = max(0, min(99, new_x))

        if new_y < 0 or new_y >= 100:
            entity.velocity_y = -entity.velocity_y
            new_y = max(0, min(99, new_y))

        # Update entity position
        entity.x = new_x
        entity.y = new_y

# Run movement update every frame (16ms)
mcrfpy.setTimer("movement", update_entities, 16)

# Benchmark statistics
frame_count = 0
start_time = None

def benchmark_timer(ms):
    global frame_count, start_time

    if start_time is None:
        import time
        start_time = time.time()

    frame_count += 1

    # After 10 seconds, print summary
    import time
    elapsed = time.time() - start_time

    if elapsed >= 10.0:
        print("\n" + "=" * 60)
        print("BENCHMARK COMPLETE")
        print("=" * 60)
        print(f"Frames rendered: {frame_count}")
        print(f"Time elapsed: {elapsed:.2f}s")
        print(f"Average FPS: {frame_count / elapsed:.1f}")
        print(f"Entities: {ENTITY_COUNT}")
        print("")
        print("Check profiler overlay (F3) for detailed timing breakdown.")
        print("Entity render time and total frame time are key metrics.")
        print("=" * 60)
        # Don't exit - let user review

mcrfpy.setTimer("benchmark", benchmark_timer, 100)
