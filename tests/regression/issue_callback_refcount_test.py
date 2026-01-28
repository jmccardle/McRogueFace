#!/usr/bin/env python3
"""Test for callback property reference counting fix.

This test verifies that accessing callback properties (on_click, on_enter, etc.)
returns correctly reference-counted objects, preventing use-after-free bugs.

The bug: Callback getters were returning borrowed references instead of new
references, causing objects to be freed prematurely when Python DECREFs them.
"""
import mcrfpy
import sys
import gc

def test_callback_refcount():
    """Test that callback getters return new references."""
    errors = []

    # Create a scene
    scene = mcrfpy.Scene("test_callback_refcount")

    # Test Frame
    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))

    # Set a callback
    def my_callback(pos, button, action):
        pass

    frame.on_click = my_callback

    # Read the callback back multiple times
    # If borrowing incorrectly, this could cause use-after-free
    for i in range(10):
        cb = frame.on_click
        if cb is None:
            errors.append(f"on_click returned None on iteration {i}")
            break
        if not callable(cb):
            errors.append(f"on_click returned non-callable on iteration {i}: {type(cb)}")
            break
        # Explicitly delete to trigger any refcount issues
        del cb
        gc.collect()

    # Final check - should still return the callback
    final_cb = frame.on_click
    if final_cb is None:
        errors.append("on_click returned None after repeated access")
    elif not callable(final_cb):
        errors.append(f"on_click returned non-callable after repeated access: {type(final_cb)}")

    # Test on_enter, on_exit, on_move
    # #230 - Hover callbacks now take only (pos)
    frame.on_enter = lambda pos: None
    frame.on_exit = lambda pos: None
    frame.on_move = lambda pos: None

    for name in ['on_enter', 'on_exit', 'on_move']:
        for i in range(5):
            cb = getattr(frame, name)
            if cb is None:
                errors.append(f"{name} returned None on iteration {i}")
                break
            del cb
        gc.collect()

    return errors


def test_grid_cell_callbacks():
    """Test Grid cell callback getters (these were already correct)."""
    errors = []

    grid = mcrfpy.Grid(pos=(0, 0), size=(100, 100), grid_size=(5, 5),
                       texture=mcrfpy.default_texture, zoom=1.0)

    grid.on_cell_enter = lambda pos: None
    grid.on_cell_exit = lambda pos: None
    grid.on_cell_click = lambda pos: None

    for name in ['on_cell_enter', 'on_cell_exit', 'on_cell_click']:
        for i in range(5):
            cb = getattr(grid, name)
            if cb is None:
                errors.append(f"{name} returned None on iteration {i}")
                break
            del cb
        gc.collect()

    return errors


def test_subclass_callback():
    """Test callback access on Python subclasses."""
    errors = []

    class MyFrame(mcrfpy.Frame):
        pass

    obj = MyFrame(pos=(0, 0), size=(100, 100))

    # Set callback via property
    obj.on_click = lambda pos, button, action: print("clicked")

    # Read back multiple times
    for i in range(5):
        cb = obj.on_click
        if cb is None:
            errors.append(f"Subclass on_click returned None on iteration {i}")
            break
        if not callable(cb):
            errors.append(f"Subclass on_click returned non-callable: {type(cb)}")
            break
        del cb
        gc.collect()

    return errors


def run_tests():
    """Run all callback refcount tests."""
    all_errors = []

    print("Testing callback property refcount...")
    errors = test_callback_refcount()
    if errors:
        all_errors.extend(errors)
        print(f"  FAIL: {len(errors)} errors")
    else:
        print("  PASS: on_click, on_enter, on_exit, on_move")

    print("Testing Grid cell callbacks...")
    errors = test_grid_cell_callbacks()
    if errors:
        all_errors.extend(errors)
        print(f"  FAIL: {len(errors)} errors")
    else:
        print("  PASS: on_cell_enter, on_cell_exit, on_cell_click")

    print("Testing subclass callbacks...")
    errors = test_subclass_callback()
    if errors:
        all_errors.extend(errors)
        print(f"  FAIL: {len(errors)} errors")
    else:
        print("  PASS: MyFrame(Frame) subclass")

    if all_errors:
        print(f"\nFAILED with {len(all_errors)} errors:")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\nAll callback refcount tests PASSED")
        sys.exit(0)


if __name__ == "__main__":
    run_tests()
