"""
#495 -- scene.on_text: typed text, separate from on_key.

on_key reports physical keys (a German "z" arrives as Key.Y). on_text(text: str) receives
what the key press typed after layout, dead-key and IME processing, as UTF-8 decoded to a
str, one code point per call. automation.typeText() synthesizes it; automation.typewrite()
now delivers it too, between each key's press and release, as a real keyboard does.
"""

import mcrfpy
from mcrfpy import automation
import sys

K = mcrfpy.Key
P = mcrfpy.InputState.PRESSED
R = mcrfpy.InputState.RELEASED
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def raises(exc, fn, msg):
    try:
        fn()
    except exc:
        check(True, msg)
    except Exception as e:  # wrong type
        check(False, "%s (raised %r)" % (msg, e))
    else:
        check(False, msg + " (did not raise)")


events = []
scene = mcrfpy.Scene("issue495")
mcrfpy.current_scene = scene

# --- property ---------------------------------------------------------------
check(scene.on_text is None, "on_text defaults to None")
handler = lambda text: events.append(("text", text))
scene.on_text = handler
check(scene.on_text is handler, "on_text getter returns the handler")
raises(TypeError, lambda: setattr(scene, "on_text", 5), "non-callable on_text raises TypeError")
check(scene.on_text is handler, "failed assignment leaves the handler alone")
scene.on_key = lambda k, s: events.append(("key", k, s))


def run(fn):
    del events[:]
    fn()
    mcrfpy.step(0.016)
    return list(events)


# --- typeText: text only, no keys -----------------------------------------------
check(run(lambda: automation.typeText("z")) == [("text", "z")], "typeText('z') -> on_text('z') only")
check(run(lambda: automation.typeText("é")) == [("text", "é")], "non-ASCII (U+00E9) arrives as a str")
got = run(lambda: automation.typeText("日本😀"))
check(got == [("text", "日"), ("text", "本"), ("text", "😀")],
      "one call per code point, astral plane intact, got %r" % got)
check(all(len(t[1]) == 1 for t in got), "each call is exactly one code point")

# --- typewrite also types text, in a real keyboard's order ----------------------
got = run(lambda: automation.typewrite("a"))
check(got == [("key", K.A, P), ("text", "a"), ("key", K.A, R)],
      "typewrite('a') = press, text, release, got %r" % got)
got = run(lambda: automation.typewrite("A"))
check(("text", "A") in got and ("text", "a") not in got, "shifted letter types 'A', got %r" % got)
got = run(lambda: automation.typewrite("\n\t"))
check([e for e in got if e[0] == "text"] == [], "Enter and Tab are keys, not text, got %r" % got)

# --- control characters are not text, on either backend -------------------------
raises(ValueError, lambda: automation.typeText("\x08"), "typeText rejects Backspace (a key)")
raises(ValueError, lambda: automation.typeText("\n"), "typeText rejects newline (a key)")
raises(ValueError, lambda: automation.typeText("\x7f"), "typeText rejects DEL")
raises(ValueError, lambda: automation.typeText("a\ud800b"), "typeText rejects a lone surrogate")
check(run(lambda: None) == [], "rejected strings sent nothing")
del events[:]
raises(ValueError, lambda: automation.typeText("ok\x1b"), "validated whole before anything is sent")
mcrfpy.step(0.016)
check(events == [], "a rejected string delivers no partial text, got %r" % events)

# --- on_key is independent of on_text -------------------------------------------
got = run(lambda: automation.keyDown("a"))
check(got == [("key", K.A, P)], "a bare key press carries no text, got %r" % got)
automation.keyUp("a")

# --- None removes it; text with no handler is silently not delivered -------------
scene.on_text = None
check(scene.on_text is None, "on_text = None clears it")
check([e for e in run(lambda: automation.typeText("q")) if e[0] == "text"] == [],
      "no handler, nothing delivered")

# --- only the active scene hears it -----------------------------------------------
other = mcrfpy.Scene("issue495_other")
other.on_text = lambda t: events.append(("other", t))
check(run(lambda: automation.typeText("r")) == [], "an inactive scene's on_text is not called")

# --- subclass method ---------------------------------------------------------------
class Typing(mcrfpy.Scene):
    def on_text(self, text):
        events.append(("sub", text))


sub = Typing("issue495_sub")
mcrfpy.current_scene = sub
check(run(lambda: automation.typeText("ü")) == [("sub", "ü")], "subclass on_text method is called")
sub.on_text = lambda t: events.append(("prop", t))
check(run(lambda: automation.typeText("ü")) == [("prop", "ü")], "property handler wins over the method")

if failures:
    print("FAIL: %d check(s) failed" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
