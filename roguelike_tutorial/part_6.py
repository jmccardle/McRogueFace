"""
McRogueFace Tutorial - Part 6: Turn-based enemy movement

This tutorial builds on Part 5 by adding:
- Turn cycles where enemies move after the player
- Enemy AI that pursues or wanders
- Shared collision detection for all entities
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
    #points = mcrfpy.libtcod.line(x1, y1, x2, y2)
    points = []
    if random.choice([True, False]):
        # x1,y1 -> x2,y1 -> x2,y2
        points.extend(mcrfpy.libtcod.line(x1, y1, x2, y1))
        points.extend(mcrfpy.libtcod.line(x2, y1, x2, y2))
    else:
        # x1,y1 -> x1,y2 -> x2,y2
        points.extend(mcrfpy.libtcod.line(x1, y1, x1, y2))
        points.extend(mcrfpy.libtcod.line(x1, y2, x2, y2))

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

class GameEntity(mcrfpy.Entity):
    """An entity whose default behavior is to prevent others from moving into its tile."""

    def __init__(self, x, y, walkable=False, **kwargs):
        super().__init__(x=x, y=y, **kwargs)
        self.walkable = walkable
        self.dest_x = x
        self.dest_y = y
        self.is_moving = False

    def get_position(self):
        """Get logical position (destination if moving, otherwise current)"""
        if self.is_moving:
            return (self.dest_x, self.dest_y)
        return (int(self.x), int(self.y))

    def on_bump(self, other):
        return self.walkable # allow other's motion to proceed if entity is walkable

    def __repr__(self):
        return f"<{self.__class__.__name__} x={self.x}, y={self.y}, sprite_index={self.sprite_index}>"

class CombatEntity(GameEntity):
    def __init__(self, x, y, hp=10, damage=(1,3), **kwargs):
        super().__init__(x=x, y=y, **kwargs)
        self.hp = hp
        self.damage = damage

    def is_dead(self):
        return self.hp <= 0
    
    def start_move(self, new_x, new_y, duration=0.2, callback=None):
        """Start animating movement to new position"""
        self.dest_x = new_x
        self.dest_y = new_y
        self.is_moving = True
        
        # Define completion callback that resets is_moving
        def movement_done(anim, entity):
            self.is_moving = False
            if callback:
                callback(anim, entity)
        
        # Create animations for smooth movement
        anim_x = mcrfpy.Animation("x", float(new_x), duration, "easeInOutQuad", callback=movement_done)
        anim_y = mcrfpy.Animation("y", float(new_y), duration, "easeInOutQuad")
        
        anim_x.start(self)
        anim_y.start(self)
    
    def can_see(self, target_x, target_y):
        """Check if this entity can see the target position"""
        mx, my = self.get_position()
        
        # Simple distance check first
        dist = abs(target_x - mx) + abs(target_y - my)
        if dist > 6:
            return False
        
        # Line of sight check
        line = list(mcrfpy.libtcod.line(mx, my, target_x, target_y))
        for x, y in line[1:-1]:  # Skip start and end
            cell = grid.at(x, y)
            if cell and not cell.transparent:
                return False
        return True
    
    def ai_turn(self, player_pos):
        """Decide next move"""
        mx, my = self.get_position()
        px, py = player_pos
        
        # Simple AI: move toward player if visible
        if self.can_see(px, py):
            # Calculate direction toward player
            dx = 0
            dy = 0
            if px > mx:
                dx = 1
            elif px < mx:
                dx = -1
            if py > my:
                dy = 1
            elif py < my:
                dy = -1
                
            # Prefer cardinal movement
            if dx != 0 and dy != 0:
                # Pick horizontal or vertical based on greater distance
                if abs(px - mx) > abs(py - my):
                    dy = 0
                else:
                    dx = 0
                    
            return (mx + dx, my + dy)
        else:
            # Random wander
            dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
            return (mx + dx, my + dy)
    
    def ai_turn_dijkstra(self):
        """Decide next move using precomputed Dijkstra map"""
        mx, my = self.get_position()
        
        # Get current distance to player
        current_dist = grid.get_dijkstra_distance(mx, my)
        if current_dist is None or current_dist > 20:
            # Too far or unreachable - random wander
            dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
            return (mx + dx, my + dy)
        
        # Check all adjacent cells for best move
        best_moves = []
        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
            nx, ny = mx + dx, my + dy
            
            # Skip if out of bounds
            if nx < 0 or nx >= grid_width or ny < 0 or ny >= grid_height:
                continue
                
            # Skip if not walkable
            cell = grid.at(nx, ny)
            if not cell or not cell.walkable:
                continue
            
            # Get distance from this cell
            dist = grid.get_dijkstra_distance(nx, ny)
            if dist is not None:
                best_moves.append((dist, nx, ny))
        
        if best_moves:
            # Sort by distance
            best_moves.sort()
            
            # If multiple moves have the same best distance, pick randomly
            best_dist = best_moves[0][0]
            equal_moves = [(nx, ny) for dist, nx, ny in best_moves if dist == best_dist]
            
            if len(equal_moves) > 1:
                # Random choice among equally good moves
                nx, ny = random.choice(equal_moves)
            else:
                _, nx, ny = best_moves[0]
                
            return (nx, ny)
        else:
            # No valid moves
            return (mx, my)

# Create a player entity
player = CombatEntity(
    spawn_x, spawn_y,
    texture=hero_texture,
    sprite_index=0
)

# Add the player entity to the grid
grid.entities.append(player)

# Track all enemies
enemies = []

# Spawn enemies in other rooms
for i, room in enumerate(rooms[1:], 1):  # Skip first room (player spawn)
    if i <= 3:  # Limit to 3 enemies for now
        enemy_x, enemy_y = room.center()
        enemy = CombatEntity(
            enemy_x, enemy_y,
            texture=hero_texture,
            sprite_index=0  # Enemy sprite (borrow player's)
        )
        grid.entities.append(enemy)
        enemies.append(enemy)

# Set the grid perspective to the player by default
# Note: The new perspective system uses entity references directly
grid.perspective = player

# Initial FOV computation
def update_fov():
    """Update field of view from current perspective"""
    if grid.perspective == player:
        grid.compute_fov(int(player.x), int(player.y), radius=8, algorithm=0)
        player.update_visibility()

# Perform initial FOV calculation
update_fov()

# Center grid on current perspective
def center_on_perspective():
    if grid.perspective == player:
        grid.center = (player.x + 0.5) * 16, (player.y + 0.5) * 16

center_on_perspective()

# Movement state tracking (from Part 3)
#is_moving = False # make it an entity property
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
    global move_queue, current_destination, current_move
    global player_anim_x, player_anim_y, is_player_turn
    
    player.is_moving = False
    current_move = None
    current_destination = None
    player_anim_x = None
    player_anim_y = None
    
    # Update FOV after movement
    update_fov()
    center_on_perspective()
    
    # Player turn complete, start enemy turns and queued player move simultaneously
    is_player_turn = False
    process_enemy_turns_and_player_queue()

motion_speed = 0.20
is_player_turn = True  # Track whose turn it is

def get_blocking_entity_at(x, y):
    """Get blocking entity at position"""
    for e in grid.entities:
        if not e.walkable and (x, y) == e.get_position():
            return e
    return None

def can_move_to(x, y, mover=None):
    """Check if a position is valid for movement"""
    if x < 0 or x >= grid_width or y < 0 or y >= grid_height:
        return False
    
    point = grid.at(x, y)
    if not point or not point.walkable:
        return False
        
    # Check for blocking entities
    blocker = get_blocking_entity_at(x, y)
    if blocker and blocker != mover:
        return False
        
    return True

def process_enemy_turns_and_player_queue():
    """Process all enemy AI decisions and player's queued move simultaneously"""
    global is_player_turn, move_queue
    
    # Compute Dijkstra map once for all enemies (if using Dijkstra)
    if USE_DIJKSTRA:
        px, py = player.get_position()
        grid.compute_dijkstra(px, py, diagonal_cost=1.41)
    
    enemies_to_move = []
    claimed_positions = set()  # Track where enemies plan to move
    
    # Collect all enemy moves
    for i, enemy in enumerate(enemies):
        if enemy.is_dead():
            continue
            
        # AI decides next move
        if USE_DIJKSTRA:
            target_x, target_y = enemy.ai_turn_dijkstra()
        else:
            target_x, target_y = enemy.ai_turn(player.get_position())
        
        # Check if move is valid and not claimed by another enemy
        if can_move_to(target_x, target_y, enemy) and (target_x, target_y) not in claimed_positions:
            enemies_to_move.append((enemy, target_x, target_y))
            claimed_positions.add((target_x, target_y))
    
    # Start all enemy animations simultaneously
    any_enemy_moved = False
    if enemies_to_move:
        for enemy, tx, ty in enemies_to_move:
            enemy.start_move(tx, ty, duration=motion_speed)
            any_enemy_moved = True
    
    # Process player's queued move at the same time
    if move_queue:
        next_move = move_queue.pop(0)
        process_player_queued_move(next_move)
    else:
        # No queued move, set up callback to return control when animations finish
        if any_enemy_moved:
            # Wait for animations to complete
            mcrfpy.setTimer("turn_complete", check_turn_complete, int(motion_speed * 1000) + 50)
        else:
            # No animations, return control immediately
            is_player_turn = True

