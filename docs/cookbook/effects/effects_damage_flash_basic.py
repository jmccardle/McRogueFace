"""McRogueFace - Damage Flash Effect (basic)

Documentation: https://mcrogueface.github.io/cookbook/effects_damage_flash
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/effects/effects_damage_flash_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

# Add a color layer to your grid (do this once during setup)
grid.add_layer("color")
color_layer = grid.layers[-1]  # Get the color layer

def flash_cell(grid, x, y, color, duration=0.3):
    """Flash a grid cell with a color overlay."""
    # Get the color layer (assumes it's the last layer added)
    color_layer = None
    for layer in grid.layers:
        if isinstance(layer, mcrfpy.ColorLayer):
            color_layer = layer
            break

    if not color_layer:
        return

    # Set cell to flash color
    cell = color_layer.at(x, y)
    cell.color = mcrfpy.Color(color[0], color[1], color[2], 200)

    # Animate alpha back to 0
    anim = mcrfpy.Animation("a", 0.0, duration, "easeOut")
    anim.start(cell.color)

def damage_at_position(grid, x, y, duration=0.3):
    """Flash red at a grid position when damage occurs."""
    flash_cell(grid, x, y, (255, 0, 0), duration)

# Usage when entity takes damage
damage_at_position(grid, int(enemy.x), int(enemy.y))