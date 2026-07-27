#!/usr/bin/env python3
"""
Simulation clock exposure + per-interval advance (#396)
=======================================================

Covers three things the engine previously could not do from Python:

1. Read the SIMULATION clock. get_metrics()['runtime'] is WALL clock; the deterministic
   millisecond counter that headless timers actually run on was C++-only
   (GameEngine::getSimulationTime). It is now get_metrics()['simulation_time_ms'].

2. Let a span of simulated time pass with correct per-interval timer semantics.
   step(dt) runs ONE frame, and one frame tests each timer at most once -- so a single
   step(10.0) fires a 1000ms repeating timer ONCE, not ten times. advance(ms) walks the
   span deadline by deadline instead.

   ACCEPTANCE: a 1-second repeating timer fires EXACTLY 10 times across 10 seconds.

3. Rendering costs zero simulated time: a screenshot must not move the clock.

Headless only -- step()/advance() are no-ops in windowed mode.
"""

import mcrfpy
from mcrfpy import automation
import os
import sys
import tempfile

failures = []


def check(label, actual, expected):
    ok = actual == expected
    print(f"  {'ok  ' if ok else 'FAIL'} {label}: got {actual!r}, expected {expected!r}")
    if not ok:
        failures.append(f"{label}: got {actual!r}, expected {expected!r}")
    return ok


def sim_time():
    return mcrfpy.get_metrics()["simulation_time_ms"]


def frame():
    return mcrfpy.get_metrics()["current_frame"]


class FireLog:
    """A repeating timer that records the simulation time of every fire."""

    def __init__(self, name, interval):
        self.times = []
        self.timer = mcrfpy.Timer(name, self._cb, interval)

    def _cb(self, timer, runtime):
        # The runtime argument a headless timer receives IS the simulation clock.
        self.times.append(runtime)


def test_clock_is_exposed_and_is_not_wall_clock():
    print("Test 1: simulation_time_ms is exposed and is a distinct clock from runtime")
    m = mcrfpy.get_metrics()
    if "simulation_time_ms" not in m:
        failures.append("get_metrics() has no 'simulation_time_ms' key")
        print("  FAIL get_metrics() has no 'simulation_time_ms' key")
        return
    print("  ok   'simulation_time_ms' present in get_metrics()")
    check("simulation_time_ms is an int", isinstance(m["simulation_time_ms"], int), True)
    check("current_frame is an int", isinstance(m["current_frame"], int), True)

    # It must track the engine's own counter, not wall time: advancing the clock by a
    # known amount must move it by exactly that amount.
    before = sim_time()
    mcrfpy.step(0.25)
    check("step(0.25) advanced simulation_time_ms by 250ms", sim_time() - before, 250)

    # runtime must remain what it always was: wall-clock seconds, a float, untouched by us.
    check("runtime is still a float (wall clock, unchanged semantics)",
          isinstance(mcrfpy.get_metrics()["runtime"], float), True)


def test_acceptance_ten_fires_in_ten_seconds():
    print("Test 2: ACCEPTANCE -- 1s repeating timer fires exactly 10x across 10s advance")
    log = FireLog("accept_timer", 1000)
    start = sim_time()

    advanced = mcrfpy.advance(10000)

    check("advance(10000) reported 10000ms", advanced, 10000)
    check("simulation_time_ms advanced exactly 10000ms", sim_time() - start, 10000)
    check("timer fired exactly 10 times", len(log.times), 10)
    check("fires landed on each interval boundary",
          log.times, [start + 1000 * (i + 1) for i in range(10)])
    log.timer.stop()


def test_step_still_fires_once_per_frame():
    print("Test 3: step() keeps its one-frame contract (the gap advance() exists to close)")
    log = FireLog("step_timer", 1000)
    start_frame = frame()

    dt = mcrfpy.step(10.0)

    check("step(10.0) returned 10.0", dt, 10.0)
    check("step(10.0) ran exactly one frame", frame() - start_frame, 1)
    check("step(10.0) fires the 1s timer only ONCE (documented, not a regression)",
          len(log.times), 1)
    log.timer.stop()


