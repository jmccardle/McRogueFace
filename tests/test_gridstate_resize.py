"""Regression test: entity gridstate must resize when moving between grids.

Bug: UIEntity::set_grid() only initialized gridstate when it was empty
(size == 0). When an entity moved from a small grid to a larger grid,
gridstate kept the old size. UIEntity::updateVisibility() then wrote
past the end of the vector using the new grid's dimensions, corrupting
adjacent heap memory.

Trigger: any entity that calls update_visibility() after moving to a
larger grid. In Liber Noster this was the player entity using the
engine's perspective FOV system across zone transitions.

This script should exit cleanly. Before the fix, it segfaulted or
produced incorrect gridstate lengths.
"""
import mcrfpy

# Create a small grid and a large grid
small = mcrfpy.Grid(grid_size=(10, 10))
large = mcrfpy.Grid(grid_size=(50, 50))

# Create an entity on the small grid
entity = mcrfpy.Entity(grid_pos=(5, 5), grid=small)

# Force gridstate initialization by calling update_visibility
small.perspective = entity
small.fov_radius = 4
entity.update_visibility()  # gridstate sized to 10*10 = 100

# Verify gridstate matches small grid
gs = entity.gridstate
assert len(gs) == 100, f"Expected gridstate size 100 for 10x10 grid, got {len(gs)}"

# Move entity to the larger grid
entity.grid = large

# Gridstate must now match the large grid's dimensions
gs = entity.gridstate
assert len(gs) == 2500, f"Expected gridstate size 2500 for 50x50 grid, got {len(gs)}"

# Set up perspective on the large grid
large.perspective = entity
large.fov_radius = 8

# This triggers updateVisibility() which iterates 50*50 = 2500 cells.
# Before the fix, gridstate was only 100 entries — heap buffer overflow.
entity.update_visibility()

# Stress test: repeatedly move between grids of different sizes to
# exercise the resize path and pressure the heap allocator.
grids = [mcrfpy.Grid(grid_size=(s, s)) for s in (5, 80, 3, 60, 10, 100)]
for g in grids:
    entity.grid = g
    g.perspective = entity
    g.fov_radius = 4
    entity.update_visibility()
    gs = entity.gridstate
    expected = g.grid_w * g.grid_h
    assert len(gs) == expected, f"Expected {expected}, got {len(gs)} for {g.grid_w}x{g.grid_h}"

# Also allocate other objects between transitions to fill freed heap
# regions — makes corruption more likely to manifest as a crash.
for i in range(20):
    small_g = mcrfpy.Grid(grid_size=(5, 5))
    entity.grid = small_g
    small_g.perspective = entity
    entity.update_visibility()

    big_g = mcrfpy.Grid(grid_size=(80, 80))
    entity.grid = big_g
    big_g.perspective = entity
    entity.update_visibility()

    # Create and destroy interim objects to churn the heap
    frames = [mcrfpy.Frame() for _ in range(10)]
    del frames

print("PASS: gridstate resized correctly across all transitions")
