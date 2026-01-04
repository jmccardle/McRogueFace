#!/usr/bin/env python3
"""
Layer Performance Benchmark for McRogueFace (#147, #148, #123)

Uses C++ benchmark logger (start_benchmark/end_benchmark) for accurate timing.
Results written to JSON files for analysis.

Compares rendering performance between:
1. ColorLayer with per-cell modifications (no caching benefit)
2. ColorLayer with dirty flag caching (static after fill)
3. Various layer configurations

NOTE: The old grid.at(x,y).color API no longer exists. All color operations
now go through the ColorLayer system. This benchmark compares different
layer usage patterns to measure caching effectiveness.

Usage:
    ./mcrogueface --exec tests/benchmarks/layer_performance_test.py
    # Results in benchmark_*.json files
"""

import mcrfpy
import sys
import os
import json

# Test configuration
GRID_SIZE = 100  # 100x100 = 10,000 cells
MEASURE_FRAMES = 120
WARMUP_FRAMES = 30

current_test = None
frame_count = 0
test_results = {}  # Store filenames for each test


def run_test_phase(timer, runtime):
    """Run through warmup and measurement phases."""
    global frame_count

    frame_count += 1

    if frame_count == WARMUP_FRAMES:
        # Start benchmark after warmup
        mcrfpy.start_benchmark()
        mcrfpy.log_benchmark(f"Test: {current_test}")

    elif frame_count == WARMUP_FRAMES + MEASURE_FRAMES:
        # End benchmark and store filename
        filename = mcrfpy.end_benchmark()
        test_results[current_test] = filename
        print(f"  {current_test}: saved to {filename}")

        timer.stop()
        run_next_test()


def run_next_test():
    """Run next test in sequence."""
    global current_test, frame_count

    tests = [
        ('1_base_static', setup_base_layer_static),
        ('2_base_modified', setup_base_layer_modified),
        ('3_layer_static', setup_color_layer_static),
        ('4_layer_modified', setup_color_layer_modified),
        ('5_tile_static', setup_tile_layer_static),
        ('6_tile_modified', setup_tile_layer_modified),
        ('7_multi_layer', setup_multi_layer_static),
        ('8_comparison', setup_base_vs_layer_comparison),
    ]

    # Find current
    current_idx = -1
    if current_test:
        for i, (name, _) in enumerate(tests):
            if name == current_test:
                current_idx = i
                break

    next_idx = current_idx + 1

    if next_idx >= len(tests):
        analyze_results()
        return

    current_test = tests[next_idx][0]
    frame_count = 0

    print(f"\n[{next_idx + 1}/{len(tests)}] Running: {current_test}")
    tests[next_idx][1]()

    global test_phase_timer
    test_phase_timer = mcrfpy.Timer("test_phase", run_test_phase, 1)


# ============================================================================
# Test Scenarios
# ============================================================================

def setup_base_layer_static():
    """ColorLayer with per-cell set() calls - static after initial fill."""
    test_base_static = mcrfpy.Scene("test_base_static")
    ui = test_base_static.children

    grid = mcrfpy.Grid(grid_size=(GRID_SIZE, GRID_SIZE),
                       pos=(10, 10), size=(600, 600))
    ui.append(grid)

    # Fill using ColorLayer with per-cell set() calls (baseline)
    layer = grid.add_layer("color", z_index=-1)
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            layer.set(x, y, mcrfpy.Color((x * 2) % 256, (y * 2) % 256, 128, 255))

    test_base_static.activate()


