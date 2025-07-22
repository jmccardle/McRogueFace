"""
McRogueFace Tutorial - Part 4: Field of View

This tutorial builds on Part 3 by adding:
- Field of view calculation using grid.compute_fov()
- Entity perspective rendering with grid.perspective
- Three visibility states: unexplored (black), explored (dark), visible (lit)
- Memory of previously seen areas
- Enemy entity to demonstrate perspective switching

Key code references:
- tests/unit/test_tcod_fov_entities.py (lines 89-118) - FOV with multiple entities
- ROADMAP.md (lines 216-229) - FOV system implementation details
"""
import mcrfpy
import random

# Create and activate a new scene
mcrfpy.createScene("tutorial")
mcrfpy.setScene("tutorial")

# Load the texture (4x3 tiles, 64x48 pixels total, 16x16 per tile)
texture = mcrfpy.Texture("assets/tutorial2.png", 16, 16)

# Load the hero sprite texture
hero_texture = mcrfpy.Texture("assets/custom_player.png", 16, 16)

# Create a grid of tiles
grid_width, grid_height = 40, 30

# Calculate the size in pixels
zoom = 2.0
grid_size = grid_width * zoom * 16, grid_height * zoom * 16

# Calculate the position to center the grid on the screen
grid_position = (1024 - grid_size[0]) / 2, (768 - grid_size[1]) / 2

# Create the grid with a TCODMap for pathfinding/FOV
grid = mcrfpy.Grid(
    pos=grid_position,
    grid_size=(grid_width, grid_height),
    texture=texture,
    size=grid_size,
)

grid.zoom = zoom

# Define tile types
FLOOR_TILES = [0, 1, 2, 4, 5, 6, 8, 9, 10]
WALL_TILES = [3, 7, 11]

