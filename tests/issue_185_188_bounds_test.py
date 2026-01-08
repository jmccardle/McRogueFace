"""Test for issues #185 and #188: bounds handling changes.

Issue #185: Remove .get_bounds() method - redundant with .bounds property
Issue #188: Change .bounds and .global_bounds to return (pos, size) as pair of Vectors
"""
import mcrfpy
import sys

def test_bounds():
    """Test that bounds returns (Vector, Vector) tuple."""
    print("Testing bounds format...")

    # Create a Frame with known position and size
    frame = mcrfpy.Frame(pos=(100, 200), size=(300, 400))
    bounds = frame.bounds

    # Should be a tuple of 2 elements
    assert isinstance(bounds, tuple), f"Expected tuple, got {type(bounds)}"
    assert len(bounds) == 2, f"Expected 2 elements, got {len(bounds)}"

    pos, size = bounds

    # Check that pos is a Vector with correct values
    assert isinstance(pos, mcrfpy.Vector), f"Expected Vector for pos, got {type(pos)}"
    assert pos.x == 100, f"Expected pos.x=100, got {pos.x}"
    assert pos.y == 200, f"Expected pos.y=200, got {pos.y}"

    # Check that size is a Vector with correct values
    assert isinstance(size, mcrfpy.Vector), f"Expected Vector for size, got {type(size)}"
    assert size.x == 300, f"Expected size.x=300, got {size.x}"
    assert size.y == 400, f"Expected size.y=400, got {size.y}"

    print("  Frame bounds: PASS")

def test_global_bounds():
    """Test that global_bounds returns (Vector, Vector) tuple."""
    print("Testing global_bounds format...")

    frame = mcrfpy.Frame(pos=(50, 75), size=(150, 250))
    global_bounds = frame.global_bounds

    # Should be a tuple of 2 elements
    assert isinstance(global_bounds, tuple), f"Expected tuple, got {type(global_bounds)}"
    assert len(global_bounds) == 2, f"Expected 2 elements, got {len(global_bounds)}"

    pos, size = global_bounds
    assert isinstance(pos, mcrfpy.Vector), f"Expected Vector for pos, got {type(pos)}"
    assert isinstance(size, mcrfpy.Vector), f"Expected Vector for size, got {type(size)}"

    print("  Frame global_bounds: PASS")

def test_get_bounds_removed():
    """Test that get_bounds() method has been removed."""
    print("Testing get_bounds removal...")

    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    assert not hasattr(frame, 'get_bounds'), "get_bounds method should be removed"

    print("  get_bounds removed: PASS")

def test_caption_bounds():
    """Test bounds on Caption."""
    print("Testing Caption bounds...")

    caption = mcrfpy.Caption(text="Test", pos=(25, 50))
    bounds = caption.bounds

    assert isinstance(bounds, tuple), f"Expected tuple, got {type(bounds)}"
    assert len(bounds) == 2, f"Expected 2 elements, got {len(bounds)}"

    pos, size = bounds
    assert isinstance(pos, mcrfpy.Vector), f"Expected Vector for pos, got {type(pos)}"
    assert isinstance(size, mcrfpy.Vector), f"Expected Vector for size, got {type(size)}"

    # Caption should not have get_bounds
    assert not hasattr(caption, 'get_bounds'), "get_bounds method should be removed from Caption"

    print("  Caption bounds: PASS")

def test_sprite_bounds():
    """Test bounds on Sprite."""
    print("Testing Sprite bounds...")

    sprite = mcrfpy.Sprite(pos=(10, 20))
    bounds = sprite.bounds

    assert isinstance(bounds, tuple), f"Expected tuple, got {type(bounds)}"
    assert len(bounds) == 2, f"Expected 2 elements, got {len(bounds)}"

    pos, size = bounds
    assert isinstance(pos, mcrfpy.Vector), f"Expected Vector for pos, got {type(pos)}"
    assert isinstance(size, mcrfpy.Vector), f"Expected Vector for size, got {type(size)}"

    # Sprite should not have get_bounds
    assert not hasattr(sprite, 'get_bounds'), "get_bounds method should be removed from Sprite"

    print("  Sprite bounds: PASS")

# Run tests
print("=" * 60)
print("Testing Issues #185 and #188: Bounds Handling")
print("=" * 60)

try:
    test_bounds()
    test_global_bounds()
    test_get_bounds_removed()
    test_caption_bounds()
    test_sprite_bounds()

    print("=" * 60)
    print("All tests PASSED!")
    print("=" * 60)
    sys.exit(0)
except AssertionError as e:
    print(f"FAILED: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
