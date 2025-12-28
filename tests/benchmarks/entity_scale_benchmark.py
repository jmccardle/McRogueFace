#!/usr/bin/env python3
"""Entity Performance Benchmark for #115 (SpatialHash) and #117 (Memory Pool)

Target: 10,000 entities on 1000×1000 grid
Goal: Establish baseline metrics for spatial query and memory performance

Scenarios:
  B1: Entity creation stress (measures allocation overhead)
  B2: Full iteration (measures cache locality)
  B3: Single range query (measures current O(n) cost)
  B4: N-to-N visibility (the "what can everyone see" problem)
  B5: Movement churn (measures update cost for spatial index)

Usage:
    cd build && ./mcrogueface --headless --exec ../tests/benchmarks/entity_scale_benchmark.py

Expected output: Baseline timings and projected gains from #115/#117 implementations.
"""

import mcrfpy
import sys
import time
import random

# Configuration
# Use smaller grid for denser entity distribution (more realistic visibility tests)
GRID_SIZE = (100, 100)  # 10,000 cells - entities will actually see each other

# Full suite - may timeout on large counts due to O(n²) visibility
# ENTITY_COUNTS = [100, 500, 1000, 2500, 5000, 10000]

# Quick suite for initial baseline (on 100x100 grid, these give densities of 1-20%)
ENTITY_COUNTS = [100, 500, 1000, 2000]
QUERY_RADIUS = 15  # Smaller radius for smaller grid
MOVEMENT_PERCENT = 0.10  # 10% of entities move each frame
N2N_SAMPLE_SIZE = 50  # Sample size for N×N visibility test

results = {}
texture = None


def setup_grid_with_entities(n_entities):
    """Create a grid and populate with n entities at random positions."""
    global texture

    scene_name = f"bench_{n_entities}"
    mcrfpy.createScene(scene_name)
    ui = mcrfpy.sceneUI(scene_name)

    # Create grid - minimal rendering size since we're testing entity operations
    grid = mcrfpy.Grid(grid_size=GRID_SIZE, pos=(0, 0), size=(100, 100))
    ui.append(grid)

    # Load texture once
    if texture is None:
        try:
            texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
        except Exception as e:
            print(f"ERROR: Could not load texture: {e}")
            return None, None

    # Create entities
    for i in range(n_entities):
        x = random.randint(0, GRID_SIZE[0] - 1)
        y = random.randint(0, GRID_SIZE[1] - 1)
        entity = mcrfpy.Entity((x, y), texture, 0, grid)
        grid.entities.append(entity)

    mcrfpy.setScene(scene_name)
    return grid, scene_name


def benchmark_creation(n_entities):
    """B1: Measure time to create N entities from scratch."""
    global texture

    scene_name = "bench_create_test"
    mcrfpy.createScene(scene_name)
    ui = mcrfpy.sceneUI(scene_name)

    grid = mcrfpy.Grid(grid_size=GRID_SIZE, pos=(0, 0), size=(100, 100))
    ui.append(grid)

    if texture is None:
        try:
            texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
        except Exception as e:
            print(f"ERROR: Could not load texture: {e}")
            return None

    # Time just the entity creation loop
    start = time.perf_counter()

    for i in range(n_entities):
        x = random.randint(0, GRID_SIZE[0] - 1)
        y = random.randint(0, GRID_SIZE[1] - 1)
        entity = mcrfpy.Entity((x, y), texture, 0, grid)
        grid.entities.append(entity)

    elapsed = time.perf_counter() - start
    return elapsed * 1000  # ms


def benchmark_iteration(grid):
    """B2: Measure time to iterate all entities and read position."""
    entities_list = list(grid.entities)  # Convert to list first
    n = len(entities_list)

    start = time.perf_counter()

    total_x = 0.0
    for entity in entities_list:
        total_x += entity.x  # Force read of position

    elapsed = time.perf_counter() - start
    return elapsed * 1000, n  # ms, count


