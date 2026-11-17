"""#540 item 12 / review item 7: the sites that were still unchecked.

Scene.pos; a Grid child's grid_pos / grid_size; animation duration; default_transition_duration;
HeightMap add_hill / dig_hill / dig_bezier radii and heights (libtcod casts (int)(x - radius));
get_dijkstra_map / find_path diagonal_cost (cast to int hundredths); layer.apply_ranges bounds and
mutation of the ranges list by a component conversion (#543 class).
Left on purpose (listed in the commit): Sound / Music volume and pitch, shader uniforms."""
import sys
import mcrfpy

fails = []
V = mcrfpy.Vector
tex = mcrfpy.default_texture
nan, inf = float("nan"), float("inf")


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


# ---- Scene.pos ----
sc = mcrfpy.Scene("s540")
expect("scene.pos = ('a', 0)", lambda: setattr(sc, "pos", ("a", 0)), TypeError, "pos")
expect("scene.pos = (nan, 0)", lambda: setattr(sc, "pos", (nan, 0)), ValueError, "pos")
expect("scene.pos = Vector(0, inf)", lambda: setattr(sc, "pos", V(0, inf)), ValueError, "pos")
expect("scene.pos = 5", lambda: setattr(sc, "pos", 5), TypeError, "pos")
expect("scene.pos = (1e39, 0)", lambda: setattr(sc, "pos", (1e39, 0)), OverflowError, "pos")
ok("scene.pos = (3, 4)", lambda: setattr(sc, "pos", (3, 4)))

# ---- a Grid child's grid_pos / grid_size ----
g = mcrfpy.Grid(grid_size=(8, 8), texture=tex, size=(160, 160))
child = mcrfpy.Frame(pos=(0, 0), size=(5, 5))
g.children.append(child)
for attr in ("grid_pos", "grid_size"):
    expect(f"child.{attr} = (nan, 0)", lambda: setattr(child, attr, (nan, 0)), ValueError, attr)
    expect(f"child.{attr} = Vector(0, inf)", lambda: setattr(child, attr, V(0, inf)), ValueError, attr)
    expect(f"child.{attr} = ('a', 0)", lambda: setattr(child, attr, ("a", 0)), TypeError, attr)
    expect(f"child.{attr} = 5", lambda: setattr(child, attr, 5), TypeError, attr)
    expect(f"child.{attr} = (3e38, 0) (the pixel product leaves float range)",
           lambda: setattr(child, attr, (3e38, 0)), OverflowError, attr)
ok("child.grid_pos = (2, 3)", lambda: setattr(child, "grid_pos", (2, 3)))
ok("child.grid_size = (1, 2)", lambda: setattr(child, "grid_size", (1, 2)))

# ---- animation duration ----
f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
for bl, bad in (("nan", nan), ("inf", inf), ("-inf", -inf)):
    expect(f"animate duration {bl}", lambda: f.animate("x", 5.0, bad), ValueError, "duration")
expect("animate duration -1", lambda: f.animate("x", 5.0, -1.0), ValueError, "duration")
ok("animate duration 0", lambda: f.animate("x", 5.0, 0.0))
ok("animate duration 0.5", lambda: f.animate("x", 5.0, 0.5))

# ---- default_transition_duration ----
for bl, bad in (("nan", nan), ("inf", inf)):
    expect(f"default_transition_duration = {bl}", lambda: setattr(mcrfpy, "default_transition_duration", bad), ValueError)
expect("default_transition_duration = -1", lambda: setattr(mcrfpy, "default_transition_duration", -1.0), ValueError)
old = mcrfpy.default_transition_duration
ok("default_transition_duration = 0.25", lambda: setattr(mcrfpy, "default_transition_duration", 0.25))
mcrfpy.default_transition_duration = old

