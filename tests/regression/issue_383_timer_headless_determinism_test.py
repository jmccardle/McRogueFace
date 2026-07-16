#!/usr/bin/env python3
"""
Regression test for #383: headless Timer epoch must come from simulation_time, not the
wall clock (runtime).

Before the fix, PyTimer stamped a timer's epoch from GameEngine::runtime (an sf::Clock,
wall time) while step() ticked timers against simulation_time. The two clocks are in
unrelated frames, so a timer's FIRST fire under step() depended on process-startup wall
timing -- headless replay was nondeterministic (it surfaced as rare byte-diffs in the
#381 snippet screenshots).

This test pins the deterministic contract: given a fixed sequence of step() calls, the
fire count and the exact callback runtimes are a pure function of simulation time.

Note simulation_time is a single clock that ACCUMULATES across the whole process -- it
does not reset between timers -- so expectations are tracked relative to a running clock
that mirrors the engine's `simulation_time += int(dt*1000)`.

Run: ./build/mcrogueface --headless --exec tests/regression/issue_383_..._test.py
"""

import sys

import mcrfpy


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


sim_ms = 0  # mirrors GameEngine::simulation_time


def step_ms(ms):
    """Advance the sim by an exact number of milliseconds, tracking the clock."""
    global sim_ms
    mcrfpy.step(ms / 1000.0)
    sim_ms += ms


# --- Case 1: fires land exactly on simulation-time interval boundaries ----------------
# interval 100ms, stepped 50ms at a time for 400ms -> boundaries at epoch+100..epoch+400.
epoch1 = sim_ms
fires = []
mcrfpy.Timer("case1", lambda t, rt: fires.append(rt), 100)
for _ in range(8):
    step_ms(50)
expected1 = [epoch1 + 100 * i for i in range(1, 5)]
if fires != expected1:
    fail(f"case1: expected fires at {expected1}, got {fires}")

# --- Case 2: the FIRST fire is deterministic (the exact bug #383 exposed) -------------
# A 16ms timer created before its first step has epoch = current simulation_time, so the
# very next 16ms step fires it. Ten steps -> ten fires, one interval apart. Under the old
# wall-clock epoch the first fire could slip a step depending on startup timing.
epoch2 = sim_ms
fires2 = []
mcrfpy.Timer("case2", lambda t, rt: fires2.append(rt), 16)
for _ in range(10):
    step_ms(16)
expected2 = [epoch2 + 16 * i for i in range(1, 11)]
if fires2 != expected2:
    fail(f"case2: expected first-fire-deterministic {expected2}, got {fires2}")

# --- Case 3: one-shot timer fires exactly once and stops ------------------------------
epoch3 = sim_ms
fires3 = []
mcrfpy.Timer("case3", lambda t, rt: fires3.append(rt), 50, once=True)
for _ in range(6):
    step_ms(50)  # 300ms of stepping, well past the single 50ms fire
if fires3 != [epoch3 + 50]:
    fail(f"case3: one-shot expected [{epoch3 + 50}], got {fires3}")

print("PASS: headless timer fires are deterministic on simulation_time (#383)")
sys.exit(0)
