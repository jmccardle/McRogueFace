"""Benchmark: grid.step() turn manager with a mix of behaviors.

100 entities on a 100x100 grid, 1000 rounds. Mix of IDLE / NOISE4 / SEEK / FLEE.
Reports total time, mean per-round, p95 per-round.

Usage:
  ./mcrogueface --headless --exec ../tests/benchmarks/grid_step_bench.py
"""
import mcrfpy
import sys
import os
import time
import random
import json

sys.path.insert(0, os.path.dirname(__file__))
import _baseline


GRID_W, GRID_H = 100, 100
N_ENTITIES = 100
N_ROUNDS = 1000
SEED = 0x37


def main():
    rng = random.Random(SEED)
    scene = mcrfpy.Scene("bench_step")
    mcrfpy.current_scene = scene
    grid = mcrfpy.Grid(grid_size=(GRID_W, GRID_H))
    scene.children.append(grid)

    for y in range(GRID_H):
        for x in range(GRID_W):
            c = grid.at(x, y)
            walkable = (x not in (0, GRID_W - 1)) and (y not in (0, GRID_H - 1))
            c.walkable = walkable
            c.transparent = walkable

    # One shared threat / attractor in the center.
    center = (GRID_W // 2, GRID_H // 2)
    attractor = grid.get_dijkstra_map(center)
    safety = attractor.invert()

    for i in range(N_ENTITIES):
        ex = rng.randrange(1, GRID_W - 1)
        ey = rng.randrange(1, GRID_H - 1)
        e = mcrfpy.Entity((ex, ey), grid=grid)
        e.move_speed = 0
        mix = i % 4
        if mix == 0:
            pass  # IDLE default
        elif mix == 1:
            e.set_behavior(int(mcrfpy.Behavior.NOISE8))
        elif mix == 2:
            e.set_behavior(int(mcrfpy.Behavior.SEEK), pathfinder=attractor)
        else:
            e.set_behavior(int(mcrfpy.Behavior.FLEE), pathfinder=safety)

    round_times = []
    t_suite_start = time.perf_counter()
    for _ in range(N_ROUNDS):
        t0 = time.perf_counter()
        grid.step()
        round_times.append(time.perf_counter() - t0)
    total = time.perf_counter() - t_suite_start

    round_times.sort()
    p95 = round_times[int(0.95 * len(round_times))]
    per_step_us = (total / N_ROUNDS) / N_ENTITIES * 1e6

    out = {
        "grid": f"{GRID_W}x{GRID_H}",
        "entities": N_ENTITIES,
        "rounds": N_ROUNDS,
        "total_sec": total,
        "mean_round_ms": (total / N_ROUNDS) * 1000.0,
        "p95_round_ms": p95 * 1000.0,
        "per_entity_step_us": per_step_us,
    }
    print(f"  total:         {total:.2f} s")
    print(f"  mean round:    {out['mean_round_ms']:.3f} ms")
    print(f"  p95 round:     {out['p95_round_ms']:.3f} ms")
    print(f"  per-entity:    {out['per_entity_step_us']:.2f} us")
    print(json.dumps(out, indent=2))
    _baseline.write("grid_step_bench.json", out)
    print("DONE")


if __name__ == "__main__":
    main()
    sys.exit(0)
