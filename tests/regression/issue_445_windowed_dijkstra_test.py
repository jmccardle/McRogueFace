"""
#445 -- windowed Dijkstra maps.

A field covers a WINDOW: the roots' bounding box grown by `radius` (default: the
whole grid, up to 511) and clipped to the grid, so it is off-centre at the edges and
never allocates an out-of-bounds cell. Every distance it reports is exact: up to the
radius in general, everywhere when the field is `complete` (the flood never reached
a window edge that isn't a grid edge). Beyond that -- including off the grid --
distance() is the map's heuristic estimate, and heuristic=None makes such a query
raise. Decisions: always answer, cut at r, window-sized to_heightmap.
"""

import random
import sys

import mcrfpy

H = mcrfpy.Heuristic
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def grid_of(w, h, wall=lambda x, y: False):
    g = mcrfpy.GridData(grid_size=(w, h))
    for y in range(h):
        for x in range(w):
            g.at(x, y).walkable = not wall(x, y)
            g.at(x, y).transparent = True
    return g


def octile(dx, dy, d=1.41):
    dx, dy = abs(dx), abs(dy)
    return max(dx, dy) + (min(d, 2.0) - 1.0) * min(dx, dy)


# 1. Small grids are unchanged: the default window is the whole grid, and complete.
g = grid_of(30, 20)
dm = g.get_dijkstra_map((4, 4))
check(dm.window == (0, 0, 30, 20), "default window on 30x20 is the whole grid: %r" % (dm.window,))
check(dm.radius == 30 and dm.complete, "default radius = max(w, h) = 30, complete")
check(dm.heuristic == H.OCTILE, "default heuristic is OCTILE")
check(g.dijkstra_cache_bytes == 30 * 20 * 4, "cache counts the window: %d" % g.dijkstra_cache_bytes)

# 2. The window is clipped, off-centre at the edges, and sized exactly.
g = grid_of(100, 100)
for root, r, want in (((2, 3), 10, (0, 0, 13, 14)),
                      ((97, 50), 10, (87, 40, 13, 21)),
                      ((50, 50), 10, (40, 40, 21, 21)),
                      ((0, 99), 0, (0, 99, 1, 1))):
    m = g.get_dijkstra_map(root, radius=r)
    check(m.window == want, "root %r radius %d -> window %r (got %r)" % (root, r, want, m.window))
    hm = m.to_heightmap()
    check(hm.size == (want[2], want[3]), "to_heightmap is window-sized: %r" % (hm.size,))
check(g.get_dijkstra_map((50, 50)).radius == 100, "default radius on 100x100 is 100")

big = mcrfpy.GridData(grid_size=(1500, 600))
check(big.get_dijkstra_map((700, 300), heuristic=None).radius == 511,
      "default radius caps at 511 on a 1500-wide grid")

# 3. Exactness on random mazes: every reported distance equals the full-grid one, and
#    every cell within the radius is reported.
rng = random.Random(445)
for trial in range(4):
    W = 61
    walls = {(x, y) for y in range(W) for x in range(W) if rng.random() < 0.28}
    walls.discard((30, 30))
    g = grid_of(W, W, lambda x, y: (x, y) in walls)
    full = g.get_dijkstra_map((30, 30))          # radius 61: the whole grid
    R = 9 + trial * 4
    win = g.get_dijkstra_map((30, 30), radius=R)
    bad = []
    within = 0
    for y in range(W):
        for x in range(W):
            fd = full.distance((x, y))
            wd = win.distance((x, y))
            if win.is_exact((x, y)):
                if wd != fd:
                    bad.append(((x, y), wd, fd))
            elif fd is not None and fd <= R:
                bad.append(((x, y), "not exact", fd))
            if fd is not None and fd <= R:
                within += 1
            if not win.is_exact((x, y)) and not (wd >= R):
                bad.append(((x, y), "estimate below radius", wd))
    check(not bad, "maze %d, radius %d: %d cells within radius exact, mismatches %r"
          % (trial, R, within, bad[:3]))

# 4. Completeness: a walled room inside the window is complete -- exact everywhere,
#    outside certainly unreachable (None), including off the grid.
room = lambda x, y: (x in (40, 50) and 40 <= y <= 50) or (y in (40, 50) and 40 <= x <= 50)
g = grid_of(100, 100, room)
m = g.get_dijkstra_map((45, 45), radius=20)
check(m.complete, "a room inside the window: complete")
check(m.distance((5, 5)) is None and m.distance((-3, 500)) is None,
      "outside the room, on or off the grid: None")
check(m.is_exact((5, 5)), "and that None is exact")
m2 = g.get_dijkstra_map((45, 45), radius=3)
check(not m2.complete, "radius 3 inside a 9x9 room: the flood reaches the window edge")

# 5. Beyond the field: the estimate, floored at the radius; heuristic choice; None raises.
g = grid_of(200, 200)
m = g.get_dijkstra_map((100, 100), radius=10)
for p in ((150, 130), (100, 300), (-50, -50)):
    want = max(octile(p[0] - 100, p[1] - 100), 10.0)
    check(abs(m.distance(p) - want) < 1e-3 and not m.is_exact(p),
          "OCTILE estimate at %r = %.3f (got %r)" % (p, want, m.distance(p)))
