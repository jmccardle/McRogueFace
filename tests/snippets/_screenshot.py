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

Per-snippet parameters arrive by environment, set by tools/generate_snippet_shots.py,
which parses each snippet's `# mcrf:` header:

    MCRF_SHOT_OUT          output PNG path (required)
    MCRF_SHOT_SETUP_STEPS  step(0.016) calls before capture (default 3)

Phase 1 implements STATIC capture only: advance a few frames so timers/layout settle,
then screenshot. Animation target-time (`shot_at`) and scripted interaction (`action`)
are later phases; a snippet that needs them is not chained here yet.
"""

import os
import sys

import mcrfpy
from mcrfpy import automation

FAIL = "SHOT_FAIL"
OK = "SHOT_OK"


def fail(msg):
    print(f"{FAIL}: {msg}")
    sys.exit(1)


out = os.environ.get("MCRF_SHOT_OUT")
if not out:
    fail("MCRF_SHOT_OUT not set")

setup_steps = int(os.environ.get("MCRF_SHOT_SETUP_STEPS", "3"))

# The snippet built its scene at import. Advance a few frames so anything that only
# resolves under the clock -- a first timer fire that fills a caption, a layout pass,
# an animation's opening frames -- has settled before we capture. The headless
# screenshot forces its own synchronous renderScene() (Automation.cpp #153), so a pure
# static scene would capture correctly with zero steps; the steps are for the snippets
# that need the clock, and cost ~nothing.
for _ in range(setup_steps):
    try:
        mcrfpy.step(0.016)
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
