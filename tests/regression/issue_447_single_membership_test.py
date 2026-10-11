"""Regression test for #447 - an entity belongs to one grid, a drawable to one parent.

Every mutation path MOVES an object: it leaves its old collection (another one, or an
earlier slot of this one) before it lands. Before the fix, EntityCollection insert /
extend / [i]= / [i:j]= and Entity.__init__(grid=) left the entity in both grids (and
insert/extend/slices into its own grid duplicated it), and drawable slice assignment
could duplicate a member. A value list naming one object twice now raises ValueError,
before anything moves.

Membership is checked three ways for entities: the list, the back-reference
(entity.grid), and the spatial hash (entities_in_radius).
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


def ids(coll):
    return [x.name for x in coll]


# ---------------------------------------------------------------- entities ----

def new_grid():
    return mcrfpy.Grid(grid_size=(10, 10))


def ent(name, x, grid=None):
    e = mcrfpy.Entity((x, 0), grid=grid)
    e.name = name
    return e


def where(e, grids):
    """(list memberships, hash memberships) of e across `grids`."""
    lists = [sum(1 for x in g.entities if x is e) for g in grids]
    hashed = [sum(1 for x in g.entities_in_radius((e.cell_x, e.cell_y), 0.5) if x is e)
              for g in grids]
    return lists, hashed


def one_home(label, e, home, grids):
    lists, hashed = where(e, grids)
    want = [1 if g is home else 0 for g in grids]
    check(lists == want and hashed == want and e.grid is home.grid_data,
          "%s: in exactly one grid (lists %r, hash %r)" % (label, lists, hashed))


MOVES = [
    ("append", lambda e, g2: g2.entities.append(e)),
    ("insert", lambda e, g2: g2.entities.insert(0, e)),
    ("extend", lambda e, g2: g2.entities.extend([e])),
    ("+=", lambda e, g2: g2.entities.__iadd__([e])),
    ("[0] = e", lambda e, g2: g2.entities.__setitem__(0, e)),
    ("[0:1] = [e]", lambda e, g2: g2.entities.__setitem__(slice(0, 1), [e])),
    ("[::2] = [e]", lambda e, g2: g2.entities.__setitem__(slice(0, None, 2), [e])),
    ("e.grid = g2", lambda e, g2: setattr(e, "grid", g2)),
    ("e.__init__(grid=g2)", lambda e, g2: e.__init__((3, 0), grid=g2)),
]
for label, move in MOVES:
    g1, g2 = new_grid(), new_grid()
    e = ent("e", 3, g1)
    ent("x", 5, g2)
    move(e, g2)
    one_home("entity " + label, e, g2, [g1, g2])
    check(all(x is not e for x in g1.entities), "entity %s: gone from the old grid" % label)

# Within one grid: a member moves to its new slot, never duplicates.
def three(g):
    return [ent(n, i, g) for i, n in enumerate("abc")]

g = new_grid(); a, b, c = three(g)
g.entities.append(a)
check(ids(g.entities) == ["b", "c", "a"], "append a member: moves to the end %r" % ids(g.entities))
g = new_grid(); a, b, c = three(g)
g.entities.insert(2, a)
check(ids(g.entities) == ["b", "c", "a"],
      "insert(2, a): index resolved after a leaves slot 0 %r" % ids(g.entities))
g = new_grid(); a, b, c = three(g)
g.entities.insert(0, c)
check(ids(g.entities) == ["c", "a", "b"], "insert(0, c) %r" % ids(g.entities))
g = new_grid(); a, b, c = three(g)
g.entities.extend([a])
check(ids(g.entities) == ["b", "c", "a"], "extend([a]) %r" % ids(g.entities))
g = new_grid(); a, b, c = three(g)
g.entities[1] = a
check(ids(g.entities) == ["a", "c"] and b.grid is None,
      "[1] = a replaces b (the element at 1), a leaves slot 0 %r" % ids(g.entities))
g = new_grid(); a, b, c = three(g)
g.entities[1] = b
check(ids(g.entities) == ["a", "b", "c"] and b.grid is g.grid_data, "[1] = b (itself) is a no-op")
g = new_grid(); a, b, c = three(g)
g.entities[0:0] = [c]
check(ids(g.entities) == ["c", "a", "b"], "[0:0] = [c] %r" % ids(g.entities))
g = new_grid(); a, b, c = three(g)
d = ent("d", 4, g)
g.entities[::2] = [d, b]
check(ids(g.entities) == ["d", "b"] and a.grid is None and c.grid is None,
      "[::2] = [d, b]: assigned slots kept, d and b leave theirs %r" % ids(g.entities))
for e in (a, b, c, d):
    if e.grid is not None:
        one_home("slice member " + e.name, e, g, [g])

# Duplicates in a value list raise ValueError before anything moves.
for label, op in (("extend([e, e])", lambda g, e: g.entities.extend([e, e])),
                  ("+= [e, e]", lambda g, e: g.entities.__iadd__([e, e])),
                  ("[0:1] = [e, e]", lambda g, e: g.entities.__setitem__(slice(0, 1), [e, e]))):
    g1, g2 = new_grid(), new_grid()
    e = ent("e", 3, g1)
    keep = ent("k", 1, g2)
    try:
        op(g2, e)
        check(False, "entity %s must raise ValueError" % label)
    except ValueError:
        check(ids(g2.entities) == ["k"] and e.grid is g1.grid_data and keep.grid is g2.grid_data,
              "entity %s: ValueError, nothing moved" % label)

# A subclass with no other reference survives a move (the pin follows it, #436).
class Mob(mcrfpy.Entity):
    pass

g1, g2 = new_grid(), new_grid()
m = Mob((2, 2), grid=g1)
m.tag = "kept"
r = weakref.ref(m)
g2.entities.insert(0, m)
del m
gc.collect()
check(r() is not None and r().tag == "kept" and g2.entities[0] is r() and len(g1.entities) == 0,
      "a moved subclass keeps its pin, type and attributes")

# Re-running __init__ detaches the entity it replaces and keeps live weakrefs.
g1, g2 = new_grid(), new_grid()
e = ent("e", 3, g1)
wr = weakref.ref(e)
e.__init__((4, 0), grid=g2)
check(len(g1.entities) == 0 and g1.entities_in_radius((3, 0), 0.5) == [],
      "re-init: the replaced entity left g1 (list and hash)")
check(wr() is e, "re-init: an existing weakref still resolves")
e.__init__((4, 0))
check(len(g2.entities) == 0 and e.grid is None, "re-init without grid=: leaves g2 too")

# The old grid no longer advances an entity that moved away.
g1, g2 = new_grid(), new_grid()
e = ent("e", 3, g1)
steps = []
e.step = lambda trigger, data: steps.append(trigger)
e.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(9, 9)])
g2.entities.insert(0, e)
g1.step()
check(steps == [], "the old grid's step() no longer reaches a moved entity")

# --------------------------------------------------------------- drawables ----

def fr(name):
    f = mcrfpy.Frame()
    f.name = name
    return f


def kids(p, *names):
    out = [fr(n) for n in names]
    for k in out:
        p.children.append(k)
    return out


p = mcrfpy.Frame(); a, b, c = kids(p, "a", "b", "c")
p.children[1] = a
check(ids(p.children) == ["a", "c"] and b.parent is None and a.parent is p,
      "drawable [1] = a replaces b, a leaves slot 0 %r" % ids(p.children))
p = mcrfpy.Frame(); a, b, c = kids(p, "a", "b", "c")
p.children[0:0] = [c]
check(ids(p.children) == ["c", "a", "b"], "drawable [0:0] = [c] moves c %r" % ids(p.children))
p = mcrfpy.Frame(); a, b, c, d = kids(p, "a", "b", "c", "d")
p.children[::2] = [d, b]
check(ids(p.children) == ["d", "b"] and a.parent is None and c.parent is None,
      "drawable [::2] = [d, b] %r" % ids(p.children))
q = mcrfpy.Frame(); x = fr("x"); q.children.append(x)
p = mcrfpy.Frame(); a, = kids(p, "a")
p.children[0:1] = [x]
check(ids(p.children) == ["x"] and len(q.children) == 0 and x.parent is p and a.parent is None,
      "drawable slice from another parent moves it")
for label, op in (("extend([a, a])", lambda p, a: p.children.extend([a, a])),
                  ("[0:1] = [a, a]", lambda p, a: p.children.__setitem__(slice(0, 1), [a, a]))):
    src = mcrfpy.Frame(); a, = kids(src, "a")
    p = mcrfpy.Frame(); k, = kids(p, "k")
    try:
        op(p, a)
        check(False, "drawable %s must raise ValueError" % label)
    except ValueError:
        check(ids(p.children) == ["k"] and a.parent is src, "drawable %s: ValueError, nothing moved" % label)

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
