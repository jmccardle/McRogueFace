"""Scenario driver for issue_529_first_frame_screenshot_test.py (underscore: not a test).

Run by the engine, headless or windowed, with env CASE_529 and OUT_529 (a directory).
Prints one line, "RESULT <repr of a dict>", then exits 0. Colours: RED, then GREEN after a
mutation. The probe pixel is inside the Frame; the file bytes are compared whole.

Windowed there is no step(): frames are counted (mcrfpy.get_metrics()["current_frame"]),
never timed, so a stalled machine cannot put two actions in one frame.
"""
import os
import sys
import warnings

import mcrfpy
from mcrfpy import automation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _png  # noqa: E402

CASE = os.environ["CASE_529"]
OUT = os.environ["OUT_529"]
HEADLESS = mcrfpy.config.headless
RED, GREEN = (255, 0, 0), (0, 255, 0)
_n = [0]


def shot(via="automation"):
    """Take a screenshot; return (probe pixel, file bytes)."""
    path = os.path.join(OUT, "%s_%d.png" % (CASE, _n[0]))
    _n[0] += 1
    if via == "window":
        assert mcrfpy.Window.get().screenshot(path) is None
    else:
        assert automation.screenshot(path) is True
    w, h, ch, px = _png.read_png(path)
    i = (100 * w + 100) * ch
    with open(path, "rb") as f:
        return tuple(px[i:i + 3]), f.read()


def current_frame():
    return mcrfpy.get_metrics()["current_frame"]


def after_frames(n, fn, name):
    """Windowed: call fn() from a timer callback once n more frames have completed."""
    start = current_frame()

    def tick(timer, rt):
        if current_frame() >= start + n:
            timer.stop()
            fn()
    return mcrfpy.Timer(name, tick, 1)


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


def in_a_frame(fn, name="cb"):
    """Run fn() inside a frame (a timer callback). Headless that is inside a step();
    windowed it is a later frame of the real loop. Never stops the timer before fn
    returns (stopping then stepping from a callback is a separate engine bug)."""
    entered = []

    def cb(timer, rt):
        if entered:
            return          # a nested step() re-tested this timer: not due again, but be sure
        entered.append(1)
        fn()
        timer.stop()
    if HEADLESS:
        mcrfpy.Timer(name, cb, 50)
        mcrfpy.step(0.1)
    else:
        start = current_frame()

        def gate(timer, rt):
            if current_frame() >= start + 2:
                timer.stop()
                cb(timer, rt)
        mcrfpy.Timer(name, gate, 1)


def after_that(fn):
    """Run fn() once a frame has completed since the caller's callback. Headless the step
    already ran, so call it now."""
    if HEADLESS:
        fn()
    else:
        after_frames(3, fn, "after")


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
    # (c) after a frame the screenshot shows the mutation.
    p1, _ = shot()
    if HEADLESS:
        green()
        mcrfpy.step(0.016)
        p2, _ = shot()
        finish(p1=p1, p2=p2)
    else:
        def later():
            p2, _ = shot()
            finish(p1=p1, p2=p2)
        after_frames(3, lambda: (green(), after_frames(3, later, "later")), "mutate")

elif CASE == "midframe":
    # (d) a screenshot inside a timer callback is the previous complete frame, not a fresh
    # render of the state the callback just changed.
    p0, b0 = shot()
    got = {}

    def in_callback():
        green()
        p1, b1 = shot()
        got["px"], got["same"] = p1, (b1 == b0)

    in_a_frame(in_callback)

    def after():
        p2, _ = shot()      # a frame has run since the mutation (headless: the step is drawn now)
        finish(p0=p0, in_cb=got["px"], in_cb_same=got["same"], after=p2)
    after_that(after)

elif CASE == "nested":
    # A callback that runs a nested step(), mutates, then shoots is STILL inside a frame: the
    # scope guard restores in_frame, it does not clear it. (Windowed step() is a no-op.)
    p0, b0 = shot()
    got = {}

    def in_callback():
        mcrfpy.step(0)
        green()
        p1, b1 = shot()
        got["px"], got["same"] = p1, (b1 == b0)

    in_a_frame(in_callback)
    after_that(lambda: finish(p0=p0, in_cb=got["px"], in_cb_same=got["same"], after=shot()[0]))

elif CASE == "window":
    # Window.screenshot() follows the same rules as automation.screenshot().
    p1, b1 = shot("window")
    green()
    p2, b2 = shot("window")
    if HEADLESS:
        mcrfpy.step(0.016)
        p3, _ = shot("window")
        finish(p1=p1, p2=p2, same=(b1 == b2), p3=p3)
    else:
        after_frames(3, lambda: finish(p1=p1, p2=p2, same=(b1 == b2), p3=shot("window")[0]), "w")

elif CASE == "diff_i":
    # KNOWN DIFFERENCE (i). Headless step() draws nothing: its frame is drawn when a screenshot
    # asks, so step(); mutate; shot shows the mutation. Windowed, the frame was presented
    # before the mutation, so the same sequence shows the old image.
    p0, _ = shot()
    if HEADLESS:
        mcrfpy.step(0.016)
        green()
        finish(p0=p0, px=shot()[0])
    else:
        def mutate_and_shoot():
            green()
            finish(p0=p0, px=shot()[0])
        after_frames(3, mutate_and_shoot, "m")

elif CASE == "diff_ii":
    # KNOWN DIFFERENCE (ii). A first-ever screenshot taken inside a callback has no previous
    # frame to show, so it renders the current state, mid-frame. Headless: inside a step().
    # Windowed: inside the first frame, from Scene.update(), which runs before the first render.
    def first_in_callback():
        green()
        finish(px=shot()[0])
    if HEADLESS:
        mcrfpy.Timer("c", lambda t, rt: first_in_callback(), 10)
        mcrfpy.step(0.1)
    else:
        class Updating(mcrfpy.Scene):
            def update(self, dt):
                first_in_callback()
        up = Updating("updating")
        up.children.append(frame)
        up.activate()

elif CASE == "reentrant":
    # A warnings hook that takes a screenshot while the first-frame capture is rendering (a
    # grid with no texture warns at its first draw) must get a RuntimeError, not recurse.
    scene.children.append(mcrfpy.Grid(grid_size=(4, 4), pos=(300, 50), size=(64, 64)))
    inner = []

    def hook(message, category, filename, lineno, file=None, line=None):
        try:
            automation.screenshot(os.path.join(OUT, "inner.png"))
            inner.append("returned")
        except RuntimeError as e:
            inner.append("RuntimeError: %s" % e)
    warnings.showwarning = hook
    warnings.simplefilter("always")
    px, _ = shot()
    finish(px=px, inner=inner)

else:
    raise AssertionError("unknown case " + CASE)
