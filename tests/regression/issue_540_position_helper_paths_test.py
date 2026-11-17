"""#540 (second review): the position helper's parse paths, not just FromObjectInt.

  * ParseInt: two positional args, x=/y= keywords, pos=, a single tuple/Vector -- through
    Grid.at, HeightMap.get and automation.onScreen.
  * ParseFloat / FromObject: Frame.move / resize -- a huge int raises OverflowError and
    leaves the object unchanged (it used to raise SystemError AND write x == -1.0); nan/inf
    raise ValueError.
  * Vector detection is a type check: an object whose __class__ lies or raises is never
    read as a Vector (its memory was read before).
  * __index__ objects (numpy integers) are accepted wherever an int is; bool and IntEnum too.
  * edge values: INT_MAX / INT_MIN parse, one past raises OverflowError.
  * the generic-sequence path (not a tuple or list).
  * fill_rect with x + width past INT_MAX fills to the end of the row.
"""
import enum
import sys
import mcrfpy
from mcrfpy import automation

fails = []
INT_MAX, INT_MIN = 2**31 - 1, -(2**31)


def expect(label, fn, exc=None, value=None):
    """exc: required exact exception type; None: must not raise (and equal `value` if given)."""
    try:
        r = fn()
    except BaseException as e:
        if exc is None:
            fails.append(f"{label}: raised {type(e).__name__}: {e}")
        elif type(e) is not exc:
            fails.append(f"{label}: raised {type(e).__name__}: {e}; want {exc.__name__}")
        return
    if exc is not None:
        fails.append(f"{label}: did not raise (got {r!r}); want {exc.__name__}")
    elif value is not None and r != value:
        fails.append(f"{label}: got {r!r}, want {value!r}")


class Idx:
    def __init__(self, v): self.v = v
    def __index__(self): return self.v


class BadIdx:
    def __index__(self): raise RuntimeError("index boom")


class Seq:  # a generic sequence: not a tuple or list
    def __init__(self, a, b): self.items = (a, b)
    def __len__(self): return 2
    def __getitem__(self, i): return self.items[i]


class Color3(enum.IntEnum):
    ONE = 1
    TWO = 2


class LiesVector:  # __class__ claims to be a Vector; must not be read as one
    __class__ = mcrfpy.Vector
    def __len__(self): return 2
    def __getitem__(self, i): return (1, 1)[i]


class RaisingClass:
    @property
    def __class__(self): raise RuntimeError("class boom")
    def __len__(self): return 2
    def __getitem__(self, i): return (1, 1)[i]


grid = mcrfpy.Grid(grid_size=(6, 6), texture=mcrfpy.default_texture)
hm = mcrfpy.HeightMap((4, 4))
hm.fill(5.0)
at = lambda g: (g.x, g.y) if hasattr(g, "x") else g  # noqa: E731

# --- ParseInt paths: every argument shape reaches the same cell -----------------------------
for name, call in (
    ("2 args", lambda g: g.at(1, 2)),
    ("kw x/y", lambda g: g.at(x=1, y=2)),
    ("kw pos", lambda g: g.at(pos=(1, 2))),
    ("tuple", lambda g: g.at((1, 2))),
    ("list", lambda g: g.at([1, 2])),
    ("Vector", lambda g: g.at(mcrfpy.Vector(1, 2))),
):
    expect(f"Grid.at {name}", lambda: str(call(grid)).count("(1, 2)") == 1, value=True)

for name, call in (
    ("2 args", lambda: hm.get(1, 2)), ("kw x/y", lambda: hm.get(x=1, y=2)),
    ("kw pos", lambda: hm.get(pos=(1, 2))), ("tuple", lambda: hm[(1, 2)]),
    ("Vector", lambda: hm[mcrfpy.Vector(1, 2)]),
):
    expect(f"HeightMap.get {name}", call, value=5.0)

for name, call in (
    ("2 args", lambda: automation.onScreen(1, 2)), ("kw x/y", lambda: automation.onScreen(x=1, y=2)),
    ("kw pos", lambda: automation.onScreen(pos=(1, 2))), ("tuple", lambda: automation.onScreen((1, 2))),
):
    expect(f"automation.onScreen {name}", call, value=True)

