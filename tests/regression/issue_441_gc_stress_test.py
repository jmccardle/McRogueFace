#!/usr/bin/env python3
"""
Randomized GC-ownership stress for #441.

Builds random object graphs that mix every ownership shape the cycle collector has to
get right: nested children, grids and their entities, subclasses (pinned) and plain
wrappers, collection wrappers sharing a children vector, a view's cached GridData
wrapper, registered and unregistered scenes, and callbacks and attributes that capture
arbitrary other objects. A random subset is kept; the rest is dropped and collected.

After every collection, everything still reachable from what was kept must be intact:
each callback still has its closure, and each subclass still has its attributes. On a
debug CPython the collector also aborts if any wrapper reports a reference it doesn't
own ("refcount is too small"), so this doubles as the over-reporting check.
"""
import gc
import random
import sys

import mcrfpy

ROUNDS = 40
SEED = 441


class SubFrame(mcrfpy.Frame):
    pass


class SubCaption(mcrfpy.Caption):
    pass


class Orc(mcrfpy.Entity):
    pass


problems = []


def problem(msg):
    problems.append(msg)
    print("FAIL: " + msg)


# Every object gets a unique .name, so a callback that was set can be checked even
# after its (plain) wrapper died and was re-created: name -> attributes that were set.
EXPECT = {}
_serial = [0]


def named(o):
    _serial[0] += 1
    o.name = f"n{_serial[0]}"
    return o


def expect(o, attr, fn):
    setattr(o, attr, fn)
    EXPECT.setdefault(o.name, set()).add(attr)


def verify(o, where, seen):
    if id(o) in seen:
        return
    seen.add(id(o))
    for attr in EXPECT.get(getattr(o, "name", None), ()):
        cb = getattr(o, attr, None)
        if cb is None:
            problem(f"{where}: {type(o).__name__}.{attr} was dropped")
        elif cb.__closure__ is None or cb.__qualname__ == "":
            problem(f"{where}: {type(o).__name__}.{attr} was cleared")
    if isinstance(o, (SubFrame, SubCaption, Orc)) and not hasattr(o, "tag"):
        problem(f"{where}: {type(o).__name__} lost its attributes")
    kids = []
    if isinstance(o, (mcrfpy.Frame, mcrfpy.Grid, mcrfpy.Scene)):
        kids += list(o.children)
    if isinstance(o, (mcrfpy.Grid, mcrfpy.GridData)):
        kids += list(o.entities)
    for k in kids:
        verify(k, where, seen)


def build(rng, n):
    """Return a list of freshly built, interlinked objects."""
    pool = []
    for i in range(n):
        kind = rng.randrange(7)
        if kind == 0:
            o = SubFrame(); o.tag = i
        elif kind == 1:
            o = mcrfpy.Frame()
        elif kind == 2:
            o = SubCaption(text="c"); o.tag = i
        elif kind == 3:
            o = mcrfpy.Grid(grid_size=(4, 4))
        elif kind == 4:
            o = mcrfpy.GridData(grid_size=(4, 4))
        elif kind == 5:
            o = Orc(grid_pos=(1, 1)); o.tag = i
        else:
            o = mcrfpy.Entity(grid_pos=(1, 1))
        if not isinstance(o, mcrfpy.GridData):
            named(o)
        pool.append(o)

    grids = [o for o in pool if isinstance(o, (mcrfpy.Grid, mcrfpy.GridData))]
    for i, o in enumerate(pool):
        if isinstance(o, mcrfpy.Entity):
            if grids and rng.random() < 0.8:
                rng.choice(grids).entities.append(o)
        elif not isinstance(o, mcrfpy.GridData) and rng.random() < 0.7:
            # Parents always come earlier in the pool, so the hierarchy has no loops
            # (appending an ancestor is #442, a separate crash).
            earlier = [p for p in pool[:i] if isinstance(p, (mcrfpy.Frame, mcrfpy.Grid))]
            if earlier:
                rng.choice(earlier).children.append(o)

    for o in pool:
        # Self-capture is the shape that crashed (#441 A), so make it common.
        target = o if rng.random() < 0.4 else rng.choice(pool)
        roll = rng.random()
        if roll < 0.6:
            if isinstance(o, mcrfpy.Entity):
                expect(o, "step", (lambda t: (lambda a, b: t))(target))
            elif not isinstance(o, mcrfpy.GridData):
                expect(o, "on_click", (lambda t: (lambda p, b, a: t))(target))
        elif roll < 0.8 and isinstance(o, (SubFrame, SubCaption, Orc)):
            o.link = target
        if isinstance(o, mcrfpy.Grid) and rng.random() < 0.5:
            o.grid_data            # populate the view's cached wrapper (#348)
        if isinstance(o, mcrfpy.Grid) and rng.random() < 0.3:
            expect(o, "on_cell_click", (lambda t: (lambda c, b, a: t))(target))
    return pool


def main():
    rng = random.Random(SEED)
    host = mcrfpy.Scene("i441_stress")
    mcrfpy.current_scene = host
    kept = []
    for rnd in range(ROUNDS):
        pool = build(rng, rng.randrange(4, 14))
        # Some go on the live scene, some into a throwaway scene that is unregistered.
        throwaway = mcrfpy.Scene(f"i441_tmp_{rnd}")
        for o in pool:
            r = rng.random()
            if isinstance(o, (mcrfpy.Entity, mcrfpy.GridData)):
                continue
            try:
                if r < 0.25:
                    host.children.append(o)
                elif r < 0.4:
                    throwaway.children.append(o)
            except Exception:
                pass
        if rng.random() < 0.5:
            throwaway.on_key = (lambda t: (lambda k, a: t))(rng.choice(pool))
        if rng.random() < 0.5:
            throwaway.unregister()
        # Keep a random subset, sometimes through a collection wrapper only.
        for o in pool:
            r = rng.random()
            if r < 0.2:
                kept.append(o)
            elif r < 0.3 and isinstance(o, (mcrfpy.Frame, mcrfpy.Grid)):
                kept.append(o.children)
            elif r < 0.35 and isinstance(o, (mcrfpy.Grid, mcrfpy.GridData)):
                kept.append(o.entities)
        del pool, throwaway, o
        gc.collect()
        seen = set()
        verify(host, f"round {rnd} scene", seen)
        for k in kept:
            if isinstance(k, (mcrfpy.Drawable, mcrfpy.Entity, mcrfpy.GridData)):
                verify(k, f"round {rnd} kept", seen)
            else:
                for item in list(k):
                    verify(item, f"round {rnd} kept-collection", seen)
        if len(kept) > 30:
            del kept[: len(kept) // 2]
        if problems:
            break

    kept.clear()
    while len(host.children):
        host.children.pop()
    gc.collect()
    if problems:
        print(f"FAIL: {len(problems)} problem(s)")
        sys.exit(1)
    print(f"PASS ({ROUNDS} rounds)")
    sys.exit(0)


if __name__ == "__main__":
    main()
