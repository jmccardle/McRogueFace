#!/usr/bin/env python3
"""
Test UIDrawable subclass callback methods (#184, #230)

This tests the ability to define callback methods (on_click, on_enter,
on_exit, on_move) directly in Python subclasses of UIDrawable types
(Frame, Caption, Sprite, Grid, Line, Circle, Arc).

Callback signatures:
- on_click: (pos: Vector, button: MouseButton, action: InputState)
- on_enter/on_exit/on_move: (pos: Vector) - #230: simplified to position-only
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
# Test 1: Basic Frame subclass with on_click method
# ==============================================================================
class ClickableFrame(mcrfpy.Frame):
    """Frame subclass with on_click method"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.click_count = 0
        self.last_click_args = None

    def on_click(self, pos, button, action):
        self.click_count += 1
        self.last_click_args = (pos, button, action)


# ==============================================================================
# Test 2: Frame subclass with all hover callbacks
# #230: Hover callbacks now take only (pos), not (pos, button, action)
# ==============================================================================
class HoverFrame(mcrfpy.Frame):
    """Frame subclass with on_enter, on_exit, on_move"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []

    def on_enter(self, pos):
        self.events.append(('enter', pos.x, pos.y))

    def on_exit(self, pos):
        self.events.append(('exit', pos.x, pos.y))

    def on_move(self, pos):
        self.events.append(('move', pos.x, pos.y))


# ==============================================================================
# Test 3: Caption subclass with on_click
# ==============================================================================
class ClickableCaption(mcrfpy.Caption):
    """Caption subclass with on_click method"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked = False

    def on_click(self, pos, button, action):
        self.clicked = True


# ==============================================================================
# Test 4: Sprite subclass with on_click
# ==============================================================================
class ClickableSprite(mcrfpy.Sprite):
    """Sprite subclass with on_click method"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked = False

    def on_click(self, pos, button, action):
        self.clicked = True


# ==============================================================================
# Test 5: Grid subclass with on_click
# ==============================================================================
class ClickableGrid(mcrfpy.Grid):
    """Grid subclass with on_click method"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked = False

    def on_click(self, pos, button, action):
        self.clicked = True


# ==============================================================================
# Test 6: Circle subclass
# ==============================================================================
class ClickableCircle(mcrfpy.Circle):
    """Circle subclass with callbacks"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked = False

    def on_click(self, pos, button, action):
        self.clicked = True


# ==============================================================================
# Test 7: Line subclass
# ==============================================================================
class ClickableLine(mcrfpy.Line):
    """Line subclass with callbacks"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked = False

    def on_click(self, pos, button, action):
        self.clicked = True


# ==============================================================================
# Test 8: Arc subclass
# ==============================================================================
class ClickableArc(mcrfpy.Arc):
    """Arc subclass with callbacks"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked = False

    def on_click(self, pos, button, action):
        self.clicked = True


# ==============================================================================
# Test 9: Property callback takes precedence over subclass method
# ==============================================================================
class FrameWithBoth(mcrfpy.Frame):
    """Frame with both property callback and method"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.method_called = False
        self.property_called = False

    def on_click(self, pos, button, action):
        self.method_called = True


# ==============================================================================
# Main test execution
# ==============================================================================
print("\n=== UIDrawable Subclass Callback Tests ===\n")

# Test 1: Verify ClickableFrame is detected as subclass
try:
    frame = ClickableFrame(pos=(100, 100), size=(100, 100))
    # The frame should be marked as a Python subclass internally
    # We verify this indirectly by checking the type relationship
    assert isinstance(frame, mcrfpy.Frame), "ClickableFrame should be instance of Frame"
    assert type(frame) is not mcrfpy.Frame, "ClickableFrame should be a subclass, not Frame itself"
    assert type(frame).__name__ == "ClickableFrame", f"Type name should be ClickableFrame, got {type(frame).__name__}"
    test_passed("ClickableFrame is properly subclassed")