def process_player_queued_move(key):
    """Process player's queued move during enemy turn"""
    global current_move, current_destination
    global player_anim_x, player_anim_y, grid_anim_x, grid_anim_y
    
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
        # Check destination at animation end time (considering enemy destinations)
        future_blocker = get_future_blocking_entity_at(new_x, new_y)
        
        if future_blocker:
            # Will bump at destination
            # Schedule bump for when animations complete
            mcrfpy.setTimer("delayed_bump", lambda t: handle_delayed_bump(future_blocker), int(motion_speed * 1000))
        elif can_move_to(new_x, new_y, player):
            # Valid move, start animation
            player.is_moving = True
            current_move = key
            current_destination = (new_x, new_y)
            player.dest_x = new_x
            player.dest_y = new_y
            
            # Player animation with callback
            player_anim_x = mcrfpy.Animation("x", float(new_x), motion_speed, "easeInOutQuad", callback=player_queued_move_complete)
            player_anim_x.start(player)
            player_anim_y = mcrfpy.Animation("y", float(new_y), motion_speed, "easeInOutQuad")
            player_anim_y.start(player)
            
            # Move camera with player
            grid_anim_x = mcrfpy.Animation("center_x", (new_x + 0.5) * 16, motion_speed, "linear")
            grid_anim_y = mcrfpy.Animation("center_y", (new_y + 0.5) * 16, motion_speed, "linear")
            grid_anim_x.start(grid)
            grid_anim_y.start(grid)
        else:
            # Blocked by wall, wait for turn to complete
            mcrfpy.setTimer("turn_complete", check_turn_complete, int(motion_speed * 1000) + 50)

