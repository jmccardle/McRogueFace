"""#540 E: libtcod does BSP / bezier arithmetic in plain int. Instead of one magic bound, each
site checks the real invariant in int64 and raises ValueError naming the argument; the largest
accepted values must run clean (under `make asan`: no UBSan report).

BSP(pos, size):       x + w and y + h must fit in int.
BSP.split_once:       position - x, x + w - position (and the y forms) must fit in int.
BSP.split_recursive:  libtcod computes 2*min, x + min, x + w - min, and picks positions in
                      [x + w - min, x + min] (the interval is reversed when min > w / 2), so every
                      split edge lies within `min` of the hull of its parent's edges. After
                      `depth` levels all edges are in [x - (depth+1)*min, x + w + (depth+1)*min];
                      that hull must lie inside int and be narrower than INT_MAX (random_get_i
                      computes max - min + 1). Checked per axis with its own min size.
dig_bezier:           libtcod computes 3 * px[i] in int: |coordinate| <= INT_MAX / 3."""
import sys
import mcrfpy

fails = []
I32 = 2**31
IMAX = I32 - 1
IMIN = -I32


def expect_value_error(label, fn, name):
    try:
        fn()
    except ValueError as e:
        if name not in str(e):
            fails.append(f"{label}: message {str(e)!r} does not name {name!r}")
        return
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want ValueError")
        return
    fails.append(f"{label}: accepted")


def ok(label, fn):
    try:
        return fn()
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want success")


# ---- BSP(pos, size) ----
expect_value_error("BSP x + w", lambda: mcrfpy.BSP(pos=(IMAX, 0), size=(10, 10)), "pos")
expect_value_error("BSP y + h", lambda: mcrfpy.BSP(pos=(0, IMAX - 5), size=(10, 10)), "pos")
expect_value_error("BSP x + w by one", lambda: mcrfpy.BSP(pos=(IMAX - 9, 0), size=(10, 10)), "pos")
for label, pos in (("max", (IMAX - 10, IMAX - 10)), ("min", (IMIN, IMIN)), ("origin", (0, 0))):
    b = ok(f"BSP {label} accepted", lambda: mcrfpy.BSP(pos=pos, size=(10, 10)))
    if b is not None:
        ok(f"BSP {label} split_once", lambda: b.split_once(False, pos[0] + 5))
        ok(f"BSP {label} len", lambda: len(b))

# ---- split_once ----
b = mcrfpy.BSP(pos=(0, 0), size=(10, 10))
expect_value_error("split_once position -2**31 (right size overflows)", lambda: b.split_once(True, IMIN), "position")
expect_value_error("split_once position INT_MIN vertical", lambda: b.split_once(False, IMIN), "position")
b = mcrfpy.BSP(pos=(-5, -5), size=(10, 10))
expect_value_error("split_once position INT_MAX with negative origin", lambda: b.split_once(False, IMAX), "position")
b = mcrfpy.BSP(pos=(0, 0), size=(10, 10))
ok("split_once position INT_MAX (left size INT_MAX fits)", lambda: b.split_once(False, IMAX))
b = mcrfpy.BSP(pos=(0, 0), size=(10, 10))
ok("split_once position 5", lambda: b.split_once(True, 5))

# ---- split_recursive: hull of depth+1 minimums must stay inside int ----
def split(x, y, w, h, depth, mw, mh):
    bsp = mcrfpy.BSP(pos=(x, y), size=(w, h))
    return bsp.split_recursive(depth=depth, min_size=(mw, mh), seed=1)

