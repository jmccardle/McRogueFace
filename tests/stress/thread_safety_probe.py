"""Thread-safety probe: background threads mutate engine objects, with or
without mcrfpy.lock(), while the main thread runs frames.

Not part of run_tests.py -- driven by tests/stress/run_thread_matrix.py across
builds (release / pydebug / free-threaded / TSan, GIL on or off). Configured by
environment (an --exec script gets no argv):

  MCRF_TS_SCENARIO  ui | entity | step | anim | timer | cells        (broad churn)
                    hover | click | stepcb | animlist               (targeted: C++
                    paths that call Python while holding raw pointers/iterators)
  MCRF_TS_MODE      nolock | lock      (lock = control arm: every mutation in mcrfpy.lock())
  MCRF_TS_SECONDS   wall time to run (default 3)
  MCRF_TS_THREADS   background mutator threads (default 4)
  MCRF_TS_RENDER    1 = windowed main loop (renders each frame; needs a display)
                    0 = headless, main thread drives mcrfpy.step()

Prints one line `RESULT {json}` and exits 0. Crashes, hangs and sanitizer
reports are for the driver to observe; this script reports Python-visible
damage: unexpected exceptions and broken collection invariants.
"""
import json
import os
import random
import sys
import threading
import time

import mcrfpy
from mcrfpy import automation

SCENARIO = os.environ.get("MCRF_TS_SCENARIO", "ui")
MODE = os.environ.get("MCRF_TS_MODE", "nolock")
SECONDS = float(os.environ.get("MCRF_TS_SECONDS", "3"))
THREADS = int(os.environ.get("MCRF_TS_THREADS", "4"))
RENDER = os.environ.get("MCRF_TS_RENDER", "0") == "1"

# Maximise GIL hand-offs so interleavings that need a thread switch at an
# unlucky moment actually happen within a few seconds.
sys.setswitchinterval(1e-6)

# Exceptions that are *correct* outcomes of racing on a shared collection
# (e.g. two threads removing the same child): the second remove() raising
# ValueError is ordinary Python semantics, not engine damage.
BENIGN = {"ValueError", "IndexError", "KeyError"}
# The engine's own concurrent-modification guard (like dict's): iteration
# raising instead of reading freed memory is the *defended* outcome.
DETECTED = ("changed size during iteration",)

stats = {"ops": 0, "main_frames": 0, "exc": {}, "benign": {}, "detected": 0, "invariant": []}
stats_lock = threading.Lock()
stop = threading.Event()


def note_exc(e):
    name = type(e).__name__
    if isinstance(e, RuntimeError) and any(d in str(e) for d in DETECTED):
        with stats_lock:
            stats["detected"] += 1
        return
    bucket = "benign" if name in BENIGN else "exc"
    with stats_lock:
        d = stats[bucket]
        key = f"{name}: {str(e)[:80]}" if bucket == "exc" else name
        d[key] = d.get(key, 0) + 1


class _NoLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def guard():
    return mcrfpy.lock() if MODE == "lock" else _NoLock()


# --------------------------------------------------------------------------
# World
scene = mcrfpy.Scene("ts_probe")
root = mcrfpy.Frame(pos=(0, 0), size=(800, 600))
scene.children.append(root)
grid = mcrfpy.Grid(grid_size=(40, 30), pos=(0, 0), size=(640, 480))
scene.children.append(grid)
mcrfpy.current_scene = scene

for x in range(40):
    for y in range(30):
        c = grid.at(x, y)
        c.walkable = c.transparent = (x % 7 != 3 or y % 5 == 0)


def burn(n=200):
    # Pure bytecode, so the eval loop can hand the GIL to another thread
    # while C++ is mid-operation beneath this callback.
    s = 0
    for i in range(n):
        s += i
    return s


def new_entity():
    e = mcrfpy.Entity((random.randrange(40), random.randrange(30)))
    if SCENARIO == "step":
        e.turn_order = 1
        e.set_behavior(int(mcrfpy.Behavior.PATH))
        e.step = lambda trigger, data: burn()
    return e


