"""
McRogueFace Tutorial - Part 3: Procedural Dungeon Generation

This tutorial builds on Part 2 by adding:
- Binary Space Partition (BSP) dungeon generation
- Rooms connected by hallways using libtcod.line()
- Walkable/non-walkable terrain
- Player spawning in a valid location
- Wall tiles that block movement

Key code references:
- src/scripts/cos_level.py (lines 7-15, 184-217, 218-224) - BSP algorithm
- mcrfpy.libtcod.line() for smooth hallway generation
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
grid_width, grid_height = 40, 30  # Larger grid for dungeon

# Calculate the size in pixels to fit the entire grid on-screen
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
        """Return the center coordinates of the room"""
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)
    
    def intersects(self, other):
        """Return True if this room overlaps with another"""
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

# Dungeon generation functions
def carve_room(room):
    """Carve out a room in the grid - referenced from cos_level.py lines 117-120"""
    # Using individual updates for now (batch updates would be more efficient)
    for x in range(room.x1, room.x2):
        for y in range(room.y1, room.y2):
            if 0 <= x < grid_width and 0 <= y < grid_height:
                point = grid.at(x, y)
                if point:
                    point.tilesprite = random.choice(FLOOR_TILES)
                    point.walkable = True
                    point.transparent = True

def carve_hallway(x1, y1, x2, y2):
    """Carve a hallway between two points using libtcod.line()
    Referenced from cos_level.py lines 184-217, improved with libtcod.line()
    """
    # Get all points along the line

    # Simple solution: works if your characters have diagonal movement
    #points = mcrfpy.libtcod.line(x1, y1, x2, y2)

    # We don't, so we're going to carve a path with an elbow in it
    points = []
    if random.choice([True, False]):
        # x1,y1 -> x2,y1 -> x2,y2
        points.extend(mcrfpy.libtcod.line(x1, y1, x2, y1))
        points.extend(mcrfpy.libtcod.line(x2, y1, x2, y2))
    else:
        # x1,y1 -> x1,y2 -> x2,y2
        points.extend(mcrfpy.libtcod.line(x1, y1, x1, y2))
        points.extend(mcrfpy.libtcod.line(x1, y2, x2, y2))

    
    # Carve out each point
    for x, y in points:
        if 0 <= x < grid_width and 0 <= y < grid_height:
            point = grid.at(x, y)
            if point:
                point.tilesprite = random.choice(FLOOR_TILES)
                point.walkable = True
                point.transparent = True

def generate_dungeon(max_rooms=10, room_min_size=4, room_max_size=10):
    """Generate a dungeon using simplified BSP approach
    Referenced from cos_level.py lines 218-224
    """
    rooms = []
    
    # First, fill everything with walls
    for y in range(grid_height):
        for x in range(grid_width):
            point = grid.at(x, y)
            if point:
                point.tilesprite = random.choice(WALL_TILES)
                point.walkable = False
                point.transparent = False
    
    # Generate rooms
    for _ in range(max_rooms):
        # Random room size
        w = random.randint(room_min_size, room_max_size)
        h = random.randint(room_min_size, room_max_size)
        
        # Random position (with margin from edges)
        x = random.randint(1, grid_width - w - 1)
        y = random.randint(1, grid_height - h - 1)
        
        new_room = Room(x, y, w, h)
        
        # Check if it overlaps with existing rooms
        failed = False
        for other_room in rooms:
            if new_room.intersects(other_room):
                failed = True
                break
        
        if not failed:
            # Carve out the room
            carve_room(new_room)
            
            # If not the first room, connect to previous room
            if rooms:
                # Get centers
                prev_x, prev_y = rooms[-1].center()
                new_x, new_y = new_room.center()
                
                # Carve hallway using libtcod.line()
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
    # Fallback spawn position
    spawn_x, spawn_y = 4, 4

# Create a player entity at the spawn position
player = mcrfpy.Entity(
    (spawn_x, spawn_y),
    texture=hero_texture,
    sprite_index=0
)

# Add the player entity to the grid
grid.entities.append(player)
grid.center = (player.x + 0.5) * 16, (player.y + 0.5) * 16

# Movement state tracking (from Part 2)
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
    
    grid.center = (player.x + 0.5) * 16, (player.y + 0.5) * 16
    
    if move_queue:
        next_move = move_queue.pop(0)
        process_move(next_move)

motion_speed = 0.20  # Slightly faster for dungeon exploration

def can_move_to(x, y):
    """Check if a position is valid for movement"""
    # Boundary check
    if x < 0 or x >= grid_width or y < 0 or y >= grid_height:
        return False
    
    # Walkability check
    point = grid.at(x, y)
    if point and point.walkable:
        return True
    return False

def process_move(key):
    """Process a move based on the key"""
    global is_moving, current_move, current_destination, move_queue
    global player_anim_x, player_anim_y, grid_anim_x, grid_anim_y
    
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
    
    # Check if we can move to the new position
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
        else:
            # Play a "bump" sound or visual feedback here
            print(f"Can't move to ({new_x}, {new_y}) - blocked!")

def handle_keys(key, state):
    """Handle keyboard input to move the player"""
    if state == "start":
        if key in ["W", "Up", "S", "Down", "A", "Left", "D", "Right"]:
            process_move(key)

# Register the keyboard handler
mcrfpy.keypressScene(handle_keys)

# Add UI elements
title = mcrfpy.Caption((320, 10),
    text="McRogueFace Tutorial - Part 3: Dungeon Generation",
)
title.fill_color = mcrfpy.Color(255, 255, 255, 255)
mcrfpy.sceneUI("tutorial").append(title)

instructions = mcrfpy.Caption((150, 750),
    text=f"Procedural dungeon with {len(rooms)} rooms connected by hallways!",
)
instructions.font_size = 18
instructions.fill_color = mcrfpy.Color(200, 200, 200, 255)
mcrfpy.sceneUI("tutorial").append(instructions)

# Debug info
debug_caption = mcrfpy.Caption((10, 40),
    text=f"Grid: {grid_width}x{grid_height} | Player spawned at ({spawn_x}, {spawn_y})",
)
debug_caption.font_size = 16
debug_caption.fill_color = mcrfpy.Color(255, 255, 0, 255)
mcrfpy.sceneUI("tutorial").append(debug_caption)

print("Tutorial Part 3 loaded!")
print(f"Generated dungeon with {len(rooms)} rooms")
print(f"Player spawned at ({spawn_x}, {spawn_y})")
print("Walls now block movement!")
print("Use WASD or Arrow keys to explore the dungeon!")
