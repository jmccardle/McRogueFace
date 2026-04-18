"""Benchmark: find_path() across grid sizes, obstacle densities, heuristics, weights,
and with/without collision-label entity blocking.

Kanban #37 coverage: pathfinding throughput at varying obstacle densities (10/30/50%)
plus an explicit with-vs-without collision-label comparison (10 / 100 entities tagged
'blocker' on a 100x100 grid).

Usage:
  ./mcrogueface --headless --exec ../tests/benchmarks/pathfinding_bench.py
"""
import mcrfpy
import sys
import os
import time
import json
import random

sys.path.insert(0, os.path.dirname(__file__))
import _baseline


GRID_SIZES = [(100, 100), (500, 500)]
OBSTACLE_DENSITIES = [0.10, 0.30, 0.50]
HEURISTICS = [
    ("EUCLIDEAN", mcrfpy.Heuristic.EUCLIDEAN),
    ("MANHATTAN", mcrfpy.Heuristic.MANHATTAN),
    ("CHEBYSHEV", mcrfpy.Heuristic.CHEBYSHEV),
    ("DIAGONAL",  mcrfpy.Heuristic.DIAGONAL),
    ("ZERO",      mcrfpy.Heuristic.ZERO),
]
WEIGHTS = [1.0, 1.5, 2.0]
TRIALS_PER_CONFIG = 5

COLLIDE_GRID = (100, 100)
COLLIDE_DENSITY = 0.10
COLLIDE_BLOCKER_COUNTS = [0, 10, 100]
COLLIDE_TRIALS = 20

SEED = 0x315


def make_grid(w, h, density, seed):
    rng = random.Random(seed)
    g = mcrfpy.Grid(grid_size=(w, h))
    for y in range(h):
        for x in range(w):
            c = g.at(x, y)
            walkable = (x in (0, w - 1) or y in (0, h - 1)) or rng.random() > density
            c.walkable = walkable
            c.transparent = walkable
    # Guarantee corners walkable.
    g.at(1, 1).walkable = True
    g.at(w - 2, h - 2).walkable = True
    return g


def pick_endpoints(w, h, rng):
    return (1, 1), (w - 2, h - 2)


def bench_one(g, start, end, heuristic, weight, collide, trials):
    total_t = 0.0
    hits = 0
    length_sum = 0
    for _ in range(trials):
        t0 = time.perf_counter()
        if collide:
            p = g.find_path(start, end, heuristic=heuristic, weight=weight, collide=collide)
        else:
            p = g.find_path(start, end, heuristic=heuristic, weight=weight)
        elapsed = time.perf_counter() - t0
        total_t += elapsed
        if p is not None:
            steps = list(p)
            if steps:
                hits += 1
                length_sum += len(steps)
    return {
        "mean_ms": (total_t / trials) * 1000.0,
        "hits": hits,
        "mean_length": length_sum / max(hits, 1),
    }


def collide_block_section(rng):
    """100x100 grid, walkable arena, tag N entities with 'blocker' label.

    Compares `find_path(..., collide='blocker')` (with) vs `find_path(...)` (without)
    holding all other variables constant. The same grid is reused across N values,
    walkable cells are unchanged; only the entity set differs.
    """
    w, h = COLLIDE_GRID
    g = make_grid(w, h, COLLIDE_DENSITY, rng.randrange(2**31))
    start, end = pick_endpoints(w, h, rng)

    runs = []
    for n_blockers in COLLIDE_BLOCKER_COUNTS:
        # Fresh entity set each iteration. Old entities are garbage-collected once
        # the local list goes out of scope.
        entities = []
        for _ in range(n_blockers):
            while True:
                ex = rng.randrange(2, w - 2)
                ey = rng.randrange(2, h - 2)
                if g.at(ex, ey).walkable and (ex, ey) not in (start, end):
                    break
            e = mcrfpy.Entity((ex, ey), grid=g)
            e.add_label("blocker")
            entities.append(e)

        # WITHOUT collide arg (entities present but ignored).
        wo = bench_one(g, start, end, mcrfpy.Heuristic.EUCLIDEAN, 1.0, None, COLLIDE_TRIALS)
        # WITH collide arg.
        wi = bench_one(g, start, end, mcrfpy.Heuristic.EUCLIDEAN, 1.0, "blocker", COLLIDE_TRIALS)

        runs.append({
            "grid": f"{w}x{h}",
            "blockers": n_blockers,
            "without_collide_ms": wo["mean_ms"],
            "with_collide_ms": wi["mean_ms"],
            "without_collide_path_len": wo["mean_length"],
            "with_collide_path_len": wi["mean_length"],
            "overhead_ms": wi["mean_ms"] - wo["mean_ms"],
        })
        print(f"  collide n={n_blockers:<3}  "
              f"without={wo['mean_ms']:6.2f} ms (len={wo['mean_length']:.0f})  "
              f"with={wi['mean_ms']:6.2f} ms (len={wi['mean_length']:.0f})  "
              f"overhead={wi['mean_ms'] - wo['mean_ms']:+6.2f} ms")

        # Drop entities from the grid before next iteration so the count is correct.
        for e in entities:
            e.die()
        del entities

    return runs


def main():
    rng = random.Random(SEED)
    out = {"config": {
        "grid_sizes": GRID_SIZES,
        "obstacle_densities": OBSTACLE_DENSITIES,
        "heuristics": [h[0] for h in HEURISTICS],
        "weights": WEIGHTS,
        "trials": TRIALS_PER_CONFIG,
        "collide_blocker_counts": COLLIDE_BLOCKER_COUNTS,
        "collide_trials": COLLIDE_TRIALS,
    }, "runs": []}

    for (w, h) in GRID_SIZES:
        for density in OBSTACLE_DENSITIES:
            seed = rng.randrange(2**31)
            g = make_grid(w, h, density, seed)
            start, end = pick_endpoints(w, h, rng)
            for (hname, heuristic) in HEURISTICS:
                for weight in WEIGHTS:
                    r = bench_one(g, start, end, heuristic, weight, None, TRIALS_PER_CONFIG)
                    out["runs"].append({
                        "grid": f"{w}x{h}", "density": density,
                        "heuristic": hname, "weight": weight,
                        "collide": None, **r,
                    })
                    print(f"  {w}x{h} d={density:.2f} h={hname:<9} w={weight:.1f} "
                          f"mean={r['mean_ms']:7.2f} ms  len={r['mean_length']:.1f}")

    print()
    print(f"=== Collision-label comparison ({COLLIDE_GRID[0]}x{COLLIDE_GRID[1]}, "
          f"{COLLIDE_TRIALS} trials/config) ===")
    out["collide_runs"] = collide_block_section(rng)

    print(json.dumps(out, indent=2))
    _baseline.write("pathfinding_bench.json", out)
    print("DONE")


if __name__ == "__main__":
    main()
    sys.exit(0)
