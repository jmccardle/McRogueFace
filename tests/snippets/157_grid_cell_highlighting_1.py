# mcrf: objects=[Color,ColorLayer,Grid,Scene] verified=0.2.8-dev status=ok
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

highlight_cells([(1, 1), (2, 1), (3, 1)], mcrfpy.Color(50, 100, 255, 100))
