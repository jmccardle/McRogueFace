"""Regression test for #438 (3D side of #447) - an Entity3D in two viewports at once.

EntityCollection3D.append / extend never removed the entity from its previous
viewport's list (a TODO stood there), so it sat in both while `entity.viewport` named
only the last. Removing it from one then released a subclass's identity pin although
the other list still owned it, and the instance came back as a base Entity3D.

Now both paths go through Entity3D::moveToViewport(): the entity leaves its old list
first, appending a member moves it to the end, and extend() refuses duplicates.
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


def viewport():
    vp = mcrfpy.Viewport3D()
    vp.set_grid_size(16, 16)
    return vp


def count(vp, e):
    return sum(1 for x in vp.entities if x is e)


for label, move in (("append", lambda e, v2: v2.entities.append(e)),
                    ("extend", lambda e, v2: v2.entities.extend([e]))):
    v1, v2 = viewport(), viewport()
    e = mcrfpy.Entity3D(pos=(1, 1))
    v1.entities.append(e)
    move(e, v2)
    check((count(v1, e), count(v2, e)) == (0, 1),
          "%s to another viewport: in v1 x%d, v2 x%d" % (label, count(v1, e), count(v2, e)))

# A member appended again moves to the end, never twice.
v = viewport()
a, b = mcrfpy.Entity3D(pos=(1, 1)), mcrfpy.Entity3D(pos=(2, 2))
v.entities.extend([a, b])
v.entities.append(a)
check([x is a for x in v.entities] == [False, True], "append a member: moves to the end")

# Duplicates in extend() raise before anything moves.
v1, v2 = viewport(), viewport()
e = mcrfpy.Entity3D(pos=(1, 1))
v1.entities.append(e)
try:
    v2.entities.extend([e, e])
    check(False, "extend([e, e]) must raise ValueError")
except ValueError:
    check(count(v1, e) == 1 and len(v2.entities) == 0, "extend([e, e]): ValueError, nothing moved")

# The pin scenario from the issue: a subclass moved between viewports and then removed
# from the OLD one must not lose its pin -- it isn't there any more.
class Probe(mcrfpy.Entity3D):
    pass

v1, v2 = viewport(), viewport()
p = Probe(pos=(3, 3))
p.tag = "kept"
v1.entities.append(p)
v2.entities.append(p)
r = weakref.ref(p)
del p
try:
    v1.entities.remove(r())
    check(False, "removing from the old viewport must raise: it is no longer a member")
except ValueError:
    pass
gc.collect()
check(r() is not None and type(r()) is Probe and r().tag == "kept" and v2.entities[0] is r(),
      "the subclass stays pinned by its one viewport, type and attributes intact")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
