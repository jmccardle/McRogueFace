"""Headless smoke test for The Gauntlet trials (Gitea #340).

For every trial: setup -> set_load at two levels -> tick -> teardown, asserting
object counts move the right way and teardown fully disposes the scene. Fast and
suite-friendly (no rendering, no scoring ramp).

Run:
  ./mcrogueface --headless --exec ../tests/unit/gauntlet_trials_test.py
"""
import os
import sys

import mcrfpy

HERE = os.path.dirname(os.path.abspath(__file__))
GAUNTLET = os.path.normpath(os.path.join(HERE, "..", "benchmarks", "gauntlet"))
sys.path.insert(0, GAUNTLET)

from scoring import load_at_step  # noqa: E402
from trials import make_trials    # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("  FAIL: " + msg)
    else:
        print("  ok: " + msg)


def run_trial(trial):
    name = trial.name
    print("[%s]" % name)
    scene = mcrfpy.Scene("gt_" + trial.key)
    mcrfpy.current_scene = scene
    ui = scene.children

    trial.setup(scene, ui)

    level1 = int(trial.base_load)
    trial.set_load(level1)
    load1 = trial.load
    check(load1 > 0, "%s set_load(base=%d) -> load=%d" % (name, level1, load1))
    check(len(ui) >= 1, "%s populates scene after set_load" % name)

    # Drive a few sim ticks + engine steps (advances animations/behaviors).
    for _ in range(4):
        trial.tick(100)
        mcrfpy.step(0.016)

    level2 = load_at_step(trial.base_load, trial.growth, 3)
    trial.set_load(level2)
    load2 = trial.load
    check(load2 > load1, "%s set_load(up=%d) grows load %d -> %d"
          % (name, level2, load1, load2))

    for _ in range(4):
        trial.tick(100)
        mcrfpy.step(0.016)

    # Reduce back down; load must shrink and not error.
    trial.set_load(level1)
    check(trial.load <= load2, "%s set_load(down) shrinks load -> %d" % (name, trial.load))

    trial.teardown()
    check(len(scene.children) == 0, "%s teardown clears scene children" % name)


def main():
    for trial in make_trials():
        try:
            run_trial(trial)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            failures.append("%s raised %r" % (trial.name, ex))

    print("=" * 50)
    if failures:
        print("GAUNTLET TRIALS TEST FAILED (%d issues)" % len(failures))
        for f in failures:
            print("  - " + f)
        print("FAIL")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
