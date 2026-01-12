"""Unit tests for BSP (Binary Space Partitioning) procedural generation.

Tests for issues #202-#206:
- #202: BSP core class with splitting
- #203: BSPNode lightweight node reference
- #204: BSP iteration (leaves, traverse) with Traversal enum
- #205: BSP query methods (find)
- #206: BSP.to_heightmap (returns HeightMap; BSPMap subclass deferred)
"""
import sys
import mcrfpy

def test_bsp_construction():
    """Test BSP construction with bounds."""
    print("Testing BSP construction...")

    # Basic construction
    bsp = mcrfpy.BSP(bounds=((0, 0), (100, 80)))
    assert bsp is not None, "BSP should be created"

    # Check bounds property
    bounds = bsp.bounds
    assert bounds == ((0, 0), (100, 80)), f"Bounds should be ((0, 0), (100, 80)), got {bounds}"

    # Check root property
    root = bsp.root
    assert root is not None, "Root should not be None"
    assert root.bounds == ((0, 0), (100, 80)), f"Root bounds mismatch"

    # Construction with offset
    bsp2 = mcrfpy.BSP(bounds=((10, 20), (50, 40)))
    assert bsp2.bounds == ((10, 20), (50, 40)), "Offset bounds not preserved"

    print("  BSP construction: PASS")

def test_bsp_split_once():
    """Test single split operation (#202)."""
    print("Testing BSP split_once...")

    bsp = mcrfpy.BSP(bounds=((0, 0), (100, 80)))

    # Before split, root should be a leaf
    assert bsp.root.is_leaf, "Root should be leaf before split"

    # Horizontal split at y=40
    result = bsp.split_once(horizontal=True, position=40)
    assert result is bsp, "split_once should return self for chaining"

    # After split, root should not be a leaf
    root = bsp.root
    assert not root.is_leaf, "Root should not be leaf after split"
    assert root.split_horizontal == True, "Split should be horizontal"
    assert root.split_position == 40, "Split position should be 40"

    # Check children exist
    left = root.left
    right = root.right
    assert left is not None, "Left child should exist"
    assert right is not None, "Right child should exist"
    assert left.is_leaf, "Left child should be leaf"
    assert right.is_leaf, "Right child should be leaf"

    print("  BSP split_once: PASS")

def test_bsp_split_recursive():
    """Test recursive splitting (#202)."""
    print("Testing BSP split_recursive...")

    bsp = mcrfpy.BSP(bounds=((0, 0), (80, 60)))

    # Recursive split with seed for reproducibility
    result = bsp.split_recursive(depth=3, min_size=(8, 8), max_ratio=1.5, seed=42)
    assert result is bsp, "split_recursive should return self"

    # Count leaves
    leaves = list(bsp.leaves())
    assert len(leaves) > 1, f"Should have multiple leaves, got {len(leaves)}"
    assert len(leaves) <= 8, f"Should have at most 2^3=8 leaves, got {len(leaves)}"

    # All leaves should be within bounds
    for leaf in leaves:
        x, y = leaf.bounds[0]
        w, h = leaf.bounds[1]
        assert x >= 0 and y >= 0, f"Leaf position out of bounds: {leaf.bounds}"
        assert x + w <= 80 and y + h <= 60, f"Leaf extends beyond bounds: {leaf.bounds}"
        assert w >= 8 and h >= 8, f"Leaf smaller than min_size: {leaf.bounds}"

    print("  BSP split_recursive: PASS")

def test_bsp_clear():
    """Test clear operation (#202)."""
    print("Testing BSP clear...")

    bsp = mcrfpy.BSP(bounds=((0, 0), (100, 80)))
    bsp.split_recursive(depth=4, min_size=(8, 8), seed=42)

    # Should have multiple leaves
    leaves_before = len(list(bsp.leaves()))
    assert leaves_before > 1, "Should have multiple leaves after split"

    # Clear
    result = bsp.clear()
    assert result is bsp, "clear should return self"

    # Should be back to single leaf
    leaves_after = list(bsp.leaves())
    assert len(leaves_after) == 1, f"Should have 1 leaf after clear, got {len(leaves_after)}"

    # Root should be a leaf with original bounds
    assert bsp.root.is_leaf, "Root should be leaf after clear"
    assert bsp.bounds == ((0, 0), (100, 80)), "Bounds should be restored"

    print("  BSP clear: PASS")