# huge ints through every ParseInt branch
for name, call in (
    ("Grid.at 2 args", lambda: grid.at(2**70, 0)),
    ("Grid.at 2nd arg", lambda: grid.at(0, 2**70)),
    ("Grid.at kw x/y", lambda: grid.at(x=2**70, y=0)),
    ("Grid.at kw pos", lambda: grid.at(pos=(2**70, 0))),
    ("Grid.at tuple", lambda: grid.at((2**70, 0))),
    ("HeightMap.get 2 args", lambda: hm.get(2**70, 0)),
    ("HeightMap.get kw pos", lambda: hm.get(pos=[0, 2**70])),
    ("automation.onScreen 2 args", lambda: automation.onScreen(2**70, 0)),
    ("automation.onScreen kw", lambda: automation.onScreen(x=0, y=2**70)),
    ("automation.onScreen pos", lambda: automation.onScreen(pos=(2**70, 0))),
):
    expect(name + " huge", call, OverflowError)

# --- edge values -----------------------------------------------------------------------------
expect("onScreen INT_MAX parses", lambda: automation.onScreen(INT_MAX, INT_MAX), value=False)
expect("onScreen INT_MIN parses", lambda: automation.onScreen(INT_MIN, INT_MIN), value=False)
expect("onScreen INT_MAX+1", lambda: automation.onScreen(INT_MAX + 1, 0), OverflowError)
expect("onScreen INT_MIN-1", lambda: automation.onScreen(0, INT_MIN - 1), OverflowError)
expect("HeightMap INT_MAX is out of range, not a parse error", lambda: hm.get(INT_MAX, 0), IndexError)
expect("HeightMap INT_MIN is out of range, not a parse error", lambda: hm.get(INT_MIN, 0), IndexError)
expect("HeightMap INT_MAX+1", lambda: hm.get(INT_MAX + 1, 0), OverflowError)
expect("tuple INT_MAX+1 (list)", lambda: hm.get(pos=[INT_MAX + 1, 0]), OverflowError)

# --- Frame.move / resize: float paths ---------------------------------------------------------
# Ints convert like floats: anything that fits a float is accepted (2**70 is 1.18e21), and
# anything beyond FLT_MAX raises OverflowError for ints and floats alike.
f = mcrfpy.Frame(pos=(3, 4), size=(10, 10))
HUGE = 10**40
expect("move 10**40", lambda: f.move(HUGE, 0), OverflowError)
expect("move -10**40 (y)", lambda: f.move(0, -HUGE), OverflowError)
expect("move tuple 10**40", lambda: f.move((HUGE, 0)), OverflowError)
expect("move kw x/y 10**40", lambda: f.move(x=HUGE, y=0), OverflowError)
expect("move kw pos 10**40", lambda: f.move(pos=(HUGE, 0)), OverflowError)
expect("resize 10**40", lambda: f.resize((HUGE, 5)), OverflowError)
expect("move 1e40", lambda: f.move(1e40, 0), OverflowError)
expect("move 1e300", lambda: f.move(1e300, 0), OverflowError)
expect("move 10**400 (beyond a double)", lambda: f.move(10**400, 0), OverflowError)
expect("move nan", lambda: f.move(float("nan"), 0), ValueError)
expect("move inf", lambda: f.move(0, float("inf")), ValueError)
expect("move kw x/y nan", lambda: f.move(x=0, y=float("nan")), ValueError)
expect("move kw pos inf", lambda: f.move(pos=(float("inf"), 0)), ValueError)
expect("move Vector nan", lambda: f.move(mcrfpy.Vector(float("nan"), 0)), ValueError)
if (f.x, f.y, f.w, f.h) != (3.0, 4.0, 10.0, 10.0):
    fails.append(f"Frame changed by failed move/resize: {(f.x, f.y, f.w, f.h)}")
expect("move ok", lambda: f.move(2, 3))
if (f.x, f.y) != (5.0, 7.0):
    fails.append(f"Frame.move(2, 3) gave {(f.x, f.y)}")
