"""#540 follow-ups to items 10, 11, 14 (review of fix/540-helper-followups).

1. fill_rect must not rebuild the helper's exception: a user exception raised in __len__ /
   __getitem__ keeps its type, args and (SystemExit) code.
2. HeightMap size= goes through the helper: 2**32+3 is not (3), 2**70 is not "must be positive".
3. A TypeError raised INSIDE a user's __len__ propagates with its own message; IndexError from
   __getitem__ propagates. A type with no length slot is simply not a position.
4. The helper's OverflowError / ValueError name the argument, and no path leaks CPython's raw
   "Python int too large to convert to C long".
5. add_bsp / multiply_bsp: offset and region arithmetic cannot overflow int and paint cells of a
   region that is entirely off the map.
"""
import sys
import mcrfpy

fails = []


def expect(label, fn, exc, needle=None, absent=None):
    try:
        fn()
    except exc as e:
        s = str(e)
        if needle is not None and needle not in s:
            fails.append(f"{label}: message {s!r} lacks {needle!r}")
        if absent is not None and absent in s:
            fails.append(f"{label}: message {s!r} must not contain {absent!r}")
        return e
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want {exc.__name__}")
        return None
    fails.append(f"{label}: did not raise")
    return None


def ok(label, fn):
    try:
        fn()
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want success")


V = mcrfpy.Vector
NAN = float("nan")
BIG = 2**70

# ---- 1. fill_rect keeps user exceptions untouched ----
class TwoArg(Exception):
    def __init__(self, a, b):
        super().__init__(a, b)
        self.a, self.b = a, b


class LenTwoArg:
    def __len__(self): raise TwoArg(1, 2)
    def __getitem__(self, i): return 0


class GetTwoArg:
    def __len__(self): return 2
    def __getitem__(self, i): raise TwoArg(3, 4)


class LenExit:
    def __len__(self): raise SystemExit(7)
    def __getitem__(self, i): return 0


class GetExit:
    def __len__(self): return 2
    def __getitem__(self, i): raise SystemExit(9)


color = mcrfpy.ColorLayer("c", -1, (6, 6))
tile = mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (6, 6))
c = mcrfpy.Color(1, 2, 3, 255)
rects = {
    "ColorLayer.fill_rect": lambda p, s: color.fill_rect(p, s, c),
    "TileLayer.fill_rect": lambda p, s: tile.fill_rect(p, s, 1),
}
for label, fn in rects.items():
    for argname, mk in (("pos", lambda o: fn(o, (1, 1))), ("size", lambda o: fn((0, 0), o))):
        e = expect(f"{label} {argname} __len__ TwoArg", lambda: mk(LenTwoArg()), TwoArg)
        if e is not None and (e.args != (1, 2) or (e.a, e.b) != (1, 2)):
            fails.append(f"{label} {argname}: TwoArg rebuilt: args={e.args}")
        e = expect(f"{label} {argname} __getitem__ TwoArg", lambda: mk(GetTwoArg()), TwoArg)
        if e is not None and e.args != (3, 4):
            fails.append(f"{label} {argname}: TwoArg rebuilt: args={e.args}")
        e = expect(f"{label} {argname} __len__ SystemExit", lambda: mk(LenExit()), SystemExit)
        if e is not None and e.code != 7:
            fails.append(f"{label} {argname}: SystemExit code {e.code!r}, want 7")
        e = expect(f"{label} {argname} __getitem__ SystemExit", lambda: mk(GetExit()), SystemExit)
        if e is not None and e.code != 9:
            fails.append(f"{label} {argname}: SystemExit code {e.code!r}, want 9")

# ---- 3. TypeError inside __len__; IndexError from __getitem__; no length slot ----
class LenTypeError:
    def __len__(self): raise TypeError("my own len message")
    def __getitem__(self, i): return 0


class GetIndexError:
    def __len__(self): return 2
    def __getitem__(self, i): raise IndexError("my own index message")


class NoLen:
    def __getitem__(self, i): return 0


for label, fn in {
    "TileLayer.set": lambda p: tile.set(p, 1),
    "fill_rect pos": lambda p: tile.fill_rect(p, (1, 1), 1),
    "Frame.move": lambda p: mcrfpy.Frame(pos=(0, 0), size=(1, 1)).move(p),
}.items():
    expect(f"{label} __len__ TypeError keeps message", lambda: fn(LenTypeError()), TypeError, "my own len message")
    expect(f"{label} __getitem__ IndexError", lambda: fn(GetIndexError()), IndexError, "my own index message")
    e = expect(f"{label} no length slot", lambda: fn(NoLen()), TypeError)
    if e is not None and "no len" in str(e):
        fails.append(f"{label} no length slot: leaked len() error {e}")

