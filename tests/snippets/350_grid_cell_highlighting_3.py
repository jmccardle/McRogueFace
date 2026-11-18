# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene] verified=0.3.6 status=ok
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

# region: movement-range
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
# endregion

show_movement_range()