# Room class for BSP
class Room:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        self.w = w
        self.h = h
    
    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)
    
    def intersects(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

# Dungeon generation functions (from Part 3)
def carve_room(room):
    for x in range(room.x1, room.x2):
        for y in range(room.y1, room.y2):
            if 0 <= x < grid_width and 0 <= y < grid_height:
                point = grid.at(x, y)
                if point:
                    point.tilesprite = random.choice(FLOOR_TILES)
                    point.walkable = True
                    point.transparent = True

def carve_hallway(x1, y1, x2, y2):
    points = mcrfpy.libtcod.line(x1, y1, x2, y2)
    
    for x, y in points:
        if 0 <= x < grid_width and 0 <= y < grid_height:
            point = grid.at(x, y)
            if point:
                point.tilesprite = random.choice(FLOOR_TILES)
                point.walkable = True
                point.transparent = True

def generate_dungeon(max_rooms=10, room_min_size=4, room_max_size=10):
    rooms = []
    
    # Fill with walls
    for y in range(grid_height):
        for x in range(grid_width):
            point = grid.at(x, y)
            if point:
                point.tilesprite = random.choice(WALL_TILES)
                point.walkable = False
                point.transparent = False
    
    # Generate rooms
    for _ in range(max_rooms):
        w = random.randint(room_min_size, room_max_size)
        h = random.randint(room_min_size, room_max_size)
        x = random.randint(1, grid_width - w - 1)
        y = random.randint(1, grid_height - h - 1)
        
        new_room = Room(x, y, w, h)
        
        failed = False
        for other_room in rooms:
            if new_room.intersects(other_room):
                failed = True
                break
        
        if not failed:
            carve_room(new_room)
            
            if rooms:
                prev_x, prev_y = rooms[-1].center()
                new_x, new_y = new_room.center()
                carve_hallway(prev_x, prev_y, new_x, new_y)
            
            rooms.append(new_room)
    
    return rooms

# Generate the dungeon
rooms = generate_dungeon(max_rooms=8, room_min_size=4, room_max_size=8)

# Add the grid to the scene
mcrfpy.sceneUI("tutorial").append(grid)

# Spawn player in the first room
if rooms:
    spawn_x, spawn_y = rooms[0].center()
else:
    spawn_x, spawn_y = 4, 4

# Create a player entity
player = mcrfpy.Entity(
    (spawn_x, spawn_y),
    texture=hero_texture,
    sprite_index=0
)

# Add the player entity to the grid
grid.entities.append(player)

# Create an enemy entity in another room (to demonstrate perspective switching)
enemy = None
if len(rooms) > 1:
    enemy_x, enemy_y = rooms[1].center()
    enemy = mcrfpy.Entity(
        (enemy_x, enemy_y),
        texture=texture,
        sprite_index=117  # Enemy sprite
    )
    grid.entities.append(enemy)

# Set the grid perspective to the player by default
# Note: The new perspective system uses entity references directly
grid.perspective = player

# Initial FOV computation
def update_fov():
    """Update field of view from current perspective
    Referenced from test_tcod_fov_entities.py lines 89-118
    """
    if grid.perspective == player:
        grid.compute_fov(int(player.x), int(player.y), radius=8, algorithm=0)
    elif enemy and grid.perspective == enemy:
        grid.compute_fov(int(enemy.x), int(enemy.y), radius=6, algorithm=0)

# Perform initial FOV calculation
update_fov()

# Center grid on current perspective
def center_on_perspective():
    if grid.perspective == player:
        grid.center = (player.x + 0.5) * 16, (player.y + 0.5) * 16
    elif enemy and grid.perspective == enemy:
        grid.center = (enemy.x + 0.5) * 16, (enemy.y + 0.5) * 16

center_on_perspective()

# Movement state tracking (from Part 3)
is_moving = False
move_queue = []
current_destination = None
current_move = None

# Store animation references
player_anim_x = None
player_anim_y = None
grid_anim_x = None
grid_anim_y = None

def movement_complete(anim, target):
    """Called when movement animation completes"""
    global is_moving, move_queue, current_destination, current_move
    global player_anim_x, player_anim_y
    
    is_moving = False
    current_move = None
    current_destination = None
    player_anim_x = None
    player_anim_y = None
    
    # Update FOV after movement
    update_fov()
    center_on_perspective()
    
    if move_queue:
        next_move = move_queue.pop(0)
        process_move(next_move)

motion_speed = 0.20

def can_move_to(x, y):
    """Check if a position is valid for movement"""
    if x < 0 or x >= grid_width or y < 0 or y >= grid_height:
        return False
    
    point = grid.at(x, y)
    if point and point.walkable:
        return True
    return False

def process_move(key):
    """Process a move based on the key"""
    global is_moving, current_move, current_destination, move_queue
    global player_anim_x, player_anim_y, grid_anim_x, grid_anim_y
    
    # Only allow player movement when in player perspective
    if grid.perspective != player:
        return
    
    if is_moving:
        move_queue.clear()
        move_queue.append(key)
        return
    
    px, py = int(player.x), int(player.y)
    new_x, new_y = px, py
    
    if key == "W" or key == "Up":
        new_y -= 1
    elif key == "S" or key == "Down":
        new_y += 1
    elif key == "A" or key == "Left":
        new_x -= 1
    elif key == "D" or key == "Right":
        new_x += 1
    
    if new_x != px or new_y != py:
        if can_move_to(new_x, new_y):
            is_moving = True
            current_move = key
            current_destination = (new_x, new_y)
            
            if new_x != px:
                player_anim_x = mcrfpy.Animation("x", float(new_x), motion_speed, "easeInOutQuad", callback=movement_complete)
                player_anim_x.start(player)
            elif new_y != py:
                player_anim_y = mcrfpy.Animation("y", float(new_y), motion_speed, "easeInOutQuad", callback=movement_complete)
                player_anim_y.start(player)
            
            grid_anim_x = mcrfpy.Animation("center_x", (new_x + 0.5) * 16, motion_speed, "linear")
            grid_anim_y = mcrfpy.Animation("center_y", (new_y + 0.5) * 16, motion_speed, "linear")
            grid_anim_x.start(grid)
            grid_anim_y.start(grid)

def handle_keys(key, state):
    """Handle keyboard input"""
    if state == "start":
        # Movement keys
        if key in ["W", "Up", "S", "Down", "A", "Left", "D", "Right"]:
            process_move(key)
        
        # Perspective switching
        elif key == "Tab":
            # Switch perspective between player and enemy
            if enemy:
                if grid.perspective == player:
                    grid.perspective = enemy
                    print("Switched to enemy perspective")
                else:
                    grid.perspective = player
                    print("Switched to player perspective")
                
                # Update FOV and camera for new perspective
                update_fov()
                center_on_perspective()

# Register the keyboard handler
mcrfpy.keypressScene(handle_keys)

# Add UI elements
title = mcrfpy.Caption((320, 10),
    text="McRogueFace Tutorial - Part 4: Field of View",
)
title.fill_color = mcrfpy.Color(255, 255, 255, 255)
mcrfpy.sceneUI("tutorial").append(title)

instructions = mcrfpy.Caption((150, 720),
    text="Use WASD/Arrows to move. Press Tab to switch perspective!",
)
instructions.font_size = 18
instructions.fill_color = mcrfpy.Color(200, 200, 200, 255)
mcrfpy.sceneUI("tutorial").append(instructions)

# FOV info
fov_caption = mcrfpy.Caption((150, 745),
    text="FOV: Player (radius 8) | Enemy visible in other room",
)
fov_caption.font_size = 16
fov_caption.fill_color = mcrfpy.Color(100, 200, 255, 255)
mcrfpy.sceneUI("tutorial").append(fov_caption)

# Debug info
debug_caption = mcrfpy.Caption((10, 40),
    text=f"Grid: {grid_width}x{grid_height} | Rooms: {len(rooms)} | Perspective: Player",
)
debug_caption.font_size = 16
debug_caption.fill_color = mcrfpy.Color(255, 255, 0, 255)
mcrfpy.sceneUI("tutorial").append(debug_caption)

# Update function for perspective display
def update_perspective_display():
    current_perspective = "Player" if grid.perspective == player else "Enemy"
    debug_caption.text = f"Grid: {grid_width}x{grid_height} | Rooms: {len(rooms)} | Perspective: {current_perspective}"
    
    if grid.perspective == player:
        fov_caption.text = "FOV: Player (radius 8) | Tab to switch perspective"
    else:
        fov_caption.text = "FOV: Enemy (radius 6) | Tab to switch perspective"

# Timer to update display
def update_display(runtime):
    update_perspective_display()

mcrfpy.setTimer("display_update", update_display, 100)

print("Tutorial Part 4 loaded!")
print("Field of View system active!")
print("- Unexplored areas are black")
print("- Previously seen areas are dark") 
print("- Currently visible areas are lit")
print("Press Tab to switch between player and enemy perspective!")
print("Use WASD or Arrow keys to move!")