expect("move kw x/y ok", lambda: f.move(x=1, y=1))
expect("move kw pos ok", lambda: f.move(pos=(1, 2)))
if (f.x, f.y) != (7.0, 10.0):
    fails.append(f"keyword moves gave {(f.x, f.y)}")
expect("move bool", lambda: f.move(True, False))
if (f.x, f.y) != (8.0, 10.0):
    fails.append(f"Frame.move(True, False) gave {(f.x, f.y)}")
# int and float of the same magnitude behave the same
fa = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
fb = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
expect("move 10**20 accepted", lambda: fa.move(10**20, 0))
expect("move 1e20 accepted", lambda: fb.move(1e20, 0))
if fa.x != fb.x or fa.x == 0.0:
    fails.append(f"10**20 -> {fa.x}, 1e20 -> {fb.x}")
expect("move 2**70 accepted (it fits a float)", lambda: mcrfpy.Frame(pos=(0, 0), size=(1, 1)).move(2**70, 0))

# HeightMap float-position methods: nan/inf must raise, not reach an unchecked cast (segfault)
expect("get_interpolated nan", lambda: hm.get_interpolated(float("nan"), 0), ValueError)
expect("get_interpolated inf", lambda: hm.get_interpolated(0, float("inf")), ValueError)
expect("get_normal nan", lambda: hm.get_normal(float("nan"), 0), ValueError)
expect("get_normal inf", lambda: hm.get_normal(0, -float("inf")), ValueError)

# --- Vector detection is a type check ----------------------------------------------------------
expect("__class__ lies: read as its sequence, not as Vector memory", lambda: hm[LiesVector()], value=5.0)
# The helper never consults __class__ (a type check on the real type), so an object whose
# __class__ raises is just a 2-sequence: the lookup succeeds with the sequence's cell.
expect("raising __class__ is a plain sequence", lambda: hm[RaisingClass()], value=5.0)
fl = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
expect("move with lying __class__", lambda: fl.move(LiesVector()))
if (fl.x, fl.y) != (1.0, 1.0):
    fails.append(f"move(LiesVector()) -> {(fl.x, fl.y)}, want (1.0, 1.0)")
fr = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
expect("move with raising __class__", lambda: fr.move(RaisingClass()))
if (fr.x, fr.y) != (1.0, 1.0):
    fails.append(f"move(RaisingClass()) -> {(fr.x, fr.y)}, want (1.0, 1.0)")

# --- __index__, bool, IntEnum, generic sequence ------------------------------------------------
hm2 = mcrfpy.HeightMap((4, 4))
hm2.fill(7.0)
expect("__index__ in tuple", lambda: hm2[(Idx(1), Idx(2))], value=7.0)
expect("__index__ as 2 args", lambda: hm2.get(Idx(1), Idx(2)), value=7.0)
expect("__index__ huge", lambda: hm2.get(Idx(2**70), 0), OverflowError)
expect("__index__ past int", lambda: hm2.get(Idx(INT_MAX + 1), 0), OverflowError)
expect("__index__ raising propagates its own error", lambda: hm2.get(BadIdx(), 0), RuntimeError)
expect("bool", lambda: hm2[(True, True)], value=7.0)
expect("IntEnum", lambda: hm2[(Color3.ONE, Color3.TWO)], value=7.0)
expect("generic sequence", lambda: hm2[Seq(1, 2)], value=7.0)
expect("generic sequence huge", lambda: hm2[Seq(2**70, 0)], OverflowError)  # int paths: past int
expect("generic sequence nan float", lambda: hm2[Seq(float("nan"), 0)], ValueError)
expect("whole float in generic sequence", lambda: hm2[Seq(1.0, 2.0)], value=7.0)

f2 = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
expect("float path __index__", lambda: f2.move(Idx(2), Idx(3)))
if (f2.x, f2.y) != (2.0, 3.0):
    fails.append(f"Frame.move with __index__ gave {(f2.x, f2.y)}")