def test_bspnode_properties():
    """Test BSPNode properties (#203)."""
    print("Testing BSPNode properties...")

    bsp = mcrfpy.BSP(bounds=((0, 0), (100, 80)))
    bsp.split_recursive(depth=3, min_size=(8, 8), seed=42)

    root = bsp.root

    # Root properties
    assert root.level == 0, f"Root level should be 0, got {root.level}"
    assert root.parent is None, "Root parent should be None"
    assert not root.is_leaf, "Split root should not be leaf"

    # Split properties (not leaf)
    assert root.split_horizontal is not None, "Split horizontal should be bool for non-leaf"
    assert root.split_position is not None, "Split position should be int for non-leaf"

    # Navigate to a leaf
    current = root
    while not current.is_leaf:
        current = current.left

    # Leaf properties
    assert current.is_leaf, "Should be a leaf"
    assert current.split_horizontal is None, "Leaf split_horizontal should be None"
    assert current.split_position is None, "Leaf split_position should be None"
    assert current.level > 0, "Leaf level should be > 0"

    # Test center method
    bounds = current.bounds
    cx, cy = current.center()
    expected_cx = bounds[0][0] + bounds[1][0] // 2
    expected_cy = bounds[0][1] + bounds[1][1] // 2
    assert cx == expected_cx, f"Center x mismatch: {cx} != {expected_cx}"
    assert cy == expected_cy, f"Center y mismatch: {cy} != {expected_cy}"

    print("  BSPNode properties: PASS")

def test_bspnode_navigation():
    """Test BSPNode navigation (#203)."""
    print("Testing BSPNode navigation...")

    bsp = mcrfpy.BSP(bounds=((0, 0), (100, 80)))
    bsp.split_once(horizontal=True, position=40)

    root = bsp.root
    left = root.left
    right = root.right

    # Parent navigation
    assert left.parent is not None, "Left parent should exist"
    assert left.parent.bounds == root.bounds, "Left parent should be root"

    # Sibling navigation
    assert left.sibling is not None, "Left sibling should exist"
    assert left.sibling.bounds == right.bounds, "Left sibling should be right"
    assert right.sibling is not None, "Right sibling should exist"
    assert right.sibling.bounds == left.bounds, "Right sibling should be left"

    # Root has no parent or sibling
    assert root.parent is None, "Root parent should be None"
    assert root.sibling is None, "Root sibling should be None"

    print("  BSPNode navigation: PASS")

def test_bspnode_contains():
    """Test BSPNode contains method (#203)."""
    print("Testing BSPNode contains...")

    bsp = mcrfpy.BSP(bounds=((10, 20), (50, 40)))  # x: 10-60, y: 20-60

    root = bsp.root

    # Inside
    assert root.contains((30, 40)), "Center should be inside"
    assert root.contains((10, 20)), "Top-left corner should be inside"
    assert root.contains((59, 59)), "Near bottom-right should be inside"

    # Outside
    assert not root.contains((5, 40)), "Left of bounds should be outside"
    assert not root.contains((65, 40)), "Right of bounds should be outside"
    assert not root.contains((30, 15)), "Above bounds should be outside"
    assert not root.contains((30, 65)), "Below bounds should be outside"

    print("  BSPNode contains: PASS")

def test_bsp_leaves_iteration():
    """Test leaves iteration (#204)."""
    print("Testing BSP leaves iteration...")

    bsp = mcrfpy.BSP(bounds=((0, 0), (80, 60)))
    bsp.split_recursive(depth=3, min_size=(8, 8), seed=42)

    # Iterate leaves
    leaves = list(bsp.leaves())
    assert len(leaves) > 0, "Should have at least one leaf"

    # All should be leaves
    for leaf in leaves:
        assert leaf.is_leaf, f"Should be leaf: {leaf}"

    # Can convert to list multiple times
    leaves2 = list(bsp.leaves())
    assert len(leaves) == len(leaves2), "Multiple iterations should yield same count"

    print("  BSP leaves iteration: PASS")

def test_bsp_traverse():
    """Test traverse with different orders (#204)."""
    print("Testing BSP traverse...")

    bsp = mcrfpy.BSP(bounds=((0, 0), (80, 60)))
    bsp.split_recursive(depth=2, min_size=(8, 8), seed=42)

    # Test all traversal orders
    orders = [
        mcrfpy.Traversal.PRE_ORDER,
        mcrfpy.Traversal.IN_ORDER,
        mcrfpy.Traversal.POST_ORDER,
        mcrfpy.Traversal.LEVEL_ORDER,
        mcrfpy.Traversal.INVERTED_LEVEL_ORDER,
    ]

    for order in orders:
        nodes = list(bsp.traverse(order=order))
        assert len(nodes) > 0, f"Should have nodes for {order}"
        # All traversals should visit same number of nodes
        assert len(nodes) == len(list(bsp.traverse())), f"Node count mismatch for {order}"

    # Default should be LEVEL_ORDER
    default_nodes = list(bsp.traverse())
    level_nodes = list(bsp.traverse(mcrfpy.Traversal.LEVEL_ORDER))
    assert len(default_nodes) == len(level_nodes), "Default should match LEVEL_ORDER"

    # PRE_ORDER: root first
    pre_nodes = list(bsp.traverse(mcrfpy.Traversal.PRE_ORDER))
    assert pre_nodes[0].bounds == bsp.root.bounds, "PRE_ORDER should start with root"

    # POST_ORDER: root last
    post_nodes = list(bsp.traverse(mcrfpy.Traversal.POST_ORDER))
    assert post_nodes[-1].bounds == bsp.root.bounds, "POST_ORDER should end with root"

    print("  BSP traverse: PASS")

