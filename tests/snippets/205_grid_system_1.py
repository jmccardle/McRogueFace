# mcrf: objects=[Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy

# Create a scene first
scene = mcrfpy.Scene("game")
mcrfpy.current_scene = scene

# Basic grid creation
grid = mcrfpy.Grid(
    grid_size=(50, 50),      # 50x50 tiles
    texture=mcrfpy.default_texture,  # Built-in tileset
    pos=(0, 0),              # Screen position
    size=(800, 600)          # Display size in pixels
)

# Add to scene
scene.children.append(grid)
