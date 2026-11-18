"""#550: the atlas's wide table (Texture.is_wide, src/EastAsianWide.h) agrees with the terminal.

Texture.from_font gives a wide codepoint two tiles and TerminalLayer draws them across the two
cells the terminal gives it, so both must use one width rule: libghostty-vt's (see
tools/generate_east_asian_wide.py). Every codepoint of the BMP and SMP that this Python's
unicodedata calls assigned and not a control/surrogate/private-use/line or paragraph separator
is written into a terminal followed by "X"; the X lands two columns on exactly when the
terminal made the codepoint wide. A second pass checks zero width the same way ("a" + cp + "X":
the X is in column 1 exactly when cp combined with the "a") against the layer's own zero-width rule.
Batched 1000 rows a write, read back with at(); no rendering.
"""
import sys
import time
import unicodedata

import mcrfpy

FONT = mcrfpy.Font("assets/JetbrainsMono.ttf")
TEX = mcrfpy.Texture.from_font(FONT, 8, codepoints="aX")
X = TEX.index("X")
ROWS = 1000
t = mcrfpy.TerminalLayer(texture=TEX, grid_size=(4, ROWS), scrollback=0)

SKIP = {"Cc", "Cs", "Co", "Cn", "Zl", "Zp"}
cps = [cp for cp in range(0x20000) if unicodedata.category(chr(cp)) not in SKIP]
start = time.perf_counter()
mismatches = []
for i in range(0, len(cps), ROWS):
    batch = cps[i:i + ROWS]
    t.write("\x1b[2J\x1b[H" + "\r\n".join(chr(cp) + "X" for cp in batch))
    for y, cp in enumerate(batch):
        term_wide = t.at(2, y) == X
        if term_wide != TEX.is_wide(cp):
            mismatches.append(cp)
# Zero width: "a" + cp + "X" puts the X in column 1 exactly when the terminal attached cp to the
# "a". The layer's own zero-width rule (same generated table) shows through print(), which refuses
# text that starts with a zero-width codepoint.
zero_mismatches = []
for i in range(0, len(cps), ROWS):
    batch = cps[i:i + ROWS]
    t.write("\x1b[2J\x1b[H" + "\r\n".join("a" + chr(cp) + "X" for cp in batch))
    for y, cp in enumerate(batch):
        term_zero = t.at(1, y) == X and cp != ord("X")
        try:
            t.print(chr(cp), pos=(0, 0))
            layer_zero = False
        except ValueError:
            layer_zero = True
        if term_zero != layer_zero:
            zero_mismatches.append(cp)
mismatches += zero_mismatches
elapsed = time.perf_counter() - start
print(f"{len(cps)} codepoints (Python Unicode {unicodedata.unidata_version}) in {elapsed:.2f} s")
if mismatches:
    print(f"FAIL: {len(mismatches)} disagree, e.g. " + ", ".join(f"U+{cp:04X}" for cp in mismatches[:20]))
    sys.exit(1)
print("PASS")
sys.exit(0)
