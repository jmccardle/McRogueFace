"""#540 item 14: the generic-sequence branches of the position helper used to PyErr_Clear()
whenever __len__ or __getitem__ raised, turning any error (MemoryError, a bug in the user's
class) into "Expected a position ...". Errors from the object now propagate. A sequence
type that has no __len__ at all is simply not a 2-sequence: still the helper's TypeError."""
import sys
import mcrfpy

fails = []


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
    fails.append(f"{label}: did not raise")


class Boom(Exception): pass


class LenRaises:
    def __len__(self): raise Boom("len boom")
    def __getitem__(self, i): return 0


class GetRaisesFirst:
    def __len__(self): return 2
    def __getitem__(self, i): raise Boom("getitem boom")


class GetRaisesSecond:
    def __len__(self): return 2
    def __getitem__(self, i):
        if i == 1: raise MemoryError("getitem mem")
        return 0


class NoLen:  # sequence protocol (has __getitem__) but no __len__
    def __getitem__(self, i): return 0


class WrongLen:
    def __len__(self): return 3
    def __getitem__(self, i): return 0


class Good:
    def __len__(self): return 2
    def __getitem__(self, i): return (1, 2)[i]


tile = mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (6, 6))
grid = mcrfpy.Grid(grid_size=(6, 6), texture=mcrfpy.default_texture)
frame = mcrfpy.Frame(pos=(0, 0), size=(10, 10))

callers = {
    "int path (TileLayer.set)": lambda p: tile.set(p, 1),
    "int path (Grid.at)": lambda p: grid.at(p),
    "float path (Frame.move)": lambda p: frame.move(p),
}
for label, fn in callers.items():
    expect(f"{label} __len__ raises", lambda: fn(LenRaises()), Boom, "len boom")
    expect(f"{label} __getitem__(0) raises", lambda: fn(GetRaisesFirst()), Boom, "getitem boom")
    expect(f"{label} __getitem__(1) raises MemoryError", lambda: fn(GetRaisesSecond()), MemoryError)
    expect(f"{label} no __len__", lambda: fn(NoLen()), TypeError)
    expect(f"{label} wrong len", lambda: fn(WrongLen()), TypeError)
    try:
        fn(Good())
    except Exception as e:
        fails.append(f"{label} good sequence raised {type(e).__name__}: {e}")

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
