# mcrf: objects=[Entity,FOV,Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("fov-demo")
mcrfpy.current_scene = scene

# Create grid and set algorithm
grid = mcrfpy.Grid(grid_size=(80, 45), texture=mcrfpy.default_texture, pos=(0, 0), size=(800, 450))
grid.fov = mcrfpy.FOV.SHADOW
grid.fov_radius = 10
scene.children.append(grid)

player = mcrfpy.Entity(grid_pos=(5, 5), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

enemies = [mcrfpy.Entity(grid_pos=(10, 10), texture=mcrfpy.default_texture, sprite_index=85)]
for enemy in enemies:
    grid.entities.append(enemy)

# Compute FOV from the player's tile position (radius defaults to grid.fov_radius when omitted)
grid.compute_fov(player.grid_pos)

# Use in visibility checks
for enemy in enemies:
    if grid.is_in_fov(enemy.grid_x, enemy.grid_y):
        enemy.visible = True
