#!/usr/bin/env python3
"""Validate screenshot functionality and analyze pixel data

The headless renderer must produce a PNG that actually contains the drawn
content -- not a transparent/blank image. This test draws frames of known
colors at known positions, screenshots them, decodes the PNG and asserts the
expected color is present at the expected pixel. It also covers filename edge
cases (spaces, empty, very long).
"""
import mcrfpy
from mcrfpy import automation
from datetime import datetime
import os
import struct
import sys
import zlib

FAILURES = []

OUT_DIR = "test_screenshots"


def check(cond, msg):
    if not cond:
        print("FAIL: %s" % msg)
        FAILURES.append(msg)


# --------------------------------------------------------------------------- #
# Minimal PNG reader (stdlib only): 8-bit RGB/RGBA, non-interlaced -- what the
# engine's screenshot encoder emits. (Same reader as
# tests/regression/issue_355_camera_rotation_hit_test.py)
# --------------------------------------------------------------------------- #
def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos = 8
    idat = b""
    width = height = depth = color = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            assert depth == 8, "unexpected bit depth %d" % depth
            assert color in (2, 6), "unexpected color type %d" % color
            assert interlace == 0, "interlaced PNG not supported"
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break

    raw = zlib.decompress(idat)
    channels = 3 if color == 2 else 4
    stride = width * channels
    out = bytearray(height * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        filt = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if filt == 1:      # Sub
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filt == 2:    # Up
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filt == 3:    # Average
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif filt == 4:    # Paeth
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        elif filt != 0:
            raise AssertionError("bad PNG filter %d" % filt)
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return width, height, channels, bytes(out)


class Image:
    def __init__(self, path):
        self.w, self.h, self.ch, self.px = read_png(path)

    def at(self, x, y):
        i = (y * self.w + x) * self.ch
        return tuple(self.px[i:i + 3]), (self.px[i + 3] if self.ch == 4 else 255)


def test_screenshot_validation():
    """Create visible content and validate screenshot output"""
    print("=== Screenshot Validation Test ===\n")

    # Create a scene with bright, visible content
    screenshot_validation = mcrfpy.Scene("screenshot_validation")
    screenshot_validation.activate()
    ui = screenshot_validation.children

    print("Creating UI elements...")

    # Light gray background frame, added FIRST so it is behind everything.
    # (The old version appended it last and tried ui.remove(index) to reorder;
    #  UICollection.remove takes a Drawable, not an index -- insert(0, ...) is
    #  the supported way to put a drawable at the back.)
    background = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                              fill_color=mcrfpy.Color(200, 200, 200))
    ui.append(background)

    # Bright red frame with white outline
    frame1 = mcrfpy.Frame(pos=(50, 50), size=(300, 200),
                          fill_color=mcrfpy.Color(255, 0, 0),        # Bright red
                          outline_color=mcrfpy.Color(255, 255, 255),  # White
                          outline=5.0)
    ui.append(frame1)
    print("Added red frame at (50, 50)")

    # Bright green frame
    frame2 = mcrfpy.Frame(pos=(400, 50), size=(300, 200),
                          fill_color=mcrfpy.Color(0, 255, 0),        # Bright green
                          outline_color=mcrfpy.Color(0, 0, 0),       # Black
                          outline=3.0)
    ui.append(frame2)
    print("Added green frame at (400, 50)")

    # Blue frame
    frame3 = mcrfpy.Frame(pos=(50, 300), size=(300, 200),
                          fill_color=mcrfpy.Color(0, 0, 255),        # Bright blue
                          outline_color=mcrfpy.Color(255, 255, 0),   # Yellow
                          outline=4.0)
    ui.append(frame3)
    print("Added blue frame at (50, 300)")

    # Add text captions (Caption.font is read-only as of #320 -- set in ctor)
    caption1 = mcrfpy.Caption(pos=(10, 10), font=mcrfpy.default_font,
                              text="RED FRAME TEST",
                              fill_color=mcrfpy.Color(255, 255, 255))
    caption1.font_size = 24
    frame1.children.append(caption1)  # child coords are frame-relative

    caption2 = mcrfpy.Caption(pos=(410, 60), font=mcrfpy.default_font,
                              text="GREEN FRAME TEST",
                              fill_color=mcrfpy.Color(0, 0, 0))
    caption2.font_size = 24
    ui.append(caption2)

    caption3 = mcrfpy.Caption(pos=(60, 310), font=mcrfpy.default_font,
                              text="BLUE FRAME TEST",
                              fill_color=mcrfpy.Color(255, 255, 0))
    caption3.font_size = 24
    ui.append(caption3)

    print("\nTotal UI elements: %d" % len(ui))
    check(len(ui) == 6, "expected 6 top-level drawables, got %d" % len(ui))

    # Take multiple screenshots with different names (incl. spaces in filename)
    os.makedirs(OUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    screenshots = [
        os.path.join(OUT_DIR, "validate_screenshot_basic_%s.png" % timestamp),
        os.path.join(OUT_DIR, "validate_screenshot_with_spaces %s.png" % timestamp),
        os.path.join(OUT_DIR, "validate_screenshot_final_%s.png" % timestamp),
    ]

    print("\nTaking screenshots...")
    for i, filename in enumerate(screenshots):
        result = automation.screenshot(filename)
        print("Screenshot %d: %s - Result: %s" % (i + 1, filename, result))
        check(result is True, "screenshot(%r) did not return True" % filename)
        check(os.path.exists(filename) and os.path.getsize(filename) > 0,
              "screenshot(%r) produced no file" % filename)

    # --- The actual point of this test: the PNG must contain the drawn content,
    # --- not a transparent/blank image.
    if not FAILURES:
        img = Image(screenshots[0])
        print("\nDecoded %dx%d (%d channels)" % (img.w, img.h, img.ch))

        expected = [
            ((900, 700), (200, 200, 200), "light gray background"),
            ((200, 150), (255, 0, 0), "red frame interior"),
            ((550, 150), (0, 255, 0), "green frame interior"),
            ((200, 400), (0, 0, 255), "blue frame interior"),
            # Outlines are stroked OUTWARD from the frame bounds, so sample just
            # left of x=50: red frame outline is 5px (45..50), blue frame's 4px (46..50).
            ((47, 150), (255, 255, 255), "white outline of red frame"),
            ((47, 400), (255, 255, 0), "yellow outline of blue frame"),
        ]
        for (x, y), want, what in expected:
            if x >= img.w or y >= img.h:
                check(False, "sample point (%d,%d) outside %dx%d image" % (x, y, img.w, img.h))
                continue
            rgb, alpha = img.at(x, y)
            check(rgb == want,
                  "%s: pixel (%d,%d) is %s, expected %s" % (what, x, y, rgb, want))
            check(alpha == 255,
                  "%s: pixel (%d,%d) is transparent (alpha=%d) -- headless "
                  "renderer produced an empty image" % (what, x, y, alpha))

        # Text must have been rasterized: white glyph pixels inside the red frame.
        # caption1 sits at frame-relative (10,10) -> absolute (60,60), 24px font.
        white_in_red = 0
        for y in range(60, 90):
            for x in range(60, 300):
                if img.at(x, y)[0] == (255, 255, 255):
                    white_in_red += 1
        check(white_in_red > 20,
              "caption text not rendered inside red frame (only %d white pixels)"
              % white_in_red)

    # Test invalid / edge-case filenames
    print("\nTesting edge cases...")

    # Empty filename: must fail cleanly (False), not raise or write anything
    result = automation.screenshot("")
    print("Empty filename result: %s" % result)
    check(result is False, "screenshot('') should return False, got %r" % result)

    # Very long (but legal, <255) filename: must succeed and produce a file
    long_name = os.path.join(OUT_DIR, "x" * 200 + ".png")
    result = automation.screenshot(long_name)
    print("Long filename result: %s" % result)
    check(result is True, "screenshot(<200-char name>) should return True, got %r" % result)
    check(os.path.exists(long_name), "long-filename screenshot produced no file")

    print("\n=== Test Complete ===")
    if FAILURES:
        print("\n%d FAILURE(S):" % len(FAILURES))
        for f in FAILURES:
            print("  - %s" % f)
        sys.exit(1)

    print("PASS")
    sys.exit(0)


# Run the test immediately (no timer needed: headless screenshots are synchronous)
test_screenshot_validation()
