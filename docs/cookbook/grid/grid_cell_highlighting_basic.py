"""McRogueFace - Cell Highlighting (Targeting) (basic)

Documentation: https://mcrogueface.github.io/cookbook/grid_cell_highlighting
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/grid/grid_cell_highlighting_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

def get_line_range(start_x, start_y, max_range):
    """Get cells in cardinal directions (ranged attack)."""
    cells = set()

    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        for dist in range(1, max_range + 1):
            x = start_x + dx * dist
            y = start_y + dy * dist

            # Stop if wall blocks line of sight
            if not grid.at(x, y).transparent:
                break

            cells.add((x, y))

    return cells

def get_radius_range(center_x, center_y, radius, include_center=False):
    """Get cells within a radius (spell area)."""
    cells = set()

    for x in range(center_x - radius, center_x + radius + 1):
        for y in range(center_y - radius, center_y + radius + 1):
            # Euclidean distance
            dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            if dist <= radius:
                if include_center or (x, y) != (center_x, center_y):
                    cells.add((x, y))

    return cells

def get_cone_range(origin_x, origin_y, direction, length, spread):
    """Get cells in a cone (breath attack)."""
    import math
    cells = set()

    # Direction angles (in radians)
    angles = {
        'n': -math.pi / 2,
        's': math.pi / 2,
        'e': 0,
        'w': math.pi,
        'ne': -math.pi / 4,
        'nw': -3 * math.pi / 4,
        'se': math.pi / 4,
        'sw': 3 * math.pi / 4
    }

    base_angle = angles.get(direction, 0)
    half_spread = math.radians(spread / 2)

    for x in range(origin_x - length, origin_x + length + 1):
        for y in range(origin_y - length, origin_y + length + 1):
            dx = x - origin_x
            dy = y - origin_y
            dist = (dx * dx + dy * dy) ** 0.5

            if dist > 0 and dist <= length:
                angle = math.atan2(dy, dx)
                angle_diff = abs((angle - base_angle + math.pi) % (2 * math.pi) - math.pi)

                if angle_diff <= half_spread:
                    cells.add((x, y))

    return cells