#!/usr/bin/env python3
"""Test Key, MouseButton, and InputState enum functionality.

Tests the input-related enums that provide type-safe key codes,
mouse buttons, and event states. Legacy string comparison was
removed in #306 -- these enums now use standard IntEnum comparison.
"""

import mcrfpy
import sys


def test_key_enum():
    """Test Key enum members and int values."""
    print("Testing Key enum...")

    # Test that enum exists and has expected members
    assert hasattr(mcrfpy, 'Key'), "mcrfpy.Key should exist"
    assert hasattr(mcrfpy.Key, 'A'), "Key.A should exist"
    assert hasattr(mcrfpy.Key, 'ESCAPE'), "Key.ESCAPE should exist"
    assert hasattr(mcrfpy.Key, 'LEFT_SHIFT'), "Key.LEFT_SHIFT should exist"

    # Test int values
    assert int(mcrfpy.Key.A) == 0, "Key.A should be 0"
    assert int(mcrfpy.Key.ESCAPE) == 36, "Key.ESCAPE should be 36"

    # Test enum self-comparison
    assert mcrfpy.Key.ESCAPE == mcrfpy.Key.ESCAPE, "Key.ESCAPE should equal itself"
    assert mcrfpy.Key.A != mcrfpy.Key.ESCAPE, "Key.A should not equal Key.ESCAPE"

    # Verify legacy string comparison is removed (#306)
    assert not (mcrfpy.Key.ESCAPE == "Escape"), "Legacy string comparison should be removed"
    assert not (mcrfpy.Key.A == "A"), "Legacy string comparison should be removed"

    print("  All Key tests passed")


def test_mouse_button_enum():
    """Test MouseButton enum members."""
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

    # Test enum self-comparison
    assert mcrfpy.MouseButton.LEFT == mcrfpy.MouseButton.LEFT
    assert mcrfpy.MouseButton.LEFT != mcrfpy.MouseButton.RIGHT

    # Verify legacy string comparison is removed (#306)
    assert not (mcrfpy.MouseButton.LEFT == "left"), "Legacy string comparison should be removed"
    assert not (mcrfpy.MouseButton.RIGHT == "right"), "Legacy string comparison should be removed"

    print("  All MouseButton tests passed")


def test_input_state_enum():
    """Test InputState enum members."""
    print("Testing InputState enum...")

    # Test that enum exists and has expected members
    assert hasattr(mcrfpy, 'InputState'), "mcrfpy.InputState should exist"
    assert hasattr(mcrfpy.InputState, 'PRESSED'), "InputState.PRESSED should exist"
    assert hasattr(mcrfpy.InputState, 'RELEASED'), "InputState.RELEASED should exist"

    # Test int values
    assert int(mcrfpy.InputState.PRESSED) == 0, "InputState.PRESSED should be 0"
    assert int(mcrfpy.InputState.RELEASED) == 1, "InputState.RELEASED should be 1"

    # Test enum self-comparison
    assert mcrfpy.InputState.PRESSED == mcrfpy.InputState.PRESSED
    assert mcrfpy.InputState.PRESSED != mcrfpy.InputState.RELEASED

    # Verify legacy string comparison is removed (#306)
    assert not (mcrfpy.InputState.PRESSED == "start"), "Legacy string comparison should be removed"
    assert not (mcrfpy.InputState.RELEASED == "end"), "Legacy string comparison should be removed"

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
