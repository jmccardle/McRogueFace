"""#529 -- what automation.screenshot() shows.

The rule, headless and windowed alike:
  * If no frame has been rendered in this process, a screenshot renders the first one (so a
    script that builds a scene and immediately takes a screenshot gets the scene, not a
    blank buffer).
  * Otherwise it is the last complete frame, never a mid-frame render: a second shot after
    changing objects, with no frame in between, is byte-identical to the first, and a shot
    inside a Timer callback is the previous frame.
  * Headless only: step() draws nothing (it must work with no display), so a step() that
    finished since the last render is drawn when the next screenshot, outside a frame, asks.

Each scenario runs in a child engine, once headless and once windowed (the suite runs under
xvfb-run, so a display exists), driven by _issue_529_child.py. Windowed actions are
sequenced by counted frames, never by wall-clock durations.
"""
import ast
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHILD = os.path.join(HERE, "_issue_529_child.py")
RED, GREEN = (255, 0, 0), (0, 255, 0)
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def run(case, windowed):
    out_dir = tempfile.mkdtemp(prefix="mcrf529_")
    env = dict(os.environ, CASE_529=case, OUT_529=out_dir)
    cmd = [sys.executable] + ([] if windowed else ["--headless"]) + ["--exec", CHILD]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env,
                           cwd=os.getcwd())
    except subprocess.TimeoutExpired:
        check(False, "%s/%s timed out (the scenario never reached its end)" % (case, windowed))
        return None
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
    lines = [l for l in r.stdout.splitlines() if l.startswith("RESULT ")]
    if r.returncode != 0 or len(lines) != 1:
        check(False, "%s/%s ran: rc=%d\n%s\n%s" % (case, windowed, r.returncode, r.stdout, r.stderr))
        return None
    out = ast.literal_eval(lines[0][len("RESULT "):])
    return out


for windowed in (False, True):
    mode = "windowed" if windowed else "headless"
    print("== " + mode)

    r = run("first", windowed)
    if r:
        check(r["px"] == RED, "%s (a) setup + immediate screenshot shows the scene: %r" % (mode, r["px"]))

    r = run("twice", windowed)
    if r:
        check(r["p1"] == RED, "%s (b) first shot shows the scene: %r" % (mode, r["p1"]))
        check(r["p2"] == RED and r["same"],
              "%s (b) mutation with no frame between: second shot is the first (%r, identical=%r)"
              % (mode, r["p2"], r["same"]))

    r = run("frame", windowed)
    if r:
        check(r["p1"] == RED and r["p2"] == GREEN,
              "%s (c) after a frame the shot shows the mutation: %r -> %r" % (mode, r["p1"], r["p2"]))

    r = run("midframe", windowed)
    if r:
        check(r["p0"] == RED, "%s (d) baseline shot: %r" % (mode, r["p0"]))
        check(r["in_cb"] == RED and r["in_cb_same"],
              "%s (d) shot inside a timer callback is the previous frame, byte-identical: %r"
              % (mode, r["in_cb"]))
        check(r["after"] == GREEN,
              "%s (d) after the frame the mutation shows: %r" % (mode, r["after"]))

    # A nested step() inside a callback must not take the callback out of its frame.
    r = run("nested", windowed)
    if r:
        check(r["in_cb"] == RED and r["in_cb_same"],
              "%s nested step() then mutate then shot, all inside a callback: previous frame (%r)"
              % (mode, r["in_cb"]))
        check(r["after"] == GREEN, "%s nested: after the frame the mutation shows: %r" % (mode, r["after"]))

    # Window.screenshot() follows the same rules.
    r = run("window", windowed)
    if r:
        check(r["p1"] == RED and r["p2"] == RED and r["same"],
              "%s Window.screenshot(): first shot shows the scene, a mutation with no frame is not in "
              "the second (%r, %r)" % (mode, r["p1"], r["p2"]))
        check(r["p3"] == GREEN, "%s Window.screenshot() after a frame shows the mutation: %r" % (mode, r["p3"]))

    # A screenshot taken while the first-frame capture is itself rendering raises, once.
    r = run("reentrant", windowed)
    if r:
        check(r["px"] == RED, "%s reentrant: the outer capture still succeeds: %r" % (mode, r["px"]))
        check(len(r["inner"]) >= 1 and all(
              i.startswith("RuntimeError") and "no complete frame" in i for i in r["inner"]),
              "%s reentrant: the warnings hook's screenshot raised RuntimeError: %r" % (mode, r["inner"]))

    # Known differences between the modes. DOCUMENTED BEHAVIOUR FOR NOW (the owner may change
    # them); these pin it so a change is a decision, not an accident.
    r = run("diff_i", windowed)
    if r:
        if windowed:
            check(r["px"] == RED,
                  "%s (i) frame; mutate; shot shows the OLD frame (it was presented before the mutation): %r"
                  % (mode, r["px"]))
        else:
            check(r["px"] == GREEN,
                  "%s (i) step(); mutate; shot shows the MUTATION (step draws nothing; the shot draws the "
                  "scene as it is then): %r" % (mode, r["px"]))

    r = run("diff_ii", windowed)
    if r:
        check(r["px"] == GREEN,
              "%s (ii) a first-ever shot inside a callback has no previous frame, so it renders the "
              "current state mid-frame: %r" % (mode, r["px"]))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
