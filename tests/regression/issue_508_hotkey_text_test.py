"""
Regression test for #508 -- a dev-tool hotkey was swallowed as a key but not as text.

A keystroke is KeyPressed, then the text it typed (TextEntered), then KeyReleased.
filterDevInput (#496, #503) dropped the press and release of a hotkey but let its text
through, so opening the console with Grave sent on_text("`"), and with
profiler_key = Key.P every toggle also typed "p". The text of a swallowed keystroke is
now swallowed with it; text after that keystroke (typeText, the next key) still arrives.

Needs a window (headless has no dev tools, so nothing is a hotkey there): the checks run
in a windowed child, like the #496 and #503 tests.
"""

import json
import os
import subprocess
import sys
import tempfile

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


CHILD = r'''
import json, sys
import mcrfpy
from mcrfpy import automation
K = mcrfpy.Key
W = mcrfpy.window
log = []
scene = mcrfpy.Scene("child")
scene.on_key = lambda k, s: log.append(["key", k.name, s.name])
scene.on_text = lambda t: log.append(["text", t])
mcrfpy.current_scene = scene
results = {}

def run(fn):
    del log[:]
    fn()
    return list(log)

def go(timer, runtime):
    timer.stop()
    r = results
    # a printable profiler hotkey: the whole keystroke belongs to the overlay
    W.profiler_key = K.P
    r["p_hotkey_on"] = run(lambda: automation.typewrite("p"))
    r["p_hotkey_off"] = run(lambda: automation.typewrite("p"))
    # text after the swallowed keystroke is not eaten
    r["text_after_hotkey"] = run(lambda: (automation.typewrite("p"), automation.typeText("x"),
                                          automation.typewrite("p")))
    W.profiler_key = None
    r["p_plain"] = run(lambda: automation.typewrite("p"))
    W.profiler_key = K.F3
    # the console hotkey: Grave types "`" on a US layout
    r["grave_open"] = run(lambda: automation.typewrite("`"))
    r["grave_close"] = run(lambda: automation.typewrite("`"))
    r["a_after_close"] = run(lambda: automation.typewrite("a"))
    print("RESULT " + json.dumps(r))
    sys.stdout.flush()
    sys.exit(0)

mcrfpy.Timer("go", go, 100)
'''

with tempfile.TemporaryDirectory() as d:
    script = os.path.join(d, "child.py")
    with open(script, "w") as f:
        f.write(CHILD)
    env = dict(os.environ, ALSOFT_DRIVERS="null")
    proc = subprocess.run([sys.executable, "--exec", script], capture_output=True, text=True,
                          timeout=90, env=env, cwd=os.path.dirname(sys.executable))
lines = [l for l in proc.stdout.splitlines() if l.startswith("RESULT ")]
if not lines:
    check(False, "windowed child produced no result (exit %s)\nstdout:\n%s\nstderr:\n%s"
          % (proc.returncode, proc.stdout[-1500:], proc.stderr[-1500:]))
else:
    r = json.loads(lines[0][len("RESULT "):])
    keystroke = lambda name, ch: [["key", name, "PRESSED"], ["text", ch], ["key", name, "RELEASED"]]
    check(r["p_hotkey_on"] == [], "profiler_key=P: pressing p delivers nothing, got %r" % r["p_hotkey_on"])
    check(r["p_hotkey_off"] == [], "profiler_key=P: toggling back delivers nothing, got %r" % r["p_hotkey_off"])
    check(r["text_after_hotkey"] == [["text", "x"]],
          "typeText after a swallowed hotkey still arrives, got %r" % r["text_after_hotkey"])
    check(r["p_plain"] == keystroke("P", "p"), "profiler_key=None: p is key + text, got %r" % r["p_plain"])
    check(r["grave_open"] == [], "Grave opening the console types nothing, got %r" % r["grave_open"])
    check(r["grave_close"] == [], "Grave closing the console types nothing, got %r" % r["grave_close"])
    check(r["a_after_close"] == keystroke("A", "a"), "after closing, a is key + text, got %r" % r["a_after_close"])

if failures:
    print("FAIL: %d check(s) failed" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
