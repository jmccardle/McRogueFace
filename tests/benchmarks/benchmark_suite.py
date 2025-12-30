#!/usr/bin/env python3
"""Comprehensive Performance Benchmark Suite for McRogueFace (#104, #144)

Runs 6 benchmark scenarios to establish baseline performance metrics:
1. Empty scene - Pure engine overhead
2. Static UI - 100 frames, no animation (best case for caching)
3. Animated UI - 100 frames, all animating (worst case for caching)
4. Mixed UI - 100 frames, 10 animating (realistic case)
5. Deep hierarchy - 5 levels of nesting (propagation cost)
6. Grid stress - Large grid with entities (known bottleneck)

Usage:
    ./mcrogueface --headless --exec tests/benchmarks/benchmark_suite.py

Results are printed to stdout in a format suitable for tracking over time.
"""

import mcrfpy
import sys
import random

# Benchmark configuration
WARMUP_FRAMES = 30       # Frames to skip before measuring
MEASURE_FRAMES = 120     # Frames to measure (2 seconds at 60fps)
FRAME_BUDGET_MS = 16.67  # Target: 60 FPS

# Storage for results
results = {}
current_scenario = None
frame_count = 0
metrics_samples = []


def collect_metrics(runtime):
    """Timer callback to collect metrics each frame."""
    global frame_count, metrics_samples

    frame_count += 1

    # Skip warmup frames
    if frame_count <= WARMUP_FRAMES:
        return

    # Collect sample
    m = mcrfpy.getMetrics()
    metrics_samples.append({
        'frame_time': m['frame_time'],
        'avg_frame_time': m['avg_frame_time'],
        'fps': m['fps'],
        'draw_calls': m['draw_calls'],
        'ui_elements': m['ui_elements'],
        'visible_elements': m['visible_elements'],
        'grid_render_time': m['grid_render_time'],
        'entity_render_time': m['entity_render_time'],
        'python_time': m['python_time'],
        'animation_time': m['animation_time'],
        'grid_cells_rendered': m['grid_cells_rendered'],
        'entities_rendered': m['entities_rendered'],
    })

    # Check if we have enough samples
    if len(metrics_samples) >= MEASURE_FRAMES:
        finish_scenario()


def finish_scenario():
    """Calculate statistics and store results for current scenario."""
    global results, current_scenario, metrics_samples

    mcrfpy.delTimer("benchmark_collect")

    if not metrics_samples:
        print(f"  WARNING: No samples collected for {current_scenario}")
        return

    # Calculate averages
    n = len(metrics_samples)
    avg = lambda key: sum(s[key] for s in metrics_samples) / n

    results[current_scenario] = {
        'samples': n,
        'avg_frame_time': avg('frame_time'),
        'avg_fps': avg('fps'),
        'avg_draw_calls': avg('draw_calls'),
        'avg_ui_elements': avg('ui_elements'),
        'avg_grid_render_time': avg('grid_render_time'),
        'avg_entity_render_time': avg('entity_render_time'),
        'avg_python_time': avg('python_time'),
        'avg_animation_time': avg('animation_time'),
        'avg_grid_cells': avg('grid_cells_rendered'),
        'avg_entities': avg('entities_rendered'),
        'max_frame_time': max(s['frame_time'] for s in metrics_samples),
        'min_frame_time': min(s['frame_time'] for s in metrics_samples),
    }

    # Calculate percentage breakdown
    r = results[current_scenario]
    total = r['avg_frame_time']
    if total > 0:
        r['pct_grid'] = (r['avg_grid_render_time'] / total) * 100
        r['pct_entity'] = (r['avg_entity_render_time'] / total) * 100
        r['pct_python'] = (r['avg_python_time'] / total) * 100
        r['pct_animation'] = (r['avg_animation_time'] / total) * 100
        r['pct_other'] = 100 - r['pct_grid'] - r['pct_entity'] - r['pct_python'] - r['pct_animation']

    print(f"  Completed: {n} samples, avg {r['avg_frame_time']:.2f}ms ({r['avg_fps']:.0f} FPS)")

    # Run next scenario
    run_next_scenario()


