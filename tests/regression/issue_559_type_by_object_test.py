"""#559: a type is identified by its TYPE OBJECT (PyObject_TypeCheck against the static type), never by
a tp_name string or by a module attribute looked up at call time.

Before: an object whose class is merely NAMED "mcrfpy.Frame" (type("mcrfpy.Frame", (), {})) was cast to
the C struct (a crash under ASan); a real Python subclass of Frame was rejected; after
`mcrfpy.VoxelGrid = mcrfpy.Frame` any Frame passed as a VoxelGrid."""
import os
import sys
import mcrfpy

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets", "tiled")

fails = []
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


def spoof(name):
    """A class whose tp_name is `name` and which has no C layout at all."""
    return type(name, (), {})


# ---- 1. PropertyBinding(target, property) ----
for tname in ("Frame", "Caption", "Sprite", "Grid", "GridView", "Line", "Circle", "Arc"):
    S = spoof("mcrfpy." + tname)
    expect(f"PropertyBinding(spoofed mcrfpy.{tname}, 'x')", lambda: mcrfpy.PropertyBinding(S(), "x"), TypeError)


class MyFrame(mcrfpy.Frame):
    pass


class MyGrid(mcrfpy.Grid):
    pass


class MyCaption(mcrfpy.Caption):
    pass


ok("PropertyBinding(MyFrame(), 'x') (a real subclass)", lambda: mcrfpy.PropertyBinding(MyFrame(), "x"))
ok("PropertyBinding(MyCaption(), 'x')", lambda: mcrfpy.PropertyBinding(MyCaption(), "x"))
ok("PropertyBinding(MyGrid(grid_size=(2, 2), texture=tex), 'x')",
   lambda: mcrfpy.PropertyBinding(MyGrid(grid_size=(2, 2), texture=tex), "x"))
ok("PropertyBinding(Frame(), 'x')", lambda: mcrfpy.PropertyBinding(mcrfpy.Frame(), "x"))
expect("PropertyBinding(object(), 'x')", lambda: mcrfpy.PropertyBinding(object(), "x"), TypeError)

# ---- 2. WangSet.resolve / apply, TileMapFile.apply_to_tile_layer ----
ts_path = os.path.join(ASSETS, "test_tileset.tsx")
tm_path = os.path.join(ASSETS, "test_map.tmx")
if os.path.exists(ts_path) and os.path.exists(tm_path):
    ws = mcrfpy.TileSetFile(ts_path).wang_set("terrain")
    tm = mcrfpy.TileMapFile(tm_path)
    FakeDM = spoof("mcrfpy.DiscreteMap")
    FakeTL = spoof("mcrfpy.TileLayer")

    # DiscreteMap / TileLayer may not be subclassable in this build: use the real type (a subclass,
    # when allowed, passes PyObject_TypeCheck too)
    def subclass_or_self(base, *a):
        try:
            return type("My" + base.__name__, (base,), {})(*a)
        except TypeError:
            return base(*a)

    expect("WangSet.resolve(spoofed DiscreteMap)", lambda: ws.resolve(FakeDM()), TypeError)
    ok("WangSet.resolve(a DiscreteMap subclass)", lambda: ws.resolve(subclass_or_self(mcrfpy.DiscreteMap, (3, 3))))
    expect("WangSet.apply(spoofed DiscreteMap, layer)",
           lambda: ws.apply(FakeDM(), mcrfpy.TileLayer("t", -1, tex, (3, 3))), TypeError)
    expect("WangSet.apply(dm, spoofed TileLayer)",
           lambda: ws.apply(mcrfpy.DiscreteMap((3, 3)), FakeTL()), TypeError)
    ok("WangSet.apply(dm, a TileLayer subclass)",
       lambda: ws.apply(mcrfpy.DiscreteMap((3, 3)), subclass_or_self(mcrfpy.TileLayer, "t", -1, tex, (3, 3))))
    expect("TileMapFile.apply_to_tile_layer(spoofed TileLayer, 'Ground')",
           lambda: tm.apply_to_tile_layer(FakeTL(), "Ground"), TypeError)
    ok("TileMapFile.apply_to_tile_layer(a TileLayer subclass, 'Ground')",
       lambda: tm.apply_to_tile_layer(subclass_or_self(mcrfpy.TileLayer, "t", -1, tex, (8, 8)), "Ground"))
else:
    fails.append(f"missing test assets under {ASSETS}")

# ---- 3. Viewport3D: VoxelGrid is the static type, not a module attribute ----
try:
    vp = mcrfpy.Viewport3D(pos=(0, 0), size=(64, 64))
    have_3d = hasattr(vp, "add_voxel_layer")
except Exception:
    have_3d = False
if have_3d:
    real_voxel_grid = mcrfpy.VoxelGrid
    vg = real_voxel_grid((4, 4, 4))
    ok("add_voxel_layer(a real VoxelGrid)", lambda: vp.add_voxel_layer(vg))
    mcrfpy.VoxelGrid = mcrfpy.Frame      # rebind the module attribute
    try:
        for name, call in (
            ("add_voxel_layer", lambda: vp.add_voxel_layer(mcrfpy.Frame())),
            ("remove_voxel_layer", lambda: vp.remove_voxel_layer(mcrfpy.Frame())),
            ("project_voxel_to_nav", lambda: vp.project_voxel_to_nav(mcrfpy.Frame())),
            ("clear_voxel_nav_region", lambda: vp.clear_voxel_nav_region(mcrfpy.Frame())),
        ):
            expect(f"{name}(a Frame) after mcrfpy.VoxelGrid = mcrfpy.Frame", call, TypeError)
        ok("add_voxel_layer(the real VoxelGrid) after the module attribute was rebound",
           lambda: vp.add_voxel_layer(real_voxel_grid((2, 2, 2))))
    finally:
        mcrfpy.VoxelGrid = real_voxel_grid
else:
    print("note: Viewport3D / VoxelGrid not available in this build; the 3D arm was not exercised")

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
