"""#540 second review: nested-container use-after-free (apply_ranges gradient pair, DiscreteMap /
HeightMap dict arguments), BSP re-init stale nodes, waypoints, the floor matrix for the remaining
cell-taking APIs, constructor/setter agreement (entity cell, opacity clamp), pathfinding from the
logical cell, one rule for "a real number", 'd'-parsed method floats, zoom bounds."""
import sys
import fractions
import decimal
import mcrfpy

fails = []
V = mcrfpy.Vector
tex = mcrfpy.default_texture
nan, inf = float("nan"), float("inf")


def expect(label, fn, exc, needle=None):
    try:
        fn()
    except exc as e:
        if type(e) is not exc and exc in (ValueError, OverflowError):
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


# ---- 1. apply_ranges: the (low, high) colour pair is held ----
hm = mcrfpy.HeightMap((4, 4), fill=0.5)
clayer = mcrfpy.ColorLayer("c", -1, (4, 4))
spec = None


class Evil:
    def __index__(self):
        spec.clear()
        return 7


spec = [(Evil(), 2, 3), mcrfpy.Color(4, 5, 6)]
ok("ColorLayer.apply_ranges gradient pair mutated by __index__", lambda: clayer.apply_ranges(hm, [((0, 1), spec)]))

# ---- 3. dict arguments: snapshot before user code ----
d = {}


class KeyWithValue:
    @property
    def value(self):
        d.clear()
        return 5


d[KeyWithValue()] = 2**100  # a heap object: freed by d.clear()
dm = mcrfpy.DiscreteMap((4, 4))
ok("DiscreteMap.to_heightmap(mapping) cleared by a key's .value", lambda: dm.to_heightmap(mapping=d))

w = {}


class WeightFloat:
    def __float__(self):
        w.clear()
        return 1.0


w[(0, 0)] = WeightFloat()
w[(1, 0)] = 2.0
src = mcrfpy.HeightMap((4, 4), fill=1.0)
dst = mcrfpy.HeightMap((4, 4))
ok("HeightMap.sparse_kernel_from weights cleared by a value's __float__", lambda: dst.sparse_kernel_from(src, w))
grow = {}


class KeyGrows:
    @property
    def x(self):
        for i in range(100):
            grow[(i + 10, 0)] = 1.0
        return 0

    @property
    def y(self):
        return 0


grow[KeyGrows()] = 1.0
expect("sparse_kernel_from: an object with .x / .y is not a position", lambda: dst.sparse_kernel_from(src, grow), TypeError)
ok("sparse_kernel_from ordinary", lambda: dst.sparse_kernel_from(src, {(0, 0): 0.5, (1, 0): 0.25, (-1.5, 0): 0.25}))

# ---- 4. BSP.__init__ again: stale nodes stay stale ----
b = mcrfpy.BSP((0, 0), (20, 20))
b.split_once(False, 10)
child = b.root.left
b.__init__(pos=(0, 0), size=(8, 8))
b.split_once(False, 4)
expect("node from before a re-__init__", lambda: child.bounds, RuntimeError, "stale")
expect("stale message names split_once", lambda: child.pos, RuntimeError, "split_once")
fresh = b.root.left
ok("a node fetched after the re-init is valid", lambda: fresh.bounds)
if "replaces" not in (mcrfpy.BSP.split_once.__doc__ or ""):
    fails.append("BSP.split_once docstring does not say a re-split replaces the children")

# ---- 5. waypoints: the integer helper ----
class Idx2:
    def __index__(self):
        return 2


e = mcrfpy.Entity()
ok("waypoints [(1.5, __index__ object)]", lambda: e.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(1.5, Idx2())]))
expect("waypoints (2**40, 0)", lambda: e.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(2**40, 0)]), OverflowError)
expect("waypoints (nan, 0)", lambda: e.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(nan, 0)]), ValueError)
expect("waypoints 'ab'", lambda: e.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=["ab"]), TypeError)
expect("path step (2**40, 0)", lambda: e.set_behavior(mcrfpy.Behavior.PATH, path=[(2**40, 0)]), OverflowError)
ok("waypoints Vector and list", lambda: e.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[V(1, 2), [3, 4]]))

