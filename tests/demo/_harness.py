#!/usr/bin/env python3
"""
Standalone-demo harness (#374) -- chained as a SECOND --exec after a demo in
tests/demo/standalone/, exactly as tests/snippets/_harness.py is for snippets:

    ./mcrogueface --headless --exec tests/demo/standalone/foo_demo.py --exec tests/demo/_harness.py

The standalone demos are interactive showcases: they build a scene, bind keys, and
wait for ESC. Headless, nothing ever ends them (#350), so this supplies the ending.

A demo PASSES if it ran without raising AND, after a few frames, it left an active
scene with content that renders to a real PNG. A demo that exits by itself (some
call sys.exit(0) after capturing their own shots) never reaches this file; that is
fine, its own exit status is the verdict.
"""
import os
import sys

import mcrfpy
from mcrfpy import automation


def fail(msg):
    print(f"DEMO_FAIL: {msg}")
    sys.exit(1)


for _ in range(3):
    try:
        mcrfpy.step(0.016)
    except Exception as exc:  # noqa: BLE001 -- any raise is a real failure
        import traceback
        traceback.print_exc()
        fail(f"step() raised {type(exc).__name__}: {exc}")

scene = mcrfpy.current_scene
if scene is None:
    fail("demo left no active scene")
if len(scene.children) == 0:
    fail(f"demo activated scene {scene.name!r} but added nothing to it")

out_dir = os.environ.get("MCRF_DEMO_SCREENSHOT_DIR", ".")
os.makedirs(out_dir, exist_ok=True)
path = os.path.join(out_dir, f"standalone_{scene.name}.png")
if os.path.exists(path):
    os.unlink(path)
automation.screenshot(path)
# A blank 1024x768 PNG compresses to a few hundred bytes; real content is far larger.
if not os.path.exists(path) or os.path.getsize(path) < 2000:
    fail(f"screenshot {path} missing or blank")

print(f"DEMO_OK: scene={scene.name!r} children={len(scene.children)}")
sys.exit(0)
