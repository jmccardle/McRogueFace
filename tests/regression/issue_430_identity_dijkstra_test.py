#!/usr/bin/env python3
"""
DijkstraMap object identity (#430, Phase 2: dijkstra group).

GridData caches DijkstraMap C++ objects by (root, collide label). get_dijkstra_map()
used to tp_alloc a fresh wrapper per call even on a cache hit, so two requests for the
same root returned two different Python objects around the same C++ map. The wrapper
is now cached on DijkstraMap::serial_number, so the same C++ map is the same Python
object. invert() returns a NEW C++ map, so it is a new object every time.

DijkstraMap cannot be constructed or subclassed from Python, so there is no
user-instance case to check here.
"""
import gc
import sys
import weakref

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def same(label, get):
    try:
        a, b = get(), get()
    except Exception as exc:  # an accessor that raises is a failure, not a skip
        check(False, f"{label}: raised {type(exc).__name__}: {exc}")
        return
    check(a is not None and a is b, f"{label} is stable")


def get_dijkstra_map():
    print("get_dijkstra_map")
    g = mcrfpy.Grid(grid_size=(10, 10))
    for y in range(10):
        for x in range(10):
            g.at(x, y).walkable = True
            g.at(x, y).transparent = True

    same("grid.get_dijkstra_map((5, 5))", lambda: g.get_dijkstra_map((5, 5)))
    same("grid_data.get_dijkstra_map((5, 5))", lambda: g.grid_data.get_dijkstra_map((5, 5)))
    check(g.get_dijkstra_map((5, 5)) is g.grid_data.get_dijkstra_map((5, 5)),
          "view and grid_data return the same cached map")
    check(g.get_dijkstra_map(roots=[(5, 5)]) is g.get_dijkstra_map((5, 5)),
          "roots=[r] and root=r share the cached map")
    check(g.get_dijkstra_map((1, 1)) is not g.get_dijkstra_map((5, 5)),
          "different roots are different maps")

    d = g.get_dijkstra_map((2, 2))
    check(weakref.ref(d)() is d, "DijkstraMap is weak-referenceable")

    # Dropping every Python reference must not break the next lookup: the C++ map is
    # still cached by the grid, so a new wrapper is built and then stays stable.
    del d
    gc.collect()
    same("get_dijkstra_map((2, 2)) after the wrapper died", lambda: g.get_dijkstra_map((2, 2)))

    # clear_dijkstra_maps() drops the C++ map; the next request is a new map.
    before = g.get_dijkstra_map((3, 3))
    g.clear_dijkstra_maps()
    after = g.get_dijkstra_map((3, 3))
    check(after is not before, "clear_dijkstra_maps() yields a new map object")
    check(after.distance((3, 3)) == 0.0, "the new map still works")
    check(before.distance((3, 3)) == 0.0, "the old wrapper keeps its map alive")

    # Multi-root maps are not cached by the grid: each call is a new C++ map.
    m1 = g.get_dijkstra_map(roots=[(0, 0), (9, 9)])
    m2 = g.get_dijkstra_map(roots=[(0, 0), (9, 9)])
    check(m1 is not m2, "uncached multi-root maps are distinct objects")


def invert():
    print("invert")
    g = mcrfpy.Grid(grid_size=(8, 8))
    for y in range(8):
        for x in range(8):
            g.at(x, y).walkable = True
    d = g.get_dijkstra_map((4, 4))
    inv = d.invert()
    check(isinstance(inv, mcrfpy.DijkstraMap), "invert() returns a DijkstraMap")
    check(inv is not d, "invert() is not the source map")
    check(d.invert() is not inv, "each invert() is a new map")
    check(weakref.ref(inv)() is inv, "inverted map is weak-referenceable")
    check(g.get_dijkstra_map((4, 4)) is d, "invert() leaves the cached map in place")


def main():
    get_dijkstra_map()
    invert()
    if failures:
        print(f"FAIL: {len(failures)} failure(s)")
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