def benchmark_iteration_via_collection(grid):
    """B2b: Measure iteration directly through EntityCollection."""
    start = time.perf_counter()

    total_x = 0.0
    for entity in grid.entities:
        total_x += entity.x

    elapsed = time.perf_counter() - start
    return elapsed * 1000  # ms


def benchmark_range_query(entity, radius):
    """B3: Measure single visible_entities call (current O(n) implementation)."""
    start = time.perf_counter()

    visible = entity.visible_entities(radius=radius)

    elapsed = time.perf_counter() - start
    return elapsed * 1000, len(visible)  # ms, count


def benchmark_range_query_spatial(grid, x, y, radius):
    """B3b: Measure grid.entities_in_radius call (SpatialHash O(k) implementation)."""
    start = time.perf_counter()

    visible = grid.entities_in_radius(x, y, radius)

    elapsed = time.perf_counter() - start
    return elapsed * 1000, len(visible)  # ms, count


def benchmark_n_to_n_visibility(grid, radius, sample_size):
    """B4: Measure visibility queries for a sample of entities.

    This simulates "what can every entity see" which is O(N²) currently.
    We sample to avoid timeouts on large entity counts.
    """
    entities_list = list(grid.entities)
    n = len(entities_list)
    actual_sample = min(sample_size, n)
    sample = random.sample(entities_list, actual_sample)

    start = time.perf_counter()

    total_visible = 0
    for entity in sample:
        visible = entity.visible_entities(radius=radius)
        total_visible += len(visible)

    elapsed = time.perf_counter() - start
    avg_visible = total_visible / actual_sample if actual_sample > 0 else 0

    return elapsed * 1000, actual_sample, avg_visible  # ms, sample_size, avg_found


def benchmark_n_to_n_visibility_spatial(grid, radius, sample_size):
    """B4b: Measure N×N visibility using SpatialHash.

    Same test as B4 but uses grid.entities_in_radius() instead of entity.visible_entities().
    """
    entities_list = list(grid.entities)
    n = len(entities_list)
    actual_sample = min(sample_size, n)
    sample = random.sample(entities_list, actual_sample)

    start = time.perf_counter()

    total_visible = 0
    for entity in sample:
        visible = grid.entities_in_radius(entity.x, entity.y, radius)
        total_visible += len(visible)

    elapsed = time.perf_counter() - start
    avg_visible = total_visible / actual_sample if actual_sample > 0 else 0

    return elapsed * 1000, actual_sample, avg_visible  # ms, sample_size, avg_found


def benchmark_movement(grid, move_percent):
    """B5: Move a percentage of entities to random positions.

    Currently this is just position assignment (O(1) per entity).
    With SpatialHash, this would include hash bucket updates.
    """
    entities_list = list(grid.entities)
    n = len(entities_list)
    to_move_count = int(n * move_percent)
    to_move = random.sample(entities_list, to_move_count)

    start = time.perf_counter()

    for entity in to_move:
        entity.x = random.randint(0, GRID_SIZE[0] - 1)
        entity.y = random.randint(0, GRID_SIZE[1] - 1)

    elapsed = time.perf_counter() - start
    return elapsed * 1000, to_move_count  # ms, count


