"""
Regression test for #433 -- automation.typewrite() never reached on_key.

typewrite() injected sf::Event::TextEntered for ordinary characters, which
GameEngine::processEvent drops, so typing into a scene silently did nothing
(only '\\n' and '\\t' became real key events). Now typewrite simulates key
presses: KeyPressed + KeyReleased per character (US layout), with Shift held
around uppercase/shifted characters. A character with no key raises ValueError
naming it, and the whole string is validated before any event is sent.
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


calls = []
scene = mcrfpy.Scene("issue433")
scene.on_key = lambda k, st: calls.append((k, st))
mcrfpy.current_scene = scene


def typed(text):
    del calls[:]
    automation.typewrite(text)
    mcrfpy.step(0.016)
    return list(calls)


def tap(key):
    return [(key, P), (key, R)]


def shifted(key):
    return [(K.LEFT_SHIFT, P)] + tap(key) + [(K.LEFT_SHIFT, R)]


got = typed("ab")
check(got == tap(K.A) + tap(K.B), "typewrite('ab') -> A, B press/release in order, got %r" % got)

got = typed("A1 !")
check(got == shifted(K.A) + tap(K.NUM_1) + tap(K.SPACE) + shifted(K.NUM_1),
      "uppercase and shifted characters hold Shift, got %r" % got)

got = typed("\n\t")
check(got == tap(K.ENTER) + tap(K.TAB), "newline -> Enter, tab -> Tab, got %r" % got)

expected = {
    ",": tap(K.COMMA), ".": tap(K.PERIOD), "/": tap(K.SLASH), "\\": tap(K.BACKSLASH),
    ";": tap(K.SEMICOLON), "'": tap(K.APOSTROPHE), "[": tap(K.LEFT_BRACKET),
    "]": tap(K.RIGHT_BRACKET), "-": tap(K.HYPHEN), "=": tap(K.EQUAL), "`": tap(K.GRAVE),
    "?": shifted(K.SLASH), ":": shifted(K.SEMICOLON), '"': shifted(K.APOSTROPHE),
    "_": shifted(K.HYPHEN), "+": shifted(K.EQUAL), "~": shifted(K.GRAVE),
    "{": shifted(K.LEFT_BRACKET), "}": shifted(K.RIGHT_BRACKET), "|": shifted(K.BACKSLASH),
    "<": shifted(K.COMMA), ">": shifted(K.PERIOD), ")": shifted(K.NUM_0),
    "@": shifted(K.NUM_2), "(": shifted(K.NUM_9),
}
for ch, want in expected.items():
    got = typed(ch)
    check(got == want, "typewrite(%r) -> %r, got %r" % (ch, want, got))

# Every delivered value is an enum member.
check(all(type(k) is K for k, _ in calls), "Key enum members delivered")

# A character with no key raises ValueError naming it, and nothing is sent.
for bad in ("abé", "\x01xyz", "ok\r"):
    del calls[:]
    try:
        automation.typewrite(bad)
        err = None
    except ValueError as e:
        err = str(e)
    mcrfpy.step(0.016)
    culprit = [c for c in bad if c not in "abokxyz"][0]
    check(err is not None and repr(culprit) in err,
          "typewrite(%r) raises ValueError naming %r, got %r" % (bad, culprit, err))
    check(calls == [], "typewrite(%r) sends nothing, got %r" % (bad, calls))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
