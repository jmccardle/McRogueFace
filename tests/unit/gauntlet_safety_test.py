"""Headless test for The Gauntlet memory safety guards.

Reproduces (without allocating anything) the failure that hard-locked the
desktop on 2026-07-11: a trial whose frame time never breaks the budget while
its allocation grows geometrically. Asserts the RampController now stops via a
memory guard instead of ramping unbounded, and never sets a load past the cap.

Also exercises the address-space cap + RSS probes in safety.py.

Run:
  ./mcrogueface --headless --exec ../tests/unit/gauntlet_safety_test.py
"""
import os
import sys

import mcrfpy  # noqa: F401 (engine interpreter; not used directly)

HERE = os.path.dirname(os.path.abspath(__file__))
GAUNTLET = os.path.normpath(os.path.join(HERE, "..", "benchmarks", "gauntlet"))
sys.path.insert(0, GAUNTLET)

import safety              # noqa: E402
from scoring import RampController, load_at_step  # noqa: E402
from trials import Trial   # noqa: E402
from trials.grid_titan import GridTitan  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("  FAIL: " + msg)
    else:
        print("  ok: " + msg)


class RunawayTrial(Trial):
    """A trial that would allocate S*S bytes and never breaks the frame budget.
    set_load() records the largest load it was ever asked to build so the test
    can prove the guard refused the fatal one BEFORE allocation."""
    key = "runaway"
    name = "RUNAWAY"
    unit = "side"
    base_load = 100
    growth = 1.5
    max_load = 5000
    CELL_BYTES = 32

    def __init__(self):
        super().__init__()
        self.peak_asked = 0

    def predict_bytes(self, load):
        return int(load) * int(load) * self.CELL_BYTES

    def set_load(self, level_value):
        # NEVER actually allocate -- just record the request.
        self.peak_asked = max(self.peak_asked, int(level_value))
        self.load = int(level_value)


def drive(ramp, always_ms=4.0, max_iters=100000):
    """Feed synthetic 'always under budget' samples until the ramp finishes."""
    ramp.start()
    now = 0.0
    it = 0
    while not ramp.done and it < max_iters:
        now += 16.0
        ramp.sample(now, {"frame_time": always_ms})
        it += 1
    return it < max_iters


def test_safety_probes():
    print("[safety.py probes]")
    check(safety.rss_mb() > 0.0, "rss_mb() positive (%.1f MB)" % safety.rss_mb())
    check(safety.vmsize_mb() > 0.0, "vmsize_mb() positive (%.1f MB)" % safety.vmsize_mb())


def test_predict_cap_bails_before_alloc():
    print("[predict_bytes guard]")
    trial = RunawayTrial()
    # 64 MB budget: predict_bytes(load) = load^2 * 32 exceeds it at load ~1448.
    ramp = RampController(trial, lambda: {"frame_time": 4.0},
                          mem_budget_mb=64, rss_ceiling_mb=0)
    finished = drive(ramp)
    check(finished, "ramp terminated (did not loop unbounded)")
    check(ramp.stop_reason in ("mem_predict", "max_load"),
          "stopped via memory guard, not budget: %r" % ramp.stop_reason)
    # The refused load must never have been handed to set_load.
    budget_bytes = 64 * 1024 * 1024
    check(trial.predict_bytes(trial.peak_asked) <= budget_bytes,
          "largest allocated load (%d -> %d B) stayed within budget (%d B)"
          % (trial.peak_asked, trial.predict_bytes(trial.peak_asked), budget_bytes))
    check(ramp.result["max_load"] > 0, "recorded a real max_load (%d)"
          % ramp.result["max_load"])


def test_absolute_max_load_cap():
    print("[max_load cap]")
    trial = RunawayTrial()
    # Huge memory budget so only the absolute max_load cap can stop it.
    ramp = RampController(trial, lambda: {"frame_time": 4.0},
                          mem_budget_mb=10 ** 9, rss_ceiling_mb=0)
    finished = drive(ramp)
    check(finished, "ramp terminated under max_load cap")
    check(ramp.stop_reason == "max_load", "stopped via max_load: %r" % ramp.stop_reason)
    check(trial.peak_asked <= trial.max_load,
          "never set a load above max_load (%d <= %d)"
          % (trial.peak_asked, trial.max_load))


def test_grid_titan_declares_guards():
    print("[GRID TITAN guards]")
    gt = GridTitan()
    check(gt.max_load is not None and gt.max_load > 0,
          "GRID TITAN declares max_load (%r)" % gt.max_load)
    # Predicted footprint at the cap must be a sane, tractable number (< 1 GB).
    pb = gt.predict_bytes(gt.max_load)
    check(pb is not None and pb < 1024 * 1024 * 1024,
          "GRID TITAN cap footprint tractable (%.0f MB at S=%d)"
          % (pb / 1024.0 / 1024.0, gt.max_load))


def main():
    test_safety_probes()
    test_predict_cap_bails_before_alloc()
    test_absolute_max_load_cap()
    test_grid_titan_declares_guards()

    print("=" * 50)
    if failures:
        print("GAUNTLET SAFETY TEST FAILED (%d issues)" % len(failures))
        for f in failures:
            print("  - " + f)
        print("FAIL")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
