#!/usr/bin/env python3
"""Generate src/EastAsianWide.h: the codepoints a terminal cell holds as WIDE (two columns).

Texture.from_font (#547) gives these two tiles, and TerminalLayer (#550) draws them across two
cells, so the table must agree with the terminal emulator's own width rule. The rule is
libghostty-vt 1.0.1's (Ghostty's `src/build/uucode_config.zig` WidthComponent over uucode
0.2.0's `Wcwidth` component, `src/components.zig`), on uucode's Unicode Character Database:

    standalone(cp) = 0  if General_Category is Cc, Cs, Zl or Zp
                     1  if cp == U+00AD
                     0  if Default_Ignorable_Code_Point
                     2  if cp == U+2E3A;  3 if cp == U+2E3B
                     2  if East_Asian_Width is W or F (@missing defaults applied)
                     2  if Grapheme_Cluster_Break is Regional_Indicator
                     1  otherwise                 (U+20E3 is 2 standalone)
    zero_in_grapheme(cp) = standalone == 0, or Emoji_Modifier, or General_Category Mn/Me,
                           or Grapheme_Cluster_Break V, T or Prepend
    width(cp) = 0 if zero_in_grapheme and not Emoji_Modifier and GCB != Prepend
                else min(2, standalone)

    WIDE  <=>  width(cp) == 2

Input: the UCD directory uucode ships (`ucd/`: extracted/DerivedEastAsianWidth.txt,
extracted/DerivedGeneralCategory.txt, DerivedCoreProperties.txt,
auxiliary/GraphemeBreakProperty.txt, emoji/emoji-data.txt). `make deps` fetches it into
build-deps/zig-pkg/uucode-*/ucd. Regenerate (and commit the result) when libghostty-vt moves:

    python3 tools/generate_east_asian_wide.py [UCD_DIR] > src/EastAsianWide.h
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULE_SOURCE = "libghostty-vt 1.0.1 cell width (Ghostty uucode_config WidthComponent, uucode 0.2.0 Wcwidth)"


def ucd_dir():
    if len(sys.argv) > 1:
        return sys.argv[1]
    found = sorted(glob.glob(os.path.join(ROOT, "build-deps", "zig-pkg", "uucode-*", "ucd")))
    if not found:
        sys.exit("no UCD directory given and none under build-deps/zig-pkg/uucode-*/ucd (run make deps)")
    return found[-1]


def parse(path, missing=False):
    """{cp: value} from a UCD 'range ; value' file; with missing=True, @missing lines first."""
    out = {}
    line_re = re.compile(r"^([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*([^#\s]+)")
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    if missing:
        for ln in lines:
            m = re.match(r"^#\s*@missing:\s*([0-9A-F]+)\.\.([0-9A-F]+)\s*;\s*(\S+)", ln)
            if m:
                for cp in range(int(m.group(1), 16), int(m.group(2), 16) + 1):
                    out[cp] = m.group(3)
    for ln in lines:
        m = line_re.match(ln)
        if m:
            lo = int(m.group(1), 16)
            hi = int(m.group(2), 16) if m.group(2) else lo
            for cp in range(lo, hi + 1):
                out[cp] = m.group(3)
    return out


def with_property(path, name):
    """Codepoints a binary-property file lists under `name` (a codepoint has many properties
    there, so this is a set per property, not one value per codepoint)."""
    out = set()
    line_re = re.compile(r"^([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*([^#\s]+)")
    with open(path, encoding="utf-8") as f:
        for ln in f:
            m = line_re.match(ln)
            if m and m.group(3) == name:
                lo = int(m.group(1), 16)
                out.update(range(lo, (int(m.group(2), 16) if m.group(2) else lo) + 1))
    return out


def version_of(path):
    with open(path, encoding="utf-8") as f:
        m = re.search(r"-(\d+\.\d+\.\d+)\.txt", f.readline())
    return m.group(1) if m else "unknown"


ucd = ucd_dir()
eaw = parse(os.path.join(ucd, "extracted", "DerivedEastAsianWidth.txt"), missing=True)
gc = parse(os.path.join(ucd, "extracted", "DerivedGeneralCategory.txt"), missing=True)
gcb = parse(os.path.join(ucd, "auxiliary", "GraphemeBreakProperty.txt"))
version = version_of(os.path.join(ucd, "DerivedCoreProperties.txt"))
default_ignorable = with_property(os.path.join(ucd, "DerivedCoreProperties.txt"), "Default_Ignorable_Code_Point")
emoji_modifier = with_property(os.path.join(ucd, "emoji", "emoji-data.txt"), "Emoji_Modifier")
EAW_WIDE = ("W", "F", "Wide", "Fullwidth")


def width(cp):
    cat = gc.get(cp, "Cn")
    if cat in ("Cc", "Cs", "Zl", "Zp"):
        standalone = 0
    elif cp == 0x00AD:
        standalone = 1
    elif cp in default_ignorable:
        standalone = 0
    elif cp == 0x2E3A:
        standalone = 2
    elif cp == 0x2E3B:
        standalone = 3
    elif eaw.get(cp, "N") in EAW_WIDE:
        standalone = 2
    elif gcb.get(cp) == "Regional_Indicator":
        standalone = 2
    else:
        standalone = 1
    if cp == 0x20E3:
        standalone = 2
    brk = gcb.get(cp)
    modifier = cp in emoji_modifier
    zero_in_grapheme = (standalone == 0 or modifier or cat in ("Mn", "Me") or brk in ("V", "T", "Prepend"))
    if zero_in_grapheme and not modifier and brk != "Prepend":
        return 0
    return min(2, standalone)


ranges = []
start = prev = None
for cp in range(0x110000):
    if width(cp) == 2:
        if start is None:
            start = cp
        prev = cp
    elif start is not None:
        ranges.append((start, prev))
        start = None
if start is not None:
    ranges.append((start, prev))

out = sys.stdout
out.write("// Generated by tools/generate_east_asian_wide.py -- do not edit.\n")
out.write(f"// Codepoints a terminal cell holds as wide (two columns): {RULE_SOURCE},\n")
out.write(f"// on Unicode {version} data. East Asian Width W/F plus regional indicators and U+2E3A/B,\n")
out.write("// minus the codepoints that are zero width (marks, Hangul V/T, ...). Ranges are inclusive, sorted.\n")
out.write("#pragma once\n#include <cstdint>\n\n")
out.write(f'constexpr const char* EAST_ASIAN_WIDE_UNICODE_VERSION = "{version}";\n\n')
out.write("struct EastAsianWideRange { uint32_t lo, hi; };\n")
out.write("constexpr EastAsianWideRange EAST_ASIAN_WIDE_RANGES[] = {\n")
for i in range(0, len(ranges), 4):
    out.write("    " + " ".join(f"{{0x{a:X}, 0x{b:X}}}," for a, b in ranges[i:i + 4]) + "\n")
out.write("};\n")
