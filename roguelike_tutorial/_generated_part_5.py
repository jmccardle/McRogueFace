"""
McRogueFace Tutorial - Part 5: Entity Interactions

This tutorial builds on Part 4 by adding:
- Entity class hierarchy (PlayerEntity, EnemyEntity, BoulderEntity, ButtonEntity)
- Non-blocking movement animations with destination tracking
- Bump interactions (combat, pushing)
- Step-on interactions (buttons, doors)
- Concurrent enemy AI with smooth animations

Key concepts:
- Entities inherit from mcrfpy.Entity for proper C++/Python integration
- Logic operates on destination positions during animations
- Player input is processed immediately, not blocked by animations
"""
import mcrfpy
import random

# ============================================================================
# Entity Classes - Inherit from mcrfpy.Entity
# ============================================================================

class GameEntity(mcrfpy.Entity):
    """Base class for all game entities with interaction logic"""
    def __init__(self, x, y, **kwargs):
        # Extract grid before passing to parent
        grid = kwargs.pop('grid', None)
        super().__init__(x=x, y=y, **kwargs)
        
        # Current position is tracked by parent Entity.x/y
        # Add destination tracking for animation system
        self.dest_x = x
        self.dest_y = y
        self.is_moving = False
        
        # Game properties
        self.blocks_movement = True
        self.hp = 10
        self.max_hp = 10
        self.entity_type = "generic"
        
        # Add to grid if provided
        if grid:
            grid.entities.append(self)
            
    def start_move(self, new_x, new_y, duration=0.2, callback=None):
        """Start animating movement to new position"""
        self.dest_x = new_x
        self.dest_y = new_y
        self.is_moving = True
        
        # Create animations for smooth movement
        if callback:
            # Only x animation needs callback since they run in parallel
            anim_x = mcrfpy.Animation("x", float(new_x), duration, "easeInOutQuad", callback=callback)
        else:
            anim_x = mcrfpy.Animation("x", float(new_x), duration, "easeInOutQuad")
        anim_y = mcrfpy.Animation("y", float(new_y), duration, "easeInOutQuad")
        
        anim_x.start(self)
        anim_y.start(self)
        
    def get_position(self):
        """Get logical position (destination if moving, otherwise current)"""
        if self.is_moving:
            return (self.dest_x, self.dest_y)
        return (int(self.x), int(self.y))
        
    def on_bump(self, other):
        """Called when another entity tries to move into our space"""
        return False  # Block movement by default
        
    def on_step(self, other):
        """Called when another entity steps on us (non-blocking)"""
        pass
        
    def take_damage(self, damage):
        """Apply damage and handle death"""
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.die()
            
    def die(self):
        """Remove entity from grid"""
        # The C++ die() method handles removal from grid
        super().die()

class PlayerEntity(GameEntity):
    """The player character"""
    def __init__(self, x, y, **kwargs):
        kwargs['sprite_index'] = 64  # Hero sprite
        super().__init__(x=x, y=y, **kwargs)
        self.damage = 3
        self.entity_type = "player"
        self.blocks_movement = True
        
    def on_bump(self, other):
        """Player bumps into something"""
        if other.entity_type == "enemy":
            # Deal damage
            other.take_damage(self.damage)
            return False  # Can't move into enemy space
        elif other.entity_type == "boulder":
            # Try to push
            dx = self.dest_x - int(self.x)
            dy = self.dest_y - int(self.y)
            return other.try_push(dx, dy)
        return False

class EnemyEntity(GameEntity):
    """Basic enemy with AI"""
    def __init__(self, x, y, **kwargs):
        kwargs['sprite_index'] = 65  # Enemy sprite
        super().__init__(x=x, y=y, **kwargs)
        self.damage = 1
        self.entity_type = "enemy"
        self.ai_state = "wander"
        self.hp = 5
        self.max_hp = 5
        
    def on_bump(self, other):
        """Enemy bumps into something"""
        if other.entity_type == "player":
            other.take_damage(self.damage)
            return False
        return False
        
    def can_see_player(self, player_pos, grid):
        """Check if enemy can see the player position"""
        # Simple check: within 6 tiles and has line of sight
        mx, my = self.get_position()
        px, py = player_pos
        
        dist = abs(px - mx) + abs(py - my)
        if dist > 6:
            return False
            
        # Use libtcod for line of sight
        line = list(mcrfpy.libtcod.line(mx, my, px, py))
        if len(line) > 7:  # Too far
            return False
        for x, y in line[1:-1]:  # Skip start and end points
            cell = grid.at(x, y)
            if cell and not cell.transparent:
                return False
        return True
        
    def ai_turn(self, grid, player):
        """Decide next move"""
        px, py = player.get_position()
        mx, my = self.get_position()
        
        # Simple AI: move toward player if visible
        if self.can_see_player((px, py), grid):
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
            # Random movement
            dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
            return (mx + dx, my + dy)

