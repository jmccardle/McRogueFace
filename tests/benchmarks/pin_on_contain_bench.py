#!/usr/bin/env python3
"""
Cost of keeping plain wrappers alive while their object is contained (#443).

Pin-on-contain keeps a contained object's Python wrapper alive for as long as the
container owns the object, for plain types as well as subclasses. This measures what
that costs and saves, for N plain entities in a GridData and N plain Captions in a
Frame, with the user's own references dropped:

  rss_kb          resident memory held after the build (wrappers that stay alive)
  gc_tracked      objects the cycle collector tracks
  gc_full_ms      one full gc.collect()
  iterate_ms      `for e in grid.entities: e.x` -- re-creates dead wrappers, or reuses
  index_ms        N random `grid.entities[i]` lookups

Usage: BENCH_N=10000 mcrogueface --headless --exec tests/benchmarks/pin_on_contain_bench.py
"""
import gc
import os
import random
import sys
import time

import mcrfpy

N = int(os.environ.get("BENCH_N", "10000"))
REPS = 10


def rss_kb():
    with open("/proc/self/statm") as f:
        return int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE") // 1024


def ms(fn, reps=REPS):
    best = float("inf")
    for _ in range(reps):
        t = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t)
    return best * 1000


def build():
    rng = random.Random(443)
    grid = mcrfpy.GridData(grid_size=(200, 200))
    frame = mcrfpy.Frame()
    for _ in range(N):
        grid.entities.append(mcrfpy.Entity(grid_pos=(rng.randrange(200), rng.randrange(200))))
        frame.children.append(mcrfpy.Caption(text="x"))
    return grid, frame


def main():
    gc.collect()
    base_rss, base_tracked = rss_kb(), len(gc.get_objects())

    t = time.perf_counter()
    grid, frame = build()
    build_ms = (time.perf_counter() - t) * 1000
    gc.collect()

    ents = grid.entities
    kids = frame.children
    rng = random.Random(1)
    idx = [rng.randrange(N) for _ in range(N)]

    def iterate():
        s = 0.0
        for e in ents:
            s += e.x
        for c in kids:
            s += c.x

    def index():
        for i in idx:
            ents[i]

    print(f"N                {N}")
    print(f"build_ms         {build_ms:.1f}")
    print(f"rss_kb           {rss_kb() - base_rss}")
    print(f"gc_tracked       {len(gc.get_objects()) - base_tracked}")
    print(f"gc_full_ms       {ms(gc.collect):.2f}")
    print(f"iterate_ms       {ms(iterate):.2f}")
    print(f"index_ms         {ms(index):.2f}")
    sys.exit(0)


if __name__ == "__main__":
    main()
