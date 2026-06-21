"""
Regression test for issue #320 -- Caption constructor positional signature.

The frozen docstring advertises Caption(pos=None, font=None, text='', **kwargs)
(font is the 2nd positional, text the 3rd), matching the Sprite/Entity
convention. The implementation previously laid the two positional slots out as
(pos, text) with font keyword-only, so:
  - Caption((x,y), None, "Hello")  raised "at most 2 positional arguments"
  - Caption((x,y), "string")       silently bound the string to text

The fix makes the impl match the docstring: positional order (pos, font, text).

ASCII-only source. Prints PASS/FAIL and sys.exit(0/1).
"""

import mcrfpy
import sys

failures = []


def check(label, cond):
    if not cond:
        failures.append(label)
    print(("  ok  " if cond else " FAIL ") + label)


font = mcrfpy.Font("assets/JetbrainsMono.ttf")

# --- the bug: 3 positional args (pos, font, text) must work -----------------
c = mcrfpy.Caption((50, 100), font, "Hello World")
check("Caption((pos), font, text) does not raise", True)
check("  -> text bound to 3rd positional", c.text == "Hello World")
check("  -> x from pos", c.x == 50)
check("  -> y from pos", c.y == 100)
check("  -> font getter returns the passed Font (identity)", c.font is font)

# --- font=None positionally still selects the default font -----------------
c2 = mcrfpy.Caption((10, 20), None, "Defaulted")
check("Caption((pos), None, text) works (None font -> default)", c2.text == "Defaulted")
check("  -> font getter reflects default font (not None)", c2.font is not None)
check("  -> default font is a Font instance", isinstance(c2.font, mcrfpy.Font))

# --- font getter is read-only ----------------------------------------------
try:
    c2.font = font
    check("Caption.font is read-only", False)
except AttributeError:
    check("Caption.font is read-only", True)
except Exception as e:
    check("Caption.font is read-only (got %s)" % type(e).__name__, False)

# --- font is the 2nd positional (matches Sprite/Entity resource-2nd order) --
# A real Font in slot 2 must be accepted as the font, NOT misread as text.
c3 = mcrfpy.Caption((0, 0), font)
check("Caption((pos), font) binds font, leaves text empty", c3.text == "")

# --- keyword forms remain intact -------------------------------------------
c4 = mcrfpy.Caption((5, 5), text="kwtext")
check("Caption((pos), text=...) keyword text works", c4.text == "kwtext")
c5 = mcrfpy.Caption(pos=(7, 8), font=font, text="allkw")
check("Caption(pos=, font=, text=) all-keyword works", c5.text == "allkw" and c5.x == 7)
c6 = mcrfpy.Caption()
check("Caption() no-args works", c6.text == "" and c6.x == 0)

# --- documented behavior change: a string in slot 2 is now the font --------
# (font must be a Font instance, so a str -> TypeError). Confirms the new
# positional order, and that we did not keep the old (pos, text) layout.
try:
    mcrfpy.Caption((0, 0), "this is not a font")
    check("Caption((pos), 'str') rejects string-as-font (new order)", False)
except TypeError:
    check("Caption((pos), 'str') rejects string-as-font (new order)", True)
except Exception as e:
    check("Caption((pos), 'str') rejects string-as-font (got %s)" % type(e).__name__, False)

# --- parity with siblings: all three accept 3 positional now ----------------
mcrfpy.Sprite((100, 150), None, 5)
mcrfpy.Entity((5, 10), None, 3)
mcrfpy.Caption((50, 100), None, "x")
check("Caption now matches Sprite/Entity 3-positional convention", True)


print("")
if failures:
    print("FAIL -- %d check(s) failed:" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("PASS -- Caption(pos, font, text) positional signature matches its docstring.")
sys.exit(0)
