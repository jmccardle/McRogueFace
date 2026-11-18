"""#558 audit: every binding function found to read engine state BEFORE a call that can run user code and
use it AFTER, hit with the hostile-number harness (tests/regression/_hostile.py): a conversion / finalizer /
callback re-initialises the object, clears its container, detaches it, or replaces its backing store.
An ordinary exception is an acceptable answer; a crash (ASan) or SystemError is the failure.

Run one case: MCRF_CASE=<name> ./mcrogueface --headless --exec tests/regression/issue_558_audit_sites_test.py"""
import os
import sys
import warnings
import mcrfpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # --exec does not put the script's directory on sys.path
from _hostile import Hostile, Failures  # noqa: E402

F = Failures()
tex = mcrfpy.default_texture
CASES = {}
RED = mcrfpy.Color(255, 0, 0, 255)


def case(fn):
    CASES[fn.__name__] = fn
    return fn


def hm(n=2):
    return mcrfpy.HeightMap((n, n), fill=0.5)


# ---------------------------------------------------------------- layers applied from a HeightMap
@case
def colorlayer_apply_threshold_layer_reinit():
    h = hm(2)
    layer = mcrfpy.ColorLayer("c", -1, (2, 2))
    evil = Hostile(lambda: layer.__init__("c", -1, (64, 64)), 0.0)
    F.attempt("ColorLayer.apply_threshold, layer re-init in range", lambda: layer.apply_threshold(h, (evil, 1.0), RED), evil)


@case
def colorlayer_apply_threshold_heightmap_reinit():
    h = hm(2)
    layer = mcrfpy.ColorLayer("c", -1, (2, 2))
    evil = Hostile(lambda: h.__init__((1, 1)), 0.0)
    F.attempt("ColorLayer.apply_threshold, heightmap re-init in range", lambda: layer.apply_threshold(h, (evil, 1.0), RED), evil)


@case
def colorlayer_apply_gradient_reinit():
    h = hm(2)
    layer = mcrfpy.ColorLayer("c", -1, (2, 2))
    evil = Hostile(lambda: h.__init__((1, 1)), 0.0)
    F.attempt("ColorLayer.apply_gradient", lambda: layer.apply_gradient(h, (evil, 1.0), (0, 0, 0), (255, 255, 255)), evil)


@case
def colorlayer_apply_ranges_reinit():
    h = hm(2)
    layer = mcrfpy.ColorLayer("c", -1, (2, 2))
    evil = Hostile(lambda: layer.__init__("c", -1, (64, 64)), 0.0)
    F.attempt("ColorLayer.apply_ranges", lambda: layer.apply_ranges(h, [((evil, 1.0), RED)]), evil)


@case
def tilelayer_apply_threshold_reinit():
    h = hm(2)
    layer = mcrfpy.TileLayer("t", -1, tex, (2, 2))
    evil = Hostile(lambda: h.__init__((1, 1)), 0.0)
    F.attempt("TileLayer.apply_threshold", lambda: layer.apply_threshold(h, (evil, 1.0), 3), evil)


@case
def tilelayer_apply_ranges_reinit():
    h = hm(2)
    layer = mcrfpy.TileLayer("t", -1, tex, (2, 2))
    evil = Hostile(lambda: layer.__init__("t", -1, tex, (64, 64)), 0.0)
    F.attempt("TileLayer.apply_ranges", lambda: layer.apply_ranges(h, [((evil, 1.0), 3)]), evil)


@case
def gridata_apply_threshold_bool_reinit():
    gd = mcrfpy.GridData(grid_size=(10, 10))
    h = hm(10)
    evil = Hostile(lambda: h.__init__((1, 1)), True)
    F.attempt("GridData.apply_threshold, __bool__ re-inits the HeightMap",
              lambda: gd.apply_threshold(h, (0.0, 1.0), walkable=evil), evil)


@case
def gridata_apply_ranges_bool_reinit():
    gd = mcrfpy.GridData(grid_size=(10, 10))
    h = hm(10)
    evil = Hostile(lambda: h.__init__((1, 1)), True)
    F.attempt("GridData.apply_ranges", lambda: gd.apply_ranges(h, [((0.0, 1.0), {"walkable": evil})]), evil)


