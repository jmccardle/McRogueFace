#!/usr/bin/env python3
"""
Regression test for issue #329: grid.entities[i] must be O(1), not O(n).

UIEntityCollection previously wrapped std::list and did std::advance() from
begin() on every indexed access, making grid.entities[i] O(n) and a full
"for i in range(len(e)): e[i]" loop O(n^2). After switching the backing
container to std::vector, indexed access is O(1).

This test builds a large entity collection and times a full indexed pass.
With the O(n^2) implementation this pass grows quadratically; with the O(n)
implementation it stays linear. We use a generous wall-clock bound so CI
noise cannot flake it -- the point is to catch a catastrophic regression to
quadratic behavior, not to microbenchmark.
"""

import mcrfpy
import sys
import time

N = 5000
# Generous bound: an O(1)-per-index vector pass finishes in tens of ms.
# The old O(n^2) list pass over 5000 entities does ~12.5M node advances.
WALL_CLOCK_BUDGET = 2.0  # seconds


def main():
    scene = mcrfpy.Scene("issue_329_perf")
    grid = mcrfpy.Grid(grid_size=(200, 200), pos=(0, 0), size=(400, 400))
    scene.children.append(grid)
    entities = grid.entities

    for i in range(N):
        entities.append(mcrfpy.Entity((i % 200, (i // 200) % 200)))

    assert len(entities) == N, "expected %d entities, got %d" % (N, len(entities))

    # Full indexed pass -- this is the O(n^2) hot path in the old code.
    start = time.perf_counter()
    total = 0
    for i in range(N):
        e = entities[i]
        if e is not None:
            total += 1
    elapsed = time.perf_counter() - start

    print("indexed %d entities in %.4f s (budget %.1f s)" %
          (N, elapsed, WALL_CLOCK_BUDGET))
    assert total == N, "expected to visit %d entities, visited %d" % (N, total)

    if elapsed >= WALL_CLOCK_BUDGET:
        print("FAIL: indexed pass took %.4f s (>= %.1f s) -- likely O(n^2)"
              % (elapsed, WALL_CLOCK_BUDGET))
        return False

    # Sanity: accessing the last element should not be dramatically slower
    # than accessing the first (O(1) random access).
    t0 = time.perf_counter()
    for _ in range(2000):
        _ = entities[0]
    first_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(2000):
        _ = entities[N - 1]
    last_time = time.perf_counter() - t0

    print("2000x first-index: %.4f s, 2000x last-index: %.4f s"
          % (first_time, last_time))
    # With a list, last_time would be ~N times first_time. Allow a very
    # generous constant-factor slack (20x) to stay noise-proof.
    if last_time > (first_time + 0.01) * 20:
        print("FAIL: last-index access %.4f s vastly exceeds first-index "
              "%.4f s -- indexed access is not O(1)" % (last_time, first_time))
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
