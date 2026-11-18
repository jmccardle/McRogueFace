"""#558 review: failed Grid.__init__ changes nothing; GridData.texture= obeys the camera invariant like
cell_size=; a throwing __bool__ propagates from bool setters instead of reading as true; extreme cameras
render without an unsaturated float -> int cast."""
import sys
import mcrfpy

class _Fails(list):
    def append(self, m):
        print("FAIL:", m, flush=True)  # printed as found: a later case may die on a stale error
        super().append(m)


fails = _Fails()


def expect(label, fn, exc):
    try:
        fn()
    except exc:
        return True
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want {exc.__name__}")
        return False
    fails.append(f"{label}: accepted")
    return False


class Boom:
    def __bool__(self):
        raise RuntimeError("boom")


# 2. failed __init__ leaves the object untouched
g = mcrfpy.Grid(grid_size=(10, 10), size=(800, 600), pos=(5, 6))
before = (g.zoom, tuple(g.pos), tuple(g.size), tuple(g.center))
expect("init zoom=1e-9", lambda: g.__init__(grid_size=(10, 10), size=(300, 200), pos=(50, 60), zoom=1e-9), ValueError)
after = (g.zoom, tuple(g.pos), tuple(g.size), tuple(g.center))
if before != after:
    fails.append(f"failed __init__ changed the grid: {before} -> {after}")

# 3. texture= obeys the camera invariant
g = mcrfpy.Grid(grid_size=(10, 10), size=(100, 100))
g.center = (5e8, 0)
cs = tuple(g.cell_size)
expect("texture= with centre over the limit", lambda: setattr(g, "texture", mcrfpy.default_texture), ValueError)
if g.texture is not None or tuple(g.cell_size) != cs:
    fails.append("failed texture= changed the grid")
gd = mcrfpy.GridData(grid_size=(4, 4))
view = mcrfpy.Grid(grid=gd, size=(100, 100))
view.center = (5e8, 0)
expect("GridData.texture= with a view over the limit",
       lambda: setattr(gd, "texture", mcrfpy.default_texture), ValueError)
ok_g = mcrfpy.Grid(grid_size=(4, 4), size=(100, 100))
ok_g.texture = mcrfpy.default_texture  # a sane camera still accepts it

# 5. PyObject_IsTrue errors propagate
t = mcrfpy.Timer("t558", lambda *a: None, 1000)
expect("Timer.active = Boom()", lambda: setattr(t, "active", Boom()), RuntimeError)
t.stop()
seen = []
for cls in ("Entity3D", "Viewport3D"):
    if not hasattr(mcrfpy, cls):
        continue
    try:
        o = getattr(mcrfpy, cls)()
    except Exception:
        continue
    for attr in ("visible", "anim_loop", "anim_paused", "auto_animate", "enable_vertex_snap",
                 "enable_affine", "enable_dither", "enable_fog"):
        if cls == "Viewport3D" and attr == "visible":
            continue  # the drawable's own setter, which demands a real bool
        if attr in dir(o):
            seen.append(f"{cls}.{attr}")
            expect(f"{cls}.{attr} = Boom()", lambda: setattr(o, attr, Boom()), RuntimeError)

print('3D bool setters exercised:', seen)

# 4. extreme cameras render (saturating casts)
sc = mcrfpy.Scene("r558")
g = mcrfpy.Grid(grid_size=(10, 10), size=(200, 200), texture=mcrfpy.default_texture)
g.add_layer(mcrfpy.ColorLayer(name="c", z_index=-1))
sc.children.append(g)
mcrfpy.current_scene = sc
for c in ((0, 0), (5e8, 5e8), (-5e8, -5e8)):
    g.center = c
    mcrfpy.step(0.01)
    g.at(0, 0)
try:
    g.zoom = 1.0
    g.center = (-5e8, 5e8)
    g.perspective = None
    mcrfpy.step(0.01)
except Exception as e:
    fails.append(f"render at extreme centre: {e}")

print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
