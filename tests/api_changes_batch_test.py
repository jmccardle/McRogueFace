#!/usr/bin/env python3
"""Test batch of API changes for issues #177, #179, #181, #182, #184, #185, #188, #189, #190"""
import sys
import mcrfpy

def test_issue_177_gridpoint_grid_pos():
    """Test GridPoint.grid_pos property returns tuple"""
    print("Testing #177: GridPoint.grid_pos property...")

    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=texture, pos=(0, 0), size=(160, 160))

    # Get a grid point
    point = grid.at(3, 5)

    # Test grid_pos property exists and returns tuple
    grid_pos = point.grid_pos
    assert isinstance(grid_pos, tuple), f"grid_pos should be tuple, got {type(grid_pos)}"
    assert len(grid_pos) == 2, f"grid_pos should have 2 elements, got {len(grid_pos)}"
    assert grid_pos == (3, 5), f"grid_pos should be (3, 5), got {grid_pos}"

    # Test another position
    point2 = grid.at(7, 2)
    assert point2.grid_pos == (7, 2), f"grid_pos should be (7, 2), got {point2.grid_pos}"

    print("  PASS: GridPoint.grid_pos works correctly")
    return True

def test_issue_179_181_grid_vectors():
    """Test Grid properties return Vectors instead of tuples"""
    print("Testing #179, #181: Grid Vector returns and grid_w/grid_h rename...")

    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(15, 20), texture=texture, pos=(50, 100), size=(240, 320))

    # Test center returns Vector
    center = grid.center
    assert hasattr(center, 'x') and hasattr(center, 'y'), f"center should be Vector, got {type(center)}"

    # Test grid_size returns Vector
    grid_size = grid.grid_size
    assert hasattr(grid_size, 'x') and hasattr(grid_size, 'y'), f"grid_size should be Vector, got {type(grid_size)}"
    assert grid_size.x == 15 and grid_size.y == 20, f"grid_size should be (15, 20), got ({grid_size.x}, {grid_size.y})"

    # Test pos returns Vector
    pos = grid.pos
    assert hasattr(pos, 'x') and hasattr(pos, 'y'), f"pos should be Vector, got {type(pos)}"

    print("  PASS: Grid properties return Vectors correctly")
    return True

def test_issue_182_caption_size():
    """Test Caption read-only size, w, h properties"""
    print("Testing #182: Caption read-only size/w/h properties...")

    font = mcrfpy.Font("assets/JetbrainsMono.ttf")
    caption = mcrfpy.Caption(text="Test Caption", pos=(100, 100), font=font)

    # Test size property
    size = caption.size
    assert hasattr(size, 'x') and hasattr(size, 'y'), f"size should be Vector, got {type(size)}"
    assert size.x > 0, f"width should be positive, got {size.x}"
    assert size.y > 0, f"height should be positive, got {size.y}"

    # Test w property
    w = caption.w
    assert isinstance(w, float), f"w should be float, got {type(w)}"
    assert w > 0, f"w should be positive, got {w}"

    # Test h property
    h = caption.h
    assert isinstance(h, float), f"h should be float, got {type(h)}"
    assert h > 0, f"h should be positive, got {h}"

    # Verify w and h match size
    assert abs(w - size.x) < 0.001, f"w ({w}) should match size.x ({size.x})"
    assert abs(h - size.y) < 0.001, f"h ({h}) should match size.y ({size.y})"

    # Verify read-only
    try:
        caption.size = mcrfpy.Vector(100, 100)
        print("  FAIL: size should be read-only")
        return False
    except AttributeError:
        pass  # Expected

    try:
        caption.w = 100
        print("  FAIL: w should be read-only")
        return False
    except AttributeError:
        pass  # Expected

    try:
        caption.h = 100
        print("  FAIL: h should be read-only")
        return False
    except AttributeError:
        pass  # Expected

    print("  PASS: Caption size/w/h properties work correctly")
    return True

