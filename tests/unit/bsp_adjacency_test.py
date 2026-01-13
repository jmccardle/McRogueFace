#!/usr/bin/env python3
"""Tests for BSP adjacency graph feature (#210)"""

import mcrfpy
import sys

def test_adjacency_basic():
    """Test basic adjacency on a simple 2-leaf BSP"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 50))
    # Split once - creates 2 leaves
    bsp.split_once(horizontal=False, position=50)  # Vertical split at x=50

    leaves = list(bsp.leaves())
    assert len(leaves) == 2, f"Expected 2 leaves, got {len(leaves)}"

    # Access adjacency
    adj = bsp.adjacency
    assert len(adj) == 2, f"Expected adjacency len 2, got {len(adj)}"

    # Each leaf should be adjacent to the other
    neighbors_0 = adj[0]
    neighbors_1 = adj[1]

    assert 1 in neighbors_0, f"Leaf 0 should be adjacent to leaf 1, got {neighbors_0}"
    assert 0 in neighbors_1, f"Leaf 1 should be adjacent to leaf 0, got {neighbors_1}"

    print("  test_adjacency_basic: PASS")

def test_leaf_indexing():
    """Test that leaf_index property works correctly"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 100))
    bsp.split_recursive(depth=2, min_size=(10, 10), seed=42)

    leaves = list(bsp.leaves())

    # Each leaf should have a valid index
    for i, leaf in enumerate(leaves):
        assert leaf.leaf_index == i, f"Leaf {i} has index {leaf.leaf_index}"

    # Non-leaves should return None
    root = bsp.root
    if not root.is_leaf:
        assert root.leaf_index is None, "Non-leaf should have leaf_index=None"

    print("  test_leaf_indexing: PASS")

def test_adjacency_symmetry():
    """Test that adjacency is symmetric: if A adjacent to B, then B adjacent to A"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 100))
    bsp.split_recursive(depth=3, min_size=(10, 10), seed=42)

    adj = bsp.adjacency
    n = len(adj)

    for i in range(n):
        for j in adj[i]:
            assert i in adj[j], f"Adjacency not symmetric: {i} -> {j} but not {j} -> {i}"

    print("  test_adjacency_symmetry: PASS")

def test_adjacent_tiles_basic():
    """Test that adjacent_tiles returns Vector tuples"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 50))
    bsp.split_once(horizontal=False, position=50)  # Vertical split at x=50

    leaves = list(bsp.leaves())
    assert len(leaves) == 2

    leaf0 = leaves[0]
    neighbors = bsp.adjacency[0]
    assert len(neighbors) > 0, "Leaf 0 should have neighbors"

    neighbor_idx = neighbors[0]
    wall_tiles = leaf0.adjacent_tiles[neighbor_idx]

    assert len(wall_tiles) > 0, "Should have wall tiles"

    # Check that wall tiles are Vector objects
    first_tile = wall_tiles[0]
    assert hasattr(first_tile, 'x') and hasattr(first_tile, 'y'), \
        f"Wall tile should be a Vector, got {type(first_tile)}"

    print("  test_adjacent_tiles_basic: PASS")

def test_adjacent_tiles_keyerror():
    """Test that non-adjacent lookups raise KeyError"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 100))
    bsp.split_recursive(depth=3, min_size=(10, 10), seed=42)

    leaves = list(bsp.leaves())

    # Find a non-adjacent pair
    adj = bsp.adjacency
    for i in range(len(leaves)):
        for j in range(len(leaves)):
            if i != j and j not in adj[i]:
                # i and j are not adjacent
                try:
                    _ = leaves[i].adjacent_tiles[j]
                    assert False, f"Expected KeyError for non-adjacent pair {i}, {j}"
                except KeyError:
                    pass  # Expected
                print("  test_adjacent_tiles_keyerror: PASS")
                return

    # If we get here, all pairs are adjacent (unlikely with depth 3)
    print("  test_adjacent_tiles_keyerror: SKIP (all pairs adjacent)")

def test_cache_invalidation():
    """Test that cache is invalidated on clear() and split_recursive()"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 100))
    bsp.split_recursive(depth=2, min_size=(10, 10), seed=42)

    # Access adjacency to populate cache
    adj1 = bsp.adjacency
    n1 = len(adj1)

    # Clear and re-split
    bsp.clear()
    bsp.split_recursive(depth=3, min_size=(10, 10), seed=123)

    # Access adjacency again - should be rebuilt
    adj2 = bsp.adjacency
    n2 = len(adj2)

    # Different seed/depth should give different results
    assert n2 > n1 or n2 != n1, "Cache should be invalidated after clear()"

    print("  test_cache_invalidation: PASS")

def test_wall_tiles_on_boundary():
    """Test that wall tiles are on the correct boundary"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 50))
    bsp.split_once(horizontal=False, position=50)  # Vertical split at x=50

    leaves = list(bsp.leaves())
    leaf0 = leaves[0]  # Should be left side (x: 0-50)
    leaf1 = leaves[1]  # Should be right side (x: 50-100)

    # Get wall tiles from leaf0 to leaf1
    wall_tiles = leaf0.adjacent_tiles[1]

    # Wall should be at x=49 (last column of leaf0) for leaf0
    for tile in wall_tiles:
        x, y = int(tile.x), int(tile.y)
        # Tile should be within leaf0's bounds
        assert x == 49, f"Wall tile x should be 49 (boundary), got {x}"
        assert 0 <= y < 50, f"Wall tile y should be in range 0-49, got {y}"

    print("  test_wall_tiles_on_boundary: PASS")

def test_negative_indexing():
    """Test that negative indices work for adjacency"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 100))
    bsp.split_recursive(depth=2, min_size=(10, 10), seed=42)

    adj = bsp.adjacency
    n = len(adj)

    # adj[-1] should be same as adj[n-1]
    last_positive = adj[n-1]
    last_negative = adj[-1]

    assert last_positive == last_negative, \
        f"Negative indexing failed: adj[-1]={last_negative}, adj[{n-1}]={last_positive}"

    print("  test_negative_indexing: PASS")