def test_residual_is_carried_not_discarded():
    print("Test 4: residual / partial interval is carried, not discarded")
    log = FireLog("residual_timer", 1000)
    start = sim_time()

    mcrfpy.advance(10500)

    check("10 fires in 10500ms", len(log.times), 10)
    check("simulation_time_ms is exactly +10500", sim_time() - start, 10500)
    check("timer is 500ms from its next deadline", log.timer.remaining, 500)

    # The 11th fire must come 500ms later, at +11000 -- not 1000ms later. If the residual
    # had been discarded (timer re-phased to the end of the span) this would need 1000ms.
    mcrfpy.advance(500)
    check("11th fire after only 500ms more", len(log.times), 11)
    check("11th fire landed on the original phase", log.times[-1], start + 11000)
    log.timer.stop()


def test_zero_intervals_elapsed():
    print("Test 5: zero-interval-elapsed cases")
    log = FireLog("zero_timer", 1000)
    start = sim_time()
    start_frame = frame()

    # (a) A span shorter than the interval: clock moves, nothing fires.
    mcrfpy.advance(999)
    check("advance(999) moved the clock 999ms", sim_time() - start, 999)
    check("no fire before the interval elapses", len(log.times), 0)
    check("advance(999) ran exactly one frame (the residual)", frame() - start_frame, 1)

    # (b) advance(0): nothing at all. The clock does not move and no frame runs -- an
    # advance of zero simulated time is not a frame. step(0.0) remains the way to run a
    # frame without moving the clock.
    at_zero = sim_time()
    frame_at_zero = frame()
    check("advance(0) returns 0", mcrfpy.advance(0), 0)
    check("advance(0) does not move the clock", sim_time(), at_zero)
    check("advance(0) does not run a frame", frame(), frame_at_zero)
    check("advance(0) fires nothing", len(log.times), 0)

    # Exactly hitting the deadline fires exactly once (boundary, not off-by-one).
    mcrfpy.advance(1)
    check("advance to the exact deadline fires once", len(log.times), 1)
    check("fire is at the exact boundary", log.times[-1], start + 1000)
    log.timer.stop()


def test_argument_validation():
    print("Test 6: advance() argument validation (no silent unit coercion)")
    try:
        mcrfpy.advance(1.0)
        failures.append("advance(1.0) should raise TypeError (float seconds is step()'s unit)")
        print("  FAIL advance(1.0) did not raise TypeError")
    except TypeError as e:
        print(f"  ok   advance(float) raised TypeError: {e}")

    try:
        mcrfpy.advance(-1)
        failures.append("advance(-1) should raise ValueError")
        print("  FAIL advance(-1) did not raise ValueError")
    except ValueError as e:
        print(f"  ok   advance(-1) raised ValueError: {e}")


def test_render_costs_zero_simulated_time():
    print("Test 7: rendering costs zero simulated time")
    log = FireLog("render_timer", 1000)

    # Park the clock 1ms short of a deadline: if a render advanced the clock at all, or
    # ran a frame, this timer would fire.
    mcrfpy.advance(999)
    before_time = sim_time()
    before_frame = frame()
    before_fires = len(log.times)

    shot = os.path.join(tempfile.gettempdir(), "sim_clock_render_check.png")
    took = automation.screenshot(shot)
    print(f"  screenshot() returned {took!r} -> {shot}")

    check("screenshot did not move simulation_time_ms", sim_time(), before_time)
    check("screenshot did not run a simulation frame", frame(), before_frame)
    check("screenshot did not fire the pending timer", len(log.times), before_fires)

    # And the timer is still armed for its original deadline.
    mcrfpy.advance(1)
    check("timer still fires 1ms later, on its original deadline", len(log.times), before_fires + 1)
    log.timer.stop()

    if os.path.exists(shot):
        os.remove(shot)


def main():
    scene = mcrfpy.Scene("sim_clock_test")
    scene.activate()

    # Guard: these semantics are headless-only. Fail loudly rather than silently passing
    # a windowed run in which every step()/advance() is a no-op.
    probe_before = mcrfpy.get_metrics().get("simulation_time_ms")
    mcrfpy.step(0.001)
    if probe_before is None or mcrfpy.get_metrics()["simulation_time_ms"] == probe_before:
        print("FAIL: simulation clock did not advance -- not running headless?")
        sys.exit(1)

    test_clock_is_exposed_and_is_not_wall_clock()
    test_acceptance_ten_fires_in_ten_seconds()
    test_step_still_fires_once_per_frame()
    test_residual_is_carried_not_discarded()
    test_zero_intervals_elapsed()
    test_argument_validation()
    test_render_costs_zero_simulated_time()

    print()
    if failures:
        for f in failures:
            print(f"FAILURE: {f}")
        print("FAIL")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
