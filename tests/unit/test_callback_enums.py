#!/usr/bin/env python3
"""
Test unified callback signatures with enum types (#184)

This tests that all callbacks now use consistent typed arguments:
- Drawable callbacks: (pos: Vector, button: MouseButton, action: InputState)
- Grid cell callbacks: (cell_pos: Vector, button: MouseButton, action: InputState)
- Scene on_key: (key: Key, action: InputState)
"""
import mcrfpy
import sys

# Test results tracking
results = []

def test_passed(name):
    results.append((name, True, None))
    print(f"  PASS: {name}")

def test_failed(name, error):
    results.append((name, False, str(error)))
    print(f"  FAIL: {name}: {error}")


# ==============================================================================
# Test 1: Verify enum types exist and are accessible
# ==============================================================================
print("\n=== Callback Enum Signature Tests ===\n")

try:
    # Check MouseButton enum
    assert hasattr(mcrfpy, 'MouseButton'), "MouseButton enum should exist"
    assert hasattr(mcrfpy.MouseButton, 'LEFT'), "MouseButton.LEFT should exist"
    assert hasattr(mcrfpy.MouseButton, 'RIGHT'), "MouseButton.RIGHT should exist"

    # Check InputState enum
    assert hasattr(mcrfpy, 'InputState'), "InputState enum should exist"
    assert hasattr(mcrfpy.InputState, 'PRESSED'), "InputState.PRESSED should exist"
    assert hasattr(mcrfpy.InputState, 'RELEASED'), "InputState.RELEASED should exist"

    # Check Key enum
    assert hasattr(mcrfpy, 'Key'), "Key enum should exist"
    assert hasattr(mcrfpy.Key, 'A'), "Key.A should exist"
    assert hasattr(mcrfpy.Key, 'ESCAPE'), "Key.ESCAPE should exist"

    test_passed("Enum types exist and are accessible")
except Exception as e:
    test_failed("Enum types exist and are accessible", e)

# ==============================================================================
# Test 2: Grid cell callback with enum signature (subclass method)
# ==============================================================================
try:
    class GridWithCellCallbacks(mcrfpy.Grid):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.cell_events = []

        def on_cell_click(self, cell_pos, button, action):
            # Verify types
            assert isinstance(cell_pos, mcrfpy.Vector), f"cell_pos should be Vector, got {type(cell_pos)}"
            self.cell_events.append(('click', cell_pos.x, cell_pos.y, button, action))

        # #230 - Cell hover callbacks now only receive (cell_pos)
        def on_cell_enter(self, cell_pos):
            assert isinstance(cell_pos, mcrfpy.Vector), f"cell_pos should be Vector, got {type(cell_pos)}"
            self.cell_events.append(('enter', cell_pos.x, cell_pos.y))

        def on_cell_exit(self, cell_pos):
            assert isinstance(cell_pos, mcrfpy.Vector), f"cell_pos should be Vector, got {type(cell_pos)}"
            self.cell_events.append(('exit', cell_pos.x, cell_pos.y))

    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = GridWithCellCallbacks(grid_size=(5, 5), texture=texture, pos=(0, 0), size=(100, 100))

    # Verify grid is subclass
    assert isinstance(grid, mcrfpy.Grid), "Should be Grid instance"
    assert type(grid) is not mcrfpy.Grid, "Should be subclass"

    # Manually call methods to verify signature works
    grid.on_cell_click(mcrfpy.Vector(1.0, 2.0), mcrfpy.MouseButton.LEFT, mcrfpy.InputState.PRESSED)
    # #230 - Cell hover callbacks now only receive (cell_pos)
    grid.on_cell_enter(mcrfpy.Vector(3.0, 4.0))
    grid.on_cell_exit(mcrfpy.Vector(5.0, 6.0))

    assert len(grid.cell_events) == 3, f"Should have 3 events, got {len(grid.cell_events)}"
    assert grid.cell_events[0][0] == 'click', "First event should be click"
    assert grid.cell_events[1][0] == 'enter', "Second event should be enter"
    assert grid.cell_events[2][0] == 'exit', "Third event should be exit"

    test_passed("Grid subclass cell callbacks with enum signature")
except Exception as e:
    test_failed("Grid subclass cell callbacks with enum signature", e)

# ==============================================================================
# Test 3: Grid cell callback with property-assigned callable
# ==============================================================================
try:
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(5, 5), texture=texture, pos=(0, 0), size=(100, 100))

    cell_events = []

    def on_cell_click_handler(cell_pos, button, action):
        assert isinstance(cell_pos, mcrfpy.Vector), f"cell_pos should be Vector, got {type(cell_pos)}"
        cell_events.append(('click', cell_pos.x, cell_pos.y, button, action))

    grid.on_cell_click = on_cell_click_handler

    # Manually call to test (normally engine would call this)
    grid.on_cell_click(mcrfpy.Vector(1.0, 2.0), mcrfpy.MouseButton.LEFT, mcrfpy.InputState.PRESSED)

    assert len(cell_events) == 1, f"Should have 1 event, got {len(cell_events)}"
    assert cell_events[0][3] == mcrfpy.MouseButton.LEFT, "Button should be MouseButton.LEFT"
    assert cell_events[0][4] == mcrfpy.InputState.PRESSED, "Action should be InputState.PRESSED"

    test_passed("Grid property cell callback with enum signature")