except Exception as e:
    test_failed("ClickableFrame is properly subclassed", e)

# Test 2: Verify HoverFrame is detected as subclass
try:
    hover = HoverFrame(pos=(250, 100), size=(100, 100))
    assert isinstance(hover, mcrfpy.Frame), "HoverFrame should be instance of Frame"
    assert type(hover) is not mcrfpy.Frame, "HoverFrame should be a subclass"
    assert type(hover).__name__ == "HoverFrame", "Type name should be HoverFrame"
    test_passed("HoverFrame is properly subclassed")
except Exception as e:
    test_failed("HoverFrame is properly subclassed", e)

# Test 3: Verify ClickableCaption is detected as subclass
try:
    cap = ClickableCaption(text="Click Me", pos=(400, 100))
    assert isinstance(cap, mcrfpy.Caption), "ClickableCaption should be instance of Caption"
    assert type(cap) is not mcrfpy.Caption, "ClickableCaption should be a subclass"
    test_passed("ClickableCaption is properly subclassed")
except Exception as e:
    test_failed("ClickableCaption is properly subclassed", e)

# Test 4: Verify ClickableSprite is detected as subclass
try:
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    sprite = ClickableSprite(pos=(100, 200), texture=texture)
    assert isinstance(sprite, mcrfpy.Sprite), "ClickableSprite should be instance of Sprite"
    assert type(sprite) is not mcrfpy.Sprite, "ClickableSprite should be a subclass"
    test_passed("ClickableSprite is properly subclassed")
except Exception as e:
    test_failed("ClickableSprite is properly subclassed", e)

# Test 5: Verify ClickableGrid is detected as subclass
try:
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = ClickableGrid(grid_size=(5, 5), texture=texture, pos=(100, 250), size=(100, 100))
    assert isinstance(grid, mcrfpy.Grid), "ClickableGrid should be instance of Grid"
    assert type(grid) is not mcrfpy.Grid, "ClickableGrid should be a subclass"
    test_passed("ClickableGrid is properly subclassed")
except Exception as e:
    test_failed("ClickableGrid is properly subclassed", e)

# Test 6: Verify ClickableCircle is detected as subclass
try:
    circle = ClickableCircle(center=(250, 250), radius=50)
    assert isinstance(circle, mcrfpy.Circle), "ClickableCircle should be instance of Circle"
    assert type(circle) is not mcrfpy.Circle, "ClickableCircle should be a subclass"
    test_passed("ClickableCircle is properly subclassed")
except Exception as e:
    test_failed("ClickableCircle is properly subclassed", e)

# Test 7: Verify ClickableLine is detected as subclass
try:
    line = ClickableLine(start=(0, 0), end=(100, 100), thickness=5, color=mcrfpy.Color(255, 255, 255))
    assert isinstance(line, mcrfpy.Line), "ClickableLine should be instance of Line"
    assert type(line) is not mcrfpy.Line, "ClickableLine should be a subclass"
    test_passed("ClickableLine is properly subclassed")
except Exception as e:
    test_failed("ClickableLine is properly subclassed", e)

# Test 8: Verify ClickableArc is detected as subclass
try:
    arc = ClickableArc(center=(350, 250), radius=50, start_angle=0.0, end_angle=90.0, color=mcrfpy.Color(255, 255, 255))
    assert isinstance(arc, mcrfpy.Arc), "ClickableArc should be instance of Arc"
    assert type(arc) is not mcrfpy.Arc, "ClickableArc should be a subclass"
    test_passed("ClickableArc is properly subclassed")
except Exception as e:
    test_failed("ClickableArc is properly subclassed", e)