for _ in range(20):
    grid.entities.append(new_entity())


def hot_frame(rng):
    """A small frame whose mouse callbacks run Python (GIL hand-off points)."""
    f = mcrfpy.Frame(pos=(rng.randrange(0, 780, 20), rng.randrange(0, 580, 20)), size=(20, 20))
    f.on_enter = lambda pos: burn()
    f.on_exit = lambda pos: burn()
    f.on_move = lambda pos: burn()
    f.on_click = lambda pos, button, action: burn()
    f.children.append(mcrfpy.Frame(pos=(2, 2), size=(8, 8)))
    return f


if SCENARIO in ("hover", "click"):
    grid.visible = False
    _r = random.Random(99)
    for _ in range(150):
        root.children.append(hot_frame(_r))
if SCENARIO == "animlist":
    def _anim_done(target, prop, value):
        burn()


# --------------------------------------------------------------------------
# Background mutations, one random op per iteration
def op_ui(rng):
    k = rng.random()
    if k < 0.35:
        f = mcrfpy.Frame(pos=(rng.randrange(700), rng.randrange(500)), size=(30, 30))
        f.children.append(mcrfpy.Caption(text="x", pos=(2, 2)))
        root.children.append(f)
    elif k < 0.65:
        n = len(root.children)
        if n:
            root.children.remove(root.children[rng.randrange(n)])
    elif k < 0.9:
        n = len(root.children)
        if n:
            ch = root.children[rng.randrange(n)]
            ch.x = rng.randrange(700)
            ch.y = rng.randrange(500)
    else:
        while len(root.children) > 100:
            root.children.pop()


def op_entity(rng):
    k = rng.random()
    if k < 0.35:
        grid.entities.append(new_entity())
    elif k < 0.65:
        n = len(grid.entities)
        if n:
            grid.entities.remove(grid.entities[rng.randrange(n)])
    else:
        n = len(grid.entities)
        if n:
            grid.entities[rng.randrange(n)].grid_pos = (rng.randrange(40), rng.randrange(30))


def op_anim(rng):
    f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    root.children.append(f)
    f.animate("x", float(rng.randrange(700)), 0.05, mcrfpy.Easing.LINEAR)
    if rng.random() < 0.7 and len(root.children):
        root.children.remove(f)


timers = []


def op_timer(rng):
    if rng.random() < 0.5 or not timers:
        t = mcrfpy.Timer(f"ts{rng.random()}", lambda *a: burn(50), rng.choice((1, 5, 16)))
        timers.append(t)
    else:
        t = timers.pop(rng.randrange(len(timers)))
        t.stop()


def op_cells(rng):
    c = grid.at(rng.randrange(40), rng.randrange(30))
    c.walkable = c.transparent = rng.random() < 0.7


def op_hotframes(rng):
    k = rng.random()
    n = len(root.children)
    if k < 0.3:
        root.children.append(hot_frame(rng))
    elif k < 0.6 and n:
        root.children.remove(root.children[rng.randrange(n)])
    elif n:
        f = root.children[rng.randrange(n)]
        # swap callbacks: frees the old callable objects
        if rng.random() < 0.5:
            f.on_click = None if rng.random() < 0.5 else (lambda pos, button, action: burn())
        else:
            f.on_enter = None if rng.random() < 0.5 else (lambda pos: burn())
            f.on_move = None if rng.random() < 0.5 else (lambda pos: burn())


def op_stepcb(rng):
    n = len(grid.entities)
    if n:
        # a fresh callable each time, so the previous one's refcount hits zero
        grid.entities[rng.randrange(n)].step = (lambda trigger, data: burn())


def op_animlist(rng):
    for a in mcrfpy.animations:
        _ = (a.property, a.duration, a.elapsed, a.is_complete)


OPS = {"ui": op_ui, "entity": op_entity, "step": op_entity, "anim": op_anim,
       "timer": op_timer, "cells": op_cells, "hover": op_hotframes,
       "click": op_hotframes, "stepcb": op_stepcb, "animlist": op_animlist}