# ---- 6. the floor matrix: remaining cell-taking APIs ----
if list(mcrfpy.bresenham((0.5, 0.5), (3.7, 0.2))) != [(0, 0), (1, 0), (2, 0), (3, 0)]:
    fails.append(f"bresenham floats: {mcrfpy.bresenham((0.5, 0.5), (3.7, 0.2))}")
if list(mcrfpy.bresenham(V(-0.5, 0), (2, 0))) != [(-1, 0), (0, 0), (1, 0), (2, 0)]:
    fails.append(f"bresenham Vector(-0.5, 0): {mcrfpy.bresenham(V(-0.5, 0), (2, 0))}")
expect("bresenham 1e10", lambda: mcrfpy.bresenham((0, 0), (1e10, 0)), OverflowError)
expect("bresenham 2**40", lambda: mcrfpy.bresenham((2**40, 0), (0, 0)), OverflowError)
expect("bresenham nan", lambda: mcrfpy.bresenham((nan, 0), (0, 0)), ValueError)
expect("bresenham not a position", lambda: mcrfpy.bresenham("ab", (0, 0)), TypeError, "start")
expect("bresenham too far apart (int deltas)", lambda: mcrfpy.bresenham((-2**31, 0), (2**31 - 1, 0)), OverflowError)

g = mcrfpy.Grid(grid_size=(8, 8), texture=tex)
for y in range(8):
    for x in range(8):
        g.at(x, y).walkable = True
        g.at(x, y).transparent = True
layer = mcrfpy.ColorLayer("fov", -1, (8, 8))
g.add_layer(layer)
ok("draw_fov (2.7, 3.2)", lambda: layer.draw_fov((2.7, 3.2), radius=3))
ok("draw_fov Vector", lambda: layer.draw_fov(V(2.7, 3.2), radius=3))
ok("draw_fov list", lambda: layer.draw_fov([2, 3], radius=3))
expect("draw_fov 2**40", lambda: layer.draw_fov((2**40, 0), radius=3), OverflowError)
expect("draw_fov nan", lambda: layer.draw_fov((nan, 0), radius=3), ValueError)
expect("draw_fov 'ab'", lambda: layer.draw_fov("ab", radius=3), TypeError, "source")

# subscripts floor and range-check (the old (int)PyLong_AsLong wrapped 2**32 to cell 0)
p = g[2.7, 3.2]
if tuple(p.grid_pos) != (2, 3):
    fails.append(f"grid[2.7, 3.2]: {tuple(p.grid_pos)}")
expect("grid[2**32, 0]", lambda: g[2**32, 0], OverflowError)
expect("grid[-0.5, 0]", lambda: g[-0.5, 0], IndexError)
expect("grid[nan, 0]", lambda: g[nan, 0], ValueError)
lay = mcrfpy.TileLayer("t", -1, tex, (8, 8))
lay[2.7, 3.2] = 5
if lay[2, 3] != 5:
    fails.append("layer[2.7, 3.2] = 5 did not set cell (2, 3)")
expect("layer[2**32, 0]", lambda: lay[2**32, 0], OverflowError)
gd = g.grid_data if hasattr(g, "grid_data") else None
# sizes: no wrap to a small valid size
expect("Grid(grid_size=(2**32 + 3, 3))", lambda: mcrfpy.Grid(grid_size=(2**32 + 3, 3), texture=tex), OverflowError)
expect("ColorLayer size (2**32 + 3, 3)", lambda: mcrfpy.ColorLayer("c", -1, (2**32 + 3, 3)), OverflowError)
expect("TileLayer size (2**32 + 3, 3)", lambda: mcrfpy.TileLayer("t", -1, tex, (2**32 + 3, 3)), OverflowError)
expect("DiscreteMap((2**32 + 4, 3))", lambda: mcrfpy.DiscreteMap((2**32 + 4, 3)), OverflowError)
ok("Grid(grid_size=(4.9, 3.1)) floors", lambda: mcrfpy.Grid(grid_size=(4.9, 3.1), texture=tex))

