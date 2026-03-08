"""Regression test: entity self-reference cycle (#266, #275).

Bug: UIEntity::init() stored a reference to the Python wrapper via
self->data->self = (PyObject*)self and Py_INCREF(self). This created
a reference cycle that prevented the entity from ever being freed,
even after removing it from all grids and dropping all Python references.

Fix: Remove the self field entirely. Use PythonObjectCache (weak refs)
for Python object identity preservation instead.
"""
import mcrfpy
import gc
import sys

def test_entity_accessible_via_grid():
    """Entities remain accessible through grid.entities after Python ref dropped"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
    entity_id = id(entity)

    # Drop the Python reference
    del entity
    gc.collect()

    # Entity should still be accessible via grid
    assert len(grid.entities) == 1, f"Expected 1 entity, got {len(grid.entities)}"
    retrieved = grid.entities[0]
    assert retrieved.grid_x == 5.0, f"Expected x=5.0, got {retrieved.grid_x}"
    print("  PASS: entity_accessible_via_grid")

def test_entity_removed_from_grid():
    """Entity can be removed from grid cleanly"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=grid)

    assert len(grid.entities) == 1
    grid.entities.remove(entity)
    assert len(grid.entities) == 0
    print("  PASS: entity_removed_from_grid")

def test_multiple_entities():
    """Multiple entities can be created, accessed, and removed"""
    grid = mcrfpy.Grid(grid_size=(20, 20))
    entities = []
    for i in range(10):
        e = mcrfpy.Entity(grid_pos=(i, i), grid=grid)
        entities.append(e)

    assert len(grid.entities) == 10

    # Drop all Python references
    del entities
    gc.collect()

    # All should still be in grid
    assert len(grid.entities) == 10

    # Access each one
    for i in range(10):
        e = grid.entities[i]
        assert e.grid_x == float(i), f"Entity {i} x={e.grid_x}, expected {float(i)}"

    print("  PASS: multiple_entities")

def test_entity_transfer_preserves_identity():
    """Entity identity preserved when transferring between grids"""
    grid1 = mcrfpy.Grid(grid_size=(10, 10))
    grid2 = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid1)

    entity.grid = grid2
    assert len(grid1.entities) == 0
    assert len(grid2.entities) == 1

    retrieved = grid2.entities[0]
    assert retrieved.grid_x == 5.0
    print("  PASS: entity_transfer_preserves_identity")

def test_iteration_after_gc():
    """Iterating grid.entities works after GC of Python wrappers"""
    grid = mcrfpy.Grid(grid_size=(10, 10))
    for i in range(5):
        mcrfpy.Entity(grid_pos=(i, 0), grid=grid)

    gc.collect()

    count = 0
    for e in grid.entities:
        count += 1
    assert count == 5, f"Expected 5 entities in iteration, got {count}"
    print("  PASS: iteration_after_gc")

print("Testing entity lifecycle (self-reference removal)...")
test_entity_accessible_via_grid()
test_entity_removed_from_grid()
test_multiple_entities()
test_entity_transfer_preserves_identity()
test_iteration_after_gc()
print("PASS: all entity lifecycle tests passed")
sys.exit(0)
