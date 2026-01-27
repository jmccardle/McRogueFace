#!/usr/bin/env python3
"""Minimal reproduction of segfault when calling subclass method callback.

The issue: When a Frame subclass assigns self.on_click = self._on_click,
reading it back works but there's a segfault during cleanup.
"""
import mcrfpy
import sys
import gc

class MyFrame(mcrfpy.Frame):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.on_click = self._on_click

    def _on_click(self, pos, button, action):
        print(f"Clicked at {pos}, button={button}, action={action}")


def test_minimal():
    """Minimal test case."""
    print("Creating MyFrame...")
    obj = MyFrame(pos=(100, 100), size=(100, 100))

    print(f"Reading on_click: {obj.on_click}")
    print(f"Type: {type(obj.on_click)}")

    print("Attempting to call on_click...")
    try:
        obj.on_click((50, 50), "left", "start")
        print("Call succeeded!")
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")

    print("Clearing callback...")
    obj.on_click = None

    print("Deleting object...")
    del obj

    print("Running GC...")
    gc.collect()

    print("About to exit...")
    sys.exit(0)


def test_without_callback_clear():
    """Test without clearing callback first."""
    print("Creating MyFrame...")
    obj = MyFrame(pos=(100, 100), size=(100, 100))

    print("Calling...")
    obj.on_click((50, 50), "left", "start")

    print("Deleting without clearing callback...")
    del obj
    gc.collect()

    print("About to exit...")
    sys.exit(0)


def test_added_to_scene():
    """Test when added to scene."""
    print("Creating scene and MyFrame...")
    scene = mcrfpy.Scene("test")
    obj = MyFrame(pos=(100, 100), size=(100, 100))
    scene.children.append(obj)

    print("Calling via scene.children[0]...")
    scene.children[0].on_click((50, 50), "left", "start")

    print("About to exit...")
    sys.exit(0)


if __name__ == "__main__":
    # Try different scenarios
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "2":
            test_without_callback_clear()
        elif sys.argv[1] == "3":
            test_added_to_scene()
    else:
        test_minimal()
