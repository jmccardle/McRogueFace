"""Test texture display bounds for non-uniform sprite content (#235).

Verifies that Texture accepts display_size and display_origin parameters
to crop sprite rendering to a sub-region within each atlas cell.
"""
import mcrfpy
import sys

def test_default_display_bounds():
    """Without display bounds, display dims equal sprite dims."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    assert tex.display_width == 16, f"Expected 16, got {tex.display_width}"
    assert tex.display_height == 16, f"Expected 16, got {tex.display_height}"
    assert tex.display_offset_x == 0, f"Expected 0, got {tex.display_offset_x}"
    assert tex.display_offset_y == 0, f"Expected 0, got {tex.display_offset_y}"
    print("  PASS: default display bounds")

def test_custom_display_size():
    """display_size crops sprite content within cells."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16,
                         display_size=(12, 14))
    assert tex.display_width == 12, f"Expected 12, got {tex.display_width}"
    assert tex.display_height == 14, f"Expected 14, got {tex.display_height}"
    assert tex.sprite_width == 16, f"sprite_width should be unchanged: {tex.sprite_width}"
    assert tex.sprite_height == 16, f"sprite_height should be unchanged: {tex.sprite_height}"
    print("  PASS: custom display size")

def test_custom_display_origin():
    """display_origin offsets content within cells."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16,
                         display_size=(12, 14), display_origin=(2, 1))
    assert tex.display_offset_x == 2, f"Expected 2, got {tex.display_offset_x}"
    assert tex.display_offset_y == 1, f"Expected 1, got {tex.display_offset_y}"
    print("  PASS: custom display origin")

def test_display_bounds_sprite_creation():
    """Sprites created from bounded textures should work in UI elements."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16,
                         display_size=(12, 14), display_origin=(2, 1))
    sprite = mcrfpy.Sprite(pos=(10, 10), texture=tex, sprite_index=0)
    assert sprite is not None, "Sprite creation with display bounds failed"
    print("  PASS: sprite creation with display bounds")

def test_display_bounds_in_grid():
    """Entities using bounded textures should render in grids."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16,
                         display_size=(12, 14), display_origin=(2, 1))
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex)
    entity = mcrfpy.Entity(grid_pos=(3, 3), texture=tex, sprite_index=5, grid=grid)
    assert entity is not None, "Entity creation with display bounds failed"
    print("  PASS: entity with display bounds in grid")

print("Testing #235: Texture display bounds...")
test_default_display_bounds()
test_custom_display_size()
test_custom_display_origin()
test_display_bounds_sprite_creation()
test_display_bounds_in_grid()
print("All #235 tests passed.")
sys.exit(0)