expect_value_error("min_size 2**30", lambda: split(0, 0, 100, 100, 1, 2**30, 1), "min_size")
expect_value_error("min_size 2**30 (y)", lambda: split(0, 0, 100, 100, 1, 1, 2**30), "min_size")
expect_value_error("min_size IMAX", lambda: split(0, 0, 100, 100, 1, IMAX, IMAX), "min_size")
d, m, w = 2, 3, 10
top = IMAX - w - (d + 1) * m      # largest x with x + w + (d+1)*min == INT_MAX
low = IMIN + (d + 1) * m          # smallest x with x - (d+1)*min == INT_MIN
ok("split_recursive at the high edge", lambda: split(top, 0, w, 10, d, m, m))
ok("split_recursive at the low edge", lambda: split(low, 0, w, 10, d, m, m))
ok("split_recursive at the high edge (y)", lambda: split(0, top, 10, w, d, m, m))
ok("split_recursive at the low edge (y)", lambda: split(0, low, 10, w, d, m, m))
expect_value_error("split_recursive one past the high edge", lambda: split(top + 1, 0, w, 10, d, m, m), "min_size")
expect_value_error("split_recursive one past the low edge", lambda: split(low - 1, 0, w, 10, d, m, m), "min_size")
expect_value_error("split_recursive one past the high edge (y)", lambda: split(0, top + 1, 10, w, d, m, m), "min_size")
ok("split_recursive ordinary", lambda: split(0, 0, 200, 200, 8, 5, 5))
ok("split_recursive min larger than the region", lambda: split(0, 0, 10, 10, 4, 500, 500))
# degenerate interval (min > w / 2) still deep: the drift case the hull bound is for
ok("split_recursive degenerate deep", lambda: split(0, 0, 10, 4, 16, 100, 1))

# ---- dig_bezier control points ----
hm = mcrfpy.HeightMap((16, 16))
lim = IMAX // 3
pts = lambda p: ((0, 0), (1, 1), (2, 2), p)
for i in range(4):
    for axis in (0, 1):
        for sign in (1, -1):
            c = [(0, 0), (1, 1), (2, 2), (3, 3)]
            v = [0, 0]
            v[axis] = sign * (lim + 1)
            c[i] = tuple(v)
            expect_value_error(f"dig_bezier point {i} axis {axis} {sign:+d}*(limit+1)",
                               lambda: hm.dig_bezier(tuple(c), 1.0, 1.0, 0.0, 0.0), f"control point {i}")
c = ((lim, lim), (-lim, lim), (lim, -lim), (-lim, -lim))
ok("dig_bezier at the limit", lambda: hm.dig_bezier(c, 1.0, 1.0, 0.0, 0.0))
c = ((lim, 0), (lim, 0), (lim, 0), (lim, 0))
ok("dig_bezier at the limit (constant)", lambda: hm.dig_bezier(c, 1.0, 1.0, 0.0, 0.0))
ok("dig_bezier ordinary", lambda: hm.dig_bezier(((0, 0), (5, 1), (9, 9), (15, 15)), 2.0, 1.0, 1.0, 0.5))

# ---- a re-split replaces the children (the root-only guards must cover the whole tree) ----
# libtcod's split_once APPENDS sons to a node that has some, and split_recursive recurses into the
# oldest son, whose geometry from an earlier split_once lies outside the root-only hull check.
b = mcrfpy.BSP(pos=(0, 0), size=(10, 2))
b.split_once(False, IMAX)                       # children at x = 0 and x = INT_MAX
ok("split_recursive after split_once (previously 6 UBSan reports)",
   lambda: b.split_recursive(depth=8, min_size=(10**6, 1), seed=1))
b = mcrfpy.BSP(pos=(0, 0), size=(20, 20))
b.split_once(False, 10)
b.split_once(True, 5)                           # replaces, does not append
if len(b) != 2:
    fails.append(f"two split_once calls left {len(b)} leaves, want 2")
b.split_recursive(depth=3, min_size=(2, 2), seed=1)
fresh = mcrfpy.BSP(pos=(0, 0), size=(20, 20))
fresh.split_recursive(depth=3, min_size=(2, 2), seed=1)
if sorted((n.pos, n.size) for n in b.leaves()) != sorted((n.pos, n.size) for n in fresh.leaves()):
    fails.append("split_recursive after split_once differs from a fresh split with the same seed")

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
