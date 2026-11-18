"""#560 E: an EntityCollection3D iterator holds a std::list iterator. A same-size mutation (remove one,
append one) passes the size guard and left the cursor pointing at an erased node."""
import sys
import mcrfpy

fails = []
vp = mcrfpy.Viewport3D()
vp.set_grid_size(8, 8)
ents = [mcrfpy.Entity3D(pos=(i, 0)) for i in range(4)]
for e in ents:
    vp.entities.append(e)

it = iter(vp.entities)
next(it)
vp.entities.remove(ents[1])             # the node the cursor points at
vp.entities.append(mcrfpy.Entity3D(pos=(5, 5)))   # same size again: the guard is satisfied
try:
    for _ in range(6):
        next(it)
except (StopIteration, RuntimeError):
    pass

# the viewport dying mid-iteration
vp2 = mcrfpy.Viewport3D()
vp2.set_grid_size(4, 4)
for i in range(3):
    vp2.entities.append(mcrfpy.Entity3D(pos=(i, 0)))
it2 = iter(vp2.entities)
next(it2)
del vp2
import gc; gc.collect()
try:
    for _ in range(5):
        next(it2)
except (StopIteration, RuntimeError):
    pass
print("FAIL: " + "; ".join(fails) if fails else "PASS")
sys.exit(1 if fails else 0)