# ---- 7. Entity constructor behaves like the setter ----
e1 = mcrfpy.Entity(grid_pos=(2.7, 3.2))
e2 = mcrfpy.Entity()
e2.grid_pos = (2.7, 3.2)
if (e1.draw_pos.x, e1.draw_pos.y) != (2.0, 3.0) or (e2.draw_pos.x, e2.draw_pos.y) != (2.0, 3.0):
    fails.append(f"draw_pos after Entity(grid_pos=(2.7, 3.2)): {(e1.draw_pos.x, e1.draw_pos.y)} vs setter {(e2.draw_pos.x, e2.draw_pos.y)}")

# ---- 8. pathfinding starts from the logical cell, not the draw position ----
ent = mcrfpy.Entity(grid_pos=(0, 0))
g.entities.append(ent)
ent.draw_pos = (6.5, 6.5)
path = ent.path_to(7, 7)
if not path or tuple(path[0]) != (1, 1):
    fails.append(f"path_to from cell (0, 0) with draw_pos (6.5, 6.5): first step {path[:1]}, want (1, 1)")
dmap = g.get_dijkstra_map(ent)
if dmap.distance((0, 0)) != 0.0:
    fails.append(f"dijkstra rooted at an entity at cell (0, 0): distance there is {dmap.distance((0, 0))}")

# ---- 9. docstrings ----
for name in ("grid_pos", "grid_x", "grid_y"):
    doc = getattr(mcrfpy.Entity, name).__doc__ or ""
    if "floored" not in doc or "ValueError" in doc.split("floored")[0].split(".")[-1]:
        fails.append(f"Entity.{name} docstring still describes the old behaviour: {doc[-120:]!r}")


# ---- 10. one rule for "a real number" ----
class Index:
    def __index__(self): return 3


class Flt:
    def __float__(self): return 2.75


for label, fn, want in (
    ("Vector(index, float)", lambda: V(Index(), Flt()), (3.0, 2.75)),
    ("Vector((index, float))", lambda: V((Index(), Flt())), (3.0, 2.75)),
    ("Vector(Fraction, Decimal)", lambda: V(fractions.Fraction(5, 2), decimal.Decimal("1.5")), (2.5, 1.5)),
    ("Vector(True, 2)", lambda: V(True, 2), (1.0, 2.0)),
):
    try:
        v = fn()
        if (v.x, v.y) != want:
            fails.append(f"{label}: {(v.x, v.y)}, want {want}")
    except Exception as ex:
        fails.append(f"{label}: raised {type(ex).__name__}: {ex}")
v = V(0, 0)
ok("vector.x = __float__ object", lambda: setattr(v, "x", Flt()))
if v.x != 2.75:
    fails.append(f"vector.x = Flt(): {v.x}")
for label, fn in (
    ("Vector('a', 1)", lambda: V("a", 1)),
    ("Vector(('a', 1))", lambda: V(("a", 1))),
    ("Vector(b'a', 1)", lambda: V(b"a", 1)),
    ("vector.x = 'a'", lambda: setattr(v, "x", "a")),
    ("vector.x = None", lambda: setattr(v, "x", None)),
):
    expect(label, fn, TypeError)
fr = mcrfpy.Frame(pos=(0, 0), size=(1, 1))
fr.pos = (Index(), Flt())
if (fr.x, fr.y) != (3.0, 2.75):
    fails.append(f"frame.pos = (index, float): {(fr.x, fr.y)}")
cell_g = mcrfpy.Grid(grid_size=(8, 8), texture=tex)
if tuple(cell_g.at((Index(), Flt())).grid_pos) != (3, 2):
    fails.append("grid.at((index, __float__ 2.75)) did not floor to cell (3, 2)")
expect("grid.at(('a', 1))", lambda: cell_g.at(("a", 1)), TypeError)

# ---- 11. 'd'-parsed method floats: 1e39 is OverflowError ----
big = 1e39
hmx = mcrfpy.HeightMap((16, 16))
gg = mcrfpy.Grid(grid_size=(6, 6), texture=tex)
for y in range(6):
    for x in range(6):
        gg.at(x, y).walkable = True
