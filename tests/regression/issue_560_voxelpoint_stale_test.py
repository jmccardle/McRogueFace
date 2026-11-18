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

# strong hold, as GridPoint: a point of a temporary viewport keeps working
def temp_point():
    v = mcrfpy.Viewport3D(pos=(0, 0), size=(64, 64))
    v.grid_size = (2, 2)
    return v.at(0, 0)          # the viewport itself is unreferenced once this returns
t = temp_point()
import gc; gc.collect()
t.cost = 3
check(t.cost == 3.0, "point of a temporary viewport still works")
# ...and it is not a cycle: dropping the last name frees the viewport
import weakref
v2 = mcrfpy.Viewport3D(pos=(0, 0), size=(64, 64))
v2.grid_size = (2, 2)
w2 = weakref.ref(v2)
p2 = v2.at(0, 0)
del v2, p2; gc.collect()
check(w2() is None, "viewport freed once its points are gone (no cycle)")

# float setters: errors propagate, nothing leaks, nothing is stored on failure
q = vp.at(0, 0)
q.height = 2.0
for bad, exc in ((1j, TypeError), ("x", TypeError), (10**400, OverflowError), (float("nan"), ValueError)):
    try:
        q.height = bad; fails.append(f"height = {bad!r} did not raise")
    except exc:
        pass
    except BaseException as e:
        fails.append(f"height = {bad!r}: {type(e).__name__}")
check(q.height == 2.0, "failed assignment stores nothing")
q.height = 10**30
check(abs(q.height - 1e30) < 1e24, "a large but finite int is stored")
try:
    q.cost = -1; fails.append("negative cost accepted")
except ValueError:
    pass
before = sys.getrefcount(1j)
for _ in range(1000):
    try: q.height = 1j
    except TypeError: pass
check(sys.getrefcount(1j) - before < 5, "refcount stable over 1000 failed assignments")
x = 12345.678
r0 = sys.getrefcount(x)
for _ in range(1000):
    q.height = x
check(abs(sys.getrefcount(x) - r0) < 3, "refcount stable over 1000 assignments")
print("FAIL: " + "; ".join(fails) if fails else "PASS")
sys.exit(1 if fails else 0)
