#!/usr/bin/env python3
"""
Screenshot harness -- chained as the LAST --exec, AFTER a documentation snippet, to
capture a rendered preview of the scene the snippet built:

    ./mcrogueface --headless \
        --exec tests/snippets/_seed.py \
        --exec tests/snippets/001_hello_frame.py \
        --exec tests/snippets/_screenshot.py

This is the screenshot-mode counterpart to _harness.py. The normal test suite chains
_harness.py (pass/fail: does the snippet run and leave a populated scene?). Screenshot
mode chains THIS instead, so the pass/fail gate stays fast and untouched by capture.

The snippet has already run (it is an earlier --exec, sharing this interpreter and
engine state), so its scene is live and inspectable here.

Per-snippet parameters arrive by environment, set by tools/generate_snippet_shots.py
from its OVERRIDES table:

    MCRF_SHOT_OUT          output PNG path (required)
    MCRF_SHOT_SETUP_STEPS  static-capture frames, step(0.016) each (default 3)
    MCRF_SHOT_AT           explicit capture time in seconds (overrides auto-derivation)
    MCRF_SHOT_FRACTION     fraction of an animation's duration to capture at (default 0.6)

CAPTURE TIME. When to grab the frame is decided in this order:
  1. MCRF_SHOT_AT set        -> step to exactly that sim time. Used for effects the
                                animation list can't see -- timer-driven pulses/flashes
                                (they're Timers, not .animate() calls) and fades whose
                                60%-of-duration frame is nearly blank.
  2. active .animate() found -> step to FRACTION * (longest active animation's duration),
                                so the capture lands mid-effect, not on the opening frame.
                                Fully automatic: the engine reports each animation's
                                duration via mcrfpy.animations (#381 Phase 2).
  3. otherwise (STATIC)      -> step MCRF_SHOT_SETUP_STEPS frames and capture.

Scripted interaction (`action`) is a later phase; a snippet needing it gets whichever of
the above applies for now.
"""

import os
import sys

import mcrfpy
from mcrfpy import automation

DT = 0.016

FAIL = "SHOT_FAIL"
OK = "SHOT_OK"


def fail(msg):
    print(f"{FAIL}: {msg}")
    sys.exit(1)


out = os.environ.get("MCRF_SHOT_OUT")
if not out:
    fail("MCRF_SHOT_OUT not set")

# Decide how many frames to advance before capturing (see the module docstring). This
# must be computed BEFORE stepping: mcrfpy.animations reports full durations only while
# elapsed is still ~0, i.e. before the clock has run.
def resolve_steps():
    at = os.environ.get("MCRF_SHOT_AT")
    if at is not None:
        return max(1, round(float(at) / DT))            # 1. explicit time
    durations = [a.duration for a in mcrfpy.animations if not a.is_complete]
    if durations:
        fraction = float(os.environ.get("MCRF_SHOT_FRACTION", "0.6"))
        return max(1, round(fraction * max(durations) / DT))  # 2. mid-animation
    return int(os.environ.get("MCRF_SHOT_SETUP_STEPS", "3"))   # 3. static

# The snippet built its scene at import. Advance the resolved number of frames so the
# capture lands where we want it -- a first timer fire that fills a caption, a layout
# pass, or mid-animation. The headless screenshot forces its own synchronous
# renderScene() (Automation.cpp #153), so a pure static scene captures correctly even
# at the 3-step floor; the steps are for whatever needs the clock.
for _ in range(resolve_steps()):
    try:
        mcrfpy.step(DT)
    except Exception as exc:  # noqa: BLE001 -- a raise under the clock is a real failure
        import traceback
        traceback.print_exc()
        fail(f"step() raised {type(exc).__name__}: {exc}")

scene = mcrfpy.current_scene
if scene is None:
    fail("snippet left no active scene (mcrfpy.current_scene is None)")
if len(scene.children) == 0:
    fail(f"snippet activated scene {scene.name!r} but added nothing to it")

if automation.screenshot(out) is not True:
    fail(f"screenshot({out!r}) returned falsy -- capture failed")

print(f"{OK}: {out} scene={scene.name!r} children={len(scene.children)}")
sys.exit(0)
