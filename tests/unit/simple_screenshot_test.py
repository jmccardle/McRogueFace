#!/usr/bin/env python3
"""Simple screenshot test to verify automation API"""

import mcrfpy
from mcrfpy import automation
import os
import sys

failures = []
fired = []

OUT_DIR = "test_screenshots"
GOOD_PATH = os.path.join(OUT_DIR, "test_screenshot.png")
BAD_PATH = os.path.join("no_such_dir_xyz", "test_screenshot.png")


def take_screenshot(timer, runtime):
    """Take screenshot after the timer fires"""
    print(f"Timer callback fired at runtime: {runtime}")
    fired.append(runtime)

    # A writable path must succeed and produce a real PNG file
    print(f"Trying to save to: {GOOD_PATH}")
    if automation.screenshot(GOOD_PATH) is not True:
        failures.append(f"screenshot({GOOD_PATH}) did not return True")
        return
    if not os.path.exists(GOOD_PATH):
        failures.append(f"screenshot reported success but {GOOD_PATH} does not exist")
        return
    size = os.path.getsize(GOOD_PATH)
    if size == 0:
        failures.append(f"{GOOD_PATH} is empty")
        return
    with open(GOOD_PATH, "rb") as f:
        magic = f.read(8)
    if magic != b"\x89PNG\r\n\x1a\n":
        failures.append(f"{GOOD_PATH} is not a PNG (magic={magic!r})")
        return
    print(f"Success: {GOOD_PATH} ({size} bytes)")

    # An unwritable path must fail cleanly (return False, no exception)
    print(f"Trying to save to: {BAD_PATH}")
    if automation.screenshot(BAD_PATH) is not False:
        failures.append(f"screenshot({BAD_PATH}) should have returned False")
        return
    print(f"Failed as expected: {BAD_PATH}")


# Create minimal scene
test = mcrfpy.Scene("test")

# Add a visible element (Caption.font is read-only as of #320 -- set it in the ctor)
caption = mcrfpy.Caption(pos=(100, 100), font=mcrfpy.default_font, text="Screenshot Test")
caption.fill_color = mcrfpy.Color(255, 255, 255)
caption.font_size = 24

test.children.append(caption)
test.activate()

os.makedirs(OUT_DIR, exist_ok=True)
if os.path.exists(GOOD_PATH):
    os.remove(GOOD_PATH)

# Timer fires at 500ms; headless has no clock of its own, so step() drives it (#350)
print("Setting timer...")
mcrfpy.Timer("screenshot", take_screenshot, 500, once=True)
print("Timer set, advancing the clock...")
for _ in range(20):  # 20 * 50ms = 1000ms > 500ms
    mcrfpy.step(0.05)
    if fired:
        break

if not fired:
    failures.append("timer never fired after 1000ms of stepping")

if failures:
    for f in failures:
        print(f"FAIL: {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