# Test 9: Test that base types don't have spurious is_python_subclass flag
try:
    base_frame = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
    assert type(base_frame) is mcrfpy.Frame, "Base Frame should be exactly Frame type"
    base_caption = mcrfpy.Caption(text="test", pos=(0, 0))
    assert type(base_caption) is mcrfpy.Caption, "Base Caption should be exactly Caption type"
    test_passed("Base types are NOT marked as subclasses")
except Exception as e:
    test_failed("Base types are NOT marked as subclasses", e)

# Test 10: Verify subclass methods are callable with typed arguments
try:
    frame = ClickableFrame(pos=(100, 100), size=(100, 100))
    # Verify method exists and is callable
    assert hasattr(frame, 'on_click'), "ClickableFrame should have on_click method"
    assert callable(frame.on_click), "on_click should be callable"
    # Manually call with proper typed objects to verify it works
    pos = mcrfpy.Vector(50.0, 50.0)
    button = mcrfpy.MouseButton.LEFT
    action = mcrfpy.InputState.PRESSED
    frame.on_click(pos, button, action)
    assert frame.click_count == 1, f"click_count should be 1, got {frame.click_count}"
    assert frame.last_click_args[0].x == 50.0, f"pos.x mismatch: {frame.last_click_args[0].x}"
    assert frame.last_click_args[0].y == 50.0, f"pos.y mismatch: {frame.last_click_args[0].y}"
    assert frame.last_click_args[1] == mcrfpy.MouseButton.LEFT, f"button mismatch: {frame.last_click_args[1]}"
    assert frame.last_click_args[2] == mcrfpy.InputState.PRESSED, f"action mismatch: {frame.last_click_args[2]}"
    test_passed("Subclass methods are callable and work")
except Exception as e:
    test_failed("Subclass methods are callable and work", e)

# Test 11: Verify HoverFrame methods work with typed arguments
# #230: Hover callbacks now take only (pos)
try:
    hover = HoverFrame(pos=(250, 100), size=(100, 100))
    hover.on_enter(mcrfpy.Vector(10.0, 20.0))
    hover.on_exit(mcrfpy.Vector(30.0, 40.0))
    hover.on_move(mcrfpy.Vector(50.0, 60.0))
    assert len(hover.events) == 3, f"Should have 3 events, got {len(hover.events)}"
    assert hover.events[0] == ('enter', 10.0, 20.0), f"Event mismatch: {hover.events[0]}"
    assert hover.events[1] == ('exit', 30.0, 40.0), f"Event mismatch: {hover.events[1]}"
    assert hover.events[2] == ('move', 50.0, 60.0), f"Event mismatch: {hover.events[2]}"
    test_passed("HoverFrame methods work correctly")
except Exception as e:
    test_failed("HoverFrame methods work correctly", e)

# Test 12: FrameWithBoth - verify property assignment works alongside method
try:
    both = FrameWithBoth(pos=(400, 250), size=(100, 100))
    property_was_called = [False]
    def property_callback(pos, btn, action):
        property_was_called[0] = True
    both.click = property_callback  # Assign to property
    # Property callback should be set
    assert both.click is not None, "click property should be set"
    # Method should still exist
    assert hasattr(both, 'on_click'), "on_click method should still exist"
    test_passed("FrameWithBoth allows both property and method")
except Exception as e:
    test_failed("FrameWithBoth allows both property and method", e)

# Test 13: Verify subclass instance attributes persist
try:
    frame = ClickableFrame(pos=(100, 100), size=(100, 100))
    frame.custom_attr = "test_value"
    assert frame.custom_attr == "test_value", "Custom attribute should persist"
    frame.on_click(mcrfpy.Vector(0, 0), mcrfpy.MouseButton.LEFT, mcrfpy.InputState.PRESSED)
    assert frame.click_count == 1, "Click count should be 1"
    # Verify frame is still usable after attribute access
    assert frame.x == 100, f"Frame x should be 100, got {frame.x}"
    test_passed("Subclass instance attributes persist")
except Exception as e:
    test_failed("Subclass instance attributes persist", e)

# Summary
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
