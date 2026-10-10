#!/usr/bin/env python3
"""
DiscreteMap object identity (#430, Phase 2: discretemap group).

entity.perspective_map is documented as a live reference, but it used to build a
fresh wrapper per read, so `e.perspective_map is e.perspective_map` was False and a
DiscreteMap the user assigned (or subclassed) came back as a different object. The
cache key now lives on the C++ DiscreteMap (serial_number), and every DiscreteMap a
Python caller creates (constructor and factories) is registered under it.
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


def lazy_perspective_map():
    print("lazy perspective_map")
    g = mcrfpy.Grid(grid_size=(8, 6))
    e = mcrfpy.Entity(grid_pos=(2, 2)); g.entities.append(e)
    same("Entity.perspective_map (lazy)", lambda: e.perspective_map)
    pm = e.perspective_map
    check(pm.enum_type is mcrfpy.Perspective, "engine-created map uses the Perspective enum")
    e.update_visibility()
    check(e.perspective_map is pm, "perspective_map survives update_visibility()")
    # Allocated by update_visibility() before any Python read:
    e2 = mcrfpy.Entity(grid_pos=(4, 4)); g.entities.append(e2)
    e2.update_visibility()
    same("Entity.perspective_map (allocated by update_visibility)", lambda: e2.perspective_map)


def assigned_map():
    print("assigned map")
    g = mcrfpy.Grid(grid_size=(8, 6))
    e = mcrfpy.Entity(grid_pos=(2, 2)); g.entities.append(e)

    mine = mcrfpy.DiscreteMap((8, 6), fill=1)
    e.perspective_map = mine
    check(e.perspective_map is mine, "assigned DiscreteMap comes back as itself")
    same("Entity.perspective_map (assigned)", lambda: e.perspective_map)

    # DiscreteMap is not subclassable (no Py_TPFLAGS_BASETYPE), so identity is the
    # whole contract here.
    restored = mcrfpy.DiscreteMap.from_bytes(bytes(8 * 6), (8, 6))
    e.perspective_map = restored
    check(e.perspective_map is restored, "from_bytes() map comes back as itself")

    for name, make in (
        ("invert()", lambda: mine.invert()),
        ("bool()", lambda: mine.bool(1)),
        ("from_heightmap()", lambda: mcrfpy.DiscreteMap.from_heightmap(
            mcrfpy.HeightMap((8, 6)), [((0.0, 1.0), 1)])),
    ):
        try:
            m = make()
        except Exception as exc:
            check(False, f"{name}: raised {type(exc).__name__}: {exc}")
            continue
        e.perspective_map = m
        check(e.perspective_map is m, f"{name} result comes back as itself")

    e.perspective_map = None
    fresh = e.perspective_map
    check(fresh is not None and fresh is not mine, "clearing gives a fresh lazy map")
    same("Entity.perspective_map (after clear)", lambda: e.perspective_map)


def reinit_does_not_hijack():
    print("re-init")
    g = mcrfpy.Grid(grid_size=(8, 6))
    e = mcrfpy.Entity(grid_pos=(2, 2)); g.entities.append(e)
    m = mcrfpy.DiscreteMap((8, 6))
    e.perspective_map = m
    m.__init__((3, 3))  # m now wraps a different C++ map
    pm = e.perspective_map
    check(pm is not m, "re-initialised wrapper no longer answers for the entity's map")
    check(tuple(pm.size) == (8, 6), "entity's map keeps its own size")
    same("Entity.perspective_map (after re-init)", lambda: e.perspective_map)


def wrapper_dropped():
    print("wrapper dropped")
    g = mcrfpy.Grid(grid_size=(8, 6))
    e = mcrfpy.Entity(grid_pos=(2, 2)); g.entities.append(e)
    pm = e.perspective_map
    pm[1, 1] = 2
    del pm
    gc.collect()
    again = e.perspective_map
    check(int(again[1, 1]) == 2, "re-wrapped map is still the live data")
    same("Entity.perspective_map (re-wrapped)", lambda: e.perspective_map)


def main():
    lazy_perspective_map()
    assigned_map()
    reinit_does_not_hijack()
    wrapper_dropped()
    if failures:
        print(f"FAIL: {len(failures)} failure(s)")
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
