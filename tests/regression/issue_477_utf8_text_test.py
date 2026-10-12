"""Regression test for #477 - UTF-8 is the engine's text encoding, regardless of locale.

SFML's sf::String(std::string) widens each byte to one code point through the C++
locale, so Caption(text="╔") drew the three glyphs "â•”" (or tofu) and .text came back
mangled. Text now crosses into and out of SFML through mcrf::from_utf8 / to_utf8.

The default font (JetBrains Mono) is monospace and covers box drawing and shades, so a
one-character caption must be exactly one cell wide whatever the character.
"""
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


SAMPLES = ["é", "╔═╗", "░▒▓█", "naïve café", "→ ✓", "日本"]

print("1. .text round-trips through the constructor, the setter and set via kwargs")
for s in SAMPLES:
    c = mcrfpy.Caption(text=s, pos=(0, 0))
    check(c.text == s, "ctor: %r -> %r" % (s, c.text))
    c = mcrfpy.Caption(text="x", pos=(0, 0))
    c.text = s
    check(c.text == s, "setter: %r -> %r" % (s, c.text))
    check(repr(s)[1:-1] in repr(c) or s in repr(c), "repr carries %r: %s" % (s, repr(c)))

print("1b. text that is not valid UTF-8 raises instead of being dropped")
c = mcrfpy.Caption(text="kept", pos=(0, 0))
try:
    c.text = "\ud800"
    check(False, "lone surrogate raised")
except UnicodeEncodeError:
    check(c.text == "kept", "lone surrogate raises UnicodeEncodeError, text unchanged")

print("2. one character draws as one glyph (monospace advance)")
# caption.w is the ink extent, which varies per glyph; between two 'e's it measures
# the middle character's advance, which in a monospace font is one cell.
def width(t):
    return mcrfpy.Caption(text=t, pos=(0, 0), font_size=16).w
ref_w = width("eee")
check(ref_w > 0, "reference has width (%r)" % ref_w)
for ch in ["é", "╔", "░", "█", "→"]:
    check(abs(width("e%se" % ch) - ref_w) < 0.5,
          "%r is one cell wide (%r vs %r)" % (ch, width("e%se" % ch), ref_w))
check(abs(width("e╔═══╗e") - width("eeeeeee")) < 0.5, "'╔═══╗' is five cells wide")

print("3. the window title takes and returns UTF-8")
w = mcrfpy.Window.get()
w.title = "McRogueFace — ░ test"
check(w.title == "McRogueFace — ░ test", "title round-trips: %r" % w.title)

print("=" * 50)
if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
