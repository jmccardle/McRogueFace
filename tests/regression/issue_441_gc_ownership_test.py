#!/usr/bin/env python3
"""
GC ownership of C++-held Python references (#441).

A wrapper may report the Python objects held inside its C++ object to the cycle
collector only when every other owner of that object keeps the wrapper alive.

  * Reporting more than that let the GC clear a callback that a scene or parent still
    calls: the lambda's closure was wiped and calling it segfaulted.
  * Reporting less hid cycles that run through C++ (a pinned subclass with an
    attribute pointing back at its owner), so they leaked forever.

Callbacks are checked through __closure__ instead of being called, so a regression
fails here rather than crashing the interpreter.
"""
import gc
import sys
import weakref

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def intact(cb):
    return cb is not None and cb.__closure__ is not None and cb.__qualname__ != ""


def collect():
    for _ in range(3):
        gc.collect()


class SubFrame(mcrfpy.Frame):
    pass


class SubCaption(mcrfpy.Caption):
    pass


class Orc(mcrfpy.Entity):
    pass


class Drone(mcrfpy.Entity3D):
    pass


# ---------------------------------------------------------------------------
# A: a callback that another owner still uses is never cleared
# ---------------------------------------------------------------------------

def live_callbacks_survive():
    print("callbacks of co-owned objects survive a collection")
    s = mcrfpy.Scene("i441_live")

    def frame_on_scene():
        f = mcrfpy.Frame(); s.children.append(f)
        f.on_click = lambda p, b, a: f.x
    frame_on_scene(); collect()
    check(intact(s.children[0].on_click), "Frame on a scene, on_click captures itself")

    def nested():
        outer = mcrfpy.Frame(); s.children.append(outer)
        inner = mcrfpy.Frame(); outer.children.append(inner)
        inner.on_click = lambda p, b, a: inner.x
        outer.on_click = lambda p, b, a: inner.x
        inner.on_enter = lambda p: outer.x
    nested(); collect()
    outer = s.children[1]
    check(intact(outer.on_click) and intact(outer.children[0].on_click)
          and intact(outer.children[0].on_enter), "parent and child callbacks capture each other")

    holder = mcrfpy.Frame()

    def child_of_global():
        c = mcrfpy.Caption(text="x"); holder.children.append(c)
        c.on_click = lambda p, b, a: c.x
    child_of_global(); collect()
    check(intact(holder.children[0].on_click), "Caption in a Frame held by a global, no scene")

    def grid_child_and_cells():
        g = mcrfpy.Grid(grid_size=(5, 5)); s.children.append(g)
        c = mcrfpy.Caption(text="x"); g.children.append(c)
        c.on_click = lambda p, b, a: c.x
        g.on_cell_click = lambda cell, b, a: g.x
        g.on_cell_enter = lambda cell: g.x
    grid_child_and_cells(); collect()
    g = s.children[2]
    check(intact(g.children[0].on_click), "Caption in Grid.children")
    check(intact(g.on_cell_click) and intact(g.on_cell_enter), "GridView cell callbacks")

    gd = mcrfpy.GridData(grid_size=(5, 5))

    def entity_step():
        e = mcrfpy.Entity(grid_pos=(1, 1)); gd.entities.append(e)
        e.step = lambda t, d: e.grid_pos
    entity_step(); collect()
    check(intact(gd.entities[0].step), "Entity on a live grid, step captures itself")

    def viewport():
        vp = mcrfpy.Viewport3D(pos=(0, 0), size=(50, 50)); s.children.append(vp)
        vp.on_click = lambda p, b, a: vp.x
        d = mcrfpy.Entity3D(pos=(0, 0), scale=1.0); vp.entities.append(d)
        d.on_anim_complete = lambda *a: d.pos
    viewport(); collect()
    vp = s.children[3]
    check(intact(vp.on_click), "Viewport3D on a scene, on_click captures itself")
    check(intact(vp.entities[0].on_anim_complete), "Entity3D in a live viewport, callback captures itself")

    def scene_key():
        sc = mcrfpy.Scene("i441_key")
        sc.on_key = lambda k, a: sc.children
        mcrfpy.current_scene = sc
    scene_key(); collect()
    check(intact(mcrfpy.current_scene.on_key), "registered Scene on_key captures itself")


def unreachable_wrapper_does_not_clear_live_object():
    print("a garbage wrapper does not tear down an object something else owns")
    s = mcrfpy.Scene("i441_owner")
    v = mcrfpy.Grid(grid_size=(5, 5)); s.children.append(v)
    o = Orc(grid_pos=(1, 1)); v.entities.append(o); o.hp = 9
    o.step = lambda t, d: None
    f = mcrfpy.Frame(); s.children.append(f)
    f.on_click = lambda p, b, a: None
    # Put each wrapper in a garbage cycle of its own, then drop every handle.
    for w in (v, f, o.grid):
        junk = [w]; junk.append(junk)
    del v, o, f, w, junk
    collect()
    v = s.children[0]
    check(len(v.entities) == 1 and getattr(v.entities[0], "hp", None) == 9,
          "grid keeps its subclass entity and its attributes")
    check(v.entities[0].step is not None, "entity keeps its step callback")
    check(s.children[1].on_click is not None, "frame keeps its on_click")


