#!/usr/bin/env python3
"""Test to verify headless vs windowed mode behavior"""

import mcrfpy
import sys

# Create scene
mcrfpy.createScene("headless_test")
ui = mcrfpy.sceneUI("headless_test")
mcrfpy.setScene("headless_test")

# Create a visible indicator
frame = mcrfpy.Frame(pos=(200, 200), size=(400, 200))
frame.fill_color = mcrfpy.Color(100, 200, 100, 255)
ui.append(frame)

caption = mcrfpy.Caption(pos=(400, 300), text="If you see this, windowed mode is working!")
caption.font_size = 24
caption.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(caption)

print("Script started. Window should appear unless --headless was specified.")

# Exit after 2 seconds
def exit_test(runtime):
    print("Test complete. Exiting.")
    sys.exit(0)

mcrfpy.setTimer("exit", exit_test, 2000)