"""Benchmark: per-entity FOV cost on a 1000x1000 grid (Phase 5.2 / card #37).

Measures the cost of `entity.update_visibility()` (which writes through the
DiscreteMap-backed `entity.perspective_map`, the FOV optimization landed via
#294 / commit f797120) versus a bare `grid.compute_fov(...)` call (no
per-entity bookkeeping). The delta is the cost of the perspective writeback.

Configurations:
  - 100 entities on 1000x1000 grid
  - radii: 8, 16, 32
  - FOV algorithms: BASIC, SHADOW, SYMMETRIC_SHADOWCAST

Output: JSON to stdout; baseline copy written to ./fov_opt_bench_results.json
when run from the build/ directory.

Usage:
  ./mcrogueface --headless --exec ../tests/benchmarks/fov_opt_bench.py
"""
import mcrfpy
import sys
import os
import time
import json
import random

sys.path.insert(0, os.path.dirname(__file__))
import _baseline


GRID_W, GRID_H = 1000, 1000
N_ENTITIES = 100
RADII = [8, 16, 32]
ALGORITHMS = [
    ("BASIC",                mcrfpy.FOV.BASIC),
    ("SHADOW",               mcrfpy.FOV.SHADOW),
    ("SYMMETRIC_SHADOWCAST", mcrfpy.FOV.SYMMETRIC_SHADOWCAST),
]
SEED = 0x1A2B
WARMUP_ROUNDS = 1
MEASURED_ROUNDS = 3


def build_grid(w, h):
    g = mcrfpy.Grid(grid_size=(w, h))
    # Fully-open arena. Walls only on the perimeter.
    for y in range(h):
        for x in range(w):
            c = g.at(x, y)
            walkable = (x not in (0, w - 1)) and (y not in (0, h - 1))
            c.walkable = walkable
            c.transparent = walkable
    return g


def place_entities(g, n, rng):
    ents = []
    for _ in range(n):
        x = rng.randrange(1, GRID_W - 1)
        y = rng.randrange(1, GRID_H - 1)
        e = mcrfpy.Entity((x, y), grid=g)
        ents.append(e)
    return ents


def measure_update_visibility(entities, rounds):
    t0 = time.perf_counter()
    for _ in range(rounds):
        for e in entities:
            e.update_visibility()
    return (time.perf_counter() - t0) / rounds


def measure_grid_compute_only(grid, entities, radius, algorithm, rounds):
    # entity.x/.y are pixel coords (UIDrawable). compute_fov takes grid coords.
    coords = [(e.grid_pos.x, e.grid_pos.y) for e in entities]
    t0 = time.perf_counter()
    for _ in range(rounds):
        for (x, y) in coords:
            grid.compute_fov((x, y), radius=radius, light_walls=True, algorithm=algorithm)
    return (time.perf_counter() - t0) / rounds


def main():
    rng = random.Random(SEED)
    print(f"Building {GRID_W}x{GRID_H} grid...")
    grid = build_grid(GRID_W, GRID_H)
    entities = place_entities(grid, N_ENTITIES, rng)
    print(f"Placed {len(entities)} entities.")

    runs = []
    for (aname, algo) in ALGORITHMS:
        grid.fov = algo
        for radius in RADII:
            grid.fov_radius = radius

            # Warmup (allocates perspective_map + warms TCOD caches).
            for _ in range(WARMUP_ROUNDS):
                for e in entities:
                    e.update_visibility()

            with_t = measure_update_visibility(entities, MEASURED_ROUNDS)
            wo_t   = measure_grid_compute_only(grid, entities, radius, algo, MEASURED_ROUNDS)

            with_per_us = with_t / N_ENTITIES * 1e6
            wo_per_us   = wo_t / N_ENTITIES * 1e6
            overhead_us = with_per_us - wo_per_us

            entry = {
                "grid": f"{GRID_W}x{GRID_H}",
                "entities": N_ENTITIES,
                "algorithm": aname,
                "radius": radius,
                "with_perspective_round_ms": with_t * 1000.0,
                "without_perspective_round_ms": wo_t * 1000.0,
                "with_perspective_per_entity_us": with_per_us,
                "without_perspective_per_entity_us": wo_per_us,
                "perspective_overhead_per_entity_us": overhead_us,
            }
            runs.append(entry)
            print(f"  {aname:<22} r={radius:<2}  "
                  f"compute={wo_per_us:7.2f} us/ent  "
                  f"+perspective={with_per_us:7.2f} us/ent  "
                  f"(overhead {overhead_us:+6.2f} us)")

    out = {
        "config": {
            "grid": f"{GRID_W}x{GRID_H}",
            "entities": N_ENTITIES,
            "radii": RADII,
            "algorithms": [a[0] for a in ALGORITHMS],
            "warmup_rounds": WARMUP_ROUNDS,
            "measured_rounds": MEASURED_ROUNDS,
            "seed": SEED,
        },
        "runs": runs,
    }
    print(json.dumps(out, indent=2))
    _baseline.write("fov_opt_bench.json", out)
    print("DONE")


if __name__ == "__main__":
    main()
    sys.exit(0)
