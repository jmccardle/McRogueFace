"""
McRogueFace Tutorial - Part 2: Animated Movement

This tutorial builds on Part 1 by adding:
- Animation system for smooth movement
- Movement that takes 0.5 seconds per tile
- Input blocking during movement animation
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

grid.zoom = 3.0 # we're not using the zoom variable! It's going to be really big!

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
grid.center = (player.x + 0.5) * 16, (player.y + 0.5) * 16 # grid center is in texture/pixel coordinates

# Movement state tracking
is_moving = False
move_animations = []  # Track active animations

# Animation completion callback
def movement_complete(runtime):
    """Called when movement animation completes"""
    global is_moving
    is_moving = False
    # Ensure grid is centered on final position
    grid.center = (player.x + 0.5) * 16, (player.y + 0.5) * 16

motion_speed = 0.30 # seconds per tile
# Define keyboard handler
def handle_keys(key, state):
    """Handle keyboard input to move the player"""
    global is_moving, move_animations
    
    if state == "start" and not is_moving:  # Only respond to key press when not moving
        # Get current player position in grid coordinates
        px, py = player.x, player.y
        new_x, new_y = px, py
        
        # Calculate new position based on key press
        if key == "W" or key == "Up":
            new_y -= 1
        elif key == "S" or key == "Down":
            new_y += 1
        elif key == "A" or key == "Left":
            new_x -= 1
        elif key == "D" or key == "Right":
            new_x += 1
        
        # If position changed, start movement animation
        if new_x != px or new_y != py:
            is_moving = True
            
            # Create animations for player position
            anim_x = mcrfpy.Animation("x", float(new_x), motion_speed, "easeInOutQuad")
            anim_y = mcrfpy.Animation("y", float(new_y), motion_speed, "easeInOutQuad")
            anim_x.start(player)
            anim_y.start(player)
            
            # Animate grid center to follow player
            center_x = mcrfpy.Animation("center_x", (new_x + 0.5) * 16, motion_speed, "linear")
            center_y = mcrfpy.Animation("center_y", (new_y + 0.5) * 16, motion_speed, "linear")
            center_x.start(grid)
            center_y.start(grid)
            
            # Set a timer to mark movement as complete
            mcrfpy.setTimer("move_complete", movement_complete, 500)

# Register the keyboard handler
mcrfpy.keypressScene(handle_keys)

# Add a title caption
title = mcrfpy.Caption((320, 10),
    text="McRogueFace Tutorial - Part 2",
)
title.fill_color = mcrfpy.Color(255, 255, 255, 255)
mcrfpy.sceneUI("tutorial").append(title)

# Add instructions
instructions = mcrfpy.Caption((150, 750),
    text="Smooth movement! Each step takes 0.5 seconds.",
)
instructions.font_size=18
instructions.fill_color = mcrfpy.Color(200, 200, 200, 255)
mcrfpy.sceneUI("tutorial").append(instructions)

print("Tutorial Part 2 loaded!")
print(f"Player entity created at grid position (4, 4)")
print("Movement is now animated over 0.5 seconds per tile!")
print("Use WASD or Arrow keys to move!")
