"""Test the alignment system for UIDrawable elements."""

import mcrfpy
import sys

# Test 1: Check Alignment enum exists and has expected values
print("Test 1: Checking Alignment enum...")
try:
    assert hasattr(mcrfpy, 'Alignment'), "Alignment enum not found"

    # Check all alignment values exist
    expected_alignments = [
        'TOP_LEFT', 'TOP_CENTER', 'TOP_RIGHT',
        'CENTER_LEFT', 'CENTER', 'CENTER_RIGHT',
        'BOTTOM_LEFT', 'BOTTOM_CENTER', 'BOTTOM_RIGHT'
    ]
    for name in expected_alignments:
        assert hasattr(mcrfpy.Alignment, name), f"Alignment.{name} not found"
    print("  PASS: Alignment enum has all expected values")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 2: Check that align property exists on Frame
print("Test 2: Checking align property on Frame...")
try:
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))

    # Default alignment should be None
    assert frame.align is None, f"Expected align=None, got {frame.align}"

    # Set alignment
    frame.align = mcrfpy.Alignment.CENTER
    assert frame.align == mcrfpy.Alignment.CENTER, f"Expected CENTER, got {frame.align}"

    # Set back to None
    frame.align = None
    assert frame.align is None, f"Expected None, got {frame.align}"
    print("  PASS: align property works on Frame")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 3: Check margin properties exist
print("Test 3: Checking margin properties...")
try:
    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))

    # Check default margins are 0
    assert frame.margin == 0, f"Expected margin=0, got {frame.margin}"
    assert frame.horiz_margin == 0, f"Expected horiz_margin=0, got {frame.horiz_margin}"
    assert frame.vert_margin == 0, f"Expected vert_margin=0, got {frame.vert_margin}"

    # Set margins when no alignment
    frame.margin = 10.0
    assert frame.margin == 10.0, f"Expected margin=10, got {frame.margin}"
    print("  PASS: margin properties exist and can be set")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 4: Check alignment auto-positioning
print("Test 4: Checking alignment auto-positioning...")
try:
    # Create parent frame
    parent = mcrfpy.Frame(pos=(0, 0), size=(200, 200))

    # Create child with CENTER alignment
    child = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
    child.align = mcrfpy.Alignment.CENTER

    # Add to parent - should trigger alignment
    parent.children.append(child)

    # Child should be centered: (200-50)/2 = 75
    expected_x = 75.0
    expected_y = 75.0
    assert abs(child.x - expected_x) < 0.1, f"Expected x={expected_x}, got {child.x}"
    assert abs(child.y - expected_y) < 0.1, f"Expected y={expected_y}, got {child.y}"
    print("  PASS: CENTER alignment positions child correctly")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 5: Check TOP_LEFT with margin
print("Test 5: Checking TOP_LEFT alignment with margin...")
try:
    parent = mcrfpy.Frame(pos=(0, 0), size=(200, 200))
    child = mcrfpy.Frame(pos=(999, 999), size=(50, 50))  # Start at wrong position
    child.align = mcrfpy.Alignment.TOP_LEFT
    child.margin = 10.0

    parent.children.append(child)

    # Child should be at (10, 10)
    assert abs(child.x - 10.0) < 0.1, f"Expected x=10, got {child.x}"
    assert abs(child.y - 10.0) < 0.1, f"Expected y=10, got {child.y}"
    print("  PASS: TOP_LEFT with margin positions correctly")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 6: Check BOTTOM_RIGHT alignment
print("Test 6: Checking BOTTOM_RIGHT alignment...")
try:
    parent = mcrfpy.Frame(pos=(0, 0), size=(200, 200))
    child = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
    child.align = mcrfpy.Alignment.BOTTOM_RIGHT
    child.margin = 5.0

    parent.children.append(child)

    # Child should be at (200-50-5, 200-50-5) = (145, 145)
    expected_x = 145.0
    expected_y = 145.0
    assert abs(child.x - expected_x) < 0.1, f"Expected x={expected_x}, got {child.x}"
    assert abs(child.y - expected_y) < 0.1, f"Expected y={expected_y}, got {child.y}"
    print("  PASS: BOTTOM_RIGHT with margin positions correctly")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 7: Check resize propagation
print("Test 7: Checking resize propagation to children...")
try:
    parent = mcrfpy.Frame(pos=(0, 0), size=(200, 200))
    child = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
    child.align = mcrfpy.Alignment.CENTER

    parent.children.append(child)

    # Initial position check
    assert abs(child.x - 75.0) < 0.1, f"Initial x should be 75, got {child.x}"

    # Resize parent
    parent.w = 300
    parent.h = 300

    # Child should be re-centered: (300-50)/2 = 125
    expected_x = 125.0
    expected_y = 125.0
    assert abs(child.x - expected_x) < 0.1, f"After resize, expected x={expected_x}, got {child.x}"
    assert abs(child.y - expected_y) < 0.1, f"After resize, expected y={expected_y}, got {child.y}"
    print("  PASS: Resize propagates to aligned children")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 8: Check that align=None freezes position
print("Test 8: Checking that align=None freezes position...")
try:
    parent = mcrfpy.Frame(pos=(0, 0), size=(200, 200))
    child = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
    child.align = mcrfpy.Alignment.CENTER

    parent.children.append(child)
    centered_x = child.x
    centered_y = child.y

    # Disable alignment
    child.align = None

    # Resize parent
    parent.w = 400
    parent.h = 400

    # Position should NOT change
    assert abs(child.x - centered_x) < 0.1, f"Position should be frozen at {centered_x}, got {child.x}"
    assert abs(child.y - centered_y) < 0.1, f"Position should be frozen at {centered_y}, got {child.y}"
    print("  PASS: align=None freezes position")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 9: Check CENTER alignment rejects margins
print("Test 9: Checking CENTER alignment rejects margins...")
try:
    frame = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
    frame.align = mcrfpy.Alignment.CENTER

    # Setting margin on CENTER should raise ValueError
    try:
        frame.margin = 10.0
        print("  FAIL: Expected ValueError for margin with CENTER alignment")
        sys.exit(1)
    except ValueError as e:
        pass  # Expected

    print("  PASS: CENTER alignment correctly rejects margin")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 10: Check alignment on other drawable types
print("Test 10: Checking alignment on Caption...")
try:
    parent = mcrfpy.Frame(pos=(0, 0), size=(200, 100))
    caption = mcrfpy.Caption(text="Test", pos=(0, 0))
    caption.align = mcrfpy.Alignment.CENTER

    parent.children.append(caption)

    # Caption should be roughly centered (exact position depends on text size)
    # Just verify it was moved from (0,0)
    assert caption.x > 0 or caption.y > 0, "Caption should have been repositioned"
    print("  PASS: Caption supports alignment")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

print("\n" + "=" * 40)
print("All alignment tests PASSED!")
print("=" * 40)
sys.exit(0)
