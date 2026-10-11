"""Regression test for #446 - removing an entity through grid.entities left it drawn.

Nothing in UIEntityCollection marked the grid dirty, so the view's render early-out
(#351) kept re-blitting its stale texture: `remove`, `pop` and `del` left the entity on
screen, cached or not. `entity.die()` did repaint. The fix makes UIEntity::setGrid() --
the one place membership changes -- mark the old and new grids dirty.

Each case: the grid renders empty, the entity is added (the screen must change), then
removed (the screen must return to the empty image). Every case runs with and without a
Frame(cache_subtree=True) around the grid.
"""
import mcrfpy
from mcrfpy import automation
import sys, os, tempfile

TMPDIR = tempfile.mkdtemp(prefix="mcrf446_")
_n = 0
failures = []


def shot():
    global _n
    p = os.path.join(TMPDIR, "s%d.png" % _n)
    _n += 1
    automation.screenshot(p)
    with open(p, "rb") as f:
        return f.read()


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def add_ctor(g):
    return mcrfpy.Entity((3, 3), grid=g)


def add_append(g):
    e = mcrfpy.Entity((3, 3))
    g.entities.append(e)
    return e


def add_insert(g):
    e = mcrfpy.Entity((3, 3))
    g.entities.insert(0, e)
    return e


def add_extend(g):
    e = mcrfpy.Entity((3, 3))
    g.entities.extend([e])
    return e


def add_grid_setter(g):
    e = mcrfpy.Entity((3, 3))
    e.grid = g
    return e


ADDS = [("Entity(grid=)", add_ctor), ("append", add_append), ("insert", add_insert),
        ("extend", add_extend), ("entity.grid = g", add_grid_setter)]


def rm_setitem(g, e):
    # Replace with an entity off-screen: the old one must vanish.
    g.entities[g.entities.index(e)] = mcrfpy.Entity((60, 60))


REMOVES = [
    ("remove", lambda g, e: g.entities.remove(e)),
    ("pop()", lambda g, e: g.entities.pop()),
    ("pop(0)", lambda g, e: g.entities.pop(0)),
    ("del [i]", lambda g, e: g.entities.__delitem__(0)),
    ("del [:]", lambda g, e: g.entities.__delitem__(slice(None))),
    ("[i] = other", rm_setitem),
    ("entity.grid = None", lambda g, e: setattr(e, "grid", None)),
    ("die", lambda g, e: e.die()),
]

if hasattr(mcrfpy.EntityCollection if hasattr(mcrfpy, "EntityCollection") else object, "clear"):
    REMOVES.append(("clear", lambda g, e: g.entities.clear()))


def build(scene, cache):
    holder = mcrfpy.Frame(pos=(0, 0), size=(300, 300), cache_subtree=cache)
    g = mcrfpy.Grid(grid_size=(64, 64), pos=(10, 10), size=(256, 256))
    holder.children.append(g)
    scene.children.append(holder)
    return holder, g


scene = mcrfpy.Scene("t446")
scene.activate()
for cache in (False, True):
    for aname, add in ADDS:
        holder, g = build(scene, cache)
        empty = shot()
        add(g)
        check(shot() != empty, "cache=%s: %s draws the entity" % (cache, aname))
        scene.children.remove(holder)
    for rname, remove in REMOVES:
        holder, g = build(scene, cache)
        empty = shot()
        e = add_ctor(g)
        check(shot() != empty, "cache=%s %s: entity drawn" % (cache, rname))
        remove(g, e)
        check(shot() == empty, "cache=%s: %s erases the entity" % (cache, rname))
        scene.children.remove(holder)

# Moving an entity between grids repaints both.
for cache in (False, True):
    h1, g1 = build(scene, cache)
    h2 = mcrfpy.Frame(pos=(300, 0), size=(300, 300), cache_subtree=cache)
    g2 = mcrfpy.Grid(grid_size=(64, 64), pos=(10, 10), size=(256, 256))
    h2.children.append(g2)
    scene.children.append(h2)
    empty = shot()
    e = add_ctor(g1)
    one = shot()
    e.grid = g2
    two = shot()
    check(two != one and two != empty, "cache=%s: moving to another grid repaints both" % cache)
    g2.entities.append(e)   # already there: no change
    check(shot() == two, "cache=%s: idle after the move" % cache)
    scene.children.remove(h1)
    scene.children.remove(h2)

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
