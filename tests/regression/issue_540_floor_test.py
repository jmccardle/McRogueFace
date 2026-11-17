"""#540 item 3 (decided: FLOOR). An integer (cell) position given as a Vector, tuple, list or
other sequence of floats is floored (toward negative infinity, not truncated), the same for every
input shape and every caller of the integer helper:
    (2.7, 3.2) -> (2, 3);  (-0.5, 1) -> (-1, 1)   [then the caller's own bounds check applies]
Non-finite -> ValueError; out of int range after flooring -> OverflowError."""
import sys
import mcrfpy

fails = []
V = mcrfpy.Vector


class Seq:
    def __init__(self, a, b): self.items = (a, b)
    def __len__(self): return 2
    def __getitem__(self, i): return self.items[i]


class Idx:
    def __init__(self, v): self.v = v
    def __index__(self): return self.v


def shapes(a, b):
    return {"tuple": (a, b), "list": [a, b], "Vector": V(a, b), "Seq": Seq(a, b)}


tile = mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (8, 8))
grid = mcrfpy.Grid(grid_size=(8, 8), texture=mcrfpy.default_texture)

# positive fractions floor (2.7 -> 2, 3.2 -> 3)
for kind, p in shapes(2.7, 3.2).items():
    tile.fill(-1)
    try:
        tile.set(p, 5)
        if tile.at((2, 3)) != 5:
            fails.append(f"TileLayer.set {kind}: (2.7, 3.2) did not land on cell (2, 3)")
        gp = grid.at(p)
        if tuple(gp.grid_pos) != (2, 3):
            fails.append(f"Grid.at {kind}: got {gp.grid_pos}, want (2, 3)")
    except Exception as e:
        fails.append(f"{kind} (2.7, 3.2): raised {type(e).__name__}: {e}")

# two separate numeric args
try:
    gp = grid.at(2.7, 3.2)
    if tuple(gp.grid_pos) != (2, 3):
        fails.append(f"Grid.at(2.7, 3.2): got {gp.grid_pos}, want (2, 3)")
except Exception as e:
    fails.append(f"Grid.at(2.7, 3.2): raised {type(e).__name__}: {e}")

# negative fractions floor AWAY from zero: -0.5 -> -1 (truncation would give 0, a valid cell)
for kind, p in shapes(-0.5, 1.0).items():
    for label, fn in (("TileLayer.set", lambda: tile.set(p, 5)), ("Grid.at", lambda: grid.at(p))):
        try:
            fn()
            fails.append(f"{label} {kind}: (-0.5, 1) was accepted (truncated to cell 0?)")
        except IndexError:
            pass
        except Exception as e:
            fails.append(f"{label} {kind}: (-0.5, 1) raised {type(e).__name__}: {e}; want IndexError")

# exact values are unchanged; ints and __index__ objects too
tile.fill(-1)
tile.set((4.0, 5.0), 7)
tile.set([Idx(1), 2], 7)
if tile.at((4, 5)) != 7 or tile.at((1, 2)) != 7:
    fails.append("whole-number floats / __index__ components changed meaning")

# non-finite -> ValueError; out of int range AFTER flooring -> OverflowError
nan, inf = float("nan"), float("inf")
for kind, p in {**shapes(nan, 0.0), **shapes(0.0, inf), **shapes(-inf, 0.0)}.items():
    try:
        tile.set(p, 5)
        fails.append(f"non-finite {kind} accepted")
    except ValueError:
        pass
    except Exception as e:
        fails.append(f"non-finite {kind}: raised {type(e).__name__}: {e}; want ValueError")

I32 = 2**31
cases = [
    ((I32 - 0.5, 0.0), None),            # floors to INT_MAX: in range for the helper (caller says IndexError)
    ((I32 + 0.5, 0.0), OverflowError),
    ((0.0, -I32 - 0.5), OverflowError),  # floors to -2**31 - 1
    ((-I32 + 0.5, 0.0), None),           # floors to -2**31: in range
    ((1e30, 0.0), OverflowError),
]
for arg, want in cases:
    for kind in ("tuple", "list", "Seq"):
        p = {"tuple": arg, "list": list(arg), "Seq": Seq(*arg)}[kind]
        try:
            tile.set(p, 5)
            fails.append(f"set {kind} {arg}: accepted")
        except IndexError:
            if want is not None:
                fails.append(f"set {kind} {arg}: IndexError, want {want.__name__}")
        except Exception as e:
            if want is None or type(e) is not want:
                fails.append(f"set {kind} {arg}: raised {type(e).__name__}: {e}; want {want.__name__ if want else 'IndexError'}")

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
