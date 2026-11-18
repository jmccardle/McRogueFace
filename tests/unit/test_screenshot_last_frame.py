#!/usr/bin/env python3
"""
automation.screenshot() captures the last complete frame (#529, was #153)
=========================================================================

Headless rules, asserted on pixels:
- No frame has been rendered yet: the first screenshot renders one, so a scene built and
  shot at once shows the scene.
- Otherwise a screenshot is the last complete frame, never a fresh render of changes made
  since: a second screenshot after a mutation, with no frame in between, is the same image.
- Headless step() draws nothing; a screenshot after a step() that finished since the last
  render draws the scene as it is at the time of the shot.
"""

import os
import sys
import tempfile

import mcrfpy
from mcrfpy import automation

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "regression"))
import _png  # noqa: E402

RED, GREEN = (255, 0, 0), (0, 255, 0)
TMP = tempfile.mkdtemp(prefix="mcrf_lastframe_")
_n = [0]


def shot():
    """Screenshot to a file; return (pixel inside the frame, file bytes)."""
    path = os.path.join(TMP, "s%d.png" % _n[0])
    _n[0] += 1
    assert automation.screenshot(path) is True, "screenshot() should return True"
    w, h, ch, px = _png.read_png(path, 151, 151)  # only pixel (150, 150) is read (exact crop)
    i = (150 * w + 150) * ch
    with open(path, "rb") as f:
        return tuple(px[i:i + 3]), f.read()


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        sys.exit(1)


scene = mcrfpy.Scene("last_frame")
scene.activate()
frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200), fill_color=mcrfpy.Color(255, 0, 0))
scene.children.append(frame)

print("Test 1: the first screenshot renders the first frame")
p1, b1 = shot()
check(p1 == RED, "scene built and shot at once shows the red frame: %r" % (p1,))

print("Test 2: a mutation with no frame in between is not in the next screenshot")
frame.fill_color = mcrfpy.Color(0, 255, 0)
p2, b2 = shot()
check(p2 == RED and b2 == b1, "second shot is the first image again: %r" % (p2,))
p2b, b2b = shot()
check(b2b == b1, "and so is a third")

print("Test 3: after step() the screenshot shows the mutation")
mcrfpy.step(0.1)
p3, b3 = shot()
check(p3 == GREEN, "shot after step() draws the scene as it is now: %r" % (p3,))

print("Test 4: each mutation needs a step to show")
seen = []
for i in range(3):
    frame.fill_color = mcrfpy.Color(40 + i * 80, 0, 0)
    mcrfpy.step(0.016)
    seen.append(shot()[0])
check(seen == [(40, 0, 0), (120, 0, 0), (200, 0, 0)], "three steps, three states: %r" % (seen,))

print("PASS")
sys.exit(0)
