"""Regression test: Animation system bypasses spatial hash (#256).

Bug: When entity position was changed via animate(), the spatial hash
was not updated. This caused grid.entities_in_radius() to return stale
results based on the last Python-assigned position, not the animated one.

Fix: UIEntity::setProperty() (called by the animation system) now calls
spatial_hash.update() for position property changes, matching the
behavior of Python property setters.
"""
import mcrfpy
import sys

def test_animate_updates_spatial_hash():
    """Entity animated to new position is found by spatial queries"""
    scene = mcrfpy.Scene("test_anim_spatial")
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(500, 500))
    scene.children.append(grid)

    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)

    # Verify entity is at initial position
    found = grid.entities_in_radius((5.0, 5.0), 1.0)
    assert len(found) == 1, f"Expected 1 entity at (5,5), found {len(found)}"

    # Animate to a far-away position using draw_x/draw_y
    entity.animate("draw_x", 40.0, 0.01, mcrfpy.Easing.LINEAR)
    entity.animate("draw_y", 40.0, 0.01, mcrfpy.Easing.LINEAR)

    # Step the game loop enough to complete the animation
    for _ in range(20):
        mcrfpy.step(0.01)

    # Verify entity position has changed
    pos = entity.draw_pos
    assert abs(pos.x - 40.0) < 0.1, f"draw_pos.x should be ~40, got {pos.x}"
    assert abs(pos.y - 40.0) < 0.1, f"draw_pos.y should be ~40, got {pos.y}"

    # Spatial hash should now find the entity near (40, 40), not (5, 5)
    found_new = grid.entities_in_radius((40.0, 40.0), 2.0)
    assert len(found_new) == 1, f"Expected 1 entity near (40,40), found {len(found_new)}"

    found_old = grid.entities_in_radius((5.0, 5.0), 1.0)
    assert len(found_old) == 0, f"Expected 0 entities at old pos (5,5), found {len(found_old)}"

    print("  PASS: animate_updates_spatial_hash")

def test_property_set_still_works():
    """Direct property assignment still updates spatial hash"""
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(500, 500))
    entity = mcrfpy.Entity(grid_pos=(10, 10), grid=grid)

    found = grid.entities_in_radius((10.0, 10.0), 1.0)
    assert len(found) == 1

    entity.draw_pos = mcrfpy.Vector(30.0, 30.0)

    found_new = grid.entities_in_radius((30.0, 30.0), 1.0)
    assert len(found_new) == 1, f"Expected 1 entity at (30,30), found {len(found_new)}"

    found_old = grid.entities_in_radius((10.0, 10.0), 1.0)
    assert len(found_old) == 0, f"Expected 0 at old position, found {len(found_old)}"

    print("  PASS: property_set_still_works")


print("Testing animation spatial hash update (#256)...")
test_animate_updates_spatial_hash()
test_property_set_still_works()
print("PASS: all animation spatial hash tests passed")
sys.exit(0)
