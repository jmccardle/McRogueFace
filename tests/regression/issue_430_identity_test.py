#!/usr/bin/env python3
"""
Object identity for every accessor that returns an identity-bearing engine object (#430).

Each accessor below used to build a fresh wrapper per call, so `x.attr is x.attr` was
False and a Python subclass came back as its base type. Accessors now go through the
cache-aware `to_python()` helper. tools/lint_bindings.py lists the call sites; this test
is the behavioural half of that gate.
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
    except Exception as exc:  # an accessor that raises is a failure, not a skip
        check(False, f"{label}: raised {type(exc).__name__}: {exc}")
        return
    check(a is not None and a is b, f"{label} is stable")


class Orc(mcrfpy.Entity):
    pass


def entities():
    print("entities")
    g = mcrfpy.Grid(grid_size=(10, 10))
    n = Orc(grid_pos=(4, 4), name="gob"); g.entities.append(n)
    check(g.entities.find("gob") is n, "entities.find() returns the appended object")
    same("view.entities", lambda: g.entities)
    check(g.entities is g.grid_data.entities, "view.entities is grid_data.entities")
    check(g.at(4, 4).entities[0] is n, "GridPoint.entities[0] is the entity")
    r = g.grid_data.entities_in_radius((4, 4), 2)
    check(len(r) == 1 and r[0] is n, "entities_in_radius() returns the entity")
    seer = mcrfpy.Entity(grid_pos=(5, 4)); g.entities.append(seer)
    v = seer.visible_entities()
    check(any(x is n for x in v), "visible_entities() returns the entity")
    g.perspective = n
    check(g.perspective is n, "GridView.perspective is the assigned entity")
    g.perspective = None
    popped = g.entities.pop(0)
    check(popped is n, "entities.pop() returns the object")
    same("Entity.perspective_map", lambda: seer.perspective_map)


def collections():
    print("collections")
    f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    same("Frame.children", lambda: f.children)
    g = mcrfpy.Grid(grid_size=(4, 4))
    same("GridView.children", lambda: g.children)
    s = mcrfpy.Scene("identity_scene")
    same("Scene.children", lambda: s.children)


def layers_and_grid():
    print("layers and their grid")
    c = mcrfpy.ColorLayer(name="c", z_index=-1)
    t = mcrfpy.TileLayer(name="t", z_index=1)
    g = mcrfpy.Grid(grid_size=(6, 6), layers=[c, t])
    check(g.layer("c") is c, "grid.layer(name) is the added ColorLayer")
    check(g.layer("t") is t, "grid.layer(name) is the added TileLayer")
    check(g.layers[0] is c or g.layers[1] is c, "grid.layers contains the ColorLayer")
    check(c.grid is g.grid_data, "ColorLayer.grid is the GridData")
    check(t.grid is g.grid_data, "TileLayer.grid is the GridData")


def textures():
    print("textures")
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    g = mcrfpy.Grid(grid_size=(4, 4), texture=tex)
    check(g.texture is tex, "GridView.texture is the texture passed in")
    check(g.grid_data.texture is tex, "GridData.texture is the texture passed in")
    t = mcrfpy.TileLayer(name="t", texture=tex)
    check(t.texture is tex, "TileLayer.texture is the texture passed in")


def dijkstra():
    print("dijkstra maps")
    g = mcrfpy.Grid(grid_size=(8, 8))
    same("get_dijkstra_map(root)", lambda: g.get_dijkstra_map((0, 0)))


def main():
    for t in (entities, collections, layers_and_grid, textures, dijkstra):
        t()
        gc.collect()
    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
