"""#558: ONE camera invariant for a Grid, checked wherever zoom, the view size, the camera centre or the
cell size changes; a change that would violate it raises ValueError.

render() / localToGridWorld() cast to int:  center - span / (2 * zoom),  center / cell + span / (cell * zoom) + 2
(span = the box or its rotated AABB, at most |w| + |h|; cell >= 1). With L = INT_MAX / 4 = 536870911 they all
fit an int when  |center| <= L  and  span / zoom <= L.  Minimum zoom for a view: max(|w| + |h|, 1) / L.
(GCC's UBSan has no float-cast-overflow check, so the engine's own checks are what this test pins.)"""
import sys
import mcrfpy

fails = []
tex = mcrfpy.default_texture
L = 2**31 // 4          # INT_MAX / 4 (536870911 after integer division of INT_MAX; 2**31 // 4 is one more)
L = (2**31 - 1) // 4


def expect(label, fn, exc=ValueError, needle=None):
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


def grid(size=(40, 40), **kw):
    return mcrfpy.Grid(grid_size=(4, 4), texture=tex, size=size, **kw)


# ---- zoom: the minimum depends on the size (min = (w + h) / L = 80 / L ~ 1.49e-7 for 40 x 40) ----
g = grid()
expect("zoom = 1e-8 on a 40x40 view", lambda: setattr(g, "zoom", 1e-8), needle="zoom")
ok("zoom = 2e-7 on a 40x40 view", lambda: setattr(g, "zoom", 2e-7))
if g.zoom == 0.0 or g.zoom > 1e-6:
    fails.append(f"zoom stored as {g.zoom}")
c = g.center
if not all(abs(v) <= L for v in (c.x, c.y)):
    fails.append(f"default centre at the minimum zoom is outside the bound: {c}")
ok("g.center = g.center at the minimum zoom", lambda: setattr(g, "center", g.center))

# ---- a size change that would violate it raises (zoom is now near the minimum for 40x40) ----
g = grid()
g.zoom = 2e-7
expect("g.size = (1000, 1000) after zoom = 2e-7", lambda: setattr(g, "size", (1000, 1000)), needle="size")
expect("g.w = 1e4", lambda: setattr(g, "w", 1e4))
expect("g.h = 1e4", lambda: setattr(g, "h", 1e4))
expect("g.resize(1000, 1000)", lambda: g.resize(1000, 1000))
expect("g.animate('w', 1e4)", lambda: g.animate("w", 1e4, 1.0))
expect("g.animate('size', (1000, 1000))", lambda: g.animate("size", (1000, 1000), 1.0))
expect("g.animate('w', delta) whose end violates", lambda: g.animate("w", 1e4, 1.0, delta=True))
if tuple(g.size) != (40.0, 40.0):
    fails.append(f"size changed to {tuple(g.size)} despite the rejected changes")
ok("g.size = (41, 41) stays inside the invariant", lambda: setattr(g, "size", (41, 41)))

# ---- zoom animation targets, including delta ----
g = grid()
expect("animate zoom to 1e-9", lambda: g.animate("zoom", 1e-9, 1.0))
expect("animate zoom by delta to <= 0", lambda: g.animate("zoom", -1.0, 1.0, delta=True))
ok("animate zoom to 2.0", lambda: g.animate("zoom", 2.0, 1.0))

# ---- a (0, 0) view does not make a tiny zoom acceptable: a view is at least one pixel in the arithmetic ----
g = grid()
g.size = (0, 0)
expect("zoom = 1e-10 on a (0, 0) view", lambda: setattr(g, "zoom", 1e-10))
ok("zoom = 3e-9 on a (0, 0) view (1 / 3e-9 < L)", lambda: setattr(g, "zoom", 3e-9))

# ---- camera centre: |center| <= L ----
g = grid()
expect("center = (1e9, 0)", lambda: setattr(g, "center", (1e9, 0)), needle="center")
expect("center_x = 6e8", lambda: setattr(g, "center_x", 6e8))
expect("center_y = -6e8", lambda: setattr(g, "center_y", -6e8))
expect("center_camera((1e9, 1))", lambda: g.center_camera((1e9, 1)))
expect("animate center_x to 1e9", lambda: g.animate("center_x", 1e9, 1.0))
expect("animate center to (1e9, 0)", lambda: g.animate("center", (1e9, 0), 1.0))
ok("center = (5e8, 5e8)", lambda: setattr(g, "center", (5e8, 5e8)))
expect("Grid(center_x=6e8)", lambda: grid(center_x=6e8))
expect("Grid(zoom=1e-9)", lambda: grid(zoom=1e-9))
expect("Grid(size=(100, 100), zoom=1e-9)", lambda: grid(size=(100, 100), zoom=1e-9))
ok("Grid(zoom=2.0, center_x=100)", lambda: grid(zoom=2.0, center_x=100))

# ---- cell size: a non-default centre scales by new / old, the map-sized view follows the map ----
gd = mcrfpy.GridData(grid_size=(4, 4), texture=tex)
view = mcrfpy.Grid(grid=gd)           # a view over it (size follows the map)
view.center = (5e8, 0)                # near the bound, camera is no longer the default
old_cell = tuple(gd.cell_size)
expect("cell_size x4 would scale the centre past the bound",
       lambda: setattr(gd, "cell_size", (old_cell[0] * 4, old_cell[1] * 4)), needle="center")
if tuple(gd.cell_size) != old_cell:
    fails.append(f"cell_size changed to {tuple(gd.cell_size)} despite the ValueError")
ok("cell_size back to the same value", lambda: setattr(gd, "cell_size", old_cell))
view2 = mcrfpy.Grid(grid=gd, zoom=3e-6)       # a size-follows-map view at a smallish zoom
ok("cell_size small change with views at a safe zoom", lambda: setattr(gd, "cell_size", (old_cell[0] + 1, old_cell[1] + 1)))

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