def run_single_scale(n_entities):
    """Run all benchmarks for a single entity count."""
    print(f"\n{'='*60}")
    print(f"  {n_entities:,} ENTITIES on {GRID_SIZE[0]}x{GRID_SIZE[1]} grid")
    print(f"{'='*60}")

    # B1: Creation benchmark
    print("\n[B1] Entity Creation...")
    create_ms = benchmark_creation(n_entities)
    if create_ms is None:
        print("  FAILED: Could not load texture")
        return None

    entities_per_sec = n_entities / (create_ms / 1000) if create_ms > 0 else 0
    print(f"  Time: {create_ms:.2f}ms")
    print(f"  Rate: {entities_per_sec:,.0f} entities/sec")

    # Setup grid for remaining tests
    grid, scene_name = setup_grid_with_entities(n_entities)
    if grid is None:
        return None

    # B2: Iteration benchmark
    print("\n[B2] Full Iteration (read all positions)...")
    iter_ms, count = benchmark_iteration(grid)
    iter_per_sec = count / (iter_ms / 1000) if iter_ms > 0 else 0
    print(f"  Time: {iter_ms:.3f}ms")
    print(f"  Rate: {iter_per_sec:,.0f} reads/sec")

    # B2b: Iteration via collection
    iter_coll_ms = benchmark_iteration_via_collection(grid)
    print(f"  Via EntityCollection: {iter_coll_ms:.3f}ms")

    # B3: Single range query
    print(f"\n[B3] Single Range Query (radius={QUERY_RADIUS})...")
    entities_list = list(grid.entities)
    # Pick entity near center of grid for representative query
    center_entities = [e for e in entities_list
                       if 400 < e.x < 600 and 400 < e.y < 600]
    if center_entities:
        test_entity = center_entities[0]
    else:
        test_entity = entities_list[len(entities_list)//2]

    query_ms, found = benchmark_range_query(test_entity, QUERY_RADIUS)
    print(f"  Time: {query_ms:.3f}ms")
    print(f"  Found: {found} entities in range")
    print(f"  Checked: {n_entities} entities (O(n) scan)")

    # B3b: SpatialHash range query
    print(f"\n[B3b] SpatialHash Range Query (radius={QUERY_RADIUS})...")
    spatial_query_ms, spatial_found = benchmark_range_query_spatial(
        grid, test_entity.x, test_entity.y, QUERY_RADIUS
    )
    print(f"  Time: {spatial_query_ms:.3f}ms")
    print(f"  Found: {spatial_found} entities in range")
    if query_ms > 0:
        speedup = query_ms / spatial_query_ms if spatial_query_ms > 0 else float('inf')
        print(f"  Speedup: {speedup:.1f}× faster than O(n) scan")

    # B4: N-to-N visibility
    print(f"\n[B4] N×N Visibility O(n) (sample={N2N_SAMPLE_SIZE})...")
    n2n_ms, sample_size, avg_visible = benchmark_n_to_n_visibility(
        grid, QUERY_RADIUS, N2N_SAMPLE_SIZE
    )
    per_query_ms = n2n_ms / sample_size if sample_size > 0 else 0
    print(f"  Sample time: {n2n_ms:.2f}ms ({sample_size} queries)")
    print(f"  Per query: {per_query_ms:.3f}ms")
    print(f"  Avg visible: {avg_visible:.1f} entities")

    # Extrapolate to full N×N
    full_n2n_ms = per_query_ms * n_entities
    print(f"  Estimated full N×N: {full_n2n_ms:,.0f}ms ({full_n2n_ms/1000:.1f}s)")

    # B4b: N-to-N visibility with SpatialHash
    print(f"\n[B4b] N×N Visibility SpatialHash (sample={N2N_SAMPLE_SIZE})...")
    n2n_spatial_ms, _, _ = benchmark_n_to_n_visibility_spatial(
        grid, QUERY_RADIUS, N2N_SAMPLE_SIZE
    )
    per_query_spatial_ms = n2n_spatial_ms / sample_size if sample_size > 0 else 0
    print(f"  Sample time: {n2n_spatial_ms:.2f}ms ({sample_size} queries)")
    print(f"  Per query: {per_query_spatial_ms:.3f}ms")
    full_n2n_spatial_ms = per_query_spatial_ms * n_entities
    print(f"  Estimated full N×N: {full_n2n_spatial_ms:,.0f}ms ({full_n2n_spatial_ms/1000:.1f}s)")
    if n2n_ms > 0:
        n2n_speedup = n2n_ms / n2n_spatial_ms if n2n_spatial_ms > 0 else float('inf')
        print(f"  Speedup: {n2n_speedup:.1f}× faster than O(n)")

    # B5: Movement
    print(f"\n[B5] Movement ({MOVEMENT_PERCENT*100:.0f}% of entities)...")
    move_ms, moved = benchmark_movement(grid, MOVEMENT_PERCENT)
    move_per_sec = moved / (move_ms / 1000) if move_ms > 0 else 0
    print(f"  Time: {move_ms:.3f}ms ({moved} entities)")
    print(f"  Rate: {move_per_sec:,.0f} moves/sec")

    return {
        'n': n_entities,
        'create_ms': create_ms,
        'create_rate': entities_per_sec,
        'iter_ms': iter_ms,
        'iter_coll_ms': iter_coll_ms,
        'query_ms': query_ms,
        'query_found': found,
        'spatial_query_ms': spatial_query_ms,
        'spatial_query_found': spatial_found,
        'n2n_sample_ms': n2n_ms,
        'n2n_per_query_ms': per_query_ms,
        'n2n_avg_visible': avg_visible,
        'n2n_full_estimate_ms': full_n2n_ms,
        'n2n_spatial_ms': n2n_spatial_ms,
        'n2n_spatial_full_estimate_ms': full_n2n_spatial_ms,
        'move_ms': move_ms,
        'move_count': moved,
    }


def print_summary_table():
    """Print a summary table of all results."""
    print("\n" + "=" * 100)
    print("SUMMARY TABLE")
    print("=" * 100)

    header = f"{'Entities':>10} {'Create':>10} {'Iterate':>10} {'Query O(n)':>12} {'Query Hash':>12} {'N×N O(n)':>12} {'N×N Hash':>12}"
    print(header)
    print(f"{'':>10} {'(ms)':>10} {'(ms)':>10} {'(ms)':>12} {'(ms)':>12} {'(ms)':>12} {'(ms)':>12}")
    print("-" * 100)

    for n in sorted(results.keys()):
        r = results[n]
        speedup_q = r['query_ms'] / r['spatial_query_ms'] if r['spatial_query_ms'] > 0 else 0
        speedup_n = r['n2n_full_estimate_ms'] / r['n2n_spatial_full_estimate_ms'] if r['n2n_spatial_full_estimate_ms'] > 0 else 0
        print(f"{r['n']:>10,} {r['create_ms']:>10.1f} {r['iter_ms']:>10.2f} "
              f"{r['query_ms']:>12.3f} {r['spatial_query_ms']:>12.3f} "
              f"{r['n2n_full_estimate_ms']:>12,.0f} {r['n2n_spatial_full_estimate_ms']:>12,.0f}")

    print("\nSpatialHash Speedups:")
    for n in sorted(results.keys()):
        r = results[n]
        speedup_q = r['query_ms'] / r['spatial_query_ms'] if r['spatial_query_ms'] > 0 else float('inf')
        speedup_n = r['n2n_full_estimate_ms'] / r['n2n_spatial_full_estimate_ms'] if r['n2n_spatial_full_estimate_ms'] > 0 else float('inf')
        print(f"  {r['n']:>6,} entities: Query {speedup_q:>5.1f}×, N×N {speedup_n:>5.1f}×")


def print_analysis():
    """Print performance analysis and projected gains."""
    print("\n" + "=" * 80)
    print("ANALYSIS: Projected Gains from #115 (SpatialHash) and #117 (Memory Pool)")
    print("=" * 80)

    # Find largest test run
    max_n = max(results.keys())
    r = results[max_n]

    print(f"\nBaseline at {max_n:,} entities:")
    print("-" * 40)

    # Creation analysis (#117)
    print(f"\n[#117 Memory Pool] Entity Creation:")
    print(f"  Current:   {r['create_ms']:.1f}ms ({r['create_rate']:,.0f}/sec)")
    projected_create = r['create_ms'] / 25
    print(f"  Projected: ~{projected_create:.1f}ms (25× faster)")
    print(f"  Rationale: Pool allocation eliminates malloc overhead per entity")

    # Iteration analysis (#117)
    print(f"\n[#117 Memory Pool] Iteration:")
    print(f"  Current:   {r['iter_ms']:.2f}ms")
    projected_iter = r['iter_ms'] / 5
    print(f"  Projected: ~{projected_iter:.2f}ms (5× faster)")
    print(f"  Rationale: Contiguous memory improves CPU cache utilization")

    # Range query analysis (#115)
    print(f"\n[#115 SpatialHash] Range Query:")
    print(f"  Current:   {r['query_ms']:.2f}ms (checks {max_n:,} entities)")
    print(f"  Found:     {r['query_found']} entities in radius {QUERY_RADIUS}")

    # Calculate expected speedup
    # With spatial hash, we only check entities in nearby buckets
    # Bucket size typically 32-64 cells, so for radius 25 we check ~4-16 buckets
    # Each bucket has ~10 entities at 0.01 density
    expected_checks = max(r['query_found'] * 5, 100)  # Conservative estimate
    speedup = max_n / expected_checks
    projected_query = r['query_ms'] / speedup
    print(f"  Projected: ~{projected_query:.3f}ms ({speedup:.0f}× faster)")
    print(f"  Rationale: Only check ~{expected_checks} entities in nearby hash buckets")

    # N×N analysis (#115)
    print(f"\n[#115 SpatialHash] N×N Visibility:")
    print(f"  Current:   {r['n2n_full_estimate_ms']:,.0f}ms ({r['n2n_full_estimate_ms']/1000:.1f}s)")
    projected_n2n = r['n2n_full_estimate_ms'] / speedup
    print(f"  Projected: ~{projected_n2n:,.0f}ms ({projected_n2n/1000:.2f}s)")
    print(f"  Rationale: Each of N queries benefits from {speedup:.0f}× speedup")

    # Combined benefit
    print(f"\n[Combined] Per-Frame Budget Analysis:")
    print(f"  Target: 16.67ms (60 FPS)")
    current_frame = r['iter_ms'] + r['move_ms'] + (r['n2n_per_query_ms'] * 100)  # 100 AI entities
    print(f"  Current (100 AI queries): ~{current_frame:.1f}ms")
    projected_frame = projected_iter + r['move_ms'] + (projected_query * 100)
    print(f"  Projected: ~{projected_frame:.1f}ms")
    if current_frame > 16.67 and projected_frame < 16.67:
        print(f"  Result: ENABLES 60 FPS with 100 AI entities")

    # Movement overhead warning
    print(f"\n[#115 SpatialHash] Movement Overhead:")
    print(f"  Current:   {r['move_ms']:.2f}ms (no index to update)")
    print(f"  Projected: ~{r['move_ms'] * 1.5:.2f}ms (+50% for hash updates)")
    print(f"  Note: This overhead is acceptable given query speedups")


def run_benchmarks(runtime=None):
    """Main benchmark runner."""
    global results

    print("=" * 80)
    print("Entity Scale Benchmark Suite")
    print(f"Grid: {GRID_SIZE[0]}×{GRID_SIZE[1]}, Query Radius: {QUERY_RADIUS}")
    print(f"Testing entity counts: {ENTITY_COUNTS}")
    print("=" * 80)

    for n in ENTITY_COUNTS:
        result = run_single_scale(n)
        if result:
            results[n] = result

    if results:
        print_summary_table()
        print_analysis()

    print("\nBenchmark complete.")
    sys.exit(0)


# Entry point
if __name__ == "__main__":
    # For headless mode, run immediately
    # For interactive mode, use timer to let render loop start
    import sys
    if "--headless" in sys.argv or True:  # Always run immediately for benchmarks
        run_benchmarks()
    else:
        mcrfpy.setTimer("run_bench", run_benchmarks, 100)