def test_bsp_find():
    """Test find method (#205)."""
    print("Testing BSP find...")

    bsp = mcrfpy.BSP(bounds=((0, 0), (80, 60)))
    bsp.split_recursive(depth=3, min_size=(8, 8), seed=42)

    # Find a point inside bounds
    node = bsp.find((40, 30))
    assert node is not None, "Should find node for point inside"
    assert node.is_leaf, "Found node should be a leaf (deepest)"
    assert node.contains((40, 30)), "Found node should contain the point"

    # Find at corner
    corner_node = bsp.find((0, 0))
    assert corner_node is not None, "Should find node at corner"
    assert corner_node.contains((0, 0)), "Corner node should contain (0,0)"

    # Find outside bounds
    outside = bsp.find((100, 100))
    assert outside is None, "Should return None for point outside"

    print("  BSP find: PASS")

def test_bsp_to_heightmap():
    """Test to_heightmap conversion (#206)."""
    print("Testing BSP to_heightmap...")

    bsp = mcrfpy.BSP(bounds=((0, 0), (50, 40)))
    bsp.split_recursive(depth=2, min_size=(8, 8), seed=42)

    # Basic conversion
    hmap = bsp.to_heightmap()
    assert hmap is not None, "Should create heightmap"
    assert hmap.size == (50, 40), f"Size should match bounds, got {hmap.size}"

    # Check that leaves are filled
    leaves = list(bsp.leaves())
    for leaf in leaves:
        lx, ly = leaf.bounds[0]
        val = hmap[lx, ly]
        assert val == 1.0, f"Leaf interior should be 1.0, got {val}"

    # Test with shrink
    hmap_shrink = bsp.to_heightmap(shrink=2)
    assert hmap_shrink is not None, "Should create with shrink"

    # Test with select='internal'
    hmap_internal = bsp.to_heightmap(select='internal')
    assert hmap_internal is not None, "Should create with select=internal"

    # Test with select='all'
    hmap_all = bsp.to_heightmap(select='all')
    assert hmap_all is not None, "Should create with select=all"

    # Test with custom size
    hmap_sized = bsp.to_heightmap(size=(100, 80))
    assert hmap_sized.size == (100, 80), f"Custom size should work, got {hmap_sized.size}"

    # Test with custom value
    hmap_val = bsp.to_heightmap(value=0.5)
    leaves = list(bsp.leaves())
    leaf = leaves[0]
    lx, ly = leaf.bounds[0]
    val = hmap_val[lx, ly]
    assert val == 0.5, f"Custom value should be 0.5, got {val}"

    print("  BSP to_heightmap: PASS")

def test_traversal_enum():
    """Test Traversal enum (#204)."""
    print("Testing Traversal enum...")

    # Check enum exists
    assert hasattr(mcrfpy, 'Traversal'), "Traversal enum should exist"

    # Check all members
    assert mcrfpy.Traversal.PRE_ORDER.value == 0
    assert mcrfpy.Traversal.IN_ORDER.value == 1
    assert mcrfpy.Traversal.POST_ORDER.value == 2
    assert mcrfpy.Traversal.LEVEL_ORDER.value == 3
    assert mcrfpy.Traversal.INVERTED_LEVEL_ORDER.value == 4

    print("  Traversal enum: PASS")

def test_bsp_chaining():
    """Test method chaining."""
    print("Testing BSP method chaining...")

    bsp = mcrfpy.BSP(bounds=((0, 0), (80, 60)))

    # Chain multiple operations
    result = bsp.split_recursive(depth=2, min_size=(8, 8), seed=42).clear().split_once(True, 30)
    assert result is bsp, "Chaining should return self"

    print("  BSP chaining: PASS")

def test_bsp_repr():
    """Test repr output."""
    print("Testing BSP repr...")

    bsp = mcrfpy.BSP(bounds=((0, 0), (80, 60)))
    repr_str = repr(bsp)
    assert "BSP" in repr_str, f"repr should contain BSP: {repr_str}"
    assert "80" in repr_str and "60" in repr_str, f"repr should contain size: {repr_str}"

    bsp.split_recursive(depth=2, min_size=(8, 8), seed=42)
    repr_str2 = repr(bsp)
    assert "leaves" in repr_str2, f"repr should mention leaves: {repr_str2}"

    # BSPNode repr
    node_repr = repr(bsp.root)
    assert "BSPNode" in node_repr, f"BSPNode repr: {node_repr}"

    print("  BSP repr: PASS")

def run_all_tests():
    """Run all BSP tests."""
    print("\n=== BSP Unit Tests ===\n")

    try:
        test_bsp_construction()
        test_bsp_split_once()
        test_bsp_split_recursive()
        test_bsp_clear()
        test_bspnode_properties()
        test_bspnode_navigation()
        test_bspnode_contains()
        test_bsp_leaves_iteration()
        test_bsp_traverse()
        test_bsp_find()
        test_bsp_to_heightmap()
        test_traversal_enum()
        test_bsp_chaining()
        test_bsp_repr()

        print("\n=== ALL BSP TESTS PASSED ===\n")
        sys.exit(0)
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