def run_next_scenario():
    """Run the next benchmark scenario in sequence."""
    global current_scenario, frame_count, metrics_samples

    scenarios = [
        ('1_empty', setup_empty_scene),
        ('2_static_100', setup_static_100),
        ('3_animated_100', setup_animated_100),
        ('4_mixed_100', setup_mixed_100),
        ('5_deep_hierarchy', setup_deep_hierarchy),
        ('6_grid_stress', setup_grid_stress),
    ]

    # Find current index
    current_idx = -1
    if current_scenario:
        for i, (name, _) in enumerate(scenarios):
            if name == current_scenario:
                current_idx = i
                break

    # Move to next
    next_idx = current_idx + 1

    if next_idx >= len(scenarios):
        # All done
        print_results()
        return

    # Setup next scenario
    current_scenario = scenarios[next_idx][0]
    frame_count = 0
    metrics_samples = []

    print(f"\n[{next_idx + 1}/{len(scenarios)}] Running: {current_scenario}")

    # Run setup function
    scenarios[next_idx][1]()

    # Start collection timer (runs every frame)
    mcrfpy.setTimer("benchmark_collect", collect_metrics, 1)


# ============================================================================
# Scenario Setup Functions
# ============================================================================

def setup_empty_scene():
    """Scenario 1: Empty scene - pure engine overhead."""
    mcrfpy.createScene("bench_empty")
    mcrfpy.setScene("bench_empty")