check(abs(m.distance((103, 104)) - (4 + 0.41 * 3)) < 1e-3 and m.is_exact((103, 104)),
      "inside the radius: exact")
mc = g.get_dijkstra_map((100, 100), radius=10, heuristic=H.CHEBYSHEV)
check(mc.heuristic == H.CHEBYSHEV and abs(mc.distance((150, 130)) - 50.0) < 1e-6,
      "CHEBYSHEV estimate: %r" % mc.distance((150, 130)))
mn = g.get_dijkstra_map((100, 100), radius=10, heuristic=None)
check(mn.heuristic is None and mn.distance((103, 104)) is not None,
      "heuristic=None: exact queries still answer")
try:
    mn.distance((150, 130))
    check(False, "heuristic=None beyond the field must raise")
except IndexError as e:
    check("heuristic" in str(e), "heuristic=None beyond the field raises IndexError")

# diagonal_cost below 1: the exact threshold is radius * diagonal_cost (a path of that
# cost still has at most `radius` steps). Same maze comparison at d = 0.5.
rng = random.Random(4450)
W = 41
walls = {(x, y) for y in range(W) for x in range(W) if rng.random() < 0.3}
walls.discard((20, 20))
g = grid_of(W, W, lambda x, y: (x, y) in walls)
full = g.get_dijkstra_map((20, 20), diagonal_cost=0.5)
win = g.get_dijkstra_map((20, 20), diagonal_cost=0.5, radius=8)
bad = [(x, y) for y in range(W) for x in range(W)
       if (win.is_exact((x, y)) and win.distance((x, y)) != full.distance((x, y)))
       or (not win.is_exact((x, y)) and full.distance((x, y)) is not None
           and full.distance((x, y)) <= 4.0)]
check(not bad, "diagonal_cost 0.5, radius 8: exact to 4.0 (mismatches %r)" % (bad[:3],))
check(not win.complete and abs(win.distance((40, 0)) - max(octile(20, 20, 0.5), 4.0)) < 1e-3,
      "and the estimate floor is 4.0")

# 6. Multi-root and mask windows: the bounding box grown by radius.
g = grid_of(100, 100)
m = g.get_dijkstra_map(roots=[(10, 10), (30, 12)], radius=5)
check(m.window == (5, 5, 31, 13), "multi-root window %r" % (m.window,))
mask = mcrfpy.DiscreteMap((100, 100))
mask.fill(1, pos=(60, 70), size=(3, 2))
m = g.get_dijkstra_map(roots=mask, radius=4)
check(m.window == (56, 66, 11, 10), "mask window %r" % (m.window,))
check(m.distance((61, 71)) == 0.0, "a mask cell is a root")

# 7. The cache keys radius and heuristic.
a = g.get_dijkstra_map((50, 50), radius=5)
check(g.get_dijkstra_map((50, 50), radius=5) is a, "same radius: cached")
check(g.get_dijkstra_map((50, 50), radius=6) is not a, "different radius: a different map")
check(g.get_dijkstra_map((50, 50), radius=5, heuristic=H.CHEBYSHEV) is not a,
      "different heuristic: a different map")

# 8. collide= blocks inside the window copy; the field respects it.
g = grid_of(40, 3)
for y in range(3):
    mcrfpy.Entity((20, y), grid=g).labels = {"mob"}
m = g.get_dijkstra_map((5, 1), collide="mob", radius=40)
check(m.complete and m.distance((30, 1)) is None, "labelled wall blocks the field")
check(g.find_path((5, 1), (30, 1)) is not None, "and the grid's own map is untouched")

# 9. SEEK from beyond the window walks in (greedy), then follows the exact field.
g = grid_of(120, 40)
target = (10, 20)
m = g.get_dijkstra_map(target, radius=8)
e = mcrfpy.Entity((100, 20), grid=g)
e.move_speed = 0
e.set_behavior(mcrfpy.Behavior.SEEK, pathfinder=m)
for _ in range(120):
    g.step()
check((e.cell_x, e.cell_y) == target, "SEEK from 90 cells outside the window arrives: %r"
      % ((e.cell_x, e.cell_y),))

# FLEE: the inverted field, then the inverted estimate, keep moving away.
f = mcrfpy.Entity((12, 20), grid=g)
f.move_speed = 0
f.set_behavior(mcrfpy.Behavior.FLEE, pathfinder=m.invert())
for _ in range(40):
    g.step()
check(f.cell_x > 40, "FLEE leaves the window and keeps going: x=%d" % f.cell_x)

# 10. Beyond the field without the grid: greedy steps need it, exact ones don't.
g = grid_of(60, 60)
m = g.get_dijkstra_map((30, 30), radius=5)
check(m.step_from((50, 30)) == mcrfpy.Vector(49, 30), "greedy step while the grid lives")
del g
check(m.step_from((50, 30)) is None, "greedy step after the grid is gone: None")
check(m.step_from((33, 30)) == mcrfpy.Vector(32, 30), "exact step after the grid is gone")
check(m.path_from((50, 30)) is None, "path_from beyond the field: None")

# 11. Heuristic.OCTILE in find_path.
g = grid_of(20, 20)
p = g.find_path((0, 0), (15, 9), heuristic=H.OCTILE)
check(p is not None and len(p) == 15, "find_path with OCTILE: %r" % (len(p) if p else p))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
