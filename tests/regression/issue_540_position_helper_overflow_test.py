"""#540: the shared position helper (PyPositionHelper.h) must raise the specific exception
for a component that does not fit an int -- never SystemError ("returned a result with an
exception set"), never a masking IndexError/TypeError, never an unchecked float->int cast.
Huge ints -> OverflowError; nan/inf -> ValueError; a finite float outside int -> OverflowError.
Fractional Vector truncation (#540 item 3) is undecided and deliberately not asserted."""
import sys
import mcrfpy

fails = []
c = mcrfpy.Color(1, 2, 3, 255)
V = mcrfpy.Vector
nan, inf = float("nan"), float("inf")

tile = mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (6, 6))
color = mcrfpy.ColorLayer("c", -1, (6, 6))
grid = mcrfpy.Grid(grid_size=(6, 6), texture=mcrfpy.default_texture)

# (label, callable)
callers = {
    "ColorLayer.set": lambda p: color.set(p, c),
    "TileLayer.set": lambda p: tile.set(p, 1),
    "fill_rect pos": lambda p: color.fill_rect(p, (1, 1), c),
    "fill_rect size": lambda p: color.fill_rect((0, 0), p, c),
    "TileLayer.fill_rect size": lambda p: tile.fill_rect((0, 0), p, 1),
    "compute_fov": lambda p: grid.compute_fov(p),
}
bad = [
    ((2**70, 0), OverflowError),
    ((0, -(2**70)), OverflowError),
    ((2**31, 0), OverflowError),
    ((0, -(2**31) - 1), OverflowError),
    ([2**40, 0], OverflowError),
    (V(nan, 0), ValueError),
    (V(0, inf), ValueError),
    (V(-inf, 0), ValueError),
    (V(1e30, 0), OverflowError),
    (V(0, -1e30), OverflowError),
    ((nan, 0), ValueError),
    ((inf, 0), ValueError),
    ((1e30, 0), OverflowError),
]
for label, fn in callers.items():
    for arg, exc in bad:
        try:
            fn(arg)
            fails.append(f"{label}({arg!r}) did not raise")
        except exc:
            pass
        except BaseException as e:  # SystemError, IndexError, TypeError ... are all wrong
            fails.append(f"{label}({arg!r}) raised {type(e).__name__}: {e}; want {exc.__name__}")

# Limits that are valid must still work, and no error may be left pending afterwards.
color.set((5, 5), c)
color.fill_rect((0, 0), (1, 1), c)
color.set((1.0, 2.0), c)  # whole-number floats stay accepted
for ok in ((0, 0), [1, 1], V(2, 3)):
    try:
        color.set(ok, c)
    except Exception as e:
        fails.append(f"valid position {ok!r} raised {type(e).__name__}: {e}")

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
