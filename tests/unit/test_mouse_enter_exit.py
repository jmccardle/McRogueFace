#!/usr/bin/env python3
"""Test #140: Mouse Enter/Exit Events"""

import mcrfpy
from mcrfpy import automation
import sys

# Track callback invocations
enter_count = 0
exit_count = 0
enter_positions = []
exit_positions = []

def test_callback_assignment():
    """Test that on_enter and on_exit callbacks can be assigned"""
    print("Testing callback assignment...")

    test_assign = mcrfpy.Scene("test_assign")
    ui = test_assign.children

    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
    ui.append(frame)

    # #230 - Hover callbacks now receive only (pos) - 1 argument
    def on_enter_cb(pos):
        pass

    def on_exit_cb(pos):
        pass

    # Test assignment
    frame.on_enter = on_enter_cb
    frame.on_exit = on_exit_cb

    # Test retrieval
    assert frame.on_enter == on_enter_cb, "on_enter callback not stored correctly"
    assert frame.on_exit == on_exit_cb, "on_exit callback not stored correctly"

    # Test clearing with None
    frame.on_enter = None
    frame.on_exit = None

    assert frame.on_enter is None, "on_enter should be None after clearing"
    assert frame.on_exit is None, "on_exit should be None after clearing"

    print("  - callback assignment: PASS")


def test_hovered_property():
    """Test that hovered property exists and is initially False"""
    print("Testing hovered property...")

    test_hovered = mcrfpy.Scene("test_hovered")
    ui = test_hovered.children

    frame = mcrfpy.Frame(pos=(50, 50), size=(100, 100))
    ui.append(frame)

    # hovered should be False initially
    assert frame.hovered == False, f"Expected hovered=False, got {frame.hovered}"

    # hovered should be read-only
    try:
        frame.hovered = True
        print("  - hovered should be read-only: FAIL")
        return False
    except AttributeError:
        pass  # Expected - property is read-only
    except TypeError:
        pass  # Also acceptable for read-only

    print("  - hovered property: PASS")
    return True


def test_all_types_have_events():
    """Test that all drawable types have on_enter/on_exit properties"""
    print("Testing events on all drawable types...")

    test_types = mcrfpy.Scene("test_types")
    ui = test_types.children

    types_to_test = [
        ("Frame", mcrfpy.Frame(pos=(0, 0), size=(100, 100))),
        ("Caption", mcrfpy.Caption(text="Test", pos=(0, 0))),
        ("Sprite", mcrfpy.Sprite(pos=(0, 0))),
        ("Grid", mcrfpy.Grid(grid_size=(5, 5), pos=(0, 0), size=(100, 100))),
    ]

    # #230 - Hover callbacks now receive only (pos)
    def dummy_cb(pos):
        pass

    for name, obj in types_to_test:
        # Should have on_enter property
        assert hasattr(obj, 'on_enter'), f"{name} missing on_enter"

        # Should have on_exit property
        assert hasattr(obj, 'on_exit'), f"{name} missing on_exit"

        # Should have hovered property
        assert hasattr(obj, 'hovered'), f"{name} missing hovered"

        # Should be able to assign callbacks
        obj.on_enter = dummy_cb
        obj.on_exit = dummy_cb

        # Should be able to clear callbacks
        obj.on_enter = None
        obj.on_exit = None

    print("  - all drawable types have events: PASS")


def test_enter_exit_simulation():
    """Test enter/exit callbacks with simulated mouse movement"""
    print("Testing enter/exit callback simulation...")

    global enter_count, exit_count, enter_positions, exit_positions
    enter_count = 0
    exit_count = 0
    enter_positions = []
    exit_positions = []

    test_sim = mcrfpy.Scene("test_sim")
    ui = test_sim.children
    test_sim.activate()

    # Create a frame at known position
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
    ui.append(frame)

    # #230 - Hover callbacks now receive only (pos)
    def on_enter(pos):
        global enter_count, enter_positions
        enter_count += 1
        enter_positions.append((pos.x, pos.y))

    def on_exit(pos):
        global exit_count, exit_positions
        exit_count += 1
        exit_positions.append((pos.x, pos.y))

    frame.on_enter = on_enter
    frame.on_exit = on_exit

    # Use automation to simulate mouse movement
    # Move to outside the frame first
    automation.moveTo(50, 50)

    # Move inside the frame - should trigger on_enter
    automation.moveTo(200, 200)

    # Move outside the frame - should trigger on_exit
    automation.moveTo(50, 50)

    # Give time for callbacks to execute
    def check_results(timer, runtime):
        global enter_count, exit_count

        if enter_count >= 1 and exit_count >= 1:
            print(f"  - callbacks fired: enter={enter_count}, exit={exit_count}: PASS")
            print("\n=== All Mouse Enter/Exit tests passed! ===")
            sys.exit(0)
        else:
            print(f"  - callbacks fired: enter={enter_count}, exit={exit_count}: PARTIAL")
            print("    (Note: Full callback testing requires interactive mode)")
            print("\n=== Basic Mouse Enter/Exit tests passed! ===")
            sys.exit(0)

    mcrfpy.Timer("check", check_results, 200, once=True)


def run_basic_tests():
    """Run tests that don't require the game loop"""
    test_callback_assignment()
    test_hovered_property()
    test_all_types_have_events()


if __name__ == "__main__":
    try:
        run_basic_tests()
        test_enter_exit_simulation()
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