def get_future_blocking_entity_at(x, y):
    """Get entity that will be blocking at position after current animations"""
    for e in grid.entities:
        if not e.walkable and (x, y) == (e.dest_x, e.dest_y):
            return e
    return None

def handle_delayed_bump(entity):
    """Handle bump after animations complete"""
    global is_player_turn
    entity.on_bump(player)
    is_player_turn = True

def player_queued_move_complete(anim, target):
    """Called when player's queued movement completes"""
    global is_player_turn
    player.is_moving = False
    update_fov()
    center_on_perspective()
    is_player_turn = True

def check_turn_complete(timer_name):
    """Check if all animations are complete"""
    global is_player_turn
    
    # Check if any entity is still moving
    if player.is_moving:
        mcrfpy.setTimer("turn_complete", check_turn_complete, 50)
        return
        
    for enemy in enemies:
        if enemy.is_moving:
            mcrfpy.setTimer("turn_complete", check_turn_complete, 50)
            return
    
    # All done
    is_player_turn = True

def process_move(key):
    """Process a move based on the key"""
    global current_move, current_destination, move_queue
    global player_anim_x, player_anim_y, grid_anim_x, grid_anim_y, is_player_turn
    
    # Only allow player movement on player's turn
    if not is_player_turn:
        return
    
    # Only allow player movement when in player perspective
    if grid.perspective != player:
        return
    
    if player.is_moving:
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
        # Check what's at destination
        blocker = get_blocking_entity_at(new_x, new_y)
        
        if blocker:
            # Bump interaction (combat will go here later)
            blocker.on_bump(player)
            # Still counts as a turn
            is_player_turn = False
            process_enemy_turns_and_player_queue()
        elif can_move_to(new_x, new_y, player):
            player.is_moving = True
            current_move = key
            current_destination = (new_x, new_y)
            player.dest_x = new_x
            player.dest_y = new_y
            
            # Start player move animation
            player_anim_x = mcrfpy.Animation("x", float(new_x), motion_speed, "easeInOutQuad", callback=movement_complete)
            player_anim_x.start(player)
            player_anim_y = mcrfpy.Animation("y", float(new_y), motion_speed, "easeInOutQuad")
            player_anim_y.start(player)
            
            # Move camera with player
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
        
