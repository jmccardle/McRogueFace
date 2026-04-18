"""Benchmark: single-root, multi-root, DiscreteMap-mask Dijkstra plus invert+descent.

Usage:
  ./mcrogueface --headless --exec ../tests/benchmarks/dijkstra_bench.py
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
ROOT_COUNTS = [1, 2, 5, 20]
MASK_DENSITY = 0.05
TRIALS = 5
SEED = 0x1234


def make_grid(w, h):
    g = mcrfpy.Grid(grid_size=(w, h))
    for y in range(h):
        for x in range(w):
            c = g.at(x, y)
            c.walkable = True
            c.transparent = True
    return g


def random_points(w, h, n, rng):
    pts = set()
    while len(pts) < n:
        pts.add((rng.randrange(1, w - 1), rng.randrange(1, h - 1)))
    return list(pts)


def bench_compute(g, roots, trials):
    total = 0.0
    for _ in range(trials):
        g.clear_dijkstra_maps()
        t0 = time.perf_counter()
        _ = g.get_dijkstra_map(roots=roots)
        total += time.perf_counter() - t0
    return total / trials


def bench_mask(g, mask, trials):
    total = 0.0
    for _ in range(trials):
        g.clear_dijkstra_maps()
        t0 = time.perf_counter()
        _ = g.get_dijkstra_map(roots=mask)
        total += time.perf_counter() - t0
    return total / trials


def bench_invert_descent(g, root, trials):
    d = g.get_dijkstra_map(root)
    t0 = time.perf_counter()
    for _ in range(trials):
        _ = d.invert()
    invert_t = (time.perf_counter() - t0) / trials

    inv = d.invert()
    w, h = d.root.x, d.root.y  # unused, just reading
    # Descent throughput: pick many start cells, step once each.
    starts = [(x, y) for y in range(1, g.grid_h - 1, 10) for x in range(1, g.grid_w - 1, 10)]
    n = len(starts)
    t0 = time.perf_counter()
    ok = 0
    for _ in range(trials):
        for s in starts:
            if inv.descent_step(s) is not None:
                ok += 1
    descent_t = (time.perf_counter() - t0) / (trials * n)
    return invert_t * 1000.0, descent_t * 1e6, ok // trials


def main():
    rng = random.Random(SEED)
    out = {"runs": []}

    for (w, h) in GRID_SIZES:
        g = make_grid(w, h)
        for n in ROOT_COUNTS:
            roots = random_points(w, h, n, rng)
            ms = bench_compute(g, roots, TRIALS) * 1000.0
            out["runs"].append({"grid": f"{w}x{h}", "kind": "multi_root",
                                "roots": n, "mean_ms": ms})
            print(f"  {w}x{h} multi_root({n:2d})  mean={ms:7.2f} ms")

        # Mask form
        mask = mcrfpy.DiscreteMap((w, h))
        n_mask = max(1, int(w * h * MASK_DENSITY))
        pts = random_points(w, h, n_mask, rng)
        for (x, y) in pts:
            mask.set(x, y, 1)
        ms = bench_mask(g, mask, TRIALS) * 1000.0
        out["runs"].append({"grid": f"{w}x{h}", "kind": "mask",
                            "roots": n_mask, "mean_ms": ms})
        print(f"  {w}x{h} mask({n_mask})        mean={ms:7.2f} ms")

        # Invert + descent
        root = (w // 2, h // 2)
        inv_ms, desc_us, valid = bench_invert_descent(g, root, TRIALS)
        out["runs"].append({"grid": f"{w}x{h}", "kind": "invert",
                            "mean_ms": inv_ms})
        out["runs"].append({"grid": f"{w}x{h}", "kind": "descent_step_per_call",
                            "mean_us": desc_us, "valid_per_trial": valid})
        print(f"  {w}x{h} invert             mean={inv_ms:7.2f} ms")
        print(f"  {w}x{h} descent_step/call  mean={desc_us:7.2f} us  valid={valid}")

    print(json.dumps(out, indent=2))
    _baseline.write("dijkstra_bench.json", out)
    print("DONE")


if __name__ == "__main__":
    main()
    sys.exit(0)
