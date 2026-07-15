# mcrf: objects=[Entity,Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy

# Create scene and grid
scene = mcrfpy.Scene("game")
mcrfpy.current_scene = scene

texture = mcrfpy.default_texture
grid = mcrfpy.Grid(grid_size=(50, 50), texture=texture, pos=(0, 0), size=(800, 600))
scene.children.append(grid)

# Add player entity
player = mcrfpy.Entity(grid_pos=(25, 25), texture=texture, sprite_index=0)
grid.entities.append(player)

# Set player as the perspective entity - the view now renders fog of war
# based on what the player has seen (unseen cells drawn black, discovered
# cells dimmed). Set to None for an omniscient (fully-lit) view.
grid.perspective = player
grid.fov_radius = 10
