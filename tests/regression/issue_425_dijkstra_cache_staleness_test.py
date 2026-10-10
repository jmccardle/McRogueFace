"""
Regression test for #425 -- cached Dijkstra maps went stale silently.

  1. get_dijkstra_map() cached per (root, collide label) and nothing invalidated
     the cache, so after a walkability edit it returned the old distances until
     clear_dijkstra_maps() was called.
  2. Worse for collide=: labelled entities block cells only while the map is
     computed, so moving one also left the cached map wrong -- and no
     walkability counter can see that.
  3. diagonal_cost was not in the key: a second cost evicted the first.
  4. A DijkstraMap borrowed the grid's TCODMap. invert() recomputed from it, so
     after the grid was freed it read freed memory (segfault), and even with the
     grid alive it recomputed without the collide= marks.

Now each cache entry is validated against the grid's walkability generation and
the cells its label blocks, and each map computes on its own snapshot.
"""

import gc
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def open_grid(w=10, h=3):
    g = mcrfpy.GridData(grid_size=(w, h))
    for y in range(h):
        for x in range(w):
            g.at(x, y).walkable = True
            g.at(x, y).transparent = True
    return g


def wall(g, x, walkable):
    for y in range(int(g.grid_size[1])):
        g.at(x, y).walkable = walkable


# 1. Walkability edits are seen by the next request, in both directions.
g = open_grid()
check(g.get_dijkstra_map((0, 1)).distance((9, 1)) == 9.0, "open row: distance 9")
wall(g, 5, False)
check(g.get_dijkstra_map((0, 1)).distance((9, 1)) is None,
      "after building a wall the cached map is rebuilt: unreachable")
wall(g, 5, True)
check(g.get_dijkstra_map((0, 1)).distance((9, 1)) == 9.0,
      "after removing it, reachable again")

# The cache still works: no edit, same map object.
check(g.get_dijkstra_map((0, 1)) is g.get_dijkstra_map((0, 1)),
      "an unchanged grid returns the cached map")

# A held map is a snapshot -- the cache is rebuilt, the held one is not mutated.
held = g.get_dijkstra_map((0, 1))
wall(g, 5, False)
check(held.distance((9, 1)) == 9.0, "a held map keeps the distances it was computed with")
check(g.get_dijkstra_map((0, 1)) is not held, "and the next request is a new map")
wall(g, 5, True)

# Transparency-only edits also bump the generation; harmless, but still correct.
g.at(3, 1).transparent = False
check(g.get_dijkstra_map((0, 1)).distance((9, 1)) == 9.0, "transparency edit: still correct")

# 2. collide=: moving a labelled entity is seen by the next request.
g = open_grid()
blockers = []
for y in range(3):
    e = mcrfpy.Entity((5, y), grid=g)
    e.labels = {"mob"}
    blockers.append(e)
check(g.get_dijkstra_map((0, 1), collide="mob").distance((9, 1)) is None,
      "a column of labelled entities blocks the map")
blockers[1].cell_pos = (0, 0)
check(g.get_dijkstra_map((0, 1), collide="mob").distance((9, 1)) == 9.0,
      "moving one out of the way: the next request sees the gap")
blockers[1].cell_pos = (5, 1)
check(g.get_dijkstra_map((0, 1), collide="mob").distance((9, 1)) is None,
      "moving it back: blocked again")
blockers[1].labels = set()
check(g.get_dijkstra_map((0, 1), collide="mob").distance((9, 1)) == 9.0,
      "removing the label opens the gap too")
check(g.get_dijkstra_map((0, 1)).distance((9, 1)) == 9.0,
      "a map without collide= ignores entities")

# 3. diagonal_cost is part of the key: two costs coexist.
g = open_grid(10, 10)
a = g.get_dijkstra_map((0, 0), diagonal_cost=1.41)
b = g.get_dijkstra_map((0, 0), diagonal_cost=2.0)
check(a is not b and abs(a.distance((5, 5)) - 5 * 1.41) < 0.01
      and abs(b.distance((5, 5)) - 10.0) < 0.01, "different costs give different maps")
check(g.get_dijkstra_map((0, 0), diagonal_cost=1.41) is a
      and g.get_dijkstra_map((0, 0), diagonal_cost=2.0) is b,
      "and both stay cached side by side")

# clear_dijkstra_maps() still releases.
g.clear_dijkstra_maps()
check(g.get_dijkstra_map((0, 0), diagonal_cost=1.41) is not a, "clear releases the cache")

# 4a. invert() after the grid is freed (was a segfault).
g = open_grid()
d = g.get_dijkstra_map((0, 1))
del g, a, b
gc.collect()
churn = [mcrfpy.GridData(grid_size=(40, 40)) for _ in range(20)]
inv = d.invert()
# Inverted = (farthest distance, the corner's 9.41) - distance.
check(abs(inv.distance((0, 1)) - 9.41) < 0.01 and abs(inv.distance((9, 1)) - 0.41) < 0.01,
      "invert() after the grid is freed: %r / %r" % (inv.distance((0, 1)), inv.distance((9, 1))))
check(d.distance((9, 1)) == 9.0 and d.step_from((9, 1)) == mcrfpy.Vector(8, 1),
      "distance/step_from after the grid is freed")

# 4b. invert() of a collide= map keeps the label's blocking.
g = open_grid()
for y in range(3):
    mcrfpy.Entity((5, y), grid=g).labels = {"mob"}
m = g.get_dijkstra_map((0, 1), collide="mob")
check(m.invert().distance((9, 1)) is None,
      "invert() of a collide= map: the blocked side stays unreachable")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