except Exception as e:
    test_failed("Grid property cell callback with enum signature", e)

# ==============================================================================
# Test 4: Scene on_key callback with enum signature (subclass method)
# ==============================================================================
try:
    class MyScene(mcrfpy.Scene):
        def __init__(self, name):
            super().__init__(name)
            self.key_events = []

        def on_key(self, key, action):
            # Verify types - key should be Key enum, action should be InputState enum
            self.key_events.append((key, action))

    scene = MyScene("test_key_enum_scene")

    # Manually call to test signature (normally engine would call this)
    scene.on_key(mcrfpy.Key.A, mcrfpy.InputState.PRESSED)
    scene.on_key(mcrfpy.Key.ESCAPE, mcrfpy.InputState.RELEASED)

    assert len(scene.key_events) == 2, f"Should have 2 events, got {len(scene.key_events)}"
    assert scene.key_events[0][0] == mcrfpy.Key.A, f"First key should be Key.A, got {scene.key_events[0][0]}"
    assert scene.key_events[0][1] == mcrfpy.InputState.PRESSED, f"First action should be PRESSED"
    assert scene.key_events[1][0] == mcrfpy.Key.ESCAPE, f"Second key should be Key.ESCAPE"
    assert scene.key_events[1][1] == mcrfpy.InputState.RELEASED, f"Second action should be RELEASED"

    test_passed("Scene subclass on_key with enum signature")
except Exception as e:
    test_failed("Scene subclass on_key with enum signature", e)

# ==============================================================================
# Test 5: Scene on_key callback with property-assigned callable
# ==============================================================================
try:
    scene = mcrfpy.Scene("test_key_prop_scene")

    key_events = []

    def on_key_handler(key, action):
        key_events.append((key, action))

    scene.on_key = on_key_handler

    # Manually call to test (normally engine would call this via the callable)
    scene.on_key(mcrfpy.Key.SPACE, mcrfpy.InputState.PRESSED)

    assert len(key_events) == 1, f"Should have 1 event, got {len(key_events)}"
    # Note: When calling directly on Python side, we pass enums directly
    # The engine conversion happens internally when calling through C++

    test_passed("Scene property on_key accepts enum args")
except Exception as e:
    test_failed("Scene property on_key accepts enum args", e)

# ==============================================================================
# Test 6: Verify MouseButton enum values
# ==============================================================================
try:
    # Verify the enum values are usable in comparisons
    left = mcrfpy.MouseButton.LEFT
    right = mcrfpy.MouseButton.RIGHT

    assert left != right, "LEFT should not equal RIGHT"
    assert left == mcrfpy.MouseButton.LEFT, "LEFT should equal itself"

    # Verify we can use in conditions
    def check_button(button):
        if button == mcrfpy.MouseButton.LEFT:
            return "left"
        elif button == mcrfpy.MouseButton.RIGHT:
            return "right"
        return "other"

    assert check_button(mcrfpy.MouseButton.LEFT) == "left"
    assert check_button(mcrfpy.MouseButton.RIGHT) == "right"

    test_passed("MouseButton enum values work correctly")
except Exception as e:
    test_failed("MouseButton enum values work correctly", e)

# ==============================================================================
# Test 7: Verify InputState enum values
# ==============================================================================
try:
    pressed = mcrfpy.InputState.PRESSED
    released = mcrfpy.InputState.RELEASED

    assert pressed != released, "PRESSED should not equal RELEASED"
    assert pressed == mcrfpy.InputState.PRESSED, "PRESSED should equal itself"

    test_passed("InputState enum values work correctly")
except Exception as e:
    test_failed("InputState enum values work correctly", e)

# ==============================================================================
# Test 8: Verify Key enum values
# ==============================================================================
try:
    a_key = mcrfpy.Key.A
    esc_key = mcrfpy.Key.ESCAPE

    assert a_key != esc_key, "A should not equal ESCAPE"
    assert a_key == mcrfpy.Key.A, "A should equal itself"

    # Verify various keys exist
    assert hasattr(mcrfpy.Key, 'SPACE'), "SPACE should exist"
    assert hasattr(mcrfpy.Key, 'ENTER'), "ENTER should exist"
    assert hasattr(mcrfpy.Key, 'UP'), "UP should exist"
    assert hasattr(mcrfpy.Key, 'DOWN'), "DOWN should exist"

    test_passed("Key enum values work correctly")
except Exception as e:
    test_failed("Key enum values work correctly", e)

# ==============================================================================
# Summary
# ==============================================================================
print("\n=== Test Summary ===")
passed = sum(1 for _, p, _ in results if p)
total = len(results)
print(f"Passed: {passed}/{total}")

if passed == total:
    print("\nAll tests passed!")
    sys.exit(0)
else:
    print("\nSome tests failed:")
    for name, p, err in results:
        if not p:
            print(f"  - {name}: {err}")
    sys.exit(1)
