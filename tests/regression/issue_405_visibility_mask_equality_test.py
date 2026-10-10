"""
Regression test for #405 -- VisibilityMask had no value equality or hash.

The type inherited object's identity ==/hash, so two masks recording the same view
compared unequal and never deduplicated in a set -- the wrong answer for the
persistence/replay uses the type exists for, and a silent one.

Semantics decided for 0.3.0: == is VALUE equality over origin, fov_radius,
grid_size, cells, and light_walls/algorithm when an FOV computation ran (#404:
None otherwise). tick is NOT part of it -- the same view seen on two frames is
equal -- and `is` (identity) is what distinguishes two records. hash agrees
with ==. The type is also weakref-able now.
"""

import sys
import weakref

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


W, H = 12, 9
g = mcrfpy.GridData(grid_size=(W, H))
for y in range(H):
    for x in range(W):
        g.at(x, y).walkable = True
        g.at(x, y).transparent = not (x == 6 and y != 4)


def mask(**kw):
    return g.observe(**kw)["mask"]


# Equal values, distinct records.
a = mask(origin=(2, 4), fov_radius=6)
b = mask(origin=(2, 4), fov_radius=6)
check(a is not b, "two observe() calls return two records")
check(a == b and not (a != b), "same view -> ==")
check(hash(a) == hash(b), "equal masks hash equal")
check(len({a, b}) == 1, "and deduplicate in a set")

# tick does not participate.
mcrfpy.step(1.0)
mcrfpy.step(1.0)
c = mask(origin=(2, 4), fov_radius=6)
check(c.tick != a.tick, "precondition: a later frame (%d vs %d)" % (c.tick, a.tick))
check(c == a and hash(c) == hash(a), "the same view on a later frame is equal")
check(c is not a, "but `is` still tells the records apart")

# Every other field does.
check(mask(origin=(3, 4), fov_radius=6) != a, "different origin -> !=")
check(mask(origin=(2, 4), fov_radius=5) != a, "different fov_radius -> !=")
check(mask(origin=(2, 4)) != a, "unlimited radius vs 6 -> !=")
# light_walls/algorithm must count on their own, not via the cells they change: on an
# open, wall-free grid they make no difference to the cells, so only the field differs.
open_g = mcrfpy.GridData(grid_size=(9, 9))
for y in range(9):
    for x in range(9):
        open_g.at(x, y).transparent = True
base = open_g.observe(origin=(4, 4), fov_radius=2)["mask"]
lw = open_g.observe(origin=(4, 4), fov_radius=2, light_walls=False)["mask"]
alg = open_g.observe(origin=(4, 4), fov_radius=2, algorithm=mcrfpy.FOV.SHADOW)["mask"]
check(lw.cells == base.cells and lw != base, "different light_walls, same cells -> !=")
check(alg.cells == base.cells and alg != base,
      "different algorithm, same cells -> != (cells equal: %s)" % (alg.cells == base.cells))

g.at(4, 4).transparent = False
d = mask(origin=(2, 4), fov_radius=6)
check(d.cells != a.cells and d != a, "different cells -> !=")
g.at(4, 4).transparent = True

# Unbounded masks: light_walls/algorithm did not participate (#404), so they are
# equal whatever defaults observe() was handed.
u1 = mask()
u2 = mask(light_walls=False, algorithm=mcrfpy.FOV.SHADOW)
check(u1 == u2 and hash(u1) == hash(u2), "unbounded masks ignore light_walls/algorithm")
check(u1 != a, "unbounded vs bounded -> !=")

# A different grid with the same visible cells is a different record.
g2 = mcrfpy.GridData(grid_size=(W + 1, H))
for y in range(H):
    for x in range(W + 1):
        g2.at(x, y).transparent = not (x == 6 and y != 4)
e = g2.observe(origin=(2, 4), fov_radius=6)["mask"]
check(e.cells == a.cells and e != a, "different grid_size -> != even with equal cells")

# Not equal to other types; no ordering.
check(a != a.cells and not (a == a.cells), "a mask never equals a bare frozenset")
check(a != None and a != 0, "nor None / an int")
try:
    a < b
    check(False, "ordering must raise TypeError")
except TypeError:
    check(True, "ordering raises TypeError")

# Weakref support.
r = weakref.ref(a)
check(r() is a, "weakref.ref works")
cache = weakref.WeakValueDictionary({"k": b})
del b
check("k" not in cache, "a weakly-held mask is released when dropped")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