def setup_static_100():
    """Scenario 2: 100 static frames - best case for caching."""
    mcrfpy.createScene("bench_static")
    ui = mcrfpy.sceneUI("bench_static")

    # Create 100 frames in a 10x10 grid
    for i in range(100):
        x = (i % 10) * 100 + 12
        y = (i // 10) * 70 + 12
        frame = mcrfpy.Frame(pos=(x, y), size=(80, 55))
        frame.fill_color = mcrfpy.Color(50 + i, 100, 150)
        frame.outline = 2
        frame.outline_color = mcrfpy.Color(255, 255, 255)

        # Add a caption child
        cap = mcrfpy.Caption(text=f"F{i}", pos=(5, 5))
        cap.fill_color = mcrfpy.Color(255, 255, 255)
        frame.children.append(cap)

        ui.append(frame)

    mcrfpy.setScene("bench_static")


def setup_animated_100():
    """Scenario 3: 100 frames all animating - worst case for caching."""
    mcrfpy.createScene("bench_animated")
    ui = mcrfpy.sceneUI("bench_animated")

    frames = []
    for i in range(100):
        x = (i % 10) * 100 + 12
        y = (i // 10) * 70 + 12
        frame = mcrfpy.Frame(pos=(x, y), size=(80, 55))
        frame.fill_color = mcrfpy.Color(50 + i, 100, 150)
        frames.append(frame)
        ui.append(frame)

    mcrfpy.setScene("bench_animated")

    # Start animations on all frames (color animation = content change)
    for i, frame in enumerate(frames):
        # Animate fill color - this dirties the frame
        target_r = (i * 17) % 256
        anim = mcrfpy.Animation("fill_color.r", float(target_r), 2.0, "linear")
        anim.start(frame)


def setup_mixed_100():
    """Scenario 4: 100 frames, only 10 animating - realistic case."""
    mcrfpy.createScene("bench_mixed")
    ui = mcrfpy.sceneUI("bench_mixed")

    frames = []
    for i in range(100):
        x = (i % 10) * 100 + 12
        y = (i // 10) * 70 + 12
        frame = mcrfpy.Frame(pos=(x, y), size=(80, 55))
        frame.fill_color = mcrfpy.Color(50 + i, 100, 150)
        frames.append(frame)
        ui.append(frame)

    mcrfpy.setScene("bench_mixed")

    # Animate only 10 frames (every 10th)
    for i in range(0, 100, 10):
        frame = frames[i]
        anim = mcrfpy.Animation("fill_color.r", 255.0, 2.0, "easeInOut")
        anim.start(frame)


def setup_deep_hierarchy():
    """Scenario 5: 5 levels of nesting - test dirty flag propagation cost."""
    mcrfpy.createScene("bench_deep")
    ui = mcrfpy.sceneUI("bench_deep")

    # Create 10 trees, each with 5 levels of nesting
    deepest_frames = []

    for tree in range(10):
        x_offset = tree * 100 + 12
        current_parent = None

        for level in range(5):
            frame = mcrfpy.Frame(
                pos=(10, 10) if level > 0 else (x_offset, 100),
                size=(80 - level * 10, 500 - level * 80)
            )
            frame.fill_color = mcrfpy.Color(50 + level * 40, 100, 200 - level * 30)
            frame.outline = 1

            if current_parent is None:
                ui.append(frame)
            else:
                current_parent.children.append(frame)

            current_parent = frame

            if level == 4:  # Deepest level
                deepest_frames.append(frame)

    mcrfpy.setScene("bench_deep")

    # Animate the deepest frames - tests propagation up the hierarchy
    for frame in deepest_frames:
        anim = mcrfpy.Animation("fill_color.g", 255.0, 2.0, "linear")
        anim.start(frame)


def setup_grid_stress():
    """Scenario 6: Large grid with entities - known performance bottleneck."""
    mcrfpy.createScene("bench_grid")
    ui = mcrfpy.sceneUI("bench_grid")

    # Create a 50x50 grid (2500 cells)
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(50, 50), size=(700, 700))
    grid.zoom = 0.75
    grid.center = (400, 400)  # Center view
    ui.append(grid)

    # Add color layer and fill with alternating colors
    color_layer = grid.add_layer("color", z_index=-1)
    for y in range(50):
        for x in range(50):
            if (x + y) % 2 == 0:
                color_layer.set(x, y, mcrfpy.Color(60, 60, 80))
            else:
                color_layer.set(x, y, mcrfpy.Color(40, 40, 60))

    # Add 50 entities
    try:
        texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

        for i in range(50):
            # Entity takes tuple position and keyword args
            pos = (random.randint(5, 45), random.randint(5, 45))
            entity = mcrfpy.Entity(pos, texture=texture, sprite_index=random.randint(0, 100), grid=grid)
            grid.entities.append(entity)
    except Exception as e:
        print(f"  Note: Could not create entities: {e}")

    mcrfpy.setScene("bench_grid")


# ============================================================================
# Results Output
# ============================================================================

def print_results():
    """Print final benchmark results."""
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    print(f"\n{'Scenario':<20} {'Avg FPS':>8} {'Avg ms':>8} {'Max ms':>8} {'Draw Calls':>10}")
    print("-" * 70)

    for name, r in results.items():
        print(f"{name:<20} {r['avg_fps']:>8.1f} {r['avg_frame_time']:>8.2f} {r['max_frame_time']:>8.2f} {r['avg_draw_calls']:>10.0f}")

    print("\n" + "-" * 70)
    print("TIMING BREAKDOWN (% of frame time)")
    print("-" * 70)
    print(f"{'Scenario':<20} {'Grid':>8} {'Entity':>8} {'Python':>8} {'Anim':>8} {'Other':>8}")
    print("-" * 70)

    for name, r in results.items():
        if 'pct_grid' in r:
            print(f"{name:<20} {r['pct_grid']:>7.1f}% {r['pct_entity']:>7.1f}% {r['pct_python']:>7.1f}% {r['pct_animation']:>7.1f}% {r['pct_other']:>7.1f}%")

    print("\n" + "=" * 70)

    # Performance assessment
    print("\nPERFORMANCE ASSESSMENT:")
    for name, r in results.items():
        status = "PASS" if r['avg_frame_time'] < FRAME_BUDGET_MS else "OVER BUDGET"
        print(f"  {name}: {status} ({r['avg_frame_time']:.2f}ms vs {FRAME_BUDGET_MS:.2f}ms budget)")

    print("\nBenchmark complete.")
    sys.exit(0)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("McRogueFace Performance Benchmark Suite")
    print("=" * 70)
    print(f"Configuration: {WARMUP_FRAMES} warmup frames, {MEASURE_FRAMES} measurement frames")
    print(f"Target: {FRAME_BUDGET_MS:.2f}ms per frame (60 FPS)")

    # Start the benchmark sequence
    run_next_scenario()