@case
def tilelayer_set_warning_hook_reinit():
    layer = mcrfpy.TileLayer("t", -1, tex, (100, 100))
    ran = Hostile(lambda: layer.__init__("t", -1, tex, (1, 1)), 0)

    def hook(*a, **k):
        ran.__index__()  # runs the action once

    old = warnings.showwarning
    warnings.showwarning = hook
    warnings.simplefilter("always")
    try:
        F.attempt("TileLayer[99, 99] = 10**6 with a warning hook that re-inits the layer",
                  lambda: layer.__setitem__((99, 99), 10**6), ran)
        layer.__init__("t", -1, tex, (100, 100))
        ran.calls = 0
        F.attempt("TileLayer.set((99, 99), 10**6) likewise", lambda: layer.set((99, 99), 10**6), ran)
    finally:
        warnings.showwarning = old
        warnings.resetwarnings()


# ---------------------------------------------------------------- HeightMap region / kernel / noise
@case
def heightmap_region_ops_reinit_self():
    for name, call in (
        ("fill", lambda h, e: h.fill(1.0, pos=(e, 0))),
        ("add_constant", lambda h, e: h.add_constant(1.0, pos=(e, 0))),
        ("scale", lambda h, e: h.scale(2.0, pos=(e, 0))),
        ("clamp", lambda h, e: h.clamp(0.0, 1.0, pos=(e, 0))),
    ):
        h = hm(100)
        evil = Hostile(lambda: h.__init__((2, 2)), 50)
        F.attempt(f"HeightMap.{name}(pos=(evil, 0)) with a re-init to 2x2", lambda: call(h, evil), evil)


@case
def heightmap_binary_ops_reinit():
    for name in ("add", "subtract", "multiply", "copy_from"):
        for victim in ("self", "other"):
            a, b = hm(100), hm(100)
            target = a if victim == "self" else b
            evil = Hostile(lambda: target.__init__((1, 1)), 50)
            F.attempt(f"HeightMap.{name}(other, source_pos=(evil, 0)) re-initialising {victim}",
                      lambda: getattr(a, name)(b, source_pos=(evil, 0)), evil)
    a, b = hm(100), hm(100)
    evil = Hostile(lambda: b.__init__((1, 1)), 50)
    F.attempt("HeightMap.lerp(other, 0.5, source_pos=(evil, 0))", lambda: a.lerp(b, 0.5, source_pos=(evil, 0)), evil)


@case
def heightmap_sparse_kernel_reinit():
    a, b = hm(8), hm(8)
    evil = Hostile(lambda: b.__init__((2, 2)), 0)
    F.attempt("HeightMap.sparse_kernel_from, source re-init in a key", lambda: a.sparse_kernel_from(b, {(evil, 0): 1.0}), evil)
    a = hm(8)
    evil = Hostile(lambda: a.__init__((64, 64)), 0)
    F.attempt("HeightMap.sparse_kernel, self re-init in a key", lambda: a.sparse_kernel({(evil, 0): 1.0}), evil)


@case
def noisesource_sample_reinit():
    ns = mcrfpy.NoiseSource(dimensions=2)
    evil = Hostile(lambda: ns.__init__(dimensions=4), 4)
    F.attempt("NoiseSource.sample(size, octaves=evil) re-initialising as 4D", lambda: ns.sample((4, 4), octaves=evil), evil)


# ---------------------------------------------------------------- DiscreteMap
@case
def discretemap_to_bool_callable_reinit():
    dm = mcrfpy.DiscreteMap((50, 50))
    ran = Hostile(lambda: dm.__init__((1, 1)), True)

    def pred(v):
        return bool(ran)

    F.attempt("DiscreteMap.bool(predicate that re-initialises the map)", lambda: dm.bool(pred), ran)


@case
def discretemap_init_enum_finalizer():
    dm = mcrfpy.DiscreteMap((8, 8))

    class E:
        def __del__(self):
            try:
                dm.fill(1)
            except Exception:
                pass

    dm.__init__((8, 8), enum=E())
    F.attempt("DiscreteMap re-__init__ releasing an enum whose __del__ uses the map", lambda: dm.__init__((8, 8)))


