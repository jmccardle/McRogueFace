"""Benchmark: spatial-hash query throughput (Phase 5.2 / card #37, scenario 3).

Per acceptance criteria: `queryRadius()` at radii (1, 5, 10, 50) with
(100, 1000, 10000) entities. The Python-facing call is `grid.entities_in_radius()`.

For each (count, radius) pair we measure:
  - mean per-query time (us)
  - O(n) baseline (manual scan of `grid.entities`)
  - speedup factor
  - mean hit count

Headless mode. Output: JSON to stdout.

Usage:
  ./mcrogueface --headless --exec ../tests/benchmarks/spatial_hash_bench.py
"""
import mcrfpy
import sys
import os
import time
import json
import random

sys.path.insert(0, os.path.dirname(__file__))
import _baseline


GRID_W, GRID_H = 200, 200
ENTITY_COUNTS = [100, 1000, 10000]
RADII = [1, 5, 10, 50]
QUERIES_PER_CONFIG = 200
SAMPLE_QUERY_LOCATIONS = 50  # how many distinct (x,y) sample positions
SEED = 0xCAFE


def build_grid(w, h):
    g = mcrfpy.Grid(grid_size=(w, h))
    for y in range(h):
        for x in range(w):
            c = g.at(x, y)
            c.walkable = True
            c.transparent = True
    return g


def populate(g, n, rng):
    ents = []
    seen = set()
    while len(ents) < n:
        x = rng.randrange(GRID_W)
        y = rng.randrange(GRID_H)
        if (x, y) in seen:
            continue
        seen.add((x, y))
        ents.append(mcrfpy.Entity((x, y), grid=g))
    return ents


def sample_points(rng, n):
    return [(rng.randrange(GRID_W), rng.randrange(GRID_H)) for _ in range(n)]


def bench_spatial(g, points, radius, queries):
    """Mean per-query time using SpatialHash-backed entities_in_radius."""
    n_pts = len(points)
    hits_total = 0
    t0 = time.perf_counter()
    for i in range(queries):
        result = g.entities_in_radius(points[i % n_pts], radius)
        hits_total += len(result)
    elapsed = time.perf_counter() - t0
    return elapsed / queries, hits_total / queries


def bench_naive(g, points, radius, queries):
    """O(n) baseline: enumerate grid.entities and check distance manually.

    Note: `entity.x`/`entity.y` are pixel coordinates inherited from UIDrawable.
    We compare against `entity.grid_pos`, which is the same coordinate frame
    `entities_in_radius` uses.
    """
    n_pts = len(points)
    r2 = radius * radius
    # Snapshot grid coordinates so the loop body has no Python attribute lookup
    # cost beyond the unavoidable.
    coords = [(e.grid_pos.x, e.grid_pos.y) for e in g.entities]
    hits_total = 0
    t0 = time.perf_counter()
    for i in range(queries):
        cx, cy = points[i % n_pts]
        n = 0
        for ex, ey in coords:
            dx = ex - cx
            dy = ey - cy
            if dx * dx + dy * dy <= r2:
                n += 1
        hits_total += n
    elapsed = time.perf_counter() - t0
    return elapsed / queries, hits_total / queries


def main():
    rng = random.Random(SEED)
    runs = []
    for n_ent in ENTITY_COUNTS:
        scene = mcrfpy.Scene(f"spatial_{n_ent}")
        mcrfpy.current_scene = scene
        g = build_grid(GRID_W, GRID_H)
        scene.children.append(g)
        ents = populate(g, n_ent, rng)
        pts = sample_points(rng, SAMPLE_QUERY_LOCATIONS)

        for radius in RADII:
            # Warmup the spatial hash for this entity set.
            for p in pts:
                g.entities_in_radius(p, radius)

            sp_t, sp_hits = bench_spatial(g, pts, radius, QUERIES_PER_CONFIG)
            nv_t, nv_hits = bench_naive(g, pts, radius, QUERIES_PER_CONFIG)
            speedup = (nv_t / sp_t) if sp_t > 0 else float("inf")

            entry = {
                "entities": n_ent,
                "radius": radius,
                "queries": QUERIES_PER_CONFIG,
                "spatial_per_query_us": sp_t * 1e6,
                "naive_per_query_us": nv_t * 1e6,
                "speedup": speedup,
                "spatial_mean_hits": sp_hits,
                "naive_mean_hits": nv_hits,
            }
            runs.append(entry)
            print(f"  n={n_ent:>5}  r={radius:<3}  "
                  f"spatial={sp_t * 1e6:9.2f} us  "
                  f"naive={nv_t * 1e6:10.2f} us  "
                  f"speedup={speedup:7.2f}x  "
                  f"hits={sp_hits:6.1f} (naive={nv_hits:6.1f})")

        # Tear down entities so they don't leak into the next iteration's grid.
        for e in ents:
            e.die()
        del ents
        del g

    out = {
        "config": {
            "grid": f"{GRID_W}x{GRID_H}",
            "entity_counts": ENTITY_COUNTS,
            "radii": RADII,
            "queries_per_config": QUERIES_PER_CONFIG,
            "sample_query_locations": SAMPLE_QUERY_LOCATIONS,
            "seed": SEED,
        },
        "runs": runs,
    }
    print(json.dumps(out, indent=2))
    _baseline.write("spatial_hash_bench.json", out)
    print("DONE")


if __name__ == "__main__":
    main()
    sys.exit(0)
