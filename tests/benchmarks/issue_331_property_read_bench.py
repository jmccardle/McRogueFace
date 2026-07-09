#!/usr/bin/env python3
"""
Issue #331: micro-benchmark for hot property getters.

Times tight-loop reads of properties that (pre-fix) executed
PyImport_ImportModule("mcrfpy") + PyObject_GetAttrString + full type call
per read, versus the direct tp_alloc fast path (post-fix).

Direct-execution benchmark: no game loop needed, property reads work
immediately after object construction.

Usage:
    ./mcrogueface --headless --exec tests/benchmarks/issue_331_property_read_bench.py
"""

import mcrfpy
import sys
import time

N = 200_000


def bench(label, fn):
    start = time.perf_counter()
    fn()
    elapsed = time.perf_counter() - start
    per_read_ns = elapsed / N * 1e9
    print(f"{label:24s} {elapsed*1000:8.1f} ms total  {per_read_ns:8.0f} ns/read")
    return per_read_ns


def main():
    frame = mcrfpy.Frame(pos=(10, 20), size=(100, 100))
    layer = mcrfpy.ColorLayer(name="bench", z_index=0)
    grid = mcrfpy.Grid(grid_size=(8, 8), layers=[layer])
    layer.set((3, 3), (10, 20, 30, 255))

    def read_pos():
        for _ in range(N):
            frame.pos

    def read_origin():
        for _ in range(N):
            frame.origin

    def read_global_pos():
        for _ in range(N):
            frame.global_position

    def read_layer_at():
        for _ in range(N):
            layer.at((3, 3))

    print(f"issue #331 property-read benchmark, N={N}")
    results = {
        "pos": bench("frame.pos", read_pos),
        "origin": bench("frame.origin", read_origin),
        "global_pos": bench("frame.global_position", read_global_pos),
        "layer_at": bench("ColorLayer.at", read_layer_at),
    }

    # Sanity: values must be correct regardless of construction path
    p = frame.pos
    assert (p.x, p.y) == (10.0, 20.0), f"pos wrong: {p}"
    c = layer.at((3, 3))
    assert (c.r, c.g, c.b) == (10, 20, 30), f"color wrong: {c}"

    print("PASS")
    return results


if __name__ == "__main__":
    main()
    sys.exit(0)