@case
def discretemap_region_ops_reinit():
    a, b = mcrfpy.DiscreteMap((100, 100)), mcrfpy.DiscreteMap((100, 100))
    evil = Hostile(lambda: a.__init__((2, 2)), 50)
    F.attempt("DiscreteMap.add(other, pos=(evil, 0)) re-initialising self", lambda: a.add(b, pos=(evil, 0)), evil)
    a, b = mcrfpy.DiscreteMap((100, 100)), mcrfpy.DiscreteMap((100, 100))
    evil = Hostile(lambda: b.__init__((1, 1)), 50)
    F.attempt("DiscreteMap.copy_from(other, source_pos=(evil, 0)) re-initialising other",
              lambda: a.copy_from(b, source_pos=(evil, 0)), evil)


# ---------------------------------------------------------------- Grid / GridData / view
@case
def gridview_subscript_clears_grid_data():
    g = mcrfpy.Grid(grid_size=(5, 5), texture=tex)
    evil = Hostile(lambda: setattr(g, "grid_data", None), 1)

    def go():
        g[(evil, 0)]
    F.attempt("Grid[(evil, 0)] with grid.grid_data = None", go, evil)


@case
def gridview_init_clears_grid_data():
    v = mcrfpy.Grid(grid_size=(5, 5), texture=tex)
    evil = Hostile(lambda: setattr(v, "grid_data", None), 1.0)
    F.attempt("Grid.__init__(pos=(evil, 0)) with grid.grid_data = None",
              lambda: v.__init__(grid_size=(5, 5), texture=tex, pos=(evil, 0)), evil)


@case
def griddata_get_dijkstra_map_roots_reinit():
    gd = mcrfpy.GridData(grid_size=(30, 30))
    evil = Hostile(lambda: gd.__init__(grid_size=(2, 2)), 5)
    F.attempt("GridData.get_dijkstra_map(roots=[(evil, 1)]) re-initialising the grid",
              lambda: gd.get_dijkstra_map(roots=[(evil, 1)]), evil)


# ---------------------------------------------------------------- collections
@case
def uicollection_slice_and_concat_clear():
    f = mcrfpy.Frame()

    def fill():
        f.children.clear()
        for _ in range(5):
            f.children.append(mcrfpy.Frame())

    class Idx(Hostile):
        pass

    for label, call in (
        ("children[evil:]", lambda e: f.children[e:]),
        ("del children[evil:]", lambda e: f.children.__delitem__(slice(e, None))),
        ("children[evil:] = [Frame()]", lambda e: f.children.__setitem__(slice(e, None), [mcrfpy.Frame()])),
    ):
        fill()
        evil = Hostile(lambda: f.children.clear(), 0)
        F.attempt(f"UICollection {label} with an __index__ that clears the collection", lambda: call(evil), evil)

    class L:
        def __init__(self):
            self.ran = 0

        def __len__(self):
            self.ran += 1
            f.children.clear()
            return 0

        def __getitem__(self, i):
            raise IndexError

    fill()
    lst = L()
    F.attempt("UICollection + a sequence whose __len__ clears the collection", lambda: f.children + lst)
    if lst.ran == 0:
        F.add("UICollection concat: the hostile __len__ never ran")


@case
def uicollection_finalizer_mutates():
    parent = mcrfpy.Frame()
    ran = []

    class Evil(mcrfpy.Frame):
        def __del__(self):
            ran.append(1)
            parent.children.clear()

    for label, op in (
        ("del children[1]", lambda: parent.children.__delitem__(1)),
        ("children.pop(1)", lambda: parent.children.pop(1)),
        ("children[1] = Frame()", lambda: parent.children.__setitem__(1, mcrfpy.Frame())),
        ("del children[1:]", lambda: parent.children.__delitem__(slice(1, None))),
    ):
        parent.children.clear()
        ran.clear()
        parent.children.append(mcrfpy.Frame())
        parent.children.append(Evil())
        F.attempt(f"UICollection {label} whose removed child's __del__ clears the collection", op)
        parent.children.clear()