def test_issue_184_189_module_namespace():
    """Test window singleton and hidden internal types"""
    print("Testing #184, #189: window singleton + hide classes...")

    # Test window singleton exists
    assert hasattr(mcrfpy, 'window'), "mcrfpy.window should exist"
    window = mcrfpy.window
    assert window is not None, "window should not be None"

    # Verify window properties
    assert hasattr(window, 'resolution'), "window should have resolution property"

    # Test that internal types are hidden from module namespace
    assert not hasattr(mcrfpy, 'UICollectionIter'), "UICollectionIter should be hidden from module namespace"
    assert not hasattr(mcrfpy, 'UIEntityCollectionIter'), "UIEntityCollectionIter should be hidden from module namespace"

    # But iteration should still work - test UICollection iteration
    scene = mcrfpy.Scene("test_scene")
    ui = scene.children
    ui.append(mcrfpy.Frame(pos=(0,0), size=(50,50)))
    ui.append(mcrfpy.Caption(text="hi", pos=(0,0)))

    count = 0
    for item in ui:
        count += 1
    assert count == 2, f"Should iterate over 2 items, got {count}"

    print("  PASS: window singleton and hidden types work correctly")
    return True

def test_issue_185_188_bounds_vectors():
    """Test bounds returns Vector pair, get_bounds() removed"""
    print("Testing #185, #188: Remove get_bounds(), bounds as Vector pair...")

    frame = mcrfpy.Frame(pos=(50, 100), size=(200, 150))

    # Test bounds returns tuple of Vectors
    bounds = frame.bounds
    assert isinstance(bounds, tuple), f"bounds should be tuple, got {type(bounds)}"
    assert len(bounds) == 2, f"bounds should have 2 elements, got {len(bounds)}"

    pos, size = bounds
    assert hasattr(pos, 'x') and hasattr(pos, 'y'), f"pos should be Vector, got {type(pos)}"
    assert hasattr(size, 'x') and hasattr(size, 'y'), f"size should be Vector, got {type(size)}"

    assert pos.x == 50 and pos.y == 100, f"pos should be (50, 100), got ({pos.x}, {pos.y})"
    assert size.x == 200 and size.y == 150, f"size should be (200, 150), got ({size.x}, {size.y})"

    # Test global_bounds also returns Vector pair
    global_bounds = frame.global_bounds
    assert isinstance(global_bounds, tuple), f"global_bounds should be tuple, got {type(global_bounds)}"
    assert len(global_bounds) == 2, f"global_bounds should have 2 elements"

    # Test get_bounds() method is removed (#185)
    assert not hasattr(frame, 'get_bounds'), "get_bounds() method should be removed"

    print("  PASS: bounds returns Vector pairs, get_bounds() removed")
    return True

def test_issue_190_layer_documentation():
    """Test that layer types have documentation"""
    print("Testing #190: TileLayer/ColorLayer documentation...")

    # Verify layer types exist and have docstrings
    assert hasattr(mcrfpy, 'TileLayer'), "TileLayer should exist"
    assert hasattr(mcrfpy, 'ColorLayer'), "ColorLayer should exist"

    # Check that docstrings exist and contain useful info
    tile_doc = mcrfpy.TileLayer.__doc__
    color_doc = mcrfpy.ColorLayer.__doc__

    assert tile_doc is not None and len(tile_doc) > 50, f"TileLayer should have substantial docstring, got: {tile_doc}"
    assert color_doc is not None and len(color_doc) > 50, f"ColorLayer should have substantial docstring, got: {color_doc}"

    # Check for key documentation elements
    assert "layer" in tile_doc.lower() or "tile" in tile_doc.lower(), "TileLayer doc should mention layer or tile"
    assert "layer" in color_doc.lower() or "color" in color_doc.lower(), "ColorLayer doc should mention layer or color"

    print("  PASS: Layer documentation exists")
    return True

def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("API Changes Batch Test - Issues #177, #179, #181, #182, #184, #185, #188, #189, #190")
    print("=" * 60)

    tests = [
        ("Issue #177 GridPoint.grid_pos", test_issue_177_gridpoint_grid_pos),
        ("Issue #179, #181 Grid Vectors", test_issue_179_181_grid_vectors),
        ("Issue #182 Caption size/w/h", test_issue_182_caption_size),
        ("Issue #184, #189 Module namespace", test_issue_184_189_module_namespace),
        ("Issue #185, #188 Bounds Vectors", test_issue_185_188_bounds_vectors),
        ("Issue #190 Layer documentation", test_issue_190_layer_documentation),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  FAILED: {name}")
        except Exception as e:
            failed += 1
            print(f"  ERROR in {name}: {e}")

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)

# Run tests
run_all_tests()