# Register the keyboard handler
mcrfpy.keypressScene(handle_keys)

# Add UI elements
title = mcrfpy.Caption((320, 10),
    text="McRogueFace Tutorial - Part 6: Turn-based Movement",
)
title.fill_color = mcrfpy.Color(255, 255, 255, 255)
mcrfpy.sceneUI("tutorial").append(title)

instructions = mcrfpy.Caption((150, 720),
    text="Use WASD/Arrows to move. Enemies move after you!",
)
instructions.font_size = 18
instructions.fill_color = mcrfpy.Color(200, 200, 200, 255)
mcrfpy.sceneUI("tutorial").append(instructions)

# Debug info
debug_caption = mcrfpy.Caption((10, 40),
    text=f"Grid: {grid_width}x{grid_height} | Rooms: {len(rooms)} | Enemies: {len(enemies)}",
)
debug_caption.font_size = 16
debug_caption.fill_color = mcrfpy.Color(255, 255, 0, 255)
mcrfpy.sceneUI("tutorial").append(debug_caption)

# Update function for turn display
def update_turn_display():
    turn_text = "Player" if is_player_turn else "Enemy"
    alive_enemies = sum(1 for e in enemies if not e.is_dead())
    debug_caption.text = f"Grid: {grid_width}x{grid_height} | Turn: {turn_text} | Enemies: {alive_enemies}/{len(enemies)}"

# Configuration toggle
USE_DIJKSTRA = True  # Set to False to use old line-of-sight AI

# Timer to update display
def update_display(runtime):
    update_turn_display()

mcrfpy.setTimer("display_update", update_display, 100)

print("Tutorial Part 6 loaded!")
print("Turn-based movement system active!")
print(f"Using {'Dijkstra' if USE_DIJKSTRA else 'Line-of-sight'} AI pathfinding")
print("- Enemies move after the player")
print("- Enemies pursue when they can see you" if not USE_DIJKSTRA else "- Enemies use optimal pathfinding")
print("- Enemies wander when they can't" if not USE_DIJKSTRA else "- All enemies share one pathfinding map")
print("Use WASD or Arrow keys to move!")