def pinned_subclass_keeps_its_dict():
    print("a pinned subclass in a scene-owned parent keeps its attributes")
    s = mcrfpy.Scene("i441_dict")

    def setup():
        p = mcrfpy.Frame(); s.children.append(p)
        c = SubFrame(); p.children.append(c)
        c.me = c; c.tag = "kept"
    setup(); collect()
    c = s.children[0].children[0]
    check(type(c) is SubFrame and getattr(c, "tag", None) == "kept", "attributes survive")


# ---------------------------------------------------------------------------
# B: cycles that pass through C++ are collected
# ---------------------------------------------------------------------------

def freed(build):
    """build() returns a weakref into a cycle it created and abandoned."""
    r = build()
    collect()
    return r() is None


def cycles_are_collected():
    print("cycles through C++ ownership are collected")

    def frame_child_to_parent():
        p = mcrfpy.Frame(); c = SubFrame(); p.children.append(c); c.owner = p
        return weakref.ref(c)
    check(freed(frame_child_to_parent), "Frame -> pinned child -> attr -> Frame")

    def deep_tree():
        root = mcrfpy.Frame(); mid = mcrfpy.Frame(); root.children.append(mid)
        leaf = SubFrame(); mid.children.append(leaf); leaf.root = root
        return weakref.ref(leaf)
    check(freed(deep_tree), "Frame -> Frame (no wrapper) -> pinned leaf -> attr -> root")

    def grid_child_to_grid():
        g = mcrfpy.Grid(grid_size=(5, 5)); c = SubCaption(text="x"); g.children.append(c); c.owner = g
        return weakref.ref(c)
    check(freed(grid_child_to_grid), "Grid -> children -> pinned Caption -> attr -> Grid")

    def entity_to_griddata():
        g = mcrfpy.GridData(grid_size=(5, 5)); o = Orc(grid_pos=(1, 1)); g.entities.append(o); o.home = g
        return weakref.ref(o)
    check(freed(entity_to_griddata), "GridData -> pinned Orc -> attr -> GridData")

    def entity_to_view():
        v = mcrfpy.Grid(grid_size=(5, 5)); o = Orc(grid_pos=(1, 1)); v.entities.append(o); o.view = v
        return weakref.ref(o)
    check(freed(entity_to_view), "GridView -> GridData -> pinned Orc -> attr -> GridView")

    def entity_to_cached_griddata():
        v = mcrfpy.Grid(grid_size=(5, 5)); o = Orc(grid_pos=(1, 1)); v.entities.append(o)
        o.data = v.grid_data           # the view caches this wrapper (#348)
        o.view = v
        return weakref.ref(o)
    check(freed(entity_to_cached_griddata), "GridView caching its GridData wrapper, both in the cycle")

    def plain_entity_step():
        e = mcrfpy.Entity(grid_pos=(1, 1)); e.step = lambda t, d: e.grid_pos
        return weakref.ref(e)
    check(freed(plain_entity_step), "Entity (sole owner) step captures itself")

    def subclass_entity_step():
        e = Orc(grid_pos=(1, 1)); e.step = lambda t, d: e.grid_pos
        return weakref.ref(e)
    check(freed(subclass_entity_step), "Orc (sole owner) step captures itself")

    def plain_entity_step_to_grid():
        g = mcrfpy.GridData(grid_size=(5, 5)); e = Orc(grid_pos=(1, 1)); g.entities.append(e)
        e.step = lambda t, d: g.grid_w
        return weakref.ref(e)
    check(freed(plain_entity_step_to_grid), "GridData -> pinned Orc -> step -> GridData")

    def unregistered_scene_child():
        sc = mcrfpy.Scene("i441_unreg_a"); c = SubFrame(); sc.children.append(c); c.owner = sc
        sc.unregister()
        return weakref.ref(c)
    check(freed(unregistered_scene_child), "unregistered Scene -> pinned child -> attr -> Scene")

    def unregistered_scene_key():
        sc = mcrfpy.Scene("i441_unreg_b"); c = SubFrame(); sc.children.append(c)
        sc.on_key = lambda k, a: sc.children
        sc.unregister()
        return weakref.ref(c)
    check(freed(unregistered_scene_key), "unregistered Scene on_key captures itself")

    def viewport_entity():
        vp = mcrfpy.Viewport3D(pos=(0, 0), size=(50, 50)); d = Drone(pos=(0, 0), scale=1.0)
        vp.entities.append(d); d.owner = vp
        return weakref.ref(d)
    check(freed(viewport_entity), "Viewport3D -> pinned Entity3D -> attr -> Viewport3D")

    def entity3d_callback():
        d = mcrfpy.Entity3D(pos=(0, 0), scale=1.0); d.on_anim_complete = lambda *a: d.pos
        return weakref.ref(d)
    check(freed(entity3d_callback), "Entity3D (sole owner) callback captures itself")


def main():
    live_callbacks_survive()
    unreachable_wrapper_does_not_clear_live_object()
    pinned_subclass_keeps_its_dict()
    cycles_are_collected()
    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
