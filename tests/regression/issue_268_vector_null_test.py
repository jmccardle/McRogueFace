"""Regression test: sfVector2f_to_PyObject must handle allocation failure.

Issue #268: sfVector2f_to_PyObject in UIEntity.cpp could return NULL when
tp_alloc fails, but callers didn't check. Under normal conditions this
can't be triggered, but this test exercises all Vector-returning entity
properties to ensure the code path works correctly and doesn't crash.

Fix: Callers now propagate NULL returns as Python exceptions.
"""
import mcrfpy
import sys

def test_entity_vector_properties():
    """All Vector-returning properties must return valid Vector objects."""
    grid = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)

    pos = entity.pos
    assert pos is not None, "entity.pos returned None"
    assert hasattr(pos, 'x') and hasattr(pos, 'y'), "pos missing x/y"

    draw_pos = entity.draw_pos
    assert draw_pos is not None, "entity.draw_pos returned None"

    cell_pos = entity.cell_pos
    assert cell_pos is not None, "entity.cell_pos returned None"
    assert cell_pos.x == 5 and cell_pos.y == 5, f"cell_pos wrong: {cell_pos.x}, {cell_pos.y}"

    offset = entity.sprite_offset
    assert offset is not None, "entity.sprite_offset returned None"
    assert offset.x == 0.0 and offset.y == 0.0, "Default sprite_offset should be (0,0)"

    print("  PASS: entity vector properties")

def test_entity_vector_setters():
    """Vector property setters must accept tuples and Vectors."""
    grid = mcrfpy.Grid(grid_size=(20, 20))
    entity = mcrfpy.Entity(grid_pos=(3, 3), grid=grid)

    entity.sprite_offset = (10.0, -5.0)
    assert entity.sprite_offset.x == 10.0, f"sprite_offset.x wrong: {entity.sprite_offset.x}"
    assert entity.sprite_offset.y == -5.0, f"sprite_offset.y wrong: {entity.sprite_offset.y}"

    entity.draw_pos = mcrfpy.Vector(7.5, 8.5)
    assert entity.draw_pos.x == 7.5, f"draw_pos.x wrong: {entity.draw_pos.x}"

    print("  PASS: entity vector setters")

def test_entity_no_grid_vector():
    """Entities without a grid should handle vector properties gracefully."""
    entity = mcrfpy.Entity()

    draw_pos = entity.draw_pos
    assert draw_pos is not None, "draw_pos should work without grid"

    cell_pos = entity.cell_pos
    assert cell_pos is not None, "cell_pos should work without grid"

    offset = entity.sprite_offset
    assert offset is not None, "sprite_offset should work without grid"

    print("  PASS: entity no-grid vector properties")

print("Testing issue #268: sfVector2f_to_PyObject NULL safety...")
test_entity_vector_properties()
test_entity_vector_setters()
test_entity_no_grid_vector()
print("All #268 tests passed.")
sys.exit(0)
