# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene] verified=0.3.6-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0
)
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        cell.tilesprite = 48
        cell.walkable = True

player = mcrfpy.Entity(grid_pos=(8, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

# Create a highlight layer (above tiles, below entities)
highlight_layer = mcrfpy.ColorLayer(name="highlight", z_index=1)
grid.add_layer(highlight_layer)

def highlight_cells(cells, color):
    """Highlight a list of (x, y) coordinates."""
    highlight_layer.fill(mcrfpy.Color(0, 0, 0, 0))
    for x, y in cells:
        highlight_layer.set((x, y), color)

def clear_highlights():
    """Remove all highlighting."""
    highlight_layer.fill(mcrfpy.Color(0, 0, 0, 0))

# region: attack-range
def get_line_range(start_x, start_y, max_range):
    """Get cells in cardinal directions (ranged attack)."""
    cells = set()

    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        for dist in range(1, max_range + 1):
            x = start_x + dx * dist
            y = start_y + dy * dist

            # NOTE: grid.at(x, y) can go out of bounds here before the
            # transparent check runs - add an explicit bounds guard for
            # production use.
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
# endregion

for cells, color in [
    (get_radius_range(8, 6, 3), mcrfpy.Color(255, 50, 50, 100)),
    (get_line_range(8, 6, 5), mcrfpy.Color(255, 255, 50, 150)),
    (get_cone_range(8, 6, 'e', 6, 60), mcrfpy.Color(255, 100, 0, 120)),
]:
    for x, y in cells:
        highlight_layer.set((x, y), color)
