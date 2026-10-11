"""#418 -- UICollection.clear() and EntityCollection.clear().

clear() empties a collection in one call with the same per-item teardown as remove():
drawables are unparented (Frame, GridView and Scene children), entities are detached
from the grid and its spatial hash, and both release the Python identity pin (#373/#436)
so an unreferenced subclass instance is freed. Python run by that release (a __del__)
may edit the collection; it sees an already-empty collection and its edit stands.
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


class MyFrame(mcrfpy.Frame):
    pass


class MyEntity(mcrfpy.Entity):
    pass


# --- drawable collections: Frame, GridView, Scene ---
scene = mcrfpy.Scene("t418")
owners = [("Frame.children", mcrfpy.Frame(pos=(0, 0), size=(50, 50))),
          ("GridView.children", mcrfpy.Grid(grid_size=(4, 4), pos=(0, 0), size=(64, 64))),
          ("Scene.children", scene)]
for name, owner in owners:
    kids = owner.children
    kept = [mcrfpy.Frame(), mcrfpy.Caption(text="x"), MyFrame()]
    for k in kept:
        kids.append(k)
    unheld = MyFrame()
    kids.append(unheld)
    ref = weakref.ref(unheld)
    del unheld
    gc.collect()
    check(ref() is not None and len(kids) == 4, "%s: the pin keeps an unheld subclass alive" % name)

    kids.clear()
    gc.collect()
    check(len(kids) == 0 and list(kids) == [], "%s: empty after clear()" % name)
    check(all(k.parent is None for k in kept), "%s: every member unparented" % name)
    check(ref() is None, "%s: the pin is released, the unheld subclass freed" % name)
    check(type(kept[2]) is MyFrame, "%s: a held subclass keeps its type" % name)
    kids.append(kept[2])
    check(len(kids) == 1 and kids[0] is kept[2], "%s: a cleared member can rejoin" % name)
    kids.clear()
    kids.clear()
    check(len(kids) == 0, "%s: clear() on an empty collection is a no-op" % name)

# A cleared Frame child moves cleanly to another parent.
a, b = mcrfpy.Frame(), mcrfpy.Frame()
c = mcrfpy.Frame()
a.children.append(c)
a.children.clear()
b.children.append(c)
check(c.parent is b and len(a.children) == 0, "a cleared child adopts a new parent")

# --- EntityCollection ---
g = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
kept = [mcrfpy.Entity((x, 5), grid=g) for x in range(5)] + [MyEntity((9, 9), grid=g)]
gone = MyEntity((10, 10), grid=g)
ref = weakref.ref(gone)
del gone
gc.collect()
check(ref() is not None and len(g.entities) == 7, "entities: the pin keeps an unheld subclass alive")

g.entities.clear()
gc.collect()
check(len(g.entities) == 0, "entities: empty after clear()")
check(all(e.grid is None for e in kept), "entities: every member detached")
check(ref() is None, "entities: the pin is released, the unheld subclass freed")
check(g.entities_in_radius((5, 5), 30) == [], "entities: spatial hash emptied")
check(g.at(2, 5).entities == [], "entities: no entity left on a cell")
check(type(kept[-1]) is MyEntity, "entities: a held subclass keeps its type")
g.entities.append(kept[0])
check(kept[0].grid is not None and g.entities_in_radius((0, 5), 1) == [kept[0]],
      "entities: a cleared entity rejoins, spatial hash included")
g.entities.clear()
g.entities.clear()
check(len(g.entities) == 0, "entities: clear() on an empty collection is a no-op")

# --- re-entrancy: a __del__ that edits the collection during clear() ---
holder = mcrfpy.Frame()
late = mcrfpy.Frame()


class Edits(mcrfpy.Frame):
    def __del__(self):
        holder.children.append(late)


holder.children.append(Edits())
holder.children.append(mcrfpy.Frame())
holder.children.clear()
gc.collect()
check(list(holder.children) == [late] and late.parent is holder,
      "children: an append from __del__ during clear() stands")

g = mcrfpy.Grid(grid_size=(8, 8))
late_e = mcrfpy.Entity((1, 1))


class EditsE(mcrfpy.Entity):
    def __del__(self):
        g.entities.append(late_e)


EditsE((2, 2), grid=g)
mcrfpy.Entity((3, 3), grid=g)
g.entities.clear()
gc.collect()
check(list(g.entities) == [late_e] and g.entities_in_radius((1, 1), 0.5) == [late_e],
      "entities: an append from __del__ during clear() stands, spatial hash included")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
