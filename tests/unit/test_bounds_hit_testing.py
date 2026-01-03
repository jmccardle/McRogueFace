#!/usr/bin/env python3
"""Test #138: AABB/Hit Testing System"""

import mcrfpy
import sys

def test_bounds_property():
    """Test bounds property returns correct local bounds"""
    print("Testing bounds property...")

    test_bounds = mcrfpy.Scene("test_bounds")
    ui = test_bounds.children

    frame = mcrfpy.Frame(pos=(50, 75), size=(200, 150))
    ui.append(frame)

    bounds = frame.bounds
    assert bounds[0] == 50.0, f"Expected x=50, got {bounds[0]}"
    assert bounds[1] == 75.0, f"Expected y=75, got {bounds[1]}"
    assert bounds[2] == 200.0, f"Expected w=200, got {bounds[2]}"
    assert bounds[3] == 150.0, f"Expected h=150, got {bounds[3]}"

    print("  - bounds property: PASS")


def test_global_bounds_no_parent():
    """Test global_bounds equals bounds when no parent"""
    print("Testing global_bounds without parent...")

    test_gb1 = mcrfpy.Scene("test_gb1")
    ui = test_gb1.children

    frame = mcrfpy.Frame(pos=(100, 100), size=(50, 50))
    ui.append(frame)

    bounds = frame.bounds
    global_bounds = frame.global_bounds

    assert bounds == global_bounds, f"Expected {bounds} == {global_bounds}"

    print("  - global_bounds (no parent): PASS")


def test_global_bounds_with_parent():
    """Test global_bounds correctly adds parent offset"""
    print("Testing global_bounds with parent...")

    test_gb2 = mcrfpy.Scene("test_gb2")
    ui = test_gb2.children

    parent = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
    ui.append(parent)

    child = mcrfpy.Frame(pos=(50, 50), size=(80, 60))
    parent.children.append(child)

    gb = child.global_bounds
    assert gb[0] == 150.0, f"Expected x=150, got {gb[0]}"
    assert gb[1] == 150.0, f"Expected y=150, got {gb[1]}"
    assert gb[2] == 80.0, f"Expected w=80, got {gb[2]}"
    assert gb[3] == 60.0, f"Expected h=60, got {gb[3]}"

    print("  - global_bounds (with parent): PASS")


def test_global_bounds_nested():
    """Test global_bounds with deeply nested hierarchy"""
    print("Testing global_bounds with nested hierarchy...")

    test_gb3 = mcrfpy.Scene("test_gb3")
    ui = test_gb3.children

    # Create 3-level hierarchy
    root = mcrfpy.Frame(pos=(10, 10), size=(300, 300))
    ui.append(root)

    middle = mcrfpy.Frame(pos=(20, 20), size=(200, 200))
    root.children.append(middle)

    leaf = mcrfpy.Frame(pos=(30, 30), size=(50, 50))
    middle.children.append(leaf)

    # leaf global pos should be 10+20+30 = 60, 60
    gb = leaf.global_bounds
    assert gb[0] == 60.0, f"Expected x=60, got {gb[0]}"
    assert gb[1] == 60.0, f"Expected y=60, got {gb[1]}"

    print("  - global_bounds (nested): PASS")


def test_all_drawable_types_have_bounds():
    """Test that all drawable types have bounds properties"""
    print("Testing bounds on all drawable types...")

    test_types = mcrfpy.Scene("test_types")
    ui = test_types.children

    types_to_test = [
        ("Frame", mcrfpy.Frame(pos=(0, 0), size=(100, 100))),
        ("Caption", mcrfpy.Caption(text="Test", pos=(0, 0))),
        ("Sprite", mcrfpy.Sprite(pos=(0, 0))),
        ("Grid", mcrfpy.Grid(grid_size=(5, 5), pos=(0, 0), size=(100, 100))),
    ]

    for name, obj in types_to_test:
        # Should have bounds property
        bounds = obj.bounds
        assert isinstance(bounds, tuple), f"{name}.bounds should be tuple"
        assert len(bounds) == 4, f"{name}.bounds should have 4 elements"

        # Should have global_bounds property
        gb = obj.global_bounds
        assert isinstance(gb, tuple), f"{name}.global_bounds should be tuple"
        assert len(gb) == 4, f"{name}.global_bounds should have 4 elements"

    print("  - all drawable types have bounds: PASS")


if __name__ == "__main__":
    try:
        test_bounds_property()
        test_global_bounds_no_parent()
        test_global_bounds_with_parent()
        test_global_bounds_nested()
        test_all_drawable_types_have_bounds()

        print("\n=== All AABB/Hit Testing tests passed! ===")
        sys.exit(0)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
