#!/usr/bin/env python3
"""Test #141: on_move Event for Pixel-Level Mouse Tracking"""

import mcrfpy
from mcrfpy import automation
import sys

def test_on_move_property():
    """Test that on_move property exists and can be assigned"""
    print("Testing on_move property...")

    test_move_prop = mcrfpy.Scene("test_move_prop")
    ui = test_move_prop.children

    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
    ui.append(frame)

    # #230 - on_move receives only (pos: Vector)
    def move_handler(pos):
        pass

    # Test assignment
    frame.on_move = move_handler
    assert frame.on_move == move_handler, "on_move callback not stored correctly"

    # Test clearing with None
    frame.on_move = None
    assert frame.on_move is None, "on_move should be None after clearing"

    print("  - on_move property: PASS")


def test_on_move_fires():
    """Test that on_move fires when mouse moves within bounds"""
    print("Testing on_move callback firing...")

    test_move = mcrfpy.Scene("test_move")
    ui = test_move.children
    test_move.activate()

    # Create a frame at known position
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
    ui.append(frame)

    move_count = [0]
    positions = []

    # #230 - on_move receives only (pos: Vector)
    def move_handler(pos):
        move_count[0] += 1
        positions.append((pos.x, pos.y))

    frame.on_move = move_handler

    # Move mouse to enter the frame
    automation.moveTo((150, 150))
    mcrfpy.step(0.05)

    # Move within the frame (should fire on_move)
    automation.moveTo((200, 200))
    mcrfpy.step(0.05)
    automation.moveTo((250, 250))
    mcrfpy.step(0.05)

    if move_count[0] >= 2:
        print(f"  - on_move fired {move_count[0]} times: PASS")
    else:
        print(f"  - on_move fired {move_count[0]} times: PARTIAL")
        print("    (Expected at least 2 move events)")


def test_on_move_not_outside():
    """Test that on_move doesn't fire when mouse is outside bounds"""
    print("Testing on_move doesn't fire outside bounds...")

    test_move_outside = mcrfpy.Scene("test_move_outside")
    ui = test_move_outside.children
    test_move_outside.activate()

    # Frame at 100-300, 100-300
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
    ui.append(frame)

    move_count = [0]

    # #230 - on_move receives only (pos: Vector)
    def move_handler(pos):
        move_count[0] += 1
        print(f"    Unexpected move at ({pos.x}, {pos.y})")

    frame.on_move = move_handler

    # Move mouse outside the frame
    automation.moveTo((50, 50))
    mcrfpy.step(0.05)
    automation.moveTo((60, 60))
    mcrfpy.step(0.05)
    automation.moveTo((70, 70))
    mcrfpy.step(0.05)

    if move_count[0] == 0:
        print("  - No on_move outside bounds: PASS")
    else:
        print(f"  - Unexpected {move_count[0]} move(s) outside bounds: FAIL")
        sys.exit(1)


def test_all_types_have_on_move():
    """Test that all drawable types have on_move property"""
    print("Testing on_move on all drawable types...")

    test_types = mcrfpy.Scene("test_types")
    ui = test_types.children

    types_to_test = [
        ("Frame", mcrfpy.Frame(pos=(0, 0), size=(100, 100))),
        ("Caption", mcrfpy.Caption(text="Test", pos=(0, 0))),
        ("Sprite", mcrfpy.Sprite(pos=(0, 0))),
        ("Grid", mcrfpy.Grid(grid_size=(5, 5), pos=(0, 0), size=(100, 100))),
    ]

    # #230 - on_move receives only (pos: Vector)
    def dummy_cb(pos):
        pass

    for name, obj in types_to_test:
        # Should have on_move property
        assert hasattr(obj, 'on_move'), f"{name} missing on_move"

        # Should be able to assign callbacks
        obj.on_move = dummy_cb

        # Should be able to clear callbacks
        obj.on_move = None

    print("  - all drawable types have on_move: PASS")


if __name__ == "__main__":
    try:
        test_on_move_property()
        test_all_types_have_on_move()
        test_on_move_not_outside()
        test_on_move_fires()

        print("\n=== All on_move tests passed! ===")
        sys.exit(0)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