# ---- 2. HeightMap size= ----
hm = mcrfpy.HeightMap((8, 8))
other = mcrfpy.HeightMap((4, 4))
for bad in ((2**32 + 3, 3), (BIG, 3), (2**31 + 5, 3), (3, -(2**40)), [2**32 + 3, 3]):
    expect(f"add size={bad!r}", lambda: hm.add(other, size=bad), OverflowError, "size")
expect("add size nan", lambda: hm.add(other, size=V(NAN, 1)), ValueError, "size")
expect("add size zero", lambda: hm.add(other, size=(0, 3)), ValueError, "positive")
expect("add size negative", lambda: hm.add(other, size=(3, -1)), ValueError, "positive")
expect("add size not a position", lambda: hm.add(other, size=object()), TypeError, "size")
ok("add size valid", lambda: hm.add(other, size=(2, 2)))
ok("add size valid list", lambda: hm.add(other, size=[2, 2]))

# ---- 4. argument named in OverflowError / ValueError; no raw CPython message ----
bsp = mcrfpy.BSP(pos=(0, 0), size=(8, 8))
RAW = "too large to convert"
for label, fn, name in [
    ("multiply_bsp pos 2**70", lambda: hm.multiply_bsp(bsp, pos=(BIG, 0)), "pos"),
    ("add_bsp pos 2**70", lambda: hm.add_bsp(bsp, pos=(BIG, 0)), "pos"),
    ("add pos 2**70", lambda: hm.add(other, pos=(BIG, 0)), "pos"),
    ("copy_from source_pos 2**70", lambda: hm.copy_from(other, source_pos=(0, BIG)), "source_pos"),
    ("add pos 2**32", lambda: hm.add(other, pos=(2**32, 0)), "pos"),
    ("fill_rect pos 2**70", lambda: tile.fill_rect((BIG, 0), (1, 1), 1), "pos"),
    ("fill_rect size 2**70", lambda: tile.fill_rect((0, 0), (1, BIG), 1), "size"),
    ("BSP size 2**70", lambda: mcrfpy.BSP(pos=(0, 0), size=(BIG, 1)), "size"),
    ("dig_bezier 2**70", lambda: hm.dig_bezier(((0, 0), (1, 1), (2, 2), (BIG, 0)), 1.0, 1.0, 0.0, 0.0), "control point 3"),
    ("Frame.move 10**400", lambda: mcrfpy.Frame(pos=(0, 0), size=(1, 1)).move(10**400, 0), None),
]:
    expect(label, fn, OverflowError, name, absent=RAW)
for label, fn, name in [
    ("add pos nan", lambda: hm.add(other, pos=V(NAN, 0)), "pos"),
    ("fill_rect size nan", lambda: tile.fill_rect((0, 0), V(1, NAN), 1), "size"),
    ("multiply_bsp pos inf", lambda: hm.multiply_bsp(bsp, pos=V(float("inf"), 0)), "pos"),
]:
    expect(label, fn, ValueError, name)

# ---- 5. add_bsp / multiply_bsp arithmetic ----
def values(h):
    return [h[x, y] for y in range(h.size[1]) for x in range(h.size[0])]


I32 = 2**31
for kw in (
    dict(pos=(I32 - 1, I32 - 1), shrink=I32 - 1),   # region entirely off the map; sums overflow
    dict(pos=(I32 - 1, I32 - 1)),
    dict(pos=(-I32, -I32)),                         # pos - orig overflows (orig is (5, 5))
    dict(shrink=I32 - 1),
):
    b = mcrfpy.BSP(pos=(5, 5), size=(8, 8))
    m = mcrfpy.HeightMap((8, 8))
    m.add_bsp(b, value=1.0, **kw)
    if any(v != 0.0 for v in values(m)):
        fails.append(f"add_bsp {kw}: painted {sum(1 for v in values(m) if v)} cells of an off-map region")

    ref = mcrfpy.HeightMap((8, 8), fill=1.0)
    ref.multiply_bsp(b, pos=(100, 100), value=5.0)
    m = mcrfpy.HeightMap((8, 8), fill=1.0)
    m.multiply_bsp(b, value=5.0, **kw)
    if values(m) != values(ref):
        fails.append(f"multiply_bsp {kw}: differs from the off-map reference")

# a hugely negative shrink grows the region over the whole map (both ends clamped)
b = mcrfpy.BSP(pos=(0, 0), size=(8, 8))
m = mcrfpy.HeightMap((8, 8))
m.add_bsp(b, shrink=-I32, value=1.0)
if values(m) != [1.0] * 64:
    fails.append("add_bsp shrink=-2**31: region should cover the whole map")
# normal use unchanged
m = mcrfpy.HeightMap((8, 8))
m.add_bsp(b, pos=(2, 2), value=1.0)
if sum(1 for v in values(m) if v == 1.0) != 36:
    fails.append("add_bsp pos=(2, 2): expected a 6x6 region")

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
