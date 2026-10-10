#!/usr/bin/env python3
"""
Entity ownership and identity pin (#436, covering #424, #429, #437).

An entity's Python wrapper is pinned exactly while a grid owns the entity, and only
for subclasses. Ownership changes go through one choke point, so every attach re-pins
and every detach releases. The entity's back-reference to its grid is non-owning, so
dropping a grid frees it and its entities. The step callback belongs to the entity,
not to its grid membership.
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


class Orc(mcrfpy.Entity):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.hp = 7
        self.steps = 0

    def on_step(self, trigger, data):
        self.steps += 1


def recovered(grid):
    """Drop every Python reference we hold, then fetch the entity back from C++."""
    gc.collect()
    return grid.entities[-1]


def assert_subclass_survives(grid, label):
    back = recovered(grid)
    check(type(back) is Orc and getattr(back, "hp", None) == 7,
          f"{label}: subclass and attributes survive ({type(back).__name__})")


def reattach_paths():
    print("re-attach re-pins (#429)")
    g = mcrfpy.GridData(grid_size=(10, 10))

    o = Orc(grid_pos=(3, 3)); g.entities.append(o)
    g.entities.remove(o); g.entities.append(o)
    del o
    assert_subclass_survives(g, "remove + append")

    o = g.entities.pop(); g.entities.insert(0, o)
    del o
    gc.collect()
    back = g.entities[0]
    check(type(back) is Orc, "pop + insert")
    del back

    other = mcrfpy.GridData(grid_size=(10, 10))
    o = g.entities[0]; o.die(); other.entities.append(o)
    del o
    assert_subclass_survives(other, "die() + append to another grid")

    o = other.entities[0]; o.grid = None; o.grid = g
    del o
    assert_subclass_survives(g, "grid = None, then grid = g")

    o = g.entities[-1]; o.die(); g.entities.extend([o])
    del o
    assert_subclass_survives(g, "die() + extend")

    o = g.entities[-1]; o.die()
    g.entities.append(Orc(grid_pos=(0, 0)))
    g.entities[0] = o
    del o
    gc.collect()
    check(type(g.entities[0]) is Orc and g.entities[0].hp == 7, "setitem re-pins")


def step_callbacks():
    print("step callbacks survive re-attach")
    g = mcrfpy.GridData(grid_size=(10, 10))
    fired = []
    e = mcrfpy.Entity(grid_pos=(1, 1)); g.entities.append(e)
    e.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(8, 1)])
    e.step = lambda t, d: fired.append(t)
    g.entities.remove(e); g.entities.append(e)
    e.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(8, 1)])
    g.step(n=1)
    check(e.step is not None, "plain entity keeps .step after remove + append")
    check(len(fired) == 1, f".step fires after remove + append ({len(fired)} calls)")

    o = Orc(grid_pos=(1, 3)); g.entities.append(o)
    g.entities.remove(o); g.entities.append(o)
    o.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(8, 3)])
    g.step(n=1)
    check(o.steps == 1, f"subclass on_step fires after remove + append ({o.steps} calls)")


def never_attached_is_freed():
    print("an entity that never joins a grid is freed (#424)")
    for cls in (mcrfpy.Entity, Orc):
        w = weakref.ref(cls(grid_pos=(0, 0)))
        gc.collect()
        check(w() is None, f"unattached {cls.__name__} freed")


def detached_is_freed():
    print("a detached entity is freed")
    g = mcrfpy.GridData(grid_size=(5, 5))
    o = Orc(grid_pos=(1, 1)); g.entities.append(o); g.entities.remove(o)
    w = weakref.ref(o); del o; gc.collect()
    check(w() is None, "removed Orc freed")


def grid_with_entities_is_freed():
    print("dropping a grid frees it and its entities (#437)")
    for make in (lambda: mcrfpy.GridData(grid_size=(5, 5)),
                 lambda: mcrfpy.Grid(grid_size=(5, 5))):
        for cls in (mcrfpy.Entity, Orc):
            g = make(); e = cls(grid_pos=(1, 1)); g.entities.append(e)
            we = weakref.ref(e); del e, g; gc.collect()
            check(we() is None, f"{cls.__name__} in a dropped {type(make()).__name__} freed")


def gridpoint_does_not_pin_grid():
    print("grid.at() does not keep the grid alive (GridPoint had no tp_dealloc)")
    # A pinned subclass entity lives exactly as long as its grid owns it, so its
    # wrapper dying proves the grid was freed (a plain Entity's wrapper isn't pinned).
    for label, make, at in [
        ("GridData.at()", lambda: mcrfpy.GridData(grid_size=(5, 5)), lambda g: g.at(1, 1)),
        ("Grid.at()", lambda: mcrfpy.Grid(grid_size=(5, 5)), lambda g: g.at(1, 1)),
        ("Grid[x, y]", lambda: mcrfpy.Grid(grid_size=(5, 5)), lambda g: g[1, 1]),
    ]:
        g = make()
        e = Orc(grid_pos=(1, 1)); g.entities.append(e)
        at(g).walkable
        we = weakref.ref(e); del e, g; gc.collect()
        check(we() is None, f"grid freed after {label}")


def back_reference_is_weak():
    print("entity.grid does not keep the grid alive (#437)")
    e = mcrfpy.Entity(grid_pos=(1, 1))
    g = mcrfpy.GridData(grid_size=(5, 5)); g.entities.append(e)
    check(e.grid is g, "entity.grid is the owning GridData while it lives")
    del g; gc.collect()
    check(e.grid is None, "entity.grid is None once its grid is gone")


def main():
    reattach_paths()
    step_callbacks()
    never_attached_is_freed()
    detached_is_freed()
    grid_with_entities_is_freed()
    gridpoint_does_not_pin_grid()
    back_reference_is_weak()
    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
