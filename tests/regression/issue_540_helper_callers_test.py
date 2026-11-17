"""#540 items 10, 11: callers of the position helper must not replace its exception.

10. HeightMap.dig_bezier, BSP(), BSP.split_recursive, BSP.to_heightmap and
    DijkstraMap.to_heightmap used to answer any helper failure with their own TypeError, hiding
    the OverflowError / ValueError for a component that is a number but unusable. Now: a bad
    number keeps its exception; an object that is not a position is still a TypeError that
    names the argument.
11. parseOptionalPos (HeightMap.add / lerp / copy_from / add_bsp ... pos= and source_pos=) read
    ints itself with no range check: pos=(2**70, 0) raised "cannot be negative" and
    pos=(2**32, 0) silently became (0, 0).
"""
import sys
import mcrfpy

fails = []


def expect(label, fn, exc, needle=None):
    try:
        fn()
    except exc as e:
        if needle is not None and needle not in str(e):
            fails.append(f"{label}: message {str(e)!r} does not mention {needle!r}")
        return
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want {exc.__name__}")
        return
    fails.append(f"{label}: did not raise")


def ok(label, fn):
    try:
        fn()
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want success")


hm = mcrfpy.HeightMap((8, 8))
other = mcrfpy.HeightMap((4, 4))
bsp = mcrfpy.BSP(pos=(0, 0), size=(20, 20))
bsp.split_recursive(depth=2, min_size=(3, 3), seed=1)
grid = mcrfpy.Grid(grid_size=(6, 6), texture=mcrfpy.default_texture)
dmap = grid.get_dijkstra_map((1, 1))

BIG = 2**70
NAN = float("nan")
V = mcrfpy.Vector

# ---- item 10: a bad number keeps the helper's exception ----
pts = lambda p: ((0, 0), (1, 1), (2, 2), p)
expect("dig_bezier huge", lambda: hm.dig_bezier(pts((BIG, 0)), 1.0, 1.0, 0.0, 0.0), OverflowError)
expect("dig_bezier nan Vector", lambda: hm.dig_bezier(pts(V(NAN, 0)), 1.0, 1.0, 0.0, 0.0), ValueError)
expect("BSP pos huge", lambda: mcrfpy.BSP(pos=(BIG, 0), size=(10, 10)), OverflowError)
expect("BSP size huge", lambda: mcrfpy.BSP(pos=(0, 0), size=(10, BIG)), OverflowError)
expect("BSP size nan", lambda: mcrfpy.BSP(pos=(0, 0), size=V(NAN, 1)), ValueError)
expect("split_recursive min_size huge", lambda: bsp.split_recursive(depth=1, min_size=(BIG, 1)), OverflowError)
expect("to_heightmap size huge", lambda: bsp.to_heightmap(size=(BIG, 5)), OverflowError)
expect("DijkstraMap.to_heightmap size huge", lambda: dmap.to_heightmap(size=(5, BIG)), OverflowError)

# ---- item 10: not a position is still a TypeError, naming the argument ----
expect("dig_bezier not a position", lambda: hm.dig_bezier(((0, 0), (1, 1), (2, 2), "x"), 1.0, 1.0, 0.0, 0.0), TypeError, "control point 3")
expect("BSP pos not a position", lambda: mcrfpy.BSP(pos=object(), size=(10, 10)), TypeError, "pos")
expect("BSP size not a position", lambda: mcrfpy.BSP(pos=(0, 0), size=object()), TypeError, "size")
expect("split_recursive min_size not a position", lambda: bsp.split_recursive(depth=1, min_size=object()), TypeError, "min_size")
expect("to_heightmap size not a position", lambda: bsp.to_heightmap(size=object()), TypeError, "size")
expect("DijkstraMap.to_heightmap size not a position", lambda: dmap.to_heightmap(size=object()), TypeError, "size")

# ---- item 11: parseOptionalPos range checks ----
for label, call in {
    "add pos": lambda p: hm.add(other, pos=p),
    "lerp pos": lambda p: hm.lerp(other, 0.5, pos=p),
    "copy_from pos": lambda p: hm.copy_from(other, pos=p),
    "copy_from source_pos": lambda p: hm.copy_from(other, source_pos=p),
    "add_bsp pos": lambda p: hm.add_bsp(bsp, pos=p),
}.items():
    expect(f"{label} 2**70", lambda: call((BIG, 0)), OverflowError)
    expect(f"{label} -2**70", lambda: call((0, -BIG)), OverflowError)
    expect(f"{label} 2**32", lambda: call((2**32, 0)), OverflowError)
    expect(f"{label} [2**32, 0]", lambda: call([2**32, 0]), OverflowError)
    expect(f"{label} nan", lambda: call(V(NAN, 0)), ValueError)
    expect(f"{label} not a position", lambda: call(object()), TypeError, "pos")
    ok(f"{label} valid", lambda: call((1, 1)))
    ok(f"{label} valid list", lambda: call([0, 0]))

# a negative in-range pos is still the caller's own range error, not an overflow
expect("add pos negative", lambda: hm.add(other, pos=(-1, 0)), ValueError, "negative")

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
