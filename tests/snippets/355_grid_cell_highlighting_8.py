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
        cell.transparent = True

player = mcrfpy.Entity(grid_pos=(8, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

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

def get_adjacent(x, y):
    """Cells next to (x, y); the page leaves this one to you."""
    return {(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)}


class Ability:
    target_type = 'ranged'
    range = 4
    aoe_radius = 1


grid.compute_fov((8, 6), radius=8)

# region: targeting
class TargetingSystem:
    """Handle ability targeting with visual feedback."""

    def __init__(self, grid, player):
        self.grid = grid
        self.player = player
        self.highlights = HighlightManager(grid)
        self.current_ability = None
        self.valid_targets = set()

    def start_targeting(self, ability):
        """Begin targeting for an ability."""
        self.current_ability = ability
        px, py = int(self.player.cell_x), int(self.player.cell_y)

        # Get valid targets based on ability
        if ability.target_type == 'self':
            self.valid_targets = {(px, py)}
        elif ability.target_type == 'adjacent':
            self.valid_targets = get_adjacent(px, py)
        elif ability.target_type == 'ranged':
            self.valid_targets = get_radius_range(px, py, ability.range)
        elif ability.target_type == 'line':
            self.valid_targets = get_line_range(px, py, ability.range)

        # Filter to visible tiles only
        self.valid_targets = {
            (x, y) for x, y in self.valid_targets
            if grid.is_in_fov(x, y)
        }

        # Show valid targets
        self.highlights.add('attack', self.valid_targets)

    def update_hover(self, x, y):
        """Update when cursor moves."""
        if not self.current_ability:
            return

        # Clear previous AoE preview
        self.highlights.remove('danger')

        if (x, y) in self.valid_targets:
            # Valid target - highlight it
            self.highlights.add('select', [(x, y)])

            # Show AoE if applicable
            if self.current_ability.aoe_radius > 0:
                aoe = get_radius_range(x, y, self.current_ability.aoe_radius, True)
                self.highlights.add('danger', aoe)
        else:
            self.highlights.remove('select')

    def confirm_target(self, x, y):
        """Confirm target selection."""
        if (x, y) in self.valid_targets:
            self.cancel_targeting()
            return (x, y)
        return None

    def cancel_targeting(self):
        """Cancel targeting mode."""
        self.current_ability = None
        self.valid_targets = set()
        self.highlights.clear()
# endregion

targeting = TargetingSystem(grid, player)
targeting.start_targeting(Ability())