def setup_base_layer_modified():
    """ColorLayer with single cell modified each frame - tests dirty flag."""
    test_base_mod = mcrfpy.Scene("test_base_mod")
    ui = test_base_mod.children

    grid = mcrfpy.Grid(grid_size=(GRID_SIZE, GRID_SIZE),
                       pos=(10, 10), size=(600, 600))
    ui.append(grid)

    # Fill using ColorLayer
    layer = grid.add_layer("color", z_index=-1)
    layer.fill(mcrfpy.Color(100, 100, 100, 255))

    # Timer to modify one cell per frame (triggers dirty flag each frame)
    mod_counter = [0]
    def modify_cell(timer, runtime):
        x = mod_counter[0] % GRID_SIZE
        y = (mod_counter[0] // GRID_SIZE) % GRID_SIZE
        layer.set(x, y, mcrfpy.Color(255, 0, 0, 255))
        mod_counter[0] += 1

    test_base_mod.activate()
    global modify_timer
    modify_timer = mcrfpy.Timer("modify", modify_cell, 1)


def setup_color_layer_static():
    """New ColorLayer with dirty flag caching - static after fill."""
    test_color_static = mcrfpy.Scene("test_color_static")
    ui = test_color_static.children

    grid = mcrfpy.Grid(grid_size=(GRID_SIZE, GRID_SIZE),
                       pos=(10, 10), size=(600, 600))
    ui.append(grid)

    # Add color layer and fill once
    layer = grid.add_layer("color", z_index=-1)
    layer.fill(mcrfpy.Color(100, 150, 200, 128))

    test_color_static.activate()


def setup_color_layer_modified():
    """ColorLayer with single cell modified each frame - tests dirty flag."""
    test_color_mod = mcrfpy.Scene("test_color_mod")
    ui = test_color_mod.children

    grid = mcrfpy.Grid(grid_size=(GRID_SIZE, GRID_SIZE),
                       pos=(10, 10), size=(600, 600))
    ui.append(grid)

    layer = grid.add_layer("color", z_index=-1)
    layer.fill(mcrfpy.Color(100, 100, 100, 128))

    # Timer to modify one cell per frame - triggers re-render
    mod_counter = [0]
    def modify_cell(timer, runtime):
        x = mod_counter[0] % GRID_SIZE
        y = (mod_counter[0] // GRID_SIZE) % GRID_SIZE
        layer.set(x, y, mcrfpy.Color(255, 0, 0, 255))
        mod_counter[0] += 1

    test_color_mod.activate()
    global modify_timer
    modify_timer = mcrfpy.Timer("modify", modify_cell, 1)


def setup_tile_layer_static():
    """TileLayer with caching - static after fill."""
    test_tile_static = mcrfpy.Scene("test_tile_static")
    ui = test_tile_static.children

    try:
        texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
    except:
        texture = None

    grid = mcrfpy.Grid(grid_size=(GRID_SIZE, GRID_SIZE),
                       pos=(10, 10), size=(600, 600), texture=texture)
    ui.append(grid)

    if texture:
        layer = grid.add_layer("tile", z_index=-1, texture=texture)
        layer.fill(5)

    test_tile_static.activate()


def setup_tile_layer_modified():
    """TileLayer with single cell modified each frame."""
    test_tile_mod = mcrfpy.Scene("test_tile_mod")
    ui = test_tile_mod.children

    try:
        texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
    except:
        texture = None

    grid = mcrfpy.Grid(grid_size=(GRID_SIZE, GRID_SIZE),
                       pos=(10, 10), size=(600, 600), texture=texture)
    ui.append(grid)

    layer = None
    if texture:
        layer = grid.add_layer("tile", z_index=-1, texture=texture)
        layer.fill(5)

    # Timer to modify one cell per frame
    mod_counter = [0]
    def modify_cell(timer, runtime):
        if layer:
            x = mod_counter[0] % GRID_SIZE
            y = (mod_counter[0] // GRID_SIZE) % GRID_SIZE
            layer.set(x, y, (mod_counter[0] % 20))
        mod_counter[0] += 1

    test_tile_mod.activate()
    global modify_timer
    modify_timer = mcrfpy.Timer("modify", modify_cell, 1)


def setup_multi_layer_static():
    """Multiple layers (5 color, 5 tile) - all static."""
    test_multi_static = mcrfpy.Scene("test_multi_static")
    ui = test_multi_static.children

    try:
        texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
    except:
        texture = None

    grid = mcrfpy.Grid(grid_size=(GRID_SIZE, GRID_SIZE),
                       pos=(10, 10), size=(600, 600), texture=texture)
    ui.append(grid)

    # Add 5 color layers with different z_indices and colors
    for i in range(5):
        layer = grid.add_layer("color", z_index=-(i+1)*2)
        layer.fill(mcrfpy.Color(50 + i*30, 100 + i*20, 150 - i*20, 50))

    # Add 5 tile layers
    if texture:
        for i in range(5):
            layer = grid.add_layer("tile", z_index=-(i+1)*2 - 1, texture=texture)
            layer.fill(i * 4)

    print(f"  Created {len(grid.layers)} layers")
    test_multi_static.activate()


def setup_base_vs_layer_comparison():
    """Direct comparison: same visual using base API vs layer API."""
    test_comparison = mcrfpy.Scene("test_comparison")
    ui = test_comparison.children

    # Grid using ONLY the new layer system (no base layer colors)
    grid = mcrfpy.Grid(grid_size=(GRID_SIZE, GRID_SIZE),
                       pos=(10, 10), size=(600, 600))
    ui.append(grid)

    # Single color layer that covers everything
    layer = grid.add_layer("color", z_index=-1)

    # Fill with pattern (same as base_layer_static but via layer)
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            layer.set(x, y, mcrfpy.Color((x * 2) % 256, (y * 2) % 256, 128, 255))

    test_comparison.activate()


# ============================================================================
# Results Analysis
# ============================================================================

def analyze_results():
    """Read JSON files and print comparison."""
    print("\n" + "=" * 70)
    print("LAYER PERFORMANCE BENCHMARK RESULTS")
    print("=" * 70)
    print(f"Grid size: {GRID_SIZE}x{GRID_SIZE} = {GRID_SIZE*GRID_SIZE:,} cells")
    print(f"Samples per test: {MEASURE_FRAMES} frames")

    results = {}

    for test_name, filename in test_results.items():
        if not os.path.exists(filename):
            print(f"  WARNING: {filename} not found")
            continue

        with open(filename, 'r') as f:
            data = json.load(f)

        frames = data.get('frames', [])
        if not frames:
            continue

        # Calculate averages
        avg_grid = sum(f['grid_render_ms'] for f in frames) / len(frames)
        avg_frame = sum(f['frame_time_ms'] for f in frames) / len(frames)
        avg_cells = sum(f['grid_cells_rendered'] for f in frames) / len(frames)
        avg_work = sum(f.get('work_time_ms', 0) for f in frames) / len(frames)

        results[test_name] = {
            'avg_grid_ms': avg_grid,
            'avg_frame_ms': avg_frame,
            'avg_work_ms': avg_work,
            'avg_cells': avg_cells,
            'samples': len(frames),
        }

    print(f"\n{'Test':<20} {'Grid (ms)':>10} {'Work (ms)':>10} {'Cells':>10}")
    print("-" * 70)

    for name in sorted(results.keys()):
        r = results[name]
        print(f"{name:<20} {r['avg_grid_ms']:>10.3f} {r['avg_work_ms']:>10.3f} {r['avg_cells']:>10.0f}")

    print("\n" + "-" * 70)
    print("ANALYSIS:")

    # Compare base static vs layer static
    if '1_base_static' in results and '3_layer_static' in results:
        base = results['1_base_static']['avg_grid_ms']
        layer = results['3_layer_static']['avg_grid_ms']
        if base > 0.001:
            improvement = ((base - layer) / base) * 100
            print(f"  Static ColorLayer vs Base: {improvement:+.1f}% "
                  f"({'FASTER' if improvement > 0 else 'slower'})")
            print(f"    Base: {base:.3f}ms, Layer: {layer:.3f}ms")

    # Compare base modified vs layer modified
    if '2_base_modified' in results and '4_layer_modified' in results:
        base = results['2_base_modified']['avg_grid_ms']
        layer = results['4_layer_modified']['avg_grid_ms']
        if base > 0.001:
            improvement = ((base - layer) / base) * 100
            print(f"  Modified ColorLayer vs Base: {improvement:+.1f}% "
                  f"({'FASTER' if improvement > 0 else 'slower'})")
            print(f"    Base: {base:.3f}ms, Layer: {layer:.3f}ms")

    # Cache benefit (static vs modified for layers)
    if '3_layer_static' in results and '4_layer_modified' in results:
        static = results['3_layer_static']['avg_grid_ms']
        modified = results['4_layer_modified']['avg_grid_ms']
        if static > 0.001:
            overhead = ((modified - static) / static) * 100
            print(f"  Layer cache hit vs miss: {overhead:+.1f}% "
                  f"({'overhead when dirty' if overhead > 0 else 'benefit'})")
            print(f"    Static: {static:.3f}ms, Modified: {modified:.3f}ms")

    print("\n" + "=" * 70)
    print("Benchmark JSON files saved for detailed analysis.")
    print("Key insight: Base layer has NO caching; layers require opt-in.")

    sys.exit(0)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Layer Performance Benchmark (C++ timing)")
    print("=" * 70)
    print("\nThis benchmark compares:")
    print("  - Traditional grid.at(x,y).color API (renders every frame)")
    print("  - New layer system with dirty flag caching (#147, #148)")
    print(f"\nEach test: {WARMUP_FRAMES} warmup + {MEASURE_FRAMES} measured frames")

    run_next_test()
