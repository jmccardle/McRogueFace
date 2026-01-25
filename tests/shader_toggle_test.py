#!/usr/bin/env python3
"""
Shader Toggle Test - Regression test for position corruption bug

Tests that toggling shader_enabled on and off does not corrupt frame position.
This was a bug similar to #223 where box.setPosition(0,0) during texture
rendering was never restored when switching back to standard rendering.
"""
import mcrfpy
import sys

scene = mcrfpy.Scene("toggle_test")
mcrfpy.current_scene = scene
ui = scene.children

# Background
bg = mcrfpy.Frame(pos=(0, 0), size=(800, 600), fill_color=(20, 20, 30, 255))
ui.append(bg)

# Create test frame at a specific position
test_frame = mcrfpy.Frame(
    pos=(200, 200),
    size=(150, 100),
    fill_color=(80, 120, 180, 255),
    outline_color=(255, 255, 255, 255),
    outline=3.0
)
label = mcrfpy.Caption(text="Test Frame", pos=(10, 10), font_size=14)
label.fill_color = (255, 255, 255, 255)
test_frame.children.append(label)
ui.append(test_frame)

# Status display
status = mcrfpy.Caption(text="Status: Initial", pos=(20, 20), font_size=16)
status.fill_color = (255, 255, 100, 255)
ui.append(status)

pos_display = mcrfpy.Caption(text="", pos=(20, 50), font_size=14)
pos_display.fill_color = (200, 200, 200, 255)
ui.append(pos_display)

instructions = mcrfpy.Caption(
    text="Press 1: Enable shader | 2: Disable shader | Q: Quit",
    pos=(20, 550), font_size=14
)
instructions.fill_color = (150, 150, 150, 255)
ui.append(instructions)

def update_display():
    pos_display.text = f"Position: ({test_frame.x}, {test_frame.y}) | Shader: {test_frame.shader_enabled}"

update_display()

test_count = 0

def on_key(key, state):
    global test_count
    if state != "start":
        return

    if key == "Num1" or key == "1":
        test_frame.shader_enabled = True
        status.text = "Status: Shader ENABLED"
        update_display()
        test_count += 1
    elif key == "Num2" or key == "2":
        test_frame.shader_enabled = False
        status.text = "Status: Shader DISABLED"
        update_display()
        test_count += 1

        # Check if position is still correct
        if test_frame.x != 200 or test_frame.y != 200:
            status.text = f"BUG! Position corrupted to ({test_frame.x}, {test_frame.y})"
            status.fill_color = (255, 100, 100, 255)
        else:
            status.text = "Status: Shader DISABLED - Position OK!"
            status.fill_color = (100, 255, 100, 255)
    elif key in ("Q", "Escape"):
        if test_frame.x == 200 and test_frame.y == 200:
            print(f"PASS: Position remained correct after {test_count} toggles")
        else:
            print(f"FAIL: Position corrupted to ({test_frame.x}, {test_frame.y})")
        sys.exit(0)

scene.on_key = on_key

print("Shader Toggle Test")
print("Press 1 to enable shader, 2 to disable, Q to quit")
print("Frame should stay at (200, 200) regardless of shader state")