# ---- HeightMap hills and bezier ----
hm = mcrfpy.HeightMap((16, 16))
for name, call in (
    ("add_hill", lambda c, r, h: hm.add_hill(c, r, h)),
    ("dig_hill", lambda c, r, h: hm.dig_hill(c, r, h)),
):
    for bl, bad in (("nan", nan), ("inf", inf), ("-inf", -inf)):
        expect(f"{name} radius {bl}", lambda: call((5, 5), bad, 1.0), ValueError, "radius")
        expect(f"{name} height {bl}", lambda: call((5, 5), 3.0, bad), ValueError)
    expect(f"{name} center + radius beyond int", lambda: call((2e9, 0), 2e9, 1.0), OverflowError)
    expect(f"{name} center - radius beyond int", lambda: call((-2e9, 0), 2e9, 1.0), OverflowError)
    expect(f"{name} radius 3e38", lambda: call((5, 5), 3e38, 1.0), OverflowError)
    ok(f"{name} ordinary", lambda: call((5, 5), 3.0, 1.0))
    ok(f"{name} large but in range", lambda: call((5, 5), 1e9, 1.0))
pts = ((0, 0), (5, 1), (9, 9), (15, 15))
for bl, bad in (("nan", nan), ("inf", inf)):
    for i, nm in enumerate(("start_radius", "end_radius", "start_height", "end_height")):
        args = [1.0, 1.0, 0.0, 0.0]
        args[i] = bad
        expect(f"dig_bezier {nm} {bl}", lambda: hm.dig_bezier(pts, *args), ValueError, nm)
expect("dig_bezier radius 3e38", lambda: hm.dig_bezier(pts, 3e38, 1.0, 0.0, 0.0), OverflowError)
ok("dig_bezier ordinary", lambda: hm.dig_bezier(pts, 2.0, 1.0, 1.0, 0.5))

# ---- diagonal_cost ----
gg = mcrfpy.Grid(grid_size=(6, 6), texture=tex)
for y in range(6):
    for x in range(6):
        gg.at(x, y).walkable = True
for bl, bad in (("nan", nan), ("inf", inf)):
    expect(f"get_dijkstra_map diagonal_cost {bl}", lambda: gg.get_dijkstra_map((1, 1), diagonal_cost=bad), ValueError, "diagonal_cost")
    expect(f"find_path diagonal_cost {bl}", lambda: gg.find_path((0, 0), (5, 5), diagonal_cost=bad), ValueError, "diagonal_cost")
expect("get_dijkstra_map diagonal_cost 1e30", lambda: gg.get_dijkstra_map((1, 1), diagonal_cost=1e30), OverflowError)
expect("find_path diagonal_cost 1e30", lambda: gg.find_path((0, 0), (5, 5), diagonal_cost=1e30), OverflowError)
ok("get_dijkstra_map diagonal_cost 1.5", lambda: gg.get_dijkstra_map((1, 1), diagonal_cost=1.5))

# ---- layer.apply_ranges ----
src = mcrfpy.HeightMap((4, 4), fill=0.5)
clayer = mcrfpy.ColorLayer("c", -1, (4, 4))
tlayer = mcrfpy.TileLayer("t", -1, tex, (4, 4))
red = mcrfpy.Color(255, 0, 0, 255)
for bl, bad in (("nan", nan), ("inf", inf)):
    expect(f"ColorLayer.apply_ranges min {bl}", lambda: clayer.apply_ranges(src, [((bad, 1.0), red)]), ValueError, "range")
    expect(f"TileLayer.apply_ranges max {bl}", lambda: tlayer.apply_ranges(src, [((0.0, bad), 3)]), ValueError, "range")
ok("ColorLayer.apply_ranges ordinary", lambda: clayer.apply_ranges(src, [((0.0, 1.0), red)]))
ok("TileLayer.apply_ranges ordinary", lambda: tlayer.apply_ranges(src, [((0.0, 1.0), 3)]))


def mutating_ranges(first_range_item):
    class X(int):
        def __float__(self):
            L.clear()
            return 0.0

    L = [((X(0), 1.0), first_range_item), ((0.0, 1.0), first_range_item)]
    return L


for label, call in (
    ("ColorLayer.apply_ranges", lambda L: clayer.apply_ranges(src, L)),
    ("TileLayer.apply_ranges", lambda L: tlayer.apply_ranges(src, L)),
):
    L = mutating_ranges(red if label.startswith("Color") else 3)
    try:
        call(L)
    except (IndexError, ValueError, TypeError):
        pass  # the list shrank under the loop: an ordinary error is fine, a crash is not
    except BaseException as e:
        fails.append(f"{label} with a mutating __float__: raised {type(e).__name__}: {e}")

for fl in fails:
    print("FAIL:", fl)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
