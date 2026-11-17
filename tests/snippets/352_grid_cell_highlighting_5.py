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

def get_movement_range(start_x, start_y, max_distance):
    """Get all reachable cells within movement range."""
    reachable = set()
    reachable.add((start_x, start_y))

    frontier = [(start_x, start_y, 0)]

    while frontier:
        x, y, dist = frontier.pop(0)

        if dist >= max_distance:
            continue

        # Check all adjacent cells
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy

            # Skip if already visited
            if (nx, ny) in reachable:
                continue

            # Check if walkable
            if grid.at(nx, ny).walkable:
                reachable.add((nx, ny))
                frontier.append((nx, ny, dist + 1))

    return reachable

def show_movement_range():
    """Display valid movement destinations."""
    px, py = int(player.cell_x), int(player.cell_y)
    movement_points = 5  # Player can move 5 tiles

    reachable = get_movement_range(px, py, movement_points)

    # Blue highlight for movement
    highlight_cells(reachable, mcrfpy.Color(50, 100, 255, 100))

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

current_ability = None

# region: multi-color
class HighlightManager:
    """Manage multiple highlight layers."""

    COLORS = {
        'move': mcrfpy.Color(50, 100, 255, 80),      # Blue
        'attack': mcrfpy.Color(255, 50, 50, 100),     # Red
        'heal': mcrfpy.Color(50, 255, 50, 100),       # Green
        'danger': mcrfpy.Color(255, 100, 0, 120),     # Orange
        'select': mcrfpy.Color(255, 255, 50, 150),    # Yellow
        'path': mcrfpy.Color(255, 255, 255, 80),      # White
    }

    def __init__(self, grid):
        self.grid = grid
        self.layer = mcrfpy.ColorLayer(name="highlight", z_index=1)
        grid.add_layer(self.layer)
        self.highlights = {}  # category -> set of cells

    def add(self, category, cells):
        """Add highlights for a category."""
        self.highlights[category] = set(cells)
        self._refresh()

    def remove(self, category):
        """Remove highlights for a category."""
        if category in self.highlights:
            del self.highlights[category]
            self._refresh()

    def clear(self):
        """Clear all highlights."""
        self.highlights = {}
        self.layer.fill(mcrfpy.Color(0, 0, 0, 0))

    def _refresh(self):
        """Redraw all highlights with proper layering."""
        self.layer.fill(mcrfpy.Color(0, 0, 0, 0))

        # Draw in priority order (later categories draw on top)
        priority = ['move', 'attack', 'heal', 'danger', 'path', 'select']

        for category in priority:
            if category in self.highlights:
                color = self.COLORS.get(category, mcrfpy.Color(128, 128, 128, 100))
                for x, y in self.highlights[category]:
                    self.layer.set((x, y), color)


# Usage example
highlights = HighlightManager(grid)

def on_ability_select(ability):
    """Show range when ability is selected."""
    highlights.clear()

    px, py = int(player.cell_x), int(player.cell_y)

    if ability == 'move':
        cells = get_movement_range(px, py, 5)
        highlights.add('move', cells)

    elif ability == 'attack':
        cells = get_radius_range(px, py, 3)
        highlights.add('attack', cells)

    elif ability == 'fireball':
        # Show cast range
        cast_range = get_radius_range(px, py, 8)
        highlights.add('move', cast_range)  # Blue for "where can I cast"
        # AoE preview added when hovering

def on_cell_hover(x, y):
    """Preview effect when hovering over a cell."""
    if current_ability == 'fireball':
        # Show explosion radius at cursor
        highlights.remove('danger')
        if (x, y) in highlights.highlights.get('move', set()):
            aoe = get_radius_range(x, y, 2, include_center=True)
            highlights.add('danger', aoe)
# endregion

on_ability_select("attack")
