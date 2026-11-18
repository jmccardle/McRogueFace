"""#558: convert ALL arguments first, then validate state and use it.

Each case is a hostile number (tests/regression/_hostile.py) whose conversion runs user code that
changes the object the method has ALREADY validated against: re-initialises a layer / map to 1x1,
detaches a layer from its grid, clears a BSP, re-initialises an entity. The method must not touch
freed or out-of-bounds memory; an ordinary exception is an acceptable answer. Run under `make asan`
(or any sanitizer) for the real signal: before the fix every case here is a SEGV, a heap overflow or
a use-after-free.

Run one case: MCRF_CASE=<name> ./mcrogueface --headless --exec tests/regression/issue_558_...py"""
import os
import sys
import mcrfpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # --exec does not put the script's directory on sys.path
from _hostile import Hostile, Failures  # noqa: E402

F = Failures()
tex = mcrfpy.default_texture
CASES = {}


def case(fn):
    CASES[fn.__name__] = fn
    return fn


@case
def colorlayer_draw_fov_detaches_layer():
    g = mcrfpy.Grid(grid_size=(10, 10), texture=tex)
    layer = mcrfpy.ColorLayer("fov", -1, (10, 10))
    g.add_layer(layer)
    evil = Hostile(lambda: setattr(layer, "grid", None), 1)
    F.attempt("ColorLayer.draw_fov((evil, 1)) with layer.grid = None", lambda: layer.draw_fov((evil, 1)), evil)


@case
def colorlayer_set_reinit():
    layer = mcrfpy.ColorLayer("c", -1, (50, 50))
    evil = Hostile(lambda: layer.__init__("c", -1, (1, 1)), 3)
    F.attempt("ColorLayer.set((49, 49), (evil, 2, 3)) with a re-init to 1x1",
              lambda: layer.set((49, 49), (evil, 2, 3)), evil)


@case
def colorlayer_subscript_assign_reinit():
    layer = mcrfpy.ColorLayer("c", -1, (50, 50))
    evil = Hostile(lambda: layer.__init__("c", -1, (1, 1)), 3)

    def go():
        layer[49, 49] = (evil, 2, 3)
    F.attempt("ColorLayer[49, 49] = (evil, 2, 3) with a re-init to 1x1", go, evil)


@case
def tilelayer_set_reinit():
    layer = mcrfpy.TileLayer("t", -1, tex, (50, 50))
    evil = Hostile(lambda: layer.__init__("t", -1, tex, (1, 1)), 3)
    F.attempt("TileLayer.set((49, 49), evil) with a re-init to 1x1", lambda: layer.set((49, 49), evil), evil)


@case
def discretemap_subscript_assign_reinit():
    dm = mcrfpy.DiscreteMap((50, 50))
    evil = Hostile(lambda: dm.__init__((1, 1)), 5)

    def go():
        dm[49, 49] = evil
    F.attempt("DiscreteMap[49, 49] = evil (.value / __index__) with a re-init to 1x1", go, evil)


@case
def discretemap_set_reinit():
    dm = mcrfpy.DiscreteMap((50, 50))
    evil = Hostile(lambda: dm.__init__((1, 1)), 5)
    F.attempt("DiscreteMap.set(49, 49, evil) with a re-init to 1x1", lambda: dm.set(49, 49, evil), evil)


@case
def bspnode_contains_clears_bsp():
    bsp = mcrfpy.BSP((0, 0), (20, 20))
    bsp.split_once(False, 10)
    leaf = bsp.root.left
    evil = Hostile(lambda: bsp.clear(), 5)
    F.attempt("BSPNode.contains((evil, 5)) with bsp.clear()", lambda: leaf.contains((evil, 5)), evil)


@case
def entity_set_behavior_reinit():
    e = mcrfpy.Entity()
    evil = Hostile(lambda: e.__init__(), 3)
    F.attempt("Entity.set_behavior(WAYPOINT, waypoints=[(evil, 3), (1, 1)]) with e.__init__()",
              lambda: e.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(evil, 3), (1, 1)] * 50), evil)


if __name__ == "__main__":
    only = os.environ.get("MCRF_CASE")
    for name, fn in CASES.items():
        if only and name != only:
            continue
        fn()
    F.finish()
