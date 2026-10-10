#!/usr/bin/env python3
"""
Plain wrappers are pinned while their object is contained (#443).

#441 left a gap: a plain (non-subclass) child whose own wrapper was alive had two
owners, its parent's collection and that wrapper, so neither could report its
callbacks to the cycle collector, and a cycle through it leaked. Pinning every live
wrapper of a contained object (not only subclasses) gives the object one Python-side
owner, so the cycle is reported exactly once and collected.
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


def collect():
    for _ in range(3):
        gc.collect()


def freed(build):
    r = build()
    collect()
    return r() is None


def intact(cb):
    return cb is not None and cb.__closure__ is not None


def cycles():
    print("cycles through a plain child with a live wrapper are collected")

    def self_and_parent():
        dlg = mcrfpy.Frame(); ok = mcrfpy.Caption(text="ok"); dlg.children.append(ok)
        ok.on_click = lambda *a: (ok.x, dlg.x)
        return weakref.ref(dlg)
    check(freed(self_and_parent), "Caption on_click captures itself and its parent")

    def hover_dialog():
        dlg = mcrfpy.Frame(); ok = mcrfpy.Caption(text="ok"); dlg.children.append(ok)
        ok.on_enter = lambda p: setattr(ok, "x", 1)
        ok.on_click = lambda *a: dlg.x
        return weakref.ref(dlg)
    check(freed(hover_dialog), "hover captures the button, click captures the dialog")

    def grid_child():
        g = mcrfpy.Grid(grid_size=(4, 4)); c = mcrfpy.Caption(text="c"); g.children.append(c)
        c.on_click = lambda *a: (c.x, g.x)
        return weakref.ref(g)
    check(freed(grid_child), "Grid child captures itself and the grid")

    def entity():
        g = mcrfpy.GridData(grid_size=(4, 4)); e = mcrfpy.Entity(grid_pos=(1, 1)); g.entities.append(e)
        e.step = lambda t, d: (e.grid_pos, g.grid_w)
        return weakref.ref(g)
    check(freed(entity), "Entity step captures itself and its GridData")

    def unregistered_scene():
        sc = mcrfpy.Scene("i443_unreg"); c = mcrfpy.Frame(); sc.children.append(c)
        c.on_click = lambda *a: (c.x, sc.children)
        sc.unregister()
        return weakref.ref(c)
    check(freed(unregistered_scene), "unregistered Scene child captures itself and the scene")

    def entity3d():
        vp = mcrfpy.Viewport3D(pos=(0, 0), size=(50, 50)); d = mcrfpy.Entity3D(pos=(0, 0), scale=1.0)
        vp.entities.append(d)
        d.on_anim_complete = lambda *a: (d.pos, vp.x)
        return weakref.ref(vp)
    check(freed(entity3d), "Entity3D callback captures itself and its viewport")

    def wrapper_made_later():
        # The child's wrapper is created after it was contained (by indexing).
        dlg = mcrfpy.Frame(); dlg.children.append(mcrfpy.Caption(text="ok"))
        ok = dlg.children[0]
        ok.on_click = lambda *a: (ok.x, dlg.x)
        return weakref.ref(dlg)
    check(freed(wrapper_made_later), "wrapper created by indexing a contained child")


def live_callbacks():
    print("callbacks of contained plain objects survive")
    s = mcrfpy.Scene("i443_live")

    def setup():
        dlg = mcrfpy.Frame(); s.children.append(dlg)
        ok = mcrfpy.Caption(text="ok"); dlg.children.append(ok)
        ok.on_enter = lambda p: setattr(ok, "x", 1)
        ok.on_click = lambda *a: dlg.x
    setup(); collect()
    ok = s.children[0].children[0]
    check(intact(ok.on_enter) and intact(ok.on_click), "dialog on a scene keeps its handlers")


def identity():
    print("plain contained objects keep one wrapper")
    f = mcrfpy.Frame(); f.children.append(mcrfpy.Caption(text="x"))
    r = weakref.ref(f.children[0])
    collect()
    check(r() is not None and r() is f.children[0], "weakref to a contained Caption stays valid")

    g = mcrfpy.GridData(grid_size=(4, 4)); g.entities.append(mcrfpy.Entity(grid_pos=(1, 1)))
    check(g.entities[0] is g.entities[0], "grid.entities[0] is grid.entities[0]")

    c = f.children.pop()
    r = weakref.ref(c); del c; collect()
    check(r() is None, "removing a child releases its pin")

    e = g.entities[0]; g.entities.remove(e)
    r = weakref.ref(e); del e; collect()
    check(r() is None, "removing an entity releases its pin")


def main():
    cycles()
    live_callbacks()
    identity()
    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
