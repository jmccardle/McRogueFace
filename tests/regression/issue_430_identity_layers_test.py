#!/usr/bin/env python3
"""
Object identity for grid layers (#430, Phase 2: layers group).

grid.layer(name) and grid.layers used to tp_alloc a fresh ColorLayer/TileLayer
wrapper per call. They now return the layer's one cached wrapper, keyed on
GridLayer::serial_number, so a layer the user constructed comes back as itself.
"""
import gc
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def same(label, get):
    try:
        a, b = get(), get()
    except Exception as exc:
        check(False, f"{label}: raised {type(exc).__name__}: {exc}")
        return
    check(a is not None and a is b, f"{label} is stable")


def user_layers_come_back():
    print("user-constructed layers")
    c = mcrfpy.ColorLayer(name="c", z_index=-1)
    t = mcrfpy.TileLayer(name="t", z_index=1)
    g = mcrfpy.Grid(grid_size=(6, 6), layers=[c, t])
    check(g.layer("c") is c, "grid.layer('c') is the user's ColorLayer")
    check(g.layer("t") is t, "grid.layer('t') is the user's TileLayer")
    layers = g.layers
    check(any(x is c for x in layers), "grid.layers holds the user's ColorLayer")
    check(any(x is t for x in layers), "grid.layers holds the user's TileLayer")
    same("grid.layer('c')", lambda: g.layer("c"))
    same("grid.layer('t')", lambda: g.layer("t"))
    l1, l2 = g.layers, g.layers
    check(all(a is b for a, b in zip(l1, l2)), "grid.layers elements are stable across reads")
    check(g.layer("c") is g.grid_data.layer("c"), "Grid and GridData lookups agree")


def add_layer_paths():
    print("add_layer and grid= paths")
    g = mcrfpy.Grid(grid_size=(5, 5))
    c = mcrfpy.ColorLayer(name="fog", z_index=2)
    g.add_layer(c)
    check(g.layer("fog") is c, "add_layer(): grid.layer() is the added ColorLayer")
    t = mcrfpy.TileLayer(name="deco", z_index=3, grid=g)
    check(g.layer("deco") is t, "TileLayer(grid=g): grid.layer() is the user's TileLayer")
    c2 = mcrfpy.ColorLayer(name="tint", z_index=4)
    c2.grid = g
    check(g.layer("tint") is c2, "layer.grid = g: grid.layer() is the user's ColorLayer")


def survives_dropping_name():
    print("user drops their reference")
    g = mcrfpy.Grid(grid_size=(4, 4))
    g.add_layer(mcrfpy.ColorLayer(name="x", z_index=1))
    gc.collect()
    a = g.layer("x")
    b = g.layer("x")
    check(a is not None and a is b, "grid.layer() is stable for a layer nobody else holds")
    a[1, 1] = mcrfpy.Color(10, 20, 30)
    check(g.layer("x")[1, 1].r == 10, "the re-created wrapper views the same layer")


def engine_created_layer():
    print("engine-created default layer")
    g = mcrfpy.Grid(grid_size=(4, 4))
    same("grid.layer('tilesprite')", lambda: g.layer("tilesprite"))
    ts = g.layer("tilesprite")
    if ts is not None:
        check(any(x is ts for x in g.layers), "grid.layers holds the same default-layer wrapper")
        check(ts.grid is g.grid_data, "default layer's grid is the GridData")


def grid_of_layer():
    print("layer.grid after lookup")
    c = mcrfpy.ColorLayer(name="c")
    g = mcrfpy.Grid(grid_size=(3, 3), layers=[c])
    check(g.layer("c").grid is g.grid_data, "grid.layer().grid is the GridData")
    g.remove_layer(c)
    check(c.grid is None, "removed layer reports no grid")
    check(g.layer("c") is None, "removed layer is no longer found")


def main():
    for t in (user_layers_come_back, add_layer_paths, survives_dropping_name,
              engine_created_layer, grid_of_layer):
        try:
            t()
        except Exception as exc:
            check(False, f"{t.__name__}: raised {type(exc).__name__}: {exc}")
        gc.collect()
    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
