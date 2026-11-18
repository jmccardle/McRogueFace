#!/usr/bin/env python3
"""Visual test for UICaption's visible and opacity properties."""

import mcrfpy
from mcrfpy import automation
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "regression"))
from _png import read_png  # noqa: E402

failures = []
shots = tempfile.mkdtemp(prefix="mcrf_caption_visual_")


def shot(name):
    mcrfpy.step(0.01)
    path = os.path.join(shots, name)
    automation.screenshot(path)
    return read_png(path, 440, 290)  # every count() box lies inside x < 440, y < 290 (exact crop)


def count(img, x0, y0, x1, y1, color, tol=12):
    """Pixels in the box within `tol` of `color` on every channel."""
    w, h, ch, px = img
    n = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            o = (y * w + x) * ch
            if all(abs(px[o + i] - color[i]) <= tol for i in range(3)):
                n += 1
    return n


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("FAIL:", msg)

print("=== UICaption Visual Test ===\n")

# Create test scene
test = mcrfpy.Scene("test")
mcrfpy.current_scene = test

# Create multiple captions for testing
caption1 = mcrfpy.Caption(pos=(50, 50), text="Caption 1: Normal", fill_color=mcrfpy.Color(255, 255, 255))
caption2 = mcrfpy.Caption(pos=(50, 100), text="Caption 2: Will be invisible", fill_color=mcrfpy.Color(255, 200, 200))
caption3 = mcrfpy.Caption(pos=(50, 150), text="Caption 3: 50% opacity", fill_color=mcrfpy.Color(200, 255, 200))
caption4 = mcrfpy.Caption(pos=(50, 200), text="Caption 4: 25% opacity", fill_color=mcrfpy.Color(200, 200, 255))
caption5 = mcrfpy.Caption(pos=(50, 250), text="Caption 5: 0% opacity", fill_color=mcrfpy.Color(255, 255, 200))

# Add captions to scene
ui = test.children
ui.append(caption1)
ui.append(caption2)
ui.append(caption3)
ui.append(caption4)
ui.append(caption5)

# Also add a frame as background to see transparency better
frame = mcrfpy.Frame(pos=(40, 40), size=(400, 250), fill_color=mcrfpy.Color(50, 50, 50))
frame.z_index = -1  # Put it behind the captions
ui.append(frame)

print("Scene setup complete. Running visual tests...")

# The frame was given z_index -1 before it was appended (last): it must still draw behind the
# captions (#552). Captions are told apart by their fill colours.
img = shot("caption_initial.png")
check(count(img, 50, 50, 330, 74, (255, 255, 255)) > 20, "caption1 (white) is not drawn over the frame")
check(count(img, 50, 100, 330, 124, (255, 200, 200)) > 20, "caption2 is not drawn over the frame")
check(count(img, 45, 45, 436, 286, (50, 50, 50)) > 1000, "the frame is not drawn at all")

# Test 1: Make caption2 invisible
print("Test 1: Making caption2 invisible")
caption2.visible = False
img = shot("caption_invisible.png")
check(count(img, 50, 100, 330, 124, (255, 200, 200)) == 0, "invisible caption2 still drew pixels")

# Test 2: Make caption2 visible again
print("Test 2: Making caption2 visible again")
caption2.visible = True
img = shot("caption_visible.png")
check(count(img, 50, 100, 330, 124, (255, 200, 200)) > 20, "visible caption2 drew nothing")

# Test 3: Set different opacity levels
print("Test 3: Testing opacity levels")

# Caption 3 at 50% opacity
caption3.opacity = 0.5
img = shot("caption_opacity_50.png")
check(count(img, 50, 150, 330, 174, (200, 255, 200)) == 0 and count(img, 50, 150, 330, 174, (125, 152, 125), 40) > 0,
      "caption3 at 50% opacity is not blended with the frame behind it")

# Caption 4 at 25% opacity
caption4.opacity = 0.25
img = shot("caption_opacity_25.png")

# Caption 5 at 0% opacity (fully transparent)
caption5.opacity = 0.0
img = shot("caption_opacity_0.png")
check(count(img, 50, 250, 330, 274, (255, 255, 200), 30) == 0, "caption5 at 0% opacity still drew pixels")

# Test 4: Move captions
print("Test 4: Testing move method")
caption1.move(100, 0)  # Move first caption right
caption2.move(0, 50)   # Move second caption down
img = shot("caption_moved.png")
check(count(img, 50, 50, 150, 74, (255, 255, 255)) == 0, "caption1 still drawn at its old position")
check(count(img, 150, 50, 430, 74, (255, 255, 255)) > 20, "caption1 not drawn at its new position")
check(count(img, 50, 100, 330, 124, (255, 200, 200)) == 0, "caption2 still drawn at its old position")
check(count(img, 50, 150, 330, 174, (255, 200, 200)) > 20, "caption2 not drawn at its new position")

print("\nVisual tests completed!")
print("Screenshots saved:")
print("  - caption_invisible.png")
print("  - caption_visible.png")
print("  - caption_opacity_50.png")
print("  - caption_opacity_25.png")
print("  - caption_opacity_0.png")
print("  - caption_moved.png")

if failures:
    sys.exit(1)
sys.exit(0)
