"""Regression test: animation and the spatial hash (#256, revised by #431).

#256: animating an entity's position left the spatial hash stale, so
grid.entities_in_radius() returned results for a position the entity had left.

#431 settled what the hash tracks: the logical cell (grid_pos), everywhere.
draw_pos -- set or animated -- is where the sprite is drawn and does not move
the entity in spatial queries. Moving the cell (grid_pos, or grid.step()) does,
and is never stale: these tests pin both halves.
"""
import mcrfpy
import sys


def test_animate_draw_pos_keeps_cell_in_hash():
    """Animating draw_pos moves the sprite; queries still find the entity at its cell."""
    scene = mcrfpy.Scene("test_anim_spatial")
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(500, 500))
    scene.children.append(grid)

    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
    assert len(grid.entities_in_radius((5.0, 5.0), 1.0)) == 1

    entity.animate("draw_pos", (40.0, 40.0), 0.01, mcrfpy.Easing.LINEAR)
    for _ in range(20):
        mcrfpy.step(0.01)

    pos = entity.draw_pos
    assert abs(pos.x - 40.0) < 0.1, f"draw_pos.x should be ~40, got {pos.x}"
    assert abs(pos.y - 40.0) < 0.1, f"draw_pos.y should be ~40, got {pos.y}"
    assert (entity.grid_x, entity.grid_y) == (5, 5)

    assert len(grid.entities_in_radius((5.0, 5.0), 1.0)) == 1
    assert len(grid.entities_in_radius((40.0, 40.0), 2.0)) == 0
    print("  PASS: animate_draw_pos_keeps_cell_in_hash")


def test_cell_move_updates_hash():
    """Setting the cell re-buckets the entity: no stale result at the old cell."""
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(500, 500))
    entity = mcrfpy.Entity(grid_pos=(10, 10), grid=grid)
    assert len(grid.entities_in_radius((10.0, 10.0), 1.0)) == 1

    entity.grid_pos = (40, 40)

    found_new = grid.entities_in_radius((40.0, 40.0), 1.0)
    assert len(found_new) == 1, f"Expected 1 entity at (40,40), found {len(found_new)}"
    found_old = grid.entities_in_radius((10.0, 10.0), 1.0)
    assert len(found_old) == 0, f"Expected 0 at old cell, found {len(found_old)}"
    print("  PASS: cell_move_updates_hash")


print("Testing animation spatial hash update (#256, #431)...")
test_animate_draw_pos_keeps_cell_in_hash()
test_cell_move_updates_hash()
print("PASS: all animation spatial hash tests passed")
sys.exit(0)
