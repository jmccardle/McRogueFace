#!/usr/bin/env python3
"""
Object identity for the 3D binding surface (#430 Phase 2, group "threed").

Every accessor that hands a 3D object back to Python used to tp_alloc a fresh wrapper,
so `x.attr is x.attr` was False and a Python subclass came back as its base type.
Entity3D also carried its own copy of the old take-once pin; it now has the #436
design (PyIdentityPin synced in setViewport(), subclasses only).

Covered: Entity3D (collection getitem/iter/find/pop, animation callback target),
Entity3D.viewport, Entity3D.model, Viewport3D.entities, Viewport3D.get_billboard,
Model3D factories.
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


class Golem(mcrfpy.Entity3D):
    pass


class Tree(mcrfpy.Billboard):
    pass


class Statue(mcrfpy.Model3D):
    pass


def make_viewport():
    vp = mcrfpy.Viewport3D(pos=(0, 0), size=(100, 100))
    vp.set_grid_size(16, 16)
    return vp


def entities():
    print("entity collection")
    vp = make_viewport()
    same("Viewport3D.entities", lambda: vp.entities)

    e = mcrfpy.Entity3D(pos=(1, 1))
    e.name = "plain"
    vp.entities.append(e)
    check(vp.entities[0] is e, "entities[0] is the appended Entity3D")
    check(vp.entities.find("plain") is e, "entities.find() returns the appended Entity3D")
    check(next(iter(vp.entities)) is e, "iterating entities yields the appended Entity3D")
    same("entities[0]", lambda: vp.entities[0])

    g = Golem(pos=(2, 2))
    g.name = "golem"
    g.mood = "grumpy"
    vp.entities.append(g)
    check(vp.entities[1] is g, "entities[1] is the appended subclass instance")
    check(vp.entities.find("golem") is g, "entities.find() returns the subclass instance")

    popped = vp.entities.pop(0)
    check(popped is e, "entities.pop() returns the object")


def subclass_survives_in_viewport():
    print("subclass pin (#436 design)")
    vp = make_viewport()
    g = Golem(pos=(3, 3))
    g.name = "kept"
    g.mood = "stoic"
    vp.entities.append(g)
    del g
    gc.collect()
    back = vp.entities.find("kept")
    check(type(back) is Golem, "subclass type survives while the viewport owns it")
    check(getattr(back, "mood", None) == "stoic", "subclass attributes survive")

    # pop() hands back the subclass even though popping releases the pin
    del back
    gc.collect()
    popped = vp.entities.pop(0)
    check(type(popped) is Golem and getattr(popped, "mood", None) == "stoic",
          "pop() returns the subclass instance, not a base wrapper")


def entity_back_references():
    print("entity back-references")
    vp = make_viewport()
    e = mcrfpy.Entity3D(pos=(1, 1))
    vp.entities.append(e)
    check(e.viewport is vp, "Entity3D.viewport is the owning Viewport3D")
    same("Entity3D.viewport", lambda: e.viewport)

    m = mcrfpy.Model3D.cube(1.0)
    e.model = m
    check(e.model is m, "Entity3D.model is the assigned Model3D")
    same("Entity3D.model", lambda: e.model)

    built = mcrfpy.Model3D()
    e.model = built
    check(e.model is built, "Entity3D.model is a Model3D() the user constructed")

    s = Statue.sphere(0.5)
    check(type(s) is Statue, "Model3D factory classmethod keeps the subclass")
    s.material = "marble"
    e.model = s
    check(e.model is s, "Entity3D.model is the subclass instance from a factory")


def billboards():
    print("billboards")
    vp = make_viewport()
    bb = mcrfpy.Billboard(pos=(1.0, 0.0, 1.0))
    vp.add_billboard(bb)
    check(vp.get_billboard(0) is bb, "get_billboard(0) is the added Billboard")
    same("Viewport3D.get_billboard(0)", lambda: vp.get_billboard(0))

    t = Tree(pos=(2.0, 0.0, 2.0))
    t.species = "oak"
    vp.add_billboard(t)
    check(vp.get_billboard(1) is t, "get_billboard(1) is the subclass instance")


def animation_callback_target():
    print("animation callback target")
    vp = make_viewport()
    g = Golem(pos=(0, 0))
    vp.entities.append(g)
    seen = []

    def on_complete(target, prop, value):
        seen.append(target)

    g.animate('x', 5.0, 0.25, 'linear', callback=on_complete)
    for _ in range(3):
        mcrfpy.step(0.15)
    check(len(seen) == 1 and seen[0] is g, "animation callback receives the entity itself")


def main():
    for t in (entities, subclass_survives_in_viewport, entity_back_references,
              billboards, animation_callback_target):
        t()
        gc.collect()
    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
