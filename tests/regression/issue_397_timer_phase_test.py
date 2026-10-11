"""Regression test for #397 - a wide step re-phased every timer and dropped animations.

Timer::test stamped `last_ran = now`, and one frame tested each timer once, so
step(10.5) fired a 1000ms timer ONCE (at 10500) and moved its schedule to the end of the
step: the nine skipped intervals and the 500ms residual were thrown away, and its later
firings no longer lined up with its original cadence.

Decided behaviour: a timer catches up. One frame fires it once per elapsed interval,
each call receiving that firing's own deadline as `runtime`, and the timer keeps its
phase. advance() (#396) already landed on every deadline; step() now agrees with it
firing for firing.

The same frame also skipped animations outright when dt >= 10 s (a "sanity check"), so a
running animation never finished after a wide step. Covered here too.
"""
import io
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def sim_ms():
    return mcrfpy.get_metrics()["simulation_time_ms"]


def recorder(name, interval, **kw):
    log = []
    t = mcrfpy.Timer(name, lambda timer, rt: log.append(rt), interval, **kw)
    return t, log


scene = mcrfpy.Scene("t397")
scene.activate()

# --- step(10.5): ten firings, each on its own deadline, residual kept ---
t0 = sim_ms()
t, log = recorder("cadence", 1000)
mcrfpy.step(10.5)
check(log == [t0 + 1000 * k for k in range(1, 11)],
      "step(10.5) fires a 1000ms timer ten times, on its deadlines %r" % [x - t0 for x in log])
check(t.remaining == 500, "the 500ms residual is carried, not discarded (remaining=%r)" % t.remaining)
mcrfpy.step(0.5)
check(log[-1] == t0 + 11000 and len(log) == 11,
      "the next step lands on the original cadence (%r)" % (log[-1] - t0))
t.stop()

# --- step() and advance() now agree firing for firing ---
a0 = sim_ms()
ta, la = recorder("adv", 300)
mcrfpy.advance(2000)
ta.stop()
s0 = sim_ms()
ts, ls = recorder("stp", 300)
mcrfpy.step(2.0)
ts.stop()
check([x - a0 for x in la] == [x - s0 for x in ls] and len(ls) == 6,
      "step(2.0) and advance(2000) fire a 300ms timer identically %r" % [x - s0 for x in ls])

# --- a callback that stops the timer ends the catch-up at once ---
calls = []


def stop_on_third(timer, rt):
    calls.append(rt)
    if len(calls) == 3:
        timer.stop()


stopper = mcrfpy.Timer("stopper", stop_on_third, 100)
mcrfpy.step(1.0)
check(len(calls) == 3 and stopper.stopped, "stop() inside the callback ends catch-up (%d calls)" % len(calls))

# --- pause inside the callback likewise ---
pcalls = []


def pause_on_second(timer, rt):
    pcalls.append(rt)
    if len(pcalls) == 2:
        timer.pause()


pauser = mcrfpy.Timer("pauser", pause_on_second, 100)
mcrfpy.step(1.0)
check(len(pcalls) == 2 and pauser.paused, "pause() inside the callback ends catch-up (%d calls)" % len(pcalls))
pauser.stop()

# --- a late one-shot fires once, with its deadline, and leaves the timer map ---
o0 = sim_ms()
once, olog = recorder("once", 1000, once=True)
mcrfpy.step(5.0)
check(olog == [o0 + 1000], "a one-shot fires once after a wide step, at its deadline %r" % [x - o0 for x in olog])
check(all(tm.name != "once" for tm in mcrfpy.timers),
      "a fired one-shot leaves mcrfpy.timers headless too (was kept by the headless pass)")

# --- a raising callback ends this frame's catch-up; the owed firings still come ---
r0 = sim_ms()
rlog = []


def raises(timer, rt):
    rlog.append(rt)
    raise ValueError("expected by issue_397 test")


raiser = mcrfpy.Timer("raiser", raises, 100)
# The engine prints each callback's traceback; capture it so the suite runner (which fails
# any output containing a traceback) sees only this test's verdict.
real_stderr, sys.stderr = sys.stderr, io.StringIO()
try:
    mcrfpy.step(0.5)
    first = list(rlog)
    mcrfpy.step(0.0)
finally:
    captured, sys.stderr = sys.stderr.getvalue(), real_stderr
raiser.stop()
check([x - r0 for x in first] == [100], "a raising callback stops catch-up for this frame %r" % [x - r0 for x in first])
check([x - r0 for x in rlog] == [100, 200], "the next frame resumes the owed deadlines %r" % [x - r0 for x in rlog])
check(captured.count("expected by issue_397 test") == 2, "each raise was reported, once per frame")

# --- animations survive a wide step ---
for dt in (10.0, 60.0):
    f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    scene.children.append(f)
    f.animate("x", 100.0, 0.5)
    mcrfpy.step(dt)
    check(f.x == 100.0, "an animation completes across step(%s) (x=%r)" % (dt, f.x))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
