"""#558: integer sizes that still wrapped or rejected floats now go through the integer position
helper: Vector / tuple / list / 2-sequence, floats floor, out of int range is OverflowError (the old
(int)PyLong_AsLong wrapped 2**32 + 3 to 3). DiscreteMap.set(x, y, v) floors like dm[x, y]. ColorLayer /
TileLayer(grid_size=) reject non-positive sizes like Grid(grid_size=)."""
import sys
import mcrfpy

fails = []
V = mcrfpy.Vector
tex = mcrfpy.default_texture


def expect(label, fn, exc, needle=None):
    try:
        fn()
    except exc as e:
        if type(e) is not exc:
            fails.append(f"{label}: raised {type(e).__name__}, want exactly {exc.__name__}")
        if needle is not None and needle not in str(e):
            fails.append(f"{label}: message {str(e)!r} lacks {needle!r}")
        return
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want {exc.__name__}")
        return
    fails.append(f"{label}: accepted")


def ok(label, fn):
    try:
        return fn()
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want success")


# ---- HeightMap(size) ----
expect("HeightMap((2**32 + 3, 3))", lambda: mcrfpy.HeightMap((2**32 + 3, 3)), OverflowError, "size")
expect("HeightMap((nan, 3))", lambda: mcrfpy.HeightMap((float("nan"), 3)), ValueError, "size")
expect("HeightMap((0, 3))", lambda: mcrfpy.HeightMap((0, 3)), ValueError)
expect("HeightMap('ab')", lambda: mcrfpy.HeightMap("ab"), TypeError, "size")
for label, size in (("floats", (4.9, 3.1)), ("Vector", V(4, 3)), ("list", [4, 3])):
    h = ok(f"HeightMap({label})", lambda: mcrfpy.HeightMap(size))
    if h is not None and tuple(h.size) != (4, 3):
        fails.append(f"HeightMap({label}): size {tuple(h.size)}, want (4, 3)")

# ---- DiscreteMap.from_bytes ----
expect("from_bytes size (2**32 + 4, 3)", lambda: mcrfpy.DiscreteMap.from_bytes(bytes(12), (2**32 + 4, 3)), OverflowError, "size")
expect("from_bytes size (nan, 3)", lambda: mcrfpy.DiscreteMap.from_bytes(bytes(12), (float("nan"), 3)), ValueError)
expect("from_bytes size 'ab'", lambda: mcrfpy.DiscreteMap.from_bytes(bytes(12), "ab"), TypeError, "size")
for label, size in (("floats", (4.9, 3.1)), ("Vector", V(4, 3)), ("list", [4, 3]), ("ints", (4, 3))):
    d = ok(f"from_bytes size {label}", lambda: mcrfpy.DiscreteMap.from_bytes(bytes(12), size))
    if d is not None and tuple(d.size) != (4, 3):
        fails.append(f"from_bytes size {label}: {tuple(d.size)}, want (4, 3)")

# ---- NoiseSource.sample ----
ns = mcrfpy.NoiseSource()
expect("NoiseSource.sample((2**32 + 3, 3))", lambda: ns.sample((2**32 + 3, 3)), OverflowError, "size")
expect("NoiseSource.sample((nan, 3))", lambda: ns.sample((float("nan"), 3)), ValueError)
expect("NoiseSource.sample('ab')", lambda: ns.sample("ab"), TypeError, "size")
for label, size in (("floats", (4.9, 3.1)), ("Vector", V(4, 3)), ("list", [4, 3])):
    r = ok(f"NoiseSource.sample {label}", lambda: ns.sample(size))
    if r is not None and tuple(r.size) != (4, 3):
        fails.append(f"NoiseSource.sample {label}: {tuple(r.size)}, want (4, 3)")

# ---- DiscreteMap.set(x, y, v) floors like dm[x, y] ----
dm = mcrfpy.DiscreteMap((8, 8))
ok("dm.set(2.7, 3.2, 5)", lambda: dm.set(2.7, 3.2, 5))
if dm[2, 3] != 5:
    fails.append(f"dm.set(2.7, 3.2, 5) wrote cell {[(x, y) for x in range(8) for y in range(8) if dm[x, y] == 5]}, want (2, 3)")


class Idx:
    def __index__(self):
        return 6


ok("dm.set(__index__, __index__, 7)", lambda: dm.set(Idx(), Idx(), 7))
if dm[6, 6] != 7:
    fails.append("dm.set(__index__ objects) did not write cell (6, 6)")
expect("dm.set(2**40, 0, 1)", lambda: dm.set(2**40, 0, 1), OverflowError)
expect("dm.set(nan, 0, 1)", lambda: dm.set(float("nan"), 0, 1), ValueError)
expect("dm.set('a', 0, 1)", lambda: dm.set("a", 0, 1), TypeError)
expect("dm.set(-0.5, 0, 1) is cell -1", lambda: dm.set(-0.5, 0, 1), IndexError)
expect("dm.set(9, 0, 1)", lambda: dm.set(9, 0, 1), IndexError)
ok("dm.set(x=1, y=2, value=3)", lambda: dm.set(x=1, y=2, value=3))

# ---- layer grid_size: positive, like Grid ----
for name, ctor in (
    ("ColorLayer", lambda sz: mcrfpy.ColorLayer("c", -1, sz)),
    ("TileLayer", lambda sz: mcrfpy.TileLayer("t", -1, tex, sz)),
):
    for bad in ((-1, -2), (0, 5), (5, 0), (-1, 3)):
        expect(f"{name}(grid_size={bad})", lambda: ctor(bad), ValueError, "positive")
    ok(f"{name}(grid_size=(3, 4))", lambda: ctor((3, 4)))
ok("ColorLayer without grid_size", lambda: mcrfpy.ColorLayer("c", -1))
ok("TileLayer without grid_size", lambda: mcrfpy.TileLayer("t", -1, tex))
expect("Grid(grid_size=(-1, -2)) still ValueError", lambda: mcrfpy.Grid(grid_size=(-1, -2), texture=tex), ValueError, "positive")

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