expect("add_hill radius 1e39", lambda: hmx.add_hill((5, 5), big, 1.0), OverflowError)
expect("add_hill height 1e39", lambda: hmx.add_hill((5, 5), 3.0, big), OverflowError)
expect("dig_hill target_height 1e39", lambda: hmx.dig_hill((5, 5), 3.0, big), OverflowError)
expect("dig_bezier start_radius 1e39", lambda: hmx.dig_bezier(((0, 0), (1, 1), (2, 2), (3, 3)), big, 1.0, 0.0, 0.0), OverflowError)
expect("dig_bezier end_height 1e39", lambda: hmx.dig_bezier(((0, 0), (1, 1), (2, 2), (3, 3)), 1.0, 1.0, 0.0, big), OverflowError)
expect("get_dijkstra_map diagonal_cost 1e39", lambda: gg.get_dijkstra_map((1, 1), diagonal_cost=big), OverflowError)
expect("find_path diagonal_cost 1e39", lambda: gg.find_path((0, 0), (5, 5), diagonal_cost=big), OverflowError)
expect("add_hill radius inf", lambda: hmx.add_hill((5, 5), inf, 1.0), ValueError)

# ---- 12. constructors clamp opacity like the setter ----
for label, ctor in (
    ("Frame", lambda **kw: mcrfpy.Frame(**kw)),
    ("Caption", lambda **kw: mcrfpy.Caption(**kw)),
    ("Sprite", lambda **kw: mcrfpy.Sprite(**kw)),
    ("Grid", lambda **kw: mcrfpy.Grid(grid_size=(2, 2), texture=tex, **kw)),
    ("Arc", lambda **kw: mcrfpy.Arc(**kw)),
    ("Line", lambda **kw: mcrfpy.Line(**kw)),
    ("Circle", lambda **kw: mcrfpy.Circle(**kw)),
    ("Entity", lambda **kw: mcrfpy.Entity(**kw)),
):
    for given, want in ((2, 1.0), (-1, 0.0), (0.25, 0.25)):
        try:
            got = ctor(opacity=given).opacity
        except Exception as ex:
            fails.append(f"{label}(opacity={given}): raised {type(ex).__name__}: {ex}")
            continue
        if got != want:
            fails.append(f"{label}(opacity={given}).opacity = {got}, want {want} (the setter clamps)")

# ---- 2. zoom: after narrowing, and the derived centre stays finite ----
expect("Grid(zoom=1e-46)", lambda: mcrfpy.Grid(grid_size=(4, 4), texture=tex, zoom=1e-46), ValueError, "zoom")
zg = mcrfpy.Grid(grid_size=(4, 4), texture=tex, size=(40, 40))
expect("g.zoom = 1e-38 (centre would be inf)", lambda: setattr(zg, "zoom", 1e-38), ValueError, "zoom")
expect("g.zoom = 1e-46", lambda: setattr(zg, "zoom", 1e-46), ValueError, "zoom")
expect("g.animate('zoom', 1e-38)", lambda: zg.animate("zoom", 1e-38, 1.0), ValueError, "zoom")
expect("Grid(zoom=1e-38, size=(40, 40))", lambda: mcrfpy.Grid(grid_size=(4, 4), texture=tex, size=(40, 40), zoom=1e-38), ValueError, "zoom")
ok("g.zoom = 2e-7 (the minimum for a 40x40 view is 80 / (INT_MAX / 4) ~ 1.5e-7, #558)", lambda: setattr(zg, "zoom", 2e-7))
c = zg.center
if not all(abs(x) < 3.4e38 for x in (c.x, c.y)):
    fails.append(f"center after zoom = 2e-7 is not finite: {c}")
ok("g.center = g.center", lambda: setattr(zg, "center", zg.center))
expect("Grid(center_x=1e39)", lambda: mcrfpy.Grid(grid_size=(4, 4), texture=tex, center_x=1e39), OverflowError)
expect("Grid(center_y=-1e39)", lambda: mcrfpy.Grid(grid_size=(4, 4), texture=tex, center_y=-1e39), OverflowError)
expect("Grid(center_x=inf)", lambda: mcrfpy.Grid(grid_size=(4, 4), texture=tex, center_x=inf), ValueError)

for f_ in fails:
    print("FAIL:", f_)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
