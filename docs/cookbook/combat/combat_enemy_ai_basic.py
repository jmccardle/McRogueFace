"""McRogueFace - Basic Enemy AI (basic)

Documentation: https://mcrogueface.github.io/cookbook/combat_enemy_ai
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_enemy_ai_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import random

def wander(enemy, grid):
    """Move randomly to an adjacent walkable tile."""
    ex, ey = int(enemy.x), int(enemy.y)

    # Get valid adjacent tiles
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    random.shuffle(directions)

    for dx, dy in directions:
        new_x, new_y = ex + dx, ey + dy

        if is_walkable(grid, new_x, new_y) and not is_occupied(new_x, new_y):
            enemy.x = new_x
            enemy.y = new_y
            return

    # No valid moves - stay in place

def is_walkable(grid, x, y):
    """Check if a tile can be walked on."""
    grid_w, grid_h = grid.grid_size
    if x < 0 or x >= grid_w or y < 0 or y >= grid_h:
        return False
    return grid.at(x, y).walkable

def is_occupied(x, y, entities=None):
    """Check if a tile is occupied by another entity."""
    if entities is None:
        return False

    for entity in entities:
        if int(entity.x) == x and int(entity.y) == y:
            return True
    return False