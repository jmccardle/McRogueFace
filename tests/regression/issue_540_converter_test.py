"""#540: mcrf::to_vector2f (every drawable / entity / grid pos, size, center, grid_pos ...) accepts
EXACTLY a Vector (by type) or a 2-sequence of real numbers; anything else is a TypeError that
names the argument. No fallback through Vector()'s own parser, which had:
  * use-after-free: a component conversion that runs user code (an int subclass's __float__)
    and mutates the list being read;
  * PyObject_IsInstance trusting __class__: an object that claims to be a Vector is read as one
    (out-of-bounds), and a raising __class__ left an error pending (SystemError);
  * unchecked PyFloat_AsDouble on tuple items: ((1, 'x'), 3) returned with an exception set;
  * silent garbage: Frame(size=5) was (5, 0), Entity(grid_pos=((1, 2), 3)) was (1, 2)."""
import sys
import mcrfpy

fails = []
V = mcrfpy.Vector
tex = mcrfpy.default_texture


def expect(label, fn, exc, needle=None):
    try:
        fn()
    except exc as e:
        if needle is not None and needle not in str(e):
            fails.append(f"{label}: message {str(e)!r} lacks {needle!r}")
        return
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want {exc.__name__}")
        return
    fails.append(f"{label}: accepted")


# ---- 1. use-after-free: a component conversion that clears the list ----
def make_list():
    class Y(int):
        pass

    class X(int):
        def __float__(self):
            L.clear()
            return 7.0

    L = [None, Y(5)]
    L[0] = X(1)
    return L


frame = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
grid = mcrfpy.Grid(grid_size=(4, 4), texture=tex, size=(40, 40))
targets = {
    "Frame(pos=)": lambda L: mcrfpy.Frame(pos=L),
    "Frame(size=)": lambda L: mcrfpy.Frame(size=L),
    "Caption(pos=)": lambda L: mcrfpy.Caption(pos=L),
    "Sprite(pos=)": lambda L: mcrfpy.Sprite(pos=L),
    "Grid(pos=)": lambda L: mcrfpy.Grid(grid_size=(2, 2), texture=tex, pos=L),
    "frame.pos =": lambda L: setattr(frame, "pos", L),
    "frame.size =": lambda L: setattr(frame, "size", L),
    "grid.center =": lambda L: setattr(grid, "center", L),
}
for label, fn in targets.items():
    L = make_list()
    try:
        fn(L)
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e} (the pair is snapshotted: (1, 5))")
frame.pos = make_list()
if (frame.x, frame.y) != (1.0, 5.0):
    fails.append(f"frame.pos = list: got {(frame.x, frame.y)}, want (1.0, 5.0)")

# ---- 2a. objects that lie about their class ----
class Liar:
    __slots__ = ()
    @property
    def __class__(self):
        return mcrfpy.Vector


class RaisesClass:
    __slots__ = ()
    @property
    def __class__(self):
        raise RuntimeError("class boom")


for lname, obj in (("Liar", Liar()), ("RaisesClass", RaisesClass())):
    expect(f"Entity(grid_pos={lname})", lambda: mcrfpy.Entity(grid_pos=obj), TypeError, "grid_pos")
    expect(f"Frame(pos={lname})", lambda: mcrfpy.Frame(pos=obj), TypeError, "pos")
    expect(f"Frame(size={lname})", lambda: mcrfpy.Frame(size=obj), TypeError, "size")
    expect(f"frame.pos = {lname}", lambda: setattr(frame, "pos", obj), TypeError, "pos")
    expect(f"grid.center = {lname}", lambda: setattr(grid, "center", obj), TypeError, "center")

# ---- 2b. unchecked item conversion: an item that is itself a bad pair ----
bad_items = ((1, "x"), 3)
expect("Frame(size=((1,'x'),3))", lambda: mcrfpy.Frame(size=bad_items), TypeError, "size")
expect("Entity(grid_pos=((1,'x'),3))", lambda: mcrfpy.Entity(grid_pos=bad_items), TypeError, "grid_pos")
expect("Grid(size=((1,'x'),3))", lambda: mcrfpy.Grid(grid_size=(2, 2), texture=tex, size=bad_items), TypeError, "size")
expect("Vector((1,'x'),3)", lambda: V((1, "x"), 3), TypeError)

# ---- 2c. silent garbage that used to be TypeError ----
expect("Frame(size=5)", lambda: mcrfpy.Frame(size=5), TypeError, "size")
expect("Frame(pos=5)", lambda: mcrfpy.Frame(pos=5), TypeError, "pos")
expect("Entity(grid_pos=((1,2),3))", lambda: mcrfpy.Entity(grid_pos=((1, 2), 3)), TypeError, "grid_pos")
expect("Frame(pos='ab')", lambda: mcrfpy.Frame(pos="ab"), TypeError, "pos")
expect("Frame(pos=b'ab')", lambda: mcrfpy.Frame(pos=b"ab"), TypeError, "pos")
expect("Frame(pos=(1,2,3))", lambda: mcrfpy.Frame(pos=(1, 2, 3)), TypeError, "pos")
expect("Frame(pos=(1,))", lambda: mcrfpy.Frame(pos=(1,)), TypeError, "pos")
expect("Frame(pos=None)", lambda: mcrfpy.Frame(pos=None) if False else frame.__setattr__("pos", None), TypeError, "pos")
expect("frame.size = 'ab'", lambda: setattr(frame, "size", "ab"), TypeError, "size")
expect("frame.pos = {1: 2}", lambda: setattr(frame, "pos", {1: 2}), TypeError, "pos")

# ---- what is accepted: a Vector, or any 2-sequence of real numbers ----
class Seq:
    def __len__(self): return 2
    def __getitem__(self, i): return (3, 4.5)[i]


class Idx:
    def __index__(self): return 6


for label, val, want in (
    ("Vector", V(1, 2), (1.0, 2.0)),
    ("tuple", (1, 2.5), (1.0, 2.5)),
    ("list", [3, 4], (3.0, 4.0)),
    ("sequence", Seq(), (3.0, 4.5)),
    ("__index__ items", (Idx(), 1), (6.0, 1.0)),
    ("bool items", (True, False), (1.0, 0.0)),
):
    f = mcrfpy.Frame(pos=(0, 0), size=(1, 1))
    try:
        f.pos = val
    except Exception as e:
        fails.append(f"frame.pos = {label}: raised {type(e).__name__}: {e}")
        continue
    if (f.x, f.y) != want:
        fails.append(f"frame.pos = {label}: got {(f.x, f.y)}, want {want}")

for fl in fails:
    print("FAIL:", fl)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
