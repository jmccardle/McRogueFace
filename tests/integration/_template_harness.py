"""Chained as a second --exec after a template's game.py (see template_programs_test.py).

Steps the template's scene for a while, then replays keypresses through its
on_key handler. Any exception -- at import, in a step, in a handler -- is a
failure: an uncaught one prints a Traceback, which the driver also scans for.
"""
import sys
import traceback

import mcrfpy

FRAMES = 60


def fail(msg):
    print(f"TEMPLATE_FAIL: {msg}")
    sys.exit(1)


scene = mcrfpy.current_scene
if scene is None:
    fail("template left no active scene")
if len(scene.children) == 0:
    fail(f"scene {scene.name!r} has no children")

try:
    for _ in range(FRAMES):
        mcrfpy.step(0.016)
    handler = scene.on_key
    if handler is not None:
        for key in (mcrfpy.Key.RIGHT, mcrfpy.Key.DOWN, mcrfpy.Key.LEFT,
                    mcrfpy.Key.UP, mcrfpy.Key.SPACE):
            handler(key, mcrfpy.InputState.PRESSED)
            for _ in range(5):
                mcrfpy.step(0.016)
except Exception as exc:  # noqa: BLE001
    traceback.print_exc()
    fail(f"{type(exc).__name__}: {exc}")

print(f"TEMPLATE_OK: scene={scene.name!r} children={len(scene.children)}")
sys.exit(0)