class BoulderEntity(GameEntity):
    """Pushable boulder"""
    def __init__(self, x, y, **kwargs):
        kwargs['sprite_index'] = 7  # Boulder sprite
        super().__init__(x=x, y=y, **kwargs)
        self.entity_type = "boulder"
        self.pushable = True
        
    def try_push(self, dx, dy):
        """Attempt to push boulder in direction"""
        new_x = int(self.x) + dx
        new_y = int(self.y) + dy
        
        # Check if destination is free
        if can_move_to(new_x, new_y):
            self.start_move(new_x, new_y)
            return True
        return False

class ButtonEntity(GameEntity):
    """Pressure plate that triggers when stepped on"""
    def __init__(self, x, y, target=None, **kwargs):
        kwargs['sprite_index'] = 8  # Button sprite
        super().__init__(x=x, y=y, **kwargs)
        self.blocks_movement = False  # Can be walked over
        self.entity_type = "button"
        self.pressed = False
        self.pressed_by = set()  # Track who's pressing
        self.target = target  # Door or other triggerable
        
    def on_step(self, other):
        """Activate when stepped on"""
        if other not in self.pressed_by:
            self.pressed_by.add(other)
            if not self.pressed:
                self.pressed = True
                self.sprite_index = 9  # Pressed sprite
                if self.target:
                    self.target.activate()
                    
    def on_leave(self, other):
        """Deactivate when entity leaves"""
        if other in self.pressed_by:
            self.pressed_by.remove(other)
            if len(self.pressed_by) == 0 and self.pressed:
                self.pressed = False
                self.sprite_index = 8  # Unpressed sprite
                if self.target:
                    self.target.deactivate()

class DoorEntity(GameEntity):
    """Door that can be opened by buttons"""
    def __init__(self, x, y, **kwargs):
        kwargs['sprite_index'] = 3  # Closed door sprite
        super().__init__(x=x, y=y, **kwargs)
        self.entity_type = "door"
        self.is_open = False
        
    def activate(self):
        """Open the door"""
        self.is_open = True
        self.blocks_movement = False
        self.sprite_index = 11  # Open door sprite
        
    def deactivate(self):
        """Close the door"""
        self.is_open = False
        self.blocks_movement = True
        self.sprite_index = 3  # Closed door sprite

# ============================================================================
# Global Game State
# ============================================================================

# Create and activate a new scene
mcrfpy.createScene("tutorial")
mcrfpy.setScene("tutorial")

# Load the texture
texture = mcrfpy.Texture("assets/tutorial2.png", 16, 16)

# Create a grid of tiles
grid_width, grid_height = 40, 30
zoom = 2.0
grid_size = grid_width * zoom * 16, grid_height * zoom * 16
grid_position = (1024 - grid_size[0]) / 2, (768 - grid_size[1]) / 2

# Create the grid
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

# Game state
player = None
enemies = []
all_entities = []
is_player_turn = True
move_duration = 0.2

# ============================================================================
# Dungeon Generation (from Part 3)
# ============================================================================

