"""Scenario driver for issue_529_first_frame_screenshot_test.py (underscore: not a test).

Run by the engine, headless or windowed, with env CASE_529 and OUT_529 (a directory).
Prints one line, "RESULT <repr of a dict>", then exits 0. Colours: RED, then GREEN
after a mutation. The probe pixel is inside the Frame; the file bytes are compared whole.
"""
import os
import sys

import mcrfpy
from mcrfpy import automation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _png  # noqa: E402

CASE = os.environ["CASE_529"]
OUT = os.environ["OUT_529"]
HEADLESS = mcrfpy.config.headless
RED, GREEN = (255, 0, 0), (0, 255, 0)
_n = [0]


def shot():
    """Take a screenshot; return (probe pixel, file bytes)."""
    path = os.path.join(OUT, "%s_%d.png" % (CASE, _n[0]))
    _n[0] += 1
    assert automation.screenshot(path) is True
    w, h, ch, px = _png.read_png(path)
    i = (100 * w + 100) * ch
    with open(path, "rb") as f:
        return tuple(px[i:i + 3]), f.read()


scene = mcrfpy.Scene("s529")
frame = mcrfpy.Frame(pos=(50, 50), size=(200, 200), fill_color=mcrfpy.Color(255, 0, 0))
scene.children.append(frame)
scene.activate()


def finish(**kv):
    print("RESULT " + repr(kv))
    sys.stdout.flush()
    sys.exit(0)


def green():
    frame.fill_color = mcrfpy.Color(0, 255, 0)


if CASE == "first":
    # (a) all setup, then an immediate screenshot: the first frame is rendered for it.
    px, _ = shot()
    finish(px=px)

elif CASE == "twice":
    # (b) a mutation and no frame in between: the second shot is the first one again.
    p1, b1 = shot()
    green()
    p2, b2 = shot()
    finish(p1=p1, p2=p2, same=(b1 == b2))

elif CASE == "frame":
    # (c) after a frame the screenshot shows the mutation. Headless: step() is the frame.
    # Windowed: step() is a no-op, so a timer mutates and a later timer takes the shot.
    p1, _ = shot()
    if HEADLESS:
        green()
        mcrfpy.step(0.016)
        p2, _ = shot()
        finish(p1=p1, p2=p2)
    else:
        def mutate(timer, rt):
            timer.stop()
            green()

        def later(timer, rt):
            timer.stop()
            p2, _ = shot()
            finish(p1=p1, p2=p2)
        mcrfpy.Timer("mutate", mutate, 50)
        mcrfpy.Timer("later", later, 400)

elif CASE == "midframe":
    # (d) a screenshot inside a timer callback is the previous complete frame, not a fresh
    # render of the state the callback just changed.
    p0, b0 = shot()

    def in_callback(timer, rt):
        timer.stop()
        green()
        p1, b1 = shot()
        # Both modes: the callback is inside a frame; the picture has not changed.
        results["in_cb"] = (p1, b1 == b0)

    results = {}
    mcrfpy.Timer("cb", in_callback, 50)
    if HEADLESS:
        mcrfpy.step(0.1)
        p2, _ = shot()          # outside the frame: the finished step is drawn
        finish(p0=p0, in_cb=results["in_cb"][0], in_cb_same=results["in_cb"][1], after=p2)
    else:
        def after_timer(timer, rt):
            timer.stop()
            p2, _ = shot()      # a frame has run since the mutation
            finish(p0=p0, in_cb=results["in_cb"][0], in_cb_same=results["in_cb"][1], after=p2)
        mcrfpy.Timer("after", after_timer, 400)

else:
    raise AssertionError("unknown case " + CASE)
