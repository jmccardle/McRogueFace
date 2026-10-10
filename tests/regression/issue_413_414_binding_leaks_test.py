#!/usr/bin/env python3
"""
Reference leaks in binding recipes (#413, #414; sites listed by tools/lint_bindings.py).

#414: PyVector::from_arg() returns a new reference; setters that never released it made
every Vector argument immortal and leaked a fresh Vector per tuple argument.
#413: a new reference passed inline to a borrowing API (PyDict_SetItemString) leaked the
value on every call.
"""
import sys
import gc

import mcrfpy

failures = []
N = 200


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def vector_setters():
    print("Vector setters release their argument (#414)")
    cases = [
        ("Line.start", mcrfpy.Line(start=(0, 0), end=(1, 1)), "start"),
        ("Line.end", mcrfpy.Line(start=(0, 0), end=(1, 1)), "end"),
        ("Circle.center", mcrfpy.Circle(radius=3, center=(0, 0)), "center"),
        ("Arc.center", mcrfpy.Arc(center=(0, 0), radius=3), "center"),
        ("Frame.pos", mcrfpy.Frame(pos=(0, 0), size=(5, 5)), "pos"),
        ("Sprite.pos", mcrfpy.Sprite(pos=(0, 0)), "pos"),
        ("GridView.center", mcrfpy.Grid(grid_size=(4, 4)), "center"),
    ]
    ent_grid = mcrfpy.Grid(grid_size=(8, 8))
    e = mcrfpy.Entity(grid_pos=(1, 1)); ent_grid.entities.append(e)
    cases += [("Entity.cell_pos", e, "cell_pos"), ("Entity.draw_pos", e, "draw_pos"),
              ("Entity.sprite_offset", e, "sprite_offset")]
    for label, obj, attr in cases:
        v = mcrfpy.Vector(1, 2)
        before = sys.getrefcount(v)
        for _ in range(N):
            setattr(obj, attr, v)
        check(sys.getrefcount(v) - before == 0,
              f"{label} = Vector: refcount +{sys.getrefcount(v) - before} over {N} sets")
    for ctor_label, ctor in [("Line(start=v)", lambda v: mcrfpy.Line(start=v, end=(1, 1))),
                             ("Circle(center=v)", lambda v: mcrfpy.Circle(radius=2, center=v)),
                             ("Arc(center=v)", lambda v: mcrfpy.Arc(center=v, radius=2))]:
        v = mcrfpy.Vector(1, 2)
        before = sys.getrefcount(v)
        for _ in range(N):
            ctor(v)
        check(sys.getrefcount(v) - before == 0,
              f"{ctor_label}: refcount +{sys.getrefcount(v) - before} over {N} constructions")


def blocks_after(fn, n):
    gc.collect()
    before = sys.getallocatedblocks()
    for _ in range(n):
        fn()
    gc.collect()
    return sys.getallocatedblocks() - before


def leak_per_call(fn, n):
    """Allocated blocks retained per extra call, from the slope between n and 4n calls.
    Free-list and cache noise is roughly constant; a leak (at least one block per
    leaked object) grows with the call count."""
    fn()  # warm caches / lazy allocations
    return (blocks_after(fn, 4 * n) - blocks_after(fn, n)) / (3 * n)


def borrowed_sinks():
    print("dict builders release their values (#413)")
    buf = mcrfpy.SoundBuffer.sfxr("coin")
    for label, fn, n in [
        ("get_metrics()", lambda: mcrfpy.get_metrics(), 2000),
        ("SoundBuffer.sfxr_params", lambda: buf.sfxr_params, 2000),
    ]:
        # The automation click/drag helpers had the same leak (fixed in the same change), but
        # each click sleeps 10 ms, too slow to sample here; tools/lint_bindings.py's
        # borrowed-leak rule guards those sites instead.
        per_call = leak_per_call(fn, n)
        check(per_call < 0.25, f"{label}: {per_call:.3f} blocks retained per call")


def timer_fires():
    print("a firing timer does not leak references to itself")
    fired = []
    t = mcrfpy.Timer("leakcheck", lambda timer, rt: fired.append(rt), 10)
    mcrfpy.step(0.02)
    before = sys.getrefcount(t)
    for _ in range(50):
        mcrfpy.step(0.02)
    grown = sys.getrefcount(t) - before  # measured while running: stop() drops a ref (#251)
    t.stop()
    check(len(fired) > 40, f"timer fired ({len(fired)} times)")
    check(grown == 0, f"timer refcount +{grown} over {len(fired)} fires")


def main():
    vector_setters()
    borrowed_sinks()
    timer_fires()
    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
