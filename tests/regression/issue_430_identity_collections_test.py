#!/usr/bin/env python3
"""
Object identity for the collection views (#430, Phase 2, "collections" group).

Frame.children, GridView.children, Scene.children and GridData.entities (also reached
as GridView.entities) used to build a fresh wrapper per access. They are now cached,
keyed on their OWNER (UIDrawable::children_serial, Scene::children_serial,
GridData::entities_serial), so the same live collection object comes back every time.
Collections themselves cannot be constructed or subclassed from Python; what a user
builds is the Frame/Entity inside them, and those must come back as themselves.
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


class Panel(mcrfpy.Frame):
    pass


class Orc(mcrfpy.Entity):
    pass


def drawable_children():
    print("drawable children")
    f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    same("Frame.children", lambda: f.children)

    g = mcrfpy.Grid(grid_size=(4, 4))
    same("GridView.children", lambda: g.children)
    kids = g.children
    gc.collect()
    check(g.children is kids, "GridView.children survives gc.collect() while held")
    marker = mcrfpy.Caption(text="!", pos=(0, 0))
    kids.append(marker)
    check(len(g.children) == 1 and g.children[0] is marker,
          "GridView.children: append through one reference is seen through the next")


def scene_children():
    print("scene children")
    s = mcrfpy.Scene("identity_collections_scene")
    same("Scene.children", lambda: s.children)
    kids = s.children
    p = Panel(pos=(1, 2), size=(3, 4))
    p.tag = "mine"
    kids.append(p)
    del p
    gc.collect()
    check(s.children is kids, "Scene.children survives gc.collect() while held")
    got = s.children[0]
    check(type(got) is Panel and getattr(got, "tag", None) == "mine",
          "Scene.children[0] is the user's Panel subclass with its attributes")
    other = mcrfpy.Scene("identity_collections_scene_2")
    check(other.children is not s.children, "each scene has its own children collection")


def find_recursion():
    print("UICollection.find recursion")
    s = mcrfpy.Scene("identity_collections_find")
    outer = mcrfpy.Frame(pos=(0, 0), size=(100, 100), name="outer")
    inner = Panel(pos=(1, 1), size=(10, 10), name="inner_panel")
    inner.tag = "deep"
    outer.children.append(inner)
    s.children.append(outer)
    inner_children = outer.children
    del inner
    gc.collect()

    hit = s.children.find("inner_panel", recursive=True)
    check(type(hit) is Panel and getattr(hit, "tag", None) == "deep",
          "find(recursive=True) returns the user's nested Panel with its attributes")
    many = s.children.find("inner_*", recursive=True)
    check(len(many) == 1 and many[0] is hit, "wildcard find(recursive=True) returns the same object")
    check(outer.children is inner_children,
          "recursive find reuses (does not replace) the child Frame's children collection")
    check(s.children.find("nope", recursive=True) is None, "find() of a missing name is None")


def entity_collections():
    print("entity collections")
    g = mcrfpy.Grid(grid_size=(8, 8))
    same("GridView.entities", lambda: g.entities)
    same("GridData.entities", lambda: g.grid_data.entities)
    check(g.entities is g.grid_data.entities, "view.entities is view.grid_data.entities")

    second = mcrfpy.GridView(grid=g, pos=(0, 0), size=(64, 64))
    check(second.entities is g.entities, "two views of one grid share one EntityCollection")

    other = mcrfpy.Grid(grid_size=(8, 8))
    check(other.entities is not g.entities, "each grid has its own EntityCollection")

    ents = g.entities
    o = Orc(grid_pos=(2, 2), name="orc")
    o.hp = 7
    ents.append(o)
    del o
    gc.collect()
    check(g.entities is ents, "EntityCollection survives gc.collect() while held")
    got = g.entities[0]
    check(type(got) is Orc and getattr(got, "hp", None) == 7,
          "entities[0] is the user's Orc subclass with its attributes")
    check(g.entities.find("orc") is got, "entities.find() returns the same object")
    check(next(iter(g.entities)) is got, "iterating entities yields the same object")

    # The collection keeps its grid alive; dropping every other reference is safe.
    ents = g.entities
    del g, second
    gc.collect()
    check(len(ents) == 1 and type(ents[0]) is Orc,
          "a held EntityCollection stays usable after its views are dropped")


def main():
    drawable_children()
    scene_children()
    find_recursion()
    entity_collections()
    if failures:
        print(f"FAIL: {len(failures)} failure(s)")
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
