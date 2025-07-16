"""
McRogueFace Tutorial - Part 1: Entities and Keyboard Input

This tutorial builds on Part 0 by adding:
- Entity: A game object that can be placed in a grid
- Keyboard handling: Responding to key presses to move the entity
"""
import mcrfpy
import random

# Create and activate a new scene
mcrfpy.createScene("tutorial")
mcrfpy.setScene("tutorial")

# Load the texture (4x3 tiles, 64x48 pixels total, 16x16 per tile)
texture = mcrfpy.Texture("assets/tutorial2.png", 16, 16)

# Load the hero sprite texture (32x32 sprite sheet)
hero_texture = mcrfpy.Texture("assets/custom_player.png", 16, 16)

# Create a grid of tiles
# Each tile is 16x16 pixels, so with 3x zoom: 16*3 = 48 pixels per tile

grid_width, grid_height = 25, 20 # width, height in number of tiles

# calculating the size in pixels to fit the entire grid on-screen
zoom = 2.0
grid_size = grid_width * zoom * 16, grid_height * zoom * 16

# calculating the position to center the grid on the screen - assuming default 1024x768 resolution
grid_position = (1024 - grid_size[0]) / 2, (768 - grid_size[1]) / 2

grid = mcrfpy.Grid(
    pos=grid_position,
    grid_size=(grid_width, grid_height),
    texture=texture,
    size=grid_size,  # height and width on screen
)

grid.zoom = zoom
grid.center = (grid_width/2.0)*16, (grid_height/2.0)*16 # center on the middle of the central tile

# Define tile types
FLOOR_TILES = [0, 1, 2, 4, 5, 6, 8, 9, 10]
WALL_TILES = [3, 7, 11]

# Fill the grid with a simple pattern
for y in range(grid_height):
    for x in range(grid_width):
        # Create walls around the edges
        if x == 0 or x == grid_width-1 or y == 0 or y == grid_height-1:
            tile_index = random.choice(WALL_TILES)
        else:
            # Fill interior with floor tiles
            tile_index = random.choice(FLOOR_TILES)
        
        # Set the tile at this position
        point = grid.at(x, y)
        if point:
            point.tilesprite = tile_index

# Add the grid to the scene
mcrfpy.sceneUI("tutorial").append(grid)

# Create a player entity at position (4, 4)
player = mcrfpy.Entity(
    (4, 4),  # Entity positions are tile coordinates
    texture=hero_texture,
    sprite_index=0  # Use the first sprite in the texture
)

# Add the player entity to the grid
grid.entities.append(player)

# Define keyboard handler
def handle_keys(key, state):
    """Handle keyboard input to move the player"""
    if state == "start":  # Only respond to key press, not release
        # Get current player position in grid coordinates
        px, py = player.x, player.y 
        
        # Calculate new position based on key press
        if key == "W" or key == "Up":
            py -= 1
        elif key == "S" or key == "Down":
            py += 1
        elif key == "A" or key == "Left":
            px -= 1
        elif key == "D" or key == "Right":
            px += 1
        
        # Update player position (no collision checking yet)
        player.x = px 
        player.y = py

# Register the keyboard handler
mcrfpy.keypressScene(handle_keys)

# Add a title caption
title = mcrfpy.Caption((320, 10),
    text="McRogueFace Tutorial - Part 1",
)
title.fill_color = mcrfpy.Color(255, 255, 255, 255)
mcrfpy.sceneUI("tutorial").append(title)

# Add instructions
instructions = mcrfpy.Caption((200, 750),
    text="Use WASD or Arrow Keys to move the hero!",
)
instructions.font_size=18
instructions.fill_color = mcrfpy.Color(200, 200, 200, 255)
mcrfpy.sceneUI("tutorial").append(instructions)

print("Tutorial Part 1 loaded!")
print(f"Player entity created at grid position (4, 4)")
print("Use WASD or Arrow keys to move!")
