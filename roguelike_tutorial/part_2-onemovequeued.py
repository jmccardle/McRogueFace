"""
McRogueFace Tutorial - Part 2: Enhanced with Single Move Queue

This tutorial builds on Part 2 by adding:
- Single queued move system for responsive input
- Debug display showing position and queue status
- Smooth continuous movement when keys are held
- Animation callbacks to prevent race conditions
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
move_queue = []  # List to store queued moves (max 1 item)
#last_position = (4, 4)  # Track last position
current_destination = None  # Track where we're currently moving to
current_move = None  # Track current move direction

# Store animation references
player_anim_x = None
player_anim_y = None
grid_anim_x = None
grid_anim_y = None

# Debug display caption
debug_caption = mcrfpy.Caption((10, 40),
    text="Last: (4, 4) | Queue: 0 | Dest: None",
)
debug_caption.font_size = 16
debug_caption.fill_color = mcrfpy.Color(255, 255, 0, 255)
mcrfpy.sceneUI("tutorial").append(debug_caption)

# Additional debug caption for movement state
move_debug_caption = mcrfpy.Caption((10, 60),
    text="Moving: False | Current: None | Queued: None",
)
move_debug_caption.font_size = 16
move_debug_caption.fill_color = mcrfpy.Color(255, 200, 0, 255)
mcrfpy.sceneUI("tutorial").append(move_debug_caption)

def key_to_direction(key):
    """Convert key to direction string"""
    if key == "W" or key == "Up":
        return "Up"
    elif key == "S" or key == "Down":
        return "Down"
    elif key == "A" or key == "Left":
        return "Left"
    elif key == "D" or key == "Right":
        return "Right"
    return None

def update_debug_display():
    """Update the debug caption with current state"""
    queue_count = len(move_queue)
    dest_text = f"({current_destination[0]}, {current_destination[1]})" if current_destination else "None"
    debug_caption.text = f"Last: ({player.x}, {player.y}) | Queue: {queue_count} | Dest: {dest_text}"
    
    # Update movement state debug
    current_dir = key_to_direction(current_move) if current_move else "None"
    queued_dir = key_to_direction(move_queue[0]) if move_queue else "None"
    move_debug_caption.text = f"Moving: {is_moving} | Current: {current_dir} | Queued: {queued_dir}"

# Animation completion callback
def movement_complete(anim, target):
    """Called when movement animation completes"""
    global is_moving, move_queue, current_destination, current_move
    global player_anim_x, player_anim_y
    print(f"In callback for animation: {anim=} {target=}")
    # Clear movement state
    is_moving = False
    current_move = None
    current_destination = None
    # Clear animation references
    player_anim_x = None
    player_anim_y = None
    
    # Update last position to where we actually are now
    #last_position = (int(player.x), int(player.y))
    
    # Ensure grid is centered on final position
    grid.center = (player.x + 0.5) * 16, (player.y + 0.5) * 16
    
    # Check if there's a queued move
    if move_queue:
        # Pop the next move from the queue
        next_move = move_queue.pop(0)
        print(f"Processing queued move: {next_move}")
        # Process it like a fresh input
        process_move(next_move)
    
    update_debug_display()

motion_speed = 0.30 # seconds per tile

def process_move(key):
    """Process a move based on the key"""
    global is_moving, current_move, current_destination, move_queue
    global player_anim_x, player_anim_y, grid_anim_x, grid_anim_y
    
    # If already moving, just update the queue
    if is_moving:
        print(f"process_move processing {key=} as a queued move (is_moving = True)")
        # Clear queue and add new move (only keep 1 queued move)
        move_queue.clear()
        move_queue.append(key)
        update_debug_display()
        return
    print(f"process_move processing {key=} as a new, immediate animation (is_moving = False)")
    # Calculate new position from current position
    px, py = int(player.x), int(player.y)
    new_x, new_y = px, py
    
    # Calculate new position based on key press (only one tile movement)
    if key == "W" or key == "Up":
        new_y -= 1
    elif key == "S" or key == "Down":
        new_y += 1
    elif key == "A" or key == "Left":
        new_x -= 1
    elif key == "D" or key == "Right":
        new_x += 1
    
    # Start the move if position changed
    if new_x != px or new_y != py:
        is_moving = True
        current_move = key
        current_destination = (new_x, new_y)
        # only animate a single axis, same callback from either
        if new_x != px:
            player_anim_x = mcrfpy.Animation("x", float(new_x), motion_speed, "easeInOutQuad", callback=movement_complete)
            player_anim_x.start(player)
        elif new_y != py:
            player_anim_y = mcrfpy.Animation("y", float(new_y), motion_speed, "easeInOutQuad", callback=movement_complete)
            player_anim_y.start(player)
        
        # Animate grid center to follow player
        grid_anim_x = mcrfpy.Animation("center_x", (new_x + 0.5) * 16, motion_speed, "linear")
        grid_anim_y = mcrfpy.Animation("center_y", (new_y + 0.5) * 16, motion_speed, "linear")
        grid_anim_x.start(grid)
        grid_anim_y.start(grid)
        
        update_debug_display()

# Define keyboard handler
def handle_keys(key, state):
    """Handle keyboard input to move the player"""
    if state == "start":
        # Only process movement keys
        if key in ["W", "Up", "S", "Down", "A", "Left", "D", "Right"]:
            print(f"handle_keys producing actual input: {key=}")
            process_move(key)


# Register the keyboard handler
mcrfpy.keypressScene(handle_keys)

# Add a title caption
title = mcrfpy.Caption((320, 10),
    text="McRogueFace Tutorial - Part 2 Enhanced",
)
title.fill_color = mcrfpy.Color(255, 255, 255, 255)
mcrfpy.sceneUI("tutorial").append(title)

# Add instructions
instructions = mcrfpy.Caption((150, 750),
    text="One-move queue system with animation callbacks!",
)
instructions.font_size=18
instructions.fill_color = mcrfpy.Color(200, 200, 200, 255)
mcrfpy.sceneUI("tutorial").append(instructions)

print("Tutorial Part 2 Enhanced loaded!")
print(f"Player entity created at grid position (4, 4)")
print("Movement now uses animation callbacks to prevent race conditions!")
print("Use WASD or Arrow keys to move!")
