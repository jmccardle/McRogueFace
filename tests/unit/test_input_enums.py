#!/usr/bin/env python3
"""Test Key, MouseButton, and InputState enum functionality.

Tests the new input-related enums that provide type-safe alternatives to
string-based key codes, mouse buttons, and event states.
"""

import mcrfpy
import sys


def test_key_enum():
    """Test Key enum members and backwards compatibility."""
    print("Testing Key enum...")

    # Test that enum exists and has expected members
    assert hasattr(mcrfpy, 'Key'), "mcrfpy.Key should exist"
    assert hasattr(mcrfpy.Key, 'A'), "Key.A should exist"
    assert hasattr(mcrfpy.Key, 'ESCAPE'), "Key.ESCAPE should exist"
    assert hasattr(mcrfpy.Key, 'LEFT_SHIFT'), "Key.LEFT_SHIFT should exist"

    # Test int values
    assert int(mcrfpy.Key.A) == 0, "Key.A should be 0"
    assert int(mcrfpy.Key.ESCAPE) == 36, "Key.ESCAPE should be 36"

    # Test backwards compatibility with legacy strings
    assert mcrfpy.Key.A == "A", "Key.A should equal 'A'"
    assert mcrfpy.Key.ESCAPE == "Escape", "Key.ESCAPE should equal 'Escape'"
    assert mcrfpy.Key.LEFT_SHIFT == "LShift", "Key.LEFT_SHIFT should equal 'LShift'"
    assert mcrfpy.Key.RIGHT_CONTROL == "RControl", "Key.RIGHT_CONTROL should equal 'RControl'"
    assert mcrfpy.Key.NUM_1 == "Num1", "Key.NUM_1 should equal 'Num1'"
    assert mcrfpy.Key.NUMPAD_5 == "Numpad5", "Key.NUMPAD_5 should equal 'Numpad5'"
    assert mcrfpy.Key.F12 == "F12", "Key.F12 should equal 'F12'"
    assert mcrfpy.Key.SPACE == "Space", "Key.SPACE should equal 'Space'"

    # Test that enum name also matches
    assert mcrfpy.Key.ESCAPE == "ESCAPE", "Key.ESCAPE should also equal 'ESCAPE'"

    print("  All Key tests passed")


def test_mouse_button_enum():
    """Test MouseButton enum members and backwards compatibility."""
    print("Testing MouseButton enum...")

    # Test that enum exists and has expected members
    assert hasattr(mcrfpy, 'MouseButton'), "mcrfpy.MouseButton should exist"
    assert hasattr(mcrfpy.MouseButton, 'LEFT'), "MouseButton.LEFT should exist"
    assert hasattr(mcrfpy.MouseButton, 'RIGHT'), "MouseButton.RIGHT should exist"
    assert hasattr(mcrfpy.MouseButton, 'MIDDLE'), "MouseButton.MIDDLE should exist"

    # Test int values
    assert int(mcrfpy.MouseButton.LEFT) == 0, "MouseButton.LEFT should be 0"
    assert int(mcrfpy.MouseButton.RIGHT) == 1, "MouseButton.RIGHT should be 1"
    assert int(mcrfpy.MouseButton.MIDDLE) == 2, "MouseButton.MIDDLE should be 2"

    # Test backwards compatibility with legacy strings
    assert mcrfpy.MouseButton.LEFT == "left", "MouseButton.LEFT should equal 'left'"
    assert mcrfpy.MouseButton.RIGHT == "right", "MouseButton.RIGHT should equal 'right'"
    assert mcrfpy.MouseButton.MIDDLE == "middle", "MouseButton.MIDDLE should equal 'middle'"
    assert mcrfpy.MouseButton.X1 == "x1", "MouseButton.X1 should equal 'x1'"
    assert mcrfpy.MouseButton.X2 == "x2", "MouseButton.X2 should equal 'x2'"

    # Test that enum name also matches
    assert mcrfpy.MouseButton.LEFT == "LEFT", "MouseButton.LEFT should also equal 'LEFT'"

    print("  All MouseButton tests passed")


def test_input_state_enum():
    """Test InputState enum members and backwards compatibility."""
    print("Testing InputState enum...")

    # Test that enum exists and has expected members
    assert hasattr(mcrfpy, 'InputState'), "mcrfpy.InputState should exist"
    assert hasattr(mcrfpy.InputState, 'PRESSED'), "InputState.PRESSED should exist"
    assert hasattr(mcrfpy.InputState, 'RELEASED'), "InputState.RELEASED should exist"

    # Test int values
    assert int(mcrfpy.InputState.PRESSED) == 0, "InputState.PRESSED should be 0"
    assert int(mcrfpy.InputState.RELEASED) == 1, "InputState.RELEASED should be 1"

    # Test backwards compatibility with legacy strings
    assert mcrfpy.InputState.PRESSED == "start", "InputState.PRESSED should equal 'start'"
    assert mcrfpy.InputState.RELEASED == "end", "InputState.RELEASED should equal 'end'"

    # Test that enum name also matches
    assert mcrfpy.InputState.PRESSED == "PRESSED", "InputState.PRESSED should also equal 'PRESSED'"
    assert mcrfpy.InputState.RELEASED == "RELEASED", "InputState.RELEASED should also equal 'RELEASED'"

    print("  All InputState tests passed")


def test_enum_repr():
    """Test that enum repr/str work correctly."""
    print("Testing enum repr/str...")

    # Test repr
    assert "Key.ESCAPE" in repr(mcrfpy.Key.ESCAPE), f"repr should contain 'Key.ESCAPE', got {repr(mcrfpy.Key.ESCAPE)}"
    assert "MouseButton.LEFT" in repr(mcrfpy.MouseButton.LEFT), f"repr should contain 'MouseButton.LEFT'"
    assert "InputState.PRESSED" in repr(mcrfpy.InputState.PRESSED), f"repr should contain 'InputState.PRESSED'"

    # Test str
    assert str(mcrfpy.Key.ESCAPE) == "ESCAPE", f"str(Key.ESCAPE) should be 'ESCAPE', got {str(mcrfpy.Key.ESCAPE)}"
    assert str(mcrfpy.MouseButton.LEFT) == "LEFT", f"str(MouseButton.LEFT) should be 'LEFT'"
    assert str(mcrfpy.InputState.PRESSED) == "PRESSED", f"str(InputState.PRESSED) should be 'PRESSED'"

    print("  All repr/str tests passed")


def main():
    """Run all enum tests."""
    print("=" * 50)
    print("Input Enum Unit Tests")
    print("=" * 50)

    try:
        test_key_enum()
        test_mouse_button_enum()
        test_input_state_enum()
        test_enum_repr()

        print()
        print("=" * 50)
        print("All tests PASSED")
        print("=" * 50)
        sys.exit(0)

    except AssertionError as e:
        print(f"\nTest FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
