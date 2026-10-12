"""Regression gate for #458 - Color("red") works: names, "source:name", and hex.

Before: any str passed to Color(), and so to every Color setter (#450), raised
NotImplementedError("Color names aren't ready yet").

Decided rules (see src/ColorNames.h, tools/generate_color_table.py):
  * Names ignore case and every ASCII character but letters and digits.
  * An unprefixed name takes the first source that has it: css, xkcd, crayola, jenny.
  * "source:name" looks only in that source.
  * "#rgb", "#rgba", "#rrggbb", "#rrggbbaa" are hex; the '#' is required.
  * Alpha for a name is a= only; hex alpha plus a= is "given twice" (TypeError).
  * An unknown name / source / malformed hex raises ValueError; no fallback colour.
"""
import sys

import mcrfpy

C = mcrfpy.Color
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def rgba(c):
    return (c.r, c.g, c.b, c.a)


def raises(exc, fn, contains=None):
    try:
        fn()
    except exc as e:
        return contains is None or all(s in str(e) for s in contains), str(e)
    except Exception as e:
        return False, "wrong exception %s: %s" % (type(e).__name__, e)
    return False, "no exception"


# --- names and normalization ---
check(rgba(C("red")) == (255, 0, 0, 255), "Color('red') is CSS red")
for spelling in ("Dark Green", "dark_green", "dark-green", "DARKGREEN", "  darkgreen  "):
    check(rgba(C(spelling)) == (0, 100, 0, 255), "%r is CSS darkgreen" % spelling)
check(rgba(C("rebeccapurple")) == (102, 51, 153, 255), "CSS Level 4 rebeccapurple present")
check(C("grey") == C("gray") == C(128, 128, 128), "grey and gray are both CSS #808080")
check(C("sandybrown") == C(0xF4, 0xA4, 0x60), "sandybrown is the spec's #F4A460 (archive had salmon)")

# --- precedence: css > xkcd > crayola > jenny ---
check(C("blue") == C(0, 0, 255), "unprefixed 'blue' is CSS")
check(C("xkcd:blue") == C(0x03, 0x43, 0xDF), "'xkcd:blue' is the survey's blue")
check(C("crayola:red") == C(0xED, 0x0A, 0x3F), "'crayola:red' is the Wikipedia Crayola red")
check(C("jenny:red") == C(0xEE, 0x20, 0x4D), "'jenny:red' is the jenny-list red")
check(C("dust") == C(0xB2, 0x99, 0x6E), "xkcd-only name 'dust' is unprefixed")
check(C("Brick Red") == C(0x8F, 0x14, 0x02), "xkcd 'brick red' beats crayola's")
check(C("Pacific Blue") == C(0x00, 0x9D, 0xC4), "crayola 'Pacific Blue' beats jenny's")
check(C("Atomic Tangerine") == C(0xFF, 0xA4, 0x74), "jenny-only name reachable unprefixed")
check(C("XKCD : dust") == C("dust"), "source prefix ignores case and spaces")
# Within xkcd, the later (more common) spelling wins a shared key.
check(C("xkcd:dark green") == C("xkcd:darkgreen") == C(0x03, 0x35, 0x00),
      "xkcd 'dark green' / 'darkgreen' share a key, later spelling kept")
check(C("Robin's Egg Blue") == C("robins egg blue"), "apostrophes ignored")

# --- hex ---
check(rgba(C("#f00")) == (255, 0, 0, 255), "#rgb")
check(rgba(C("#f008")) == (255, 0, 0, 0x88), "#rgba")
check(rgba(C("#FF8000")) == (255, 128, 0, 255), "#rrggbb")
check(rgba(C("#ff800080")) == (255, 128, 0, 128), "#rrggbbaa")
for bad in ("#", "#ff", "#fffff", "#ggg", "#ff00zz", "#ff 000"):
    ok, msg = raises(ValueError, lambda: C(bad), ["hex"])
    check(ok, "Color(%r) raises ValueError: %s" % (bad, msg))
check(rgba(C.from_hex("ff0000")) == (255, 0, 0, 255), "from_hex still takes no '#'")
ok, msg = raises(ValueError, lambda: C.from_hex("FF00G0"))
check(ok, "from_hex rejects a non-hex digit (stoul used to accept a prefix): %s" % msg)
ok, msg = raises(ValueError, lambda: C.from_hex("1g0000"))
check(ok, "from_hex('1g0000') rejected: %s" % msg)

