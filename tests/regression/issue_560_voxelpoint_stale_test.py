"""#560 A: a VoxelPoint names its cell by viewport + coordinates, never a raw pointer into the nav grid."""
import sys
import mcrfpy

fails = []
def check(c, m):
    if not c: fails.append(m)

vp = mcrfpy.Viewport3D(pos=(0, 0), size=(64, 64))
vp.grid_size = (4, 4)
p = vp.at(1, 1)
p.cost = 2.5
check(p.cost == 2.5, "cost round-trips")
vp.grid_size = (3000, 3000)          # reallocates navGrid_
p.cost = 1                           # was a use-after-free
check(p.cost == 1.0, "point still resolves after a grow")
check(p.grid_pos == (1, 1), "grid_pos")
q = vp.at(2999, 2999)
vp.grid_size = (2, 2)                # the cell no longer exists
for name, fn in (("get", lambda: q.cost), ("set", lambda: setattr(q, "walkable", False)),
                 ("pos", lambda: q.grid_pos)):
    try:
        fn(); fails.append(name + " on a stale cell did not raise")
    except RuntimeError:
        pass
check("stale" in repr(q), "repr of stale point")
check("stale" not in repr(vp.at(1, 1)), "repr of live point")
del vp
import gc; gc.collect()
try:
    p.cost; fails.append("point of a dead viewport did not raise")
except RuntimeError:
    pass
print("FAIL: " + "; ".join(fails) if fails else "PASS")
sys.exit(1 if fails else 0)
