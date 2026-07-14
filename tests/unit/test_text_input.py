#!/usr/bin/env python3
"""
Test the text input widget system

Exercises src/scripts/text_input_widget.py (FocusManager + TextInput) headlessly:
building the widgets into a scene, focus/blur, typing, editing keys, cursor
movement, placeholder visibility and on_change notifications.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', 'src', 'scripts'))

import mcrfpy
from text_input_widget import FocusManager, TextInput

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
        print(f"FAIL: {message}")
    return condition


# The TextInput widget speaks a string key protocol; the engine delivers
# mcrfpy.Key enums (#184). Translate at the scene handler, as a real game would.
KEY_NAMES = {
    mcrfpy.Key.BACKSPACE: "BackSpace",
    mcrfpy.Key.DELETE: "Delete",
    mcrfpy.Key.LEFT: "Left",
    mcrfpy.Key.RIGHT: "Right",
    mcrfpy.Key.HOME: "Home",
    mcrfpy.Key.END: "End",
    mcrfpy.Key.TAB: "Tab",
    mcrfpy.Key.ENTER: "Return",
    mcrfpy.Key.SPACE: " ",
}
for _letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    KEY_NAMES[getattr(mcrfpy.Key, _letter)] = _letter.lower()


def key_name(key):
    return KEY_NAMES.get(key, "Unknown")


def create_demo():
    """Create demo scene with text inputs; returns (scene, focus_mgr, inputs, status, on_key)"""
    # Create scene
    text_demo = mcrfpy.Scene("text_demo")
    scene = text_demo.children

    # Background
    bg = mcrfpy.Frame(pos=(0, 0), size=(800, 600))
    bg.fill_color = mcrfpy.Color(40, 40, 40, 255)
    scene.append(bg)

    # Title
    title = mcrfpy.Caption(pos=(20, 20), text="Text Input Widget Demo")
    title.fill_color = mcrfpy.Color(255, 255, 255, 255)
    scene.append(title)

    # Focus manager
    focus_mgr = FocusManager()

    # Create inputs
    inputs = []

    # Name input
    name_input = TextInput(50, 100, 300, label="Name:", placeholder="Enter your name")
    name_input._focus_manager = focus_mgr
    focus_mgr.register(name_input)
    name_input.add_to_scene(scene)
    inputs.append(name_input)

    # Email input
    email_input = TextInput(50, 160, 300, label="Email:", placeholder="user@example.com")
    email_input._focus_manager = focus_mgr
    focus_mgr.register(email_input)
    email_input.add_to_scene(scene)
    inputs.append(email_input)

    # Tags input
    tags_input = TextInput(50, 220, 400, label="Tags:", placeholder="comma, separated, tags")
    tags_input._focus_manager = focus_mgr
    focus_mgr.register(tags_input)
    tags_input.add_to_scene(scene)
    inputs.append(tags_input)

    # Comment input
    comment_input = TextInput(50, 280, 500, height=30, label="Comment:", placeholder="Add a comment...")
    comment_input._focus_manager = focus_mgr
    focus_mgr.register(comment_input)
    comment_input.add_to_scene(scene)
    inputs.append(comment_input)

    # Status display
    status = mcrfpy.Caption(pos=(50, 360), text="Ready for input...")
    status.fill_color = mcrfpy.Color(150, 255, 150, 255)
    scene.append(status)

    # Update handler
    def update_status(text=None):
        values = [inp.get_text() for inp in inputs]
        status.text = f"Data: {values[0]} | {values[1]} | {values[2]} | {values[3]}"

    # Set change handlers
    for inp in inputs:
        inp.on_change = update_status

    # Keyboard handler (#184: receives Key and InputState enums)
    def handle_keys(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if not focus_mgr.handle_key(key_name(key)):
            if key == mcrfpy.Key.TAB:
                focus_mgr.focus_next()
            elif key == mcrfpy.Key.ESCAPE:
                print("\nFinal values:")
                for i, inp in enumerate(inputs):
                    print(f"  Field {i+1}: '{inp.get_text()}'")

    text_demo.on_key = handle_keys
    text_demo.activate()

    return text_demo, focus_mgr, inputs, status, handle_keys


def press(handler, key):
    handler(key, mcrfpy.InputState.PRESSED)


def main():
    scene, focus_mgr, inputs, status, on_key = create_demo()

    print("\n=== Text Input Widget Test ===")

    # --- construction / registration ---
    check(len(focus_mgr.widgets) == 4, "four inputs registered with the focus manager")
    check(mcrfpy.current_scene is scene, "text_demo scene is active")

    # --- initial focus: first registered widget ---
    first, second = inputs[0], inputs[1]
    check(focus_mgr.focused_widget is first, "first input focused on registration")
    check(first.focused is True, "first input reports focused")
    check(first.cursor.visible is True, "focused input shows its cursor")
    check(second.cursor.visible is False, "unfocused input hides its cursor")
    check(second.placeholder_text.visible is True,
          "unfocused empty input shows placeholder")
    check(first.placeholder_text.visible is False,
          "focused input hides placeholder")

    # --- typing ---
    for key in (mcrfpy.Key.J, mcrfpy.Key.O, mcrfpy.Key.H, mcrfpy.Key.N):
        press(on_key, key)
    check(first.get_text() == "john", f"typing inserts text (got {first.get_text()!r})")
    check(first.cursor_pos == 4, f"cursor advances with typing (got {first.cursor_pos})")
    check(first.text_display.text == "john", "text display mirrors the text")
    check(status.text.startswith("Data: john |"),
          f"on_change updated the status caption (got {status.text!r})")

    # --- editing: backspace ---
    press(on_key, mcrfpy.Key.BACKSPACE)
    check(first.get_text() == "joh", f"backspace deletes before cursor (got {first.get_text()!r})")
    check(first.cursor_pos == 3, "backspace moves cursor back")

    # --- cursor movement: Home / Left / Right / End + insert at cursor ---
    press(on_key, mcrfpy.Key.HOME)
    check(first.cursor_pos == 0, "Home moves cursor to start")
    press(on_key, mcrfpy.Key.RIGHT)
    check(first.cursor_pos == 1, "Right moves cursor forward")
    press(on_key, mcrfpy.Key.LEFT)
    check(first.cursor_pos == 0, "Left moves cursor back")
    press(on_key, mcrfpy.Key.B)
    check(first.get_text() == "bjoh", f"insertion happens at the cursor (got {first.get_text()!r})")
    press(on_key, mcrfpy.Key.DELETE)
    check(first.get_text() == "boh", f"Delete removes character after cursor (got {first.get_text()!r})")
    press(on_key, mcrfpy.Key.END)
    check(first.cursor_pos == 3, "End moves cursor to the end")

    # --- Tab navigation: unhandled by widget, focuses next ---
    press(on_key, mcrfpy.Key.TAB)
    check(focus_mgr.focused_widget is second, "Tab focuses the next input")
    check(first.focused is False, "previous input blurred")
    check(first.cursor.visible is False, "blurred input hides its cursor")
    check(second.focused is True, "next input focused")
    check(first.placeholder_text.visible is False,
          "blurred but non-empty input keeps placeholder hidden")

    press(on_key, mcrfpy.Key.A)
    check(second.get_text() == "a", "typing goes to the newly focused input")
    check(first.get_text() == "boh", "previously focused input keeps its text")

    focus_mgr.focus_prev()
    check(focus_mgr.focused_widget is first, "focus_prev returns to the first input")

    # --- programmatic set_text / get_text ---
    inputs[3].set_text("hello world")
    check(inputs[3].get_text() == "hello world", "set_text sets the text")
    check(inputs[3].cursor_pos == len("hello world"), "set_text places cursor at end")
    check(inputs[3].text_display.text == "hello world", "set_text updates the display")
    check(inputs[3].placeholder_text.visible is False,
          "placeholder hidden once the field has text")

    # --- timer + render still work with the widgets in the scene ---
    fired = []
    mcrfpy.Timer("info", lambda t, rt: fired.append(rt), 100, once=True)
    for _ in range(4):
        mcrfpy.step(0.05)
    check(len(fired) == 1, f"one-shot timer fired exactly once (got {len(fired)})")

    mcrfpy.automation.screenshot("test_text_input.png")
    check(os.path.exists("test_text_input.png"), "scene with text inputs rendered")

    if failures:
        print(f"\nFAIL: {len(failures)} check(s) failed")
        sys.exit(1)
    print("\nPASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