expect("float path generic sequence", lambda: f2.move(Seq(1, 1)))
expect("float path generic sequence huge", lambda: f2.move(Seq(HUGE, 0)), OverflowError)
expect("float path __index__ huge", lambda: f2.move(Idx(HUGE), 0), OverflowError)
expect("float path bad __index__", lambda: f2.move(BadIdx(), 0), RuntimeError)

layer = mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (6, 6))
expect("fill_rect __index__", lambda: layer.fill_rect((Idx(0), Idx(0)), (Idx(2), Idx(2)), 4))
if layer.at((1, 1)) != 4:
    fails.append("fill_rect with __index__ positions did not fill")
expect("set __index__", lambda: layer.set((Idx(5), Idx(5)), 9))
if layer.at((5, 5)) != 9:
    fails.append("set with __index__ did not write")

# --- fillRect: x + width overflowed signed int --------------------------------------------------
tl = mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (6, 6))
tl.fill_rect((1, 0), (INT_MAX, 6), 3)
row = [tl.at((x, 0)) for x in range(6)]
col = [tl.at((1, y)) for y in range(6)]
if row != [-1, 3, 3, 3, 3, 3] or col != [3] * 6:
    fails.append(f"TileLayer.fill_rect((1,0),(INT_MAX,6)) row={row} col={col}")
cl = mcrfpy.ColorLayer("c", -1, (6, 6))
red = mcrfpy.Color(255, 0, 0, 255)
cl.fill_rect((1, 1), (6, INT_MAX), red)
if cl.at((5, 5)) != red or cl.at((1, 1)) != red or cl.at((0, 0)) == red:
    fails.append("ColorLayer.fill_rect with height INT_MAX did not fill to the end")
tl2 = mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (6, 6))
tl2.fill_rect((INT_MIN, INT_MIN), (INT_MAX, INT_MAX), 2)  # ends well before the grid: nothing
if any(tl2.at((x, y)) == 2 for x in range(6) for y in range(6)):
    fails.append("rectangle ending before the grid filled cells")
tl2.fill_rect((-3, -3), (5, 5), 2)  # covers cells 0..1
if tl2.at((1, 1)) != 2 or tl2.at((2, 2)) == 2:
    fails.append("negative-origin rectangle filled the wrong cells")

# extreme rectangles must not write out of bounds (the far edge sum can wrap int)
for kind in ("TileLayer", "ColorLayer"):
    def fresh():
        if kind == "TileLayer":
            lay = mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (6, 6))
            lay.fill(1)
            return lay, 9, lambda: [lay.at((x, y)) for y in range(6) for x in range(6)]
        lay = mcrfpy.ColorLayer("c", -1, (6, 6))
        lay.fill(mcrfpy.Color(5, 6, 7, 255))
        return lay, mcrfpy.Color(250, 1, 2, 255), lambda: [tuple((lay.at((x, y)).r, lay.at((x, y)).g, lay.at((x, y)).b))
                                                          for y in range(6) for x in range(6)]
    for label, pos, size in (
        ("origin INT_MIN, size -1", (INT_MIN, 0), (-1, 1)),
        ("origin -5, size INT_MIN", (-5, 0), (INT_MIN, 1)),
        ("origin INT_MIN, size INT_MIN", (INT_MIN, INT_MIN), (INT_MIN, INT_MIN)),
        ("origin INT_MAX, size INT_MAX", (INT_MAX, INT_MAX), (INT_MAX, INT_MAX)),
        ("zero size", (2, 2), (0, 3)),
        ("negative size", (4, 4), (-3, -3)),
    ):
        lay, val, snap = fresh()
        before = snap()
        expect(f"{kind}.fill_rect {label}", lambda: lay.fill_rect(pos, size, val))
        if snap() != before:
            fails.append(f"{kind}.fill_rect {label} changed cells")
    lay, val, snap = fresh()
    lay.fill_rect((-3, 0), (5, 1), val)  # overlaps columns 0-1 of row 0 only
    changed = [i for i, (a, b) in enumerate(zip(snap(), fresh()[2]())) if a != b]
    if changed != [0, 1]:
        fails.append(f"{kind}.fill_rect((-3, 0), (5, 1)) changed cells {changed}, want [0, 1]")

for m in fails:
    print("FAIL:", m)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