def worker(seed):
    rng = random.Random(seed)
    op = OPS[SCENARIO]
    while not stop.is_set():
        try:
            with guard():
                op(rng)
            with stats_lock:
                stats["ops"] += 1
        except Exception as e:  # noqa: BLE001 -- classify everything
            note_exc(e)
        if MODE == "lock":
            time.sleep(0)  # one bounded unit per acquire (docs/frame-lock.md, #410)


# --------------------------------------------------------------------------
# Main-thread work per frame
def main_work():
    stats["main_frames"] += 1
    try:
        if SCENARIO in ("step", "stepcb"):
            grid.step(1)
        elif SCENARIO == "hover":
            for _ in range(20):
                automation.moveTo((random.randrange(800), random.randrange(600)))
        elif SCENARIO == "click":
            for _ in range(10):
                automation.click((random.randrange(800), random.randrange(600)))
        elif SCENARIO == "animlist":
            for _ in range(10):
                f = mcrfpy.Frame(pos=(0, 0), size=(4, 4))
                root.children.append(f)
                f.animate("x", 50.0, 0.016, mcrfpy.Easing.LINEAR, callback=_anim_done)
            while len(root.children) > 50:
                root.children.pop()
        elif SCENARIO == "cells":
            grid.compute_fov((20, 15), radius=10)
            grid.find_path((1, 1), (38, 28))
        elif SCENARIO in ("ui", "anim"):
            # Python-side traversal of what the background threads mutate
            for ch in root.children:
                _ = ch.x
        elif SCENARIO == "entity":
            for e in grid.entities:
                _ = e.grid_pos
    except Exception as e:  # noqa: BLE001
        note_exc(e)


def check_invariants():
    def coll(name, c):
        n = len(c)
        seen = list(c)
        if len(seen) != n:
            stats["invariant"].append(f"{name}: len {n} but iterated {len(seen)}")
        if len({id(x) for x in seen}) != len(seen):
            stats["invariant"].append(f"{name}: duplicate members")
        return seen

    kids = coll("root.children", root.children)
    for ch in kids:
        if ch.parent is not root:
            stats["invariant"].append("root.children member with wrong parent")
            break
    ents = coll("grid.entities", grid.entities)
    for e in ents:
        if e.grid is None:
            stats["invariant"].append("grid.entities member with grid=None")
            break


def finish():
    # Threads parked in mcrfpy.lock() only get in when a frame opens the
    # window, so joining from the main thread without advancing frames would
    # deadlock against the barrier (docs/frame-lock.md, #398). The render path
    # drains in tick(); headless drains here by stepping.
    stop.set()
    if not RENDER:
        grace = time.monotonic() + 10
        while any(t.is_alive() for t in threads) and time.monotonic() < grace:
            mcrfpy.step(0.016)
    for t in threads:
        t.join(timeout=0.1)
    alive = [t.name for t in threads if t.is_alive()]
    if alive:
        stats["invariant"].append(f"threads still alive at exit: {alive}")
    check_invariants()
    stats.update(scenario=SCENARIO, mode=MODE, render=RENDER, threads=THREADS,
                 gil=getattr(sys, "_is_gil_enabled", lambda: True)(),
                 python=sys.version.split()[0] + sys.abiflags)
    print("RESULT " + json.dumps(stats, sort_keys=True), flush=True)
    sys.exit(0)


threads = [threading.Thread(target=worker, args=(i,), name=f"mutator{i}", daemon=True)
           for i in range(THREADS)]
for t in threads:
    t.start()

deadline = time.monotonic() + SECONDS
if RENDER:
    def tick(timer, runtime):
        now = time.monotonic()
        if now < deadline:
            main_work()
            return
        stop.set()  # let mutators drain; frames keep opening the lock window
        if any(t.is_alive() for t in threads) and now < deadline + 10:
            return
        timer.stop()
        finish()
    mcrfpy.Timer("ts_tick", tick, 16)
else:
    while time.monotonic() < deadline:
        main_work()
        mcrfpy.step(0.016)
    finish()
