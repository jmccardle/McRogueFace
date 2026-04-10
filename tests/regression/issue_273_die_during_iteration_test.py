"""Regression test: entity.die() during iteration raises RuntimeError (#273).

Bug: Calling entity.die() inside a for-loop over grid.entities would
invalidate the C++ list iterator, causing undefined behavior.

Fix: The EntityCollection iterator captures the collection size at start
and checks it before each yield. If die() changes the size, RuntimeError
is raised instead of silently corrupting memory.
"""
import mcrfpy
import sys

def test_die_during_iteration_raises():
    """entity.die() during iteration raises RuntimeError"""
    grid = mcrfpy.Grid(grid_size=(20, 20))
    for i in range(5):
        mcrfpy.Entity(grid_pos=(i, 0), grid=grid)

    caught = False
    try:
        for entity in grid.entities:
            entity.die()
    except RuntimeError as e:
        caught = True
        assert "changed size during iteration" in str(e), f"Wrong error: {e}"

    assert caught, "Expected RuntimeError when calling die() during iteration"
    print("  PASS: die_during_iteration_raises")

def test_safe_die_pattern():
    """Collecting entities first, then dying, works correctly"""
    grid = mcrfpy.Grid(grid_size=(20, 20))
    for i in range(5):
        mcrfpy.Entity(grid_pos=(i, 0), grid=grid)

    assert len(grid.entities) == 5

    # Safe pattern: collect references first
    to_die = list(grid.entities)
    for entity in to_die:
        entity.die()

    assert len(grid.entities) == 0
    print("  PASS: safe_die_pattern")

def test_die_removes_from_spatial_hash():
    """entity.die() properly removes from spatial hash"""
    grid = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)

    found = grid.entities_in_radius((5.0, 5.0), 1.0)
    assert len(found) == 1

    entity.die()

    found = grid.entities_in_radius((5.0, 5.0), 1.0)
    assert len(found) == 0, f"Expected 0 after die(), found {len(found)}"
    print("  PASS: die_removes_from_spatial_hash")


print("Testing entity.die() during iteration (#273)...")
test_die_during_iteration_raises()
test_safe_die_pattern()
test_die_removes_from_spatial_hash()
print("PASS: all die-during-iteration tests passed")
sys.exit(0)