# --- alpha ---
check(rgba(C("red", a=128)) == (255, 0, 0, 128), "Color('red', a=128)")
check(rgba(C("#f00", a=7)) == (255, 0, 0, 7), "Color('#f00', a=7)")
ok, msg = raises(TypeError, lambda: C("#f008", a=7), ["twice"])
check(ok, "hex alpha and a= together: %s" % msg)
ok, msg = raises(TypeError, lambda: C("red", 128))
check(ok, "positional g after a name is a TypeError: %s" % msg)
ok, msg = raises(ValueError, lambda: C("red", a=300))
check(ok, "a=300 with a name is ValueError: %s" % msg)
ok, msg = raises(ValueError, lambda: C("red", a=-1))
check(ok, "a=-1 with a name is ValueError: %s" % msg)

# --- unknown names: ValueError with close matches, never a fallback ---
ok, msg = raises(ValueError, lambda: C("redd"), ["redd", "did you mean", "'red'"])
check(ok, "unknown 'redd' suggests 'red': %s" % msg)
ok, msg = raises(ValueError, lambda: C("xkcd:dusst"), ["xkcd:dust"])
check(ok, "unknown 'xkcd:dusst' suggests 'xkcd:dust': %s" % msg)
ok, msg = raises(ValueError, lambda: C("qqqqqqqqqqqq"), ["unknown color name"])
check(ok and "did you mean" not in msg, "nothing close: no suggestion: %s" % msg)
ok, msg = raises(ValueError, lambda: C("pantone:red"), ["css", "xkcd", "crayola", "jenny"])
check(ok, "unknown source lists sources: %s" % msg)
for bad in ("", "   ", "!!!", "xkcd:"):
    ok, msg = raises(ValueError, lambda: C(bad))
    check(ok, "Color(%r) raises ValueError: %s" % (bad, msg))
ok, msg = raises(ValueError, lambda: C("réd"))
check(ok, "non-ASCII never matches: %s" % msg)

# --- Color.names() ---
names = C.names()
check(isinstance(names, list) and len(names) > 1000, "Color.names() lists %d names" % len(names))
check("red" in names and "dust" in names and "rebeccapurple" in names, "names() has css+xkcd")
bad = [n for n in names if not isinstance(n, str)]
check(not bad, "names() are all str")
unresolved = []
for n in names:
    try:
        C(n)
    except Exception as e:
        unresolved.append((n, str(e)))
check(not unresolved, "every Color.names() entry resolves %s" % unresolved[:3])
for src, count in (("css", 148), ("xkcd", 923), ("crayola", 168), ("jenny", 120)):
    got = C.names(src)
    check(len(got) == count, "Color.names(%r) has %d (want %d)" % (src, len(got), count))
    broken = [n for n in got if not isinstance(C("%s:%s" % (src, n)), C)]
    check(not broken, "every %s name resolves with its prefix" % src)
check(C.names(source="XKCD") == C.names("xkcd"), "names(source=) ignores case")
ok, msg = raises(ValueError, lambda: C.names("pantone"), ["css"])
check(ok, "names('pantone') raises ValueError: %s" % msg)

# --- every Color setter accepts names (to_color is exactly Color(value), #450) ---
frame = mcrfpy.Frame(pos=(0, 0), size=(10, 10), fill_color="navy", outline_color="#0f0")
check(frame.fill_color == C(0, 0, 128) and frame.outline_color == C(0, 255, 0),
      "Frame(fill_color='navy', outline_color='#0f0')")
frame.fill_color = "xkcd:dust"
check(frame.fill_color == C(0xB2, 0x99, 0x6E), "frame.fill_color = 'xkcd:dust'")
before = frame.fill_color
ok, msg = raises(ValueError, lambda: setattr(frame, "fill_color", "not a colour at all"))
check(ok and frame.fill_color == before, "bad name in a setter raises and leaves value: %s" % msg)
cap = mcrfpy.Caption(text="x", pos=(0, 0))
cap.fill_color = "white"
check(cap.fill_color == C(255, 255, 255), "caption.fill_color = 'white'")
layer = mcrfpy.ColorLayer(name="c")
grid = mcrfpy.Grid(grid_size=(3, 3), texture=mcrfpy.default_texture)
grid.add_layer(layer)
layer.fill("teal")
v = layer.at(1, 1)
check((C(*v) if isinstance(v, tuple) else v) == C(0, 128, 128), "ColorLayer.fill('teal')")

# --- the committed header is what the generator makes from the committed tables ---
import os
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location(
    "generate_color_table", os.path.join(ROOT, "tools", "generate_color_table.py"))
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
with open(gen.OUT, encoding="utf-8") as f:
    check(f.read() == gen.build(),
          "src/ColorNameTable.h is current (python3 tools/generate_color_table.py)")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