def test_iteration():
    """Test that adjacency can be iterated"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 100))
    bsp.split_recursive(depth=2, min_size=(10, 10), seed=42)

    adj = bsp.adjacency

    # Should be iterable
    count = 0
    for neighbors in adj:
        assert isinstance(neighbors, tuple), f"Expected tuple, got {type(neighbors)}"
        count += 1

    assert count == len(adj), f"Iteration count {count} != len {len(adj)}"

    print("  test_iteration: PASS")

def test_keys_method():
    """Test that adjacent_tiles.keys() works"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 50))
    bsp.split_once(horizontal=False, position=50)

    leaves = list(bsp.leaves())
    leaf0 = leaves[0]

    keys = leaf0.adjacent_tiles.keys()
    assert isinstance(keys, tuple), f"keys() should return tuple, got {type(keys)}"
    assert len(keys) > 0, "Should have at least one neighbor"
    assert 1 in keys, f"Leaf 1 should be in keys, got {keys}"

    print("  test_keys_method: PASS")

def test_split_once_invalidation():
    """Test that split_once invalidates adjacency cache and BSPNode references"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 100))

    # First split - creates 2 leaves
    bsp.split_once(horizontal=False, position=50)

    # Access adjacency to build cache
    adj1 = bsp.adjacency
    n1 = len(adj1)
    assert n1 == 2, f"Expected 2 leaves after first split, got {n1}"

    # Get a reference to a leaf before second split
    old_leaf = list(bsp.leaves())[0]
    old_leaf_index = old_leaf.leaf_index

    # Second split_once on the BSP (note: split_once always works on root)
    # After this, the tree structure changes, but old_leaf should be stale
    bsp.clear()  # Clear and split fresh to get more leaves
    bsp.split_once(horizontal=False, position=50)
    bsp.split_once(horizontal=True, position=50)  # Won't work - split_once only on root

    # The old leaf reference should now be stale
    try:
        _ = old_leaf.leaf_index
        assert False, "Expected RuntimeError for stale BSPNode"
    except RuntimeError:
        pass  # Expected - node is stale after clear()

    # Access adjacency - should reflect new structure (2 leaves again)
    adj2 = bsp.adjacency
    n2 = len(adj2)
    assert n2 == 2, f"Expected 2 leaves after clear+split, got {n2}"

    print("  test_split_once_invalidation: PASS")

def test_wall_tiles_perspective():
    """Test that wall tiles are from the correct leaf's perspective"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 50))
    bsp.split_once(horizontal=False, position=50)  # Vertical split at x=50

    leaves = list(bsp.leaves())
    leaf0 = leaves[0]  # Left side: x 0-50
    leaf1 = leaves[1]  # Right side: x 50-100

    # Get tiles from leaf0's perspective (should be at x=49, leaf0's edge)
    tiles_0_to_1 = leaf0.adjacent_tiles[1]
    for tile in tiles_0_to_1:
        assert int(tile.x) == 49, f"Leaf0->Leaf1 tile should be at x=49, got {tile.x}"

    # Get tiles from leaf1's perspective (should be at x=50, leaf1's edge)
    tiles_1_to_0 = leaf1.adjacent_tiles[0]
    for tile in tiles_1_to_0:
        assert int(tile.x) == 50, f"Leaf1->Leaf0 tile should be at x=50, got {tile.x}"

    print("  test_wall_tiles_perspective: PASS")

def test_get_leaf():
    """Test bsp.get_leaf(index) method"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 100))
    bsp.split_recursive(depth=2, min_size=(10, 10), seed=42)

    leaves = list(bsp.leaves())
    n = len(leaves)

    # Test positive indices
    for i in range(n):
        leaf = bsp.get_leaf(i)
        assert leaf.leaf_index == i, f"get_leaf({i}) returned leaf with index {leaf.leaf_index}"

    # Test negative index
    last_leaf = bsp.get_leaf(-1)
    assert last_leaf.leaf_index == n - 1, f"get_leaf(-1) should return leaf {n-1}, got {last_leaf.leaf_index}"

    # Test out of range
    try:
        bsp.get_leaf(n)
        assert False, "Expected IndexError for out-of-range index"
    except IndexError:
        pass  # Expected

    print("  test_get_leaf: PASS")

def test_contains_operator():
    """Test 'in' operator for adjacent_tiles"""
    bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 50))
    bsp.split_once(horizontal=False, position=50)

    leaves = list(bsp.leaves())
    leaf0 = leaves[0]

    # Leaf 1 should be adjacent to leaf 0
    assert 1 in leaf0.adjacent_tiles, "1 should be in leaf0.adjacent_tiles"

    # Some arbitrary index should not be (assuming only 2 leaves)
    assert 5 not in leaf0.adjacent_tiles, "5 should not be in leaf0.adjacent_tiles"

    print("  test_contains_operator: PASS")

def run_all_tests():
    """Run all adjacency tests"""
    print("Running BSP adjacency tests (#210)...")

    test_adjacency_basic()
    test_leaf_indexing()
    test_adjacency_symmetry()
    test_adjacent_tiles_basic()
    test_adjacent_tiles_keyerror()
    test_cache_invalidation()
    test_wall_tiles_on_boundary()
    test_negative_indexing()
    test_iteration()
    test_keys_method()
    test_split_once_invalidation()
    test_wall_tiles_perspective()
    test_get_leaf()
    test_contains_operator()

    print("\nAll BSP adjacency tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(run_all_tests())