@case
def uientitycollection_slice_concat_finalizer():
    g = mcrfpy.Grid(grid_size=(8, 8), texture=tex)

    def fill():
        g.entities.clear()
        for i in range(5):
            g.entities.append(mcrfpy.Entity(grid_pos=(i, 0)))

    for label, call in (
        ("entities[evil:]", lambda e: g.entities[e:]),
        ("del entities[evil:]", lambda e: g.entities.__delitem__(slice(e, None))),
    ):
        fill()
        evil = Hostile(lambda: g.entities.clear(), 0)
        F.attempt(f"UIEntityCollection {label} with an __index__ that clears the collection", lambda: call(evil), evil)

    ran = []

    class EvilE(mcrfpy.Entity):
        def __del__(self):
            ran.append(1)
            g.entities.clear()

    for label, op in (
        ("del entities[1]", lambda: g.entities.__delitem__(1)),
        ("del entities[1:]", lambda: g.entities.__delitem__(slice(1, None))),
    ):
        g.entities.clear()
        g.entities.append(mcrfpy.Entity(grid_pos=(0, 0)))
        g.entities.append(EvilE(grid_pos=(1, 0)))
        F.attempt(f"UIEntityCollection {label} whose removed entity's __del__ clears the collection", op)
        g.entities.clear()


@case
def frame_init_children_and_failed_init():
    parent = mcrfpy.Frame()
    seen = []

    class Evil(mcrfpy.Frame):
        def __del__(self):
            try:
                seen.append(len(parent.children))
            except Exception as e:
                seen.append(repr(e))

    parent.children.append(Evil())
    F.attempt("Frame.__init__ detaching a child whose __del__ reads frame.children", lambda: parent.__init__())
    f = mcrfpy.Frame()
    f.children.append(mcrfpy.Frame())
    F.attempt("Frame.__init__ with a bad argument", lambda: f.__init__(pos="not a position"))
    if len(f.children) != 1:
        F.add(f"a failed Frame.__init__ cost the frame its children (now {len(f.children)})")


# ---------------------------------------------------------------- entity
@case
def entity_pixel_and_sprite_grid():
    g = mcrfpy.Grid(grid_size=(8, 8), texture=tex)
    e = mcrfpy.Entity(grid_pos=(1, 1))
    g.entities.append(e)
    evil = Hostile(lambda: setattr(e, "grid", None), 3.0)
    F.attempt("entity.draw_pos... pixel setter with a conversion that detaches the entity", lambda: setattr(e, "pos", (evil, 0)), evil)

    e2 = mcrfpy.Entity()
    e2.tile_size = (2, 2)
    evil = Hostile(lambda: setattr(e2, "tile_width", 8), 0)
    F.attempt("entity.sprite_grid = [[evil, 0], [0, 0]] while tile_width changes", lambda: setattr(e2, "sprite_grid", [[evil, 0], [0, 0]]), evil)
    e2.tile_size = (2, 2)
    e2.sprite_grid = [1, 2, 3, 4]
    e2.tile_width = 4
    if e2.sprite_grid is not None:
        F.add("changing tile_width must clear a sprite_grid of the old shape")
    F.attempt("reading sprite_grid after the tile size changed", lambda: e2.sprite_grid)


@case
def entity3d_voxelpoint_and_collection():
    try:
        vp = mcrfpy.Viewport3D(pos=(0, 0), size=(64, 64))
        vp.set_grid_size(8, 8)
        p = vp.at(0, 0)
    except Exception:
        print("note: Viewport3D unavailable; the 3D arm was not exercised")
        return

    class B(int):
        def __bool__(self):
            vp.set_grid_size(512, 512)
            return True

    try:
        p.walkable = B(1)
    except TypeError:
        pass  # an int SUBCLASS is not a bool: its __bool__ is user code (the point holds a raw pointer)
    except BaseException as e:
        F.add(f"VoxelPoint.walkable = int subclass: {type(e).__name__}: {e}")
    else:
        F.add("VoxelPoint.walkable accepted an int subclass whose __bool__ is user code")
    try:
        p.walkable = True
        p.walkable = 1
    except BaseException as e:
        F.add(f"VoxelPoint.walkable = True / 1: {type(e).__name__}: {e}")


if __name__ == "__main__":
    only = os.environ.get("MCRF_CASE")
    for name, fn in CASES.items():
        if only and name != only:
            continue
        fn()
    F.finish()
