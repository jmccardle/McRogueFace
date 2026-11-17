"""#540 decision B (floor) must hold everywhere a CELL is addressed, and no float is cast to int
on a path a script can reach without a range check.

Entity(grid_pos=, x=, y=), entity.cell_pos / cell_x / cell_y, Entity.path_to, an Entity or a
position used as a pathfinding endpoint: fractions floor (toward negative infinity), nan/inf is
ValueError, a value outside int is OverflowError. Float32 boundaries are exact: the largest float
below 2**31 is 2147483520.0."""
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


def ok(label, fn):
    try:
        return fn()
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want success")


def cell(e):
    return tuple(e.cell_pos)


# ---- constructor: floor, not truncation ----
for label, kw, want in (
    ("grid_pos fractions", dict(grid_pos=(2.7, 3.2)), (2, 3)),
    ("grid_pos negative fractions", dict(grid_pos=(-0.5, -1.5)), (-1, -2)),
    ("grid_pos Vector", dict(grid_pos=V(-0.5, 1.0)), (-1, 1)),
    ("grid_pos list", dict(grid_pos=[2.7, -0.5]), (2, -1)),
    ("x / y keywords", dict(x=-0.5, y=3.9), (-1, 3)),
    ("whole numbers", dict(grid_pos=(4, 5)), (4, 5)),
):
    try:
        e = mcrfpy.Entity(**kw)
    except Exception as ex:
        fails.append(f"Entity({label}): raised {type(ex).__name__}: {ex}")
        continue
    if cell(e) != want:
        fails.append(f"Entity({label}): cell_pos {cell(e)}, want {want}")

# ---- constructor: the float -> int cast is range-checked (both ends, exact float32 boundaries) ----
for label, kw in (
    ("grid_pos=(1e10, 0)", dict(grid_pos=(1e10, 0))),
    ("grid_pos=(0, -1e10)", dict(grid_pos=(0, -1e10))),
    ("x=3e9", dict(x=3e9)),
    ("y=-3e9", dict(y=-3e9)),
    ("x=2147483648.0", dict(x=2147483648.0)),
    ("x=-2147483904.0", dict(x=-2147483904.0)),
):
    expect(f"Entity({label})", lambda: mcrfpy.Entity(**kw), OverflowError)
e = mcrfpy.Entity(x=2147483520.0, y=-2147483648.0)
if cell(e) != (2147483520, -2147483648):
    fails.append(f"Entity at the int boundaries: cell_pos {cell(e)}")
for bl, bad in (("nan", float("nan")), ("inf", float("inf"))):
    expect(f"Entity(grid_pos=({bl}, 0))", lambda: mcrfpy.Entity(grid_pos=(bad, 0)), ValueError)
    expect(f"Entity(x={bl})", lambda: mcrfpy.Entity(x=bad), ValueError)

# ---- cell_pos / cell_x / cell_y setters: floor (they used to raise "whole number of cells") ----
e = mcrfpy.Entity(grid_pos=(1, 1))
for label, val, want in (
    ("(2.7, 3.2)", (2.7, 3.2), (2, 3)),
    ("Vector(-0.5, 1)", V(-0.5, 1.0), (-1, 1)),
    ("[3.99, 0.01]", [3.99, 0.01], (3, 0)),
    ("(5, 6)", (5, 6), (5, 6)),
):
    try:
        e.cell_pos = val
    except Exception as ex:
        fails.append(f"cell_pos = {label}: raised {type(ex).__name__}: {ex}")
        continue
    if cell(e) != want:
        fails.append(f"cell_pos = {label}: {cell(e)}, want {want}")
e.cell_x = 7.9
e.cell_y = -0.1
if cell(e) != (7, -1):
    fails.append(f"cell_x = 7.9, cell_y = -0.1: {cell(e)}, want (7, -1)")
expect("cell_pos = (nan, 0)", lambda: setattr(e, "cell_pos", (float("nan"), 0)), ValueError)
expect("cell_pos = (2**31 + 0.5, 0)", lambda: setattr(e, "cell_pos", (2**31 + 0.5, 0)), OverflowError)
expect("cell_x = inf", lambda: setattr(e, "cell_x", float("inf")), ValueError)
expect("cell_pos = 'ab'", lambda: setattr(e, "cell_pos", "ab"), TypeError)
expect("cell_pos = 5", lambda: setattr(e, "cell_pos", 5), TypeError)

# ---- path_to and pathfinding endpoints ----
g = mcrfpy.Grid(grid_size=(8, 8), texture=tex)
for y in range(8):
    for x in range(8):
        p = g.at(x, y)
        p.walkable = True
        p.transparent = True
# An entity's pathfinding position is its logical CELL (grid_pos), never its draw position
# (which can sit between cells, or anywhere finite, while it animates).
ent = mcrfpy.Entity(grid_pos=(2.7, 3.2))     # floors to cell (2, 3); draw_pos snaps there
g.entities.append(ent)
path = ent.path_to(5, 5)
if not path or tuple(path[0]) != (3, 4):   # the first step away from cell (2, 3) towards (5, 5)
    fails.append(f"path_to from cell (2, 3): first step {path[:1]}, want (3, 4)")
ent.draw_pos = (1e10, 0)       # finite, and not the cell: pathfinding ignores it
ok("path_to ignores a huge draw_pos", lambda: ent.path_to(5, 5))
ok("get_dijkstra_map(entity) ignores a huge draw_pos", lambda: g.get_dijkstra_map(ent))
dm = g.get_dijkstra_map(ent)
if dm.distance((2, 3)) != 0.0:
    fails.append(f"dijkstra rooted at an entity in cell (2, 3): distance there is {dm.distance((2, 3))}")
if dm.distance((2.7, 3.2)) != dm.distance((2, 3)):
    fails.append("DijkstraMap.distance((2.7, 3.2)) != distance((2, 3))")
if dm.distance(V(5.9, 5.9)) != dm.distance((5, 5)):
    fails.append("DijkstraMap.distance(Vector(5.9, 5.9)) != distance((5, 5))")
expect("DijkstraMap.distance((2**70, 0))", lambda: dm.distance((2**70, 0)), OverflowError)
expect("DijkstraMap.distance((nan, 0))", lambda: dm.distance((float("nan"), 0)), ValueError)
expect("DijkstraMap.distance('ab')", lambda: dm.distance("ab"), TypeError)
# set_behavior(SEEK, pathfinder=(x, y)) target tuple: floored like every cell
ent.draw_pos = (1.0, 1.0)
try:
    ent.set_behavior(mcrfpy.Behavior.SEEK, pathfinder=(2.7, 3.2))
except Exception as ex:
    fails.append(f"set_behavior(SEEK, pathfinder=(2.7, 3.2)): raised {type(ex).__name__}: {ex}")
expect("set_behavior(SEEK, pathfinder=(2**70, 0))",
       lambda: ent.set_behavior(mcrfpy.Behavior.SEEK, pathfinder=(2**70, 0)), OverflowError)

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