class Room:
    def __init__(self, x, y, width, height):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        
    def center(self):
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)
        
    def intersects(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

def create_room(room):
    """Carve out a room in the grid"""
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            cell = grid.at(x, y)
            if cell:
                cell.walkable = True
                cell.transparent = True
                cell.tilesprite = random.choice(FLOOR_TILES)

def create_l_shaped_hallway(x1, y1, x2, y2):
    """Create L-shaped hallway between two points"""
    corner_x = x2
    corner_y = y1
    
    if random.random() < 0.5:
        corner_x = x1
        corner_y = y2
    
    for x, y in mcrfpy.libtcod.line(x1, y1, corner_x, corner_y):
        cell = grid.at(x, y)
        if cell:
            cell.walkable = True
            cell.transparent = True
            cell.tilesprite = random.choice(FLOOR_TILES)
    
    for x, y in mcrfpy.libtcod.line(corner_x, corner_y, x2, y2):
        cell = grid.at(x, y)
        if cell:
            cell.walkable = True
            cell.transparent = True
            cell.tilesprite = random.choice(FLOOR_TILES)

def generate_dungeon():
    """Generate a simple dungeon with rooms and hallways"""
    # Initialize all cells as walls
    for x in range(grid_width):
        for y in range(grid_height):
            cell = grid.at(x, y)
            if cell:
                cell.walkable = False
                cell.transparent = False
                cell.tilesprite = random.choice(WALL_TILES)
    
    rooms = []
    num_rooms = 0
    
    for _ in range(30):
        w = random.randint(4, 8)
        h = random.randint(4, 8)
        x = random.randint(0, grid_width - w - 1)
        y = random.randint(0, grid_height - h - 1)
        
        new_room = Room(x, y, w, h)
        
        # Check if room intersects with existing rooms
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue
            
        create_room(new_room)
        
        if num_rooms > 0:
            # Connect to previous room
            new_x, new_y = new_room.center()
            prev_x, prev_y = rooms[num_rooms - 1].center()
            create_l_shaped_hallway(prev_x, prev_y, new_x, new_y)
        
        rooms.append(new_room)
        num_rooms += 1
    
    return rooms

# ============================================================================
# Entity Management
# ============================================================================

def get_entities_at(x, y):
    """Get all entities at a specific position (including moving ones)"""
    entities = []
    for entity in all_entities:
        ex, ey = entity.get_position()
        if ex == x and ey == y:
            entities.append(entity)
    return entities

def get_blocking_entity_at(x, y):
    """Get the first blocking entity at position"""
    for entity in get_entities_at(x, y):
        if entity.blocks_movement:
            return entity
    return None

def can_move_to(x, y):
    """Check if a position is valid for movement"""
    if x < 0 or x >= grid_width or y < 0 or y >= grid_height:
        return False
        
    cell = grid.at(x, y)
    if not cell or not cell.walkable:
        return False
        
    # Check for blocking entities
    if get_blocking_entity_at(x, y):
        return False
        
    return True

def can_entity_move_to(entity, x, y):
    """Check if specific entity can move to position"""
    if x < 0 or x >= grid_width or y < 0 or y >= grid_height:
        return False
        
    cell = grid.at(x, y)
    if not cell or not cell.walkable:
        return False
        
    # Check for other blocking entities (not self)
    blocker = get_blocking_entity_at(x, y)
    if blocker and blocker != entity:
        return False
        
    return True

# ============================================================================
# Turn Management
# ============================================================================

def process_player_move(key):
    """Handle player input with immediate response"""
    global is_player_turn
    
    if not is_player_turn or player.is_moving:
        return  # Not player's turn or still animating
        
    px, py = player.get_position()
    new_x, new_y = px, py
    
    # Calculate movement direction
    if key == "W" or key == "Up":
        new_y -= 1
    elif key == "S" or key == "Down":
        new_y += 1
    elif key == "A" or key == "Left":
        new_x -= 1
    elif key == "D" or key == "Right":
        new_x += 1
    else:
        return  # Not a movement key
        
    if new_x == px and new_y == py:
        return  # No movement
    
    # Check what's at destination
    cell = grid.at(new_x, new_y)
    if not cell or not cell.walkable:
        return  # Can't move into walls
        
    blocking_entity = get_blocking_entity_at(new_x, new_y)
    
    if blocking_entity:
        # Try bump interaction
        if not player.on_bump(blocking_entity):
            # Movement blocked, but turn still happens
            is_player_turn = False
            mcrfpy.setTimer("enemy_turn", process_enemy_turns, 50)
            return
    
    # Movement is valid - start player animation
    is_player_turn = False
    player.start_move(new_x, new_y, duration=move_duration, callback=player_move_complete)
    
    # Update grid center to follow player
    grid_anim_x = mcrfpy.Animation("center_x", (new_x + 0.5) * 16, move_duration, "linear")
    grid_anim_y = mcrfpy.Animation("center_y", (new_y + 0.5) * 16, move_duration, "linear")
    grid_anim_x.start(grid)
    grid_anim_y.start(grid)
    
    # Start enemy turns after a short delay (so player sees their move start first)
    mcrfpy.setTimer("enemy_turn", process_enemy_turns, 50)

def process_enemy_turns(timer_name):
    """Process all enemy AI decisions and start their animations"""
    enemies_to_move = []
    
    for enemy in enemies:
        if enemy.hp <= 0:  # Skip dead enemies
            continue
            
        if enemy.is_moving:
            continue  # Skip if still animating
            
        # AI decides next move based on player's destination
        target_x, target_y = enemy.ai_turn(grid, player)
        
        # Check if move is valid
        cell = grid.at(target_x, target_y)
        if not cell or not cell.walkable:
            continue
            
        # Check what's at the destination
        blocking_entity = get_blocking_entity_at(target_x, target_y)
        
        if blocking_entity and blocking_entity != enemy:
            # Try bump interaction
            enemy.on_bump(blocking_entity)
            # Enemy doesn't move but still took its turn
        else:
            # Valid move - add to list
            enemies_to_move.append((enemy, target_x, target_y))
    
    # Start all enemy animations simultaneously
    for enemy, tx, ty in enemies_to_move:
        enemy.start_move(tx, ty, duration=move_duration)

def player_move_complete(anim, entity):
    """Called when player animation finishes"""
    global is_player_turn
    
    player.is_moving = False
    
    # Check for step-on interactions at new position
    for entity in get_entities_at(int(player.x), int(player.y)):
        if entity != player and not entity.blocks_movement:
            entity.on_step(player)
    
    # Update FOV from new position
    update_fov()
    
    # Player's turn is ready again
    is_player_turn = True

def update_fov():
    """Update field of view from player position"""
    px, py = int(player.x), int(player.y)
    grid.compute_fov(px, py, radius=8)
    player.update_visibility()

# ============================================================================
# Input Handling
# ============================================================================

def handle_keys(key, state):
    """Handle keyboard input"""
    if state == "start":
        # Movement keys
        if key in ["W", "Up", "S", "Down", "A", "Left", "D", "Right"]:
            process_player_move(key)

# Register the key handler
mcrfpy.keypressScene(handle_keys)

# ============================================================================
# Initialize Game
# ============================================================================

# Generate dungeon
rooms = generate_dungeon()

# Place player in first room
if rooms:
    start_x, start_y = rooms[0].center()
    player = PlayerEntity(start_x, start_y, grid=grid)
    all_entities.append(player)
    
    # Place enemies in other rooms
    for i in range(1, min(6, len(rooms))):
        room = rooms[i]
        ex, ey = room.center()
        enemy = EnemyEntity(ex, ey, grid=grid)
        enemies.append(enemy)
        all_entities.append(enemy)
    
    # Place some boulders
    for i in range(3):
        room = random.choice(rooms[1:])
        bx = random.randint(room.x1 + 1, room.x2 - 1)
        by = random.randint(room.y1 + 1, room.y2 - 1)
        if can_move_to(bx, by):
            boulder = BoulderEntity(bx, by, grid=grid)
            all_entities.append(boulder)
    
    # Place a button and door in one of the rooms
    if len(rooms) > 2:
        button_room = rooms[-2]
        door_room = rooms[-1]
        
        # Place door at entrance to last room
        dx, dy = door_room.center()
        door = DoorEntity(dx, door_room.y1, grid=grid)
        all_entities.append(door)
        
        # Place button in second to last room
        bx, by = button_room.center()
        button = ButtonEntity(bx, by, target=door, grid=grid)
        all_entities.append(button)
    
    # Set grid perspective to player
    grid.perspective = player
    grid.center_x = (start_x + 0.5) * 16
    grid.center_y = (start_y + 0.5) * 16
    
    # Initial FOV calculation
    update_fov()

# Add grid to scene
mcrfpy.sceneUI("tutorial").append(grid)

# Show instructions
title = mcrfpy.Caption((320, 10),
    text="Part 5: Entity Interactions - WASD to move, bump enemies, push boulders!",
)
title.fill_color = mcrfpy.Color(255, 255, 255, 255)
mcrfpy.sceneUI("tutorial").append(title)

print("Part 5: Entity Interactions - Tutorial loaded!")
print("- Bump into enemies to attack them")
print("- Push boulders by walking into them")
print("- Step on buttons to open doors")
print("- Enemies will pursue you when they can see you")