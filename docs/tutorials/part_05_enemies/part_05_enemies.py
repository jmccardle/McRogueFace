"""McRogueFace - Part 5: Placing Enemies

Documentation: https://mcrogueface.github.io/tutorial/part_05_enemies
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/tutorials/part_05_enemies/part_05_enemies.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy
import random

# =============================================================================
# Constants
# =============================================================================

# Sprite indices for CP437 tileset
SPRITE_WALL = 35    # '#' - wall
SPRITE_FLOOR = 46   # '.' - floor
SPRITE_PLAYER = 64  # '@' - player

# Enemy sprites (lowercase letters in CP437)
SPRITE_GOBLIN = 103  # 'g'
SPRITE_ORC = 111     # 'o'
SPRITE_TROLL = 116   # 't'

# Grid dimensions
GRID_WIDTH = 50
GRID_HEIGHT = 35

# Room generation parameters
ROOM_MIN_SIZE = 6
ROOM_MAX_SIZE = 12
MAX_ROOMS = 8

# Enemy spawn parameters
MAX_ENEMIES_PER_ROOM = 3

# FOV settings
FOV_RADIUS = 8

# Visibility colors
COLOR_VISIBLE = mcrfpy.Color(0, 0, 0, 0)
COLOR_DISCOVERED = mcrfpy.Color(0, 0, 40, 180)
COLOR_UNKNOWN = mcrfpy.Color(0, 0, 0, 255)

# =============================================================================
# Enemy Data
# =============================================================================

# Enemy templates - stats for each enemy type
ENEMY_TEMPLATES = {
    "goblin": {
        "sprite": SPRITE_GOBLIN,
        "hp": 6,
        "max_hp": 6,
        "attack": 3,
        "defense": 0,
        "color": mcrfpy.Color(100, 200, 100)  # Greenish
    },
    "orc": {
        "sprite": SPRITE_ORC,
        "hp": 10,
        "max_hp": 10,
        "attack": 4,
        "defense": 1,
        "color": mcrfpy.Color(100, 150, 100)  # Darker green
    },
    "troll": {
        "sprite": SPRITE_TROLL,
        "hp": 16,
        "max_hp": 16,
        "attack": 6,
        "defense": 2,
        "color": mcrfpy.Color(50, 150, 50)  # Dark green
    }
}

# Global storage for entity data
# Maps entity objects to their data dictionaries
entity_data: dict = {}

# Global references
player = None
grid = None
fov_layer = None

# =============================================================================
# Room Class (from Part 3)
# =============================================================================

class RectangularRoom:
    """A rectangular room with its position and size."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> tuple[int, int]:
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    @property
    def inner(self) -> tuple[slice, slice]:
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: "RectangularRoom") -> bool:
        return (
            self.x1 <= other.x2 and
            self.x2 >= other.x1 and
            self.y1 <= other.y2 and
            self.y2 >= other.y1
        )

# =============================================================================
# Exploration Tracking (from Part 4)
# =============================================================================

explored: list[list[bool]] = []

def init_explored() -> None:
    """Initialize the explored array to all False."""
    global explored
    explored = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

def mark_explored(x: int, y: int) -> None:
    """Mark a tile as explored."""
    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
        explored[y][x] = True

def is_explored(x: int, y: int) -> bool:
    """Check if a tile has been explored."""
    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
        return explored[y][x]
    return False

# =============================================================================
# Dungeon Generation (from Part 4)
# =============================================================================

def fill_with_walls(target_grid: mcrfpy.Grid) -> None:
    """Fill the entire grid with wall tiles."""
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = target_grid.at(x, y)
            cell.tilesprite = SPRITE_WALL
            cell.walkable = False
            cell.transparent = False

def carve_room(target_grid: mcrfpy.Grid, room: RectangularRoom) -> None:
    """Carve out a room by setting its inner tiles to floor."""
    inner_x, inner_y = room.inner
    for y in range(inner_y.start, inner_y.stop):
        for x in range(inner_x.start, inner_x.stop):
            if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                cell = target_grid.at(x, y)
                cell.tilesprite = SPRITE_FLOOR
                cell.walkable = True
                cell.transparent = True

def carve_tunnel_horizontal(target_grid: mcrfpy.Grid, x1: int, x2: int, y: int) -> None:
    """Carve a horizontal tunnel."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            cell = target_grid.at(x, y)
            cell.tilesprite = SPRITE_FLOOR
            cell.walkable = True
            cell.transparent = True

def carve_tunnel_vertical(target_grid: mcrfpy.Grid, y1: int, y2: int, x: int) -> None:
    """Carve a vertical tunnel."""
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            cell = target_grid.at(x, y)
            cell.tilesprite = SPRITE_FLOOR
            cell.walkable = True
            cell.transparent = True

def carve_l_tunnel(
    target_grid: mcrfpy.Grid,
    start: tuple[int, int],
    end: tuple[int, int]
) -> None:
    """Carve an L-shaped tunnel between two points."""
    x1, y1 = start
    x2, y2 = end

    if random.random() < 0.5:
        carve_tunnel_horizontal(target_grid, x1, x2, y1)
        carve_tunnel_vertical(target_grid, y1, y2, x2)
    else:
        carve_tunnel_vertical(target_grid, y1, y2, x1)
        carve_tunnel_horizontal(target_grid, x1, x2, y2)

# =============================================================================
# Enemy Management
# =============================================================================

def spawn_enemy(target_grid: mcrfpy.Grid, x: int, y: int, enemy_type: str, texture: mcrfpy.Texture) -> mcrfpy.Entity:
    """Spawn an enemy at the given position.

    Args:
        target_grid: The game grid
        x: X position in tiles
        y: Y position in tiles
        enemy_type: Type of enemy ("goblin", "orc", or "troll")
        texture: The texture to use for the sprite

    Returns:
        The created enemy Entity
    """
    template = ENEMY_TEMPLATES[enemy_type]

    enemy = mcrfpy.Entity(
        grid_pos=(x, y),
        texture=texture,
        sprite_index=template["sprite"]
    )


    # Start hidden until player sees them
    enemy.visible = False

    # Add to grid
    target_grid.entities.append(enemy)

    # Store enemy data
    entity_data[enemy] = {
        "type": enemy_type,
        "name": enemy_type.capitalize(),
        "hp": template["hp"],
        "max_hp": template["max_hp"],
        "attack": template["attack"],
        "defense": template["defense"],
        "is_player": False
    }

    return enemy

def spawn_enemies_in_room(target_grid: mcrfpy.Grid, room: RectangularRoom, texture: mcrfpy.Texture) -> None:
    """Spawn random enemies in a room.

    Args:
        target_grid: The game grid
        room: The room to spawn enemies in
        texture: The texture to use for sprites
    """
    # Random number of enemies (0 to MAX_ENEMIES_PER_ROOM)
    num_enemies = random.randint(0, MAX_ENEMIES_PER_ROOM)

    for _ in range(num_enemies):
        # Random position within the room's inner area
        inner_x, inner_y = room.inner
        x = random.randint(inner_x.start, inner_x.stop - 1)
        y = random.randint(inner_y.start, inner_y.stop - 1)

        # Check if position is already occupied
        if get_blocking_entity_at(target_grid, x, y) is not None:
            continue  # Skip this spawn attempt

        # Choose enemy type based on weighted random
        roll = random.random()
        if roll < 0.6:
            enemy_type = "goblin"  # 60% chance
        elif roll < 0.9:
            enemy_type = "orc"     # 30% chance
        else:
            enemy_type = "troll"   # 10% chance

        spawn_enemy(target_grid, x, y, enemy_type, texture)

def get_blocking_entity_at(target_grid: mcrfpy.Grid, x: int, y: int) -> mcrfpy.Entity | None:
    """Get any entity that blocks movement at the given position.

    Args:
        target_grid: The game grid
        x: X position to check
        y: Y position to check

    Returns:
        The blocking entity, or None if no entity blocks this position
    """
    for entity in target_grid.entities:
        if int(entity.x) == x and int(entity.y) == y:
            return entity
    return None

def clear_enemies(target_grid: mcrfpy.Grid) -> None:
    """Remove all enemies from the grid."""
    global entity_data

    # Get list of enemies to remove (not the player)
    enemies_to_remove = []
    for entity in target_grid.entities:
        if entity in entity_data and not entity_data[entity].get("is_player", False):
            enemies_to_remove.append(entity)

    # Remove from grid and entity_data
    for enemy in enemies_to_remove:
        # Find and remove from grid.entities
        for i, e in enumerate(target_grid.entities):
            if e == enemy:
                target_grid.entities.remove(i)
                break
        # Remove from entity_data
        if enemy in entity_data:
            del entity_data[enemy]

# =============================================================================
# Entity Visibility
# =============================================================================

def update_entity_visibility(target_grid: mcrfpy.Grid) -> None:
    """Update visibility of all entities based on FOV.

    Entities outside the player's field of view are hidden.
    """
    global player

    for entity in target_grid.entities:
        # Player is always visible
        if entity == player:
            entity.visible = True
            continue

        # Other entities are only visible if in FOV
        ex, ey = int(entity.x), int(entity.y)
        entity.visible = target_grid.is_in_fov(ex, ey)

# =============================================================================
# Field of View (from Part 4)
# =============================================================================

def update_fov(target_grid: mcrfpy.Grid, target_fov_layer, player_x: int, player_y: int) -> None:
    """Update the field of view visualization."""
    # Compute FOV from player position
    target_grid.compute_fov(player_x, player_y, FOV_RADIUS, mcrfpy.FOV.SHADOW)

    # Update each tile's visibility
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if target_grid.is_in_fov(x, y):
                mark_explored(x, y)
                target_fov_layer.set(x, y, COLOR_VISIBLE)
            elif is_explored(x, y):
                target_fov_layer.set(x, y, COLOR_DISCOVERED)
            else:
                target_fov_layer.set(x, y, COLOR_UNKNOWN)

    # Update entity visibility
    update_entity_visibility(target_grid)

# =============================================================================
# Collision Detection
# =============================================================================

def can_move_to(target_grid: mcrfpy.Grid, x: int, y: int) -> bool:
    """Check if a position is valid for movement.

    A position is valid if:
    1. It is within grid bounds
    2. The tile is walkable
    3. No entity is blocking it
    """
    # Check bounds
    if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
        return False

    # Check tile walkability
    if not target_grid.at(x, y).walkable:
        return False

    # Check for blocking entities
    if get_blocking_entity_at(target_grid, x, y) is not None:
        return False

    return True

# =============================================================================
# Dungeon Generation with Enemies
# =============================================================================

def generate_dungeon(target_grid: mcrfpy.Grid, texture: mcrfpy.Texture) -> tuple[int, int]:
    """Generate a dungeon with rooms, tunnels, and enemies.

    Args:
        target_grid: The game grid
        texture: The texture for entity sprites

    Returns:
        The (x, y) coordinates where the player should start
    """
    # Clear any existing enemies
    clear_enemies(target_grid)

    # Fill with walls
    fill_with_walls(target_grid)
    init_explored()

    rooms: list[RectangularRoom] = []

    for _ in range(MAX_ROOMS):
        room_width = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        room_height = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = random.randint(1, GRID_WIDTH - room_width - 2)
        y = random.randint(1, GRID_HEIGHT - room_height - 2)

        new_room = RectangularRoom(x, y, room_width, room_height)

        overlaps = False
        for other_room in rooms:
            if new_room.intersects(other_room):
                overlaps = True
                break

        if overlaps:
            continue

        carve_room(target_grid, new_room)

        if rooms:
            carve_l_tunnel(target_grid, new_room.center, rooms[-1].center)
            # Spawn enemies in all rooms except the first (player starting room)
            spawn_enemies_in_room(target_grid, new_room, texture)

        rooms.append(new_room)

    if rooms:
        return rooms[0].center
    return GRID_WIDTH // 2, GRID_HEIGHT // 2

# =============================================================================
# Game Setup
# =============================================================================

# Create the scene
scene = mcrfpy.Scene("game")

# Load texture
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Create the grid
grid = mcrfpy.Grid(
    pos=(50, 80),
    size=(800, 560),
    grid_size=(GRID_WIDTH, GRID_HEIGHT),
    texture=texture,
    zoom=1.0
)

# Generate the dungeon (without player first to get starting position)
fill_with_walls(grid)
init_explored()

rooms: list[RectangularRoom] = []

for _ in range(MAX_ROOMS):
    room_width = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
    room_height = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
    x = random.randint(1, GRID_WIDTH - room_width - 2)
    y = random.randint(1, GRID_HEIGHT - room_height - 2)

    new_room = RectangularRoom(x, y, room_width, room_height)

    overlaps = False
    for other_room in rooms:
        if new_room.intersects(other_room):
            overlaps = True
            break

    if overlaps:
        continue

    carve_room(grid, new_room)

    if rooms:
        carve_l_tunnel(grid, new_room.center, rooms[-1].center)

    rooms.append(new_room)

# Get player starting position
if rooms:
    player_start_x, player_start_y = rooms[0].center
else:
    player_start_x, player_start_y = GRID_WIDTH // 2, GRID_HEIGHT // 2

# Add FOV layer
fov_layer = grid.add_layer("color", z_index=-1)
for y in range(GRID_HEIGHT):
    for x in range(GRID_WIDTH):
        fov_layer.set(x, y, COLOR_UNKNOWN)

# Create the player
player = mcrfpy.Entity(
    grid_pos=(player_start_x, player_start_y),
    texture=texture,
    sprite_index=SPRITE_PLAYER
)
grid.entities.append(player)

# Store player data
entity_data[player] = {
    "type": "player",
    "name": "Player",
    "hp": 30,
    "max_hp": 30,
    "attack": 5,
    "defense": 2,
    "is_player": True
}

# Now spawn enemies in rooms (except the first one)
for i, room in enumerate(rooms):
    if i == 0:
        continue  # Skip player's starting room
    spawn_enemies_in_room(grid, room, texture)

# Calculate initial FOV
update_fov(grid, fov_layer, player_start_x, player_start_y)

# Add grid to scene
scene.children.append(grid)

# =============================================================================
# UI Elements
# =============================================================================

title = mcrfpy.Caption(
    pos=(50, 15),
    text="Part 5: Placing Enemies"
)
title.fill_color = mcrfpy.Color(255, 255, 255)
title.font_size = 24
scene.children.append(title)

instructions = mcrfpy.Caption(
    pos=(50, 50),
    text="WASD/Arrows: Move | R: Regenerate | Escape: Quit"
)
instructions.fill_color = mcrfpy.Color(180, 180, 180)
instructions.font_size = 16
scene.children.append(instructions)

pos_display = mcrfpy.Caption(
    pos=(50, 660),
    text=f"Position: ({int(player.x)}, {int(player.y)})"
)
pos_display.fill_color = mcrfpy.Color(200, 200, 100)
pos_display.font_size = 16
scene.children.append(pos_display)

status_display = mcrfpy.Caption(
    pos=(400, 660),
    text="Explore the dungeon..."
)
status_display.fill_color = mcrfpy.Color(100, 200, 100)
status_display.font_size = 16
scene.children.append(status_display)

# =============================================================================
# Input Handling
# =============================================================================

def regenerate_dungeon() -> None:
    """Generate a new dungeon and reposition the player."""
    global player, grid, fov_layer, rooms

    # Clear enemies
    clear_enemies(grid)

    # Regenerate dungeon structure
    fill_with_walls(grid)
    init_explored()

    rooms = []

    for _ in range(MAX_ROOMS):
        room_width = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        room_height = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = random.randint(1, GRID_WIDTH - room_width - 2)
        y = random.randint(1, GRID_HEIGHT - room_height - 2)

        new_room = RectangularRoom(x, y, room_width, room_height)

        overlaps = False
        for other_room in rooms:
            if new_room.intersects(other_room):
                overlaps = True
                break

        if overlaps:
            continue

        carve_room(grid, new_room)

        if rooms:
            carve_l_tunnel(grid, new_room.center, rooms[-1].center)

        rooms.append(new_room)

    # Reposition player
    if rooms:
        new_x, new_y = rooms[0].center
    else:
        new_x, new_y = GRID_WIDTH // 2, GRID_HEIGHT // 2

    player.x = new_x
    player.y = new_y

    # Spawn new enemies
    for i, room in enumerate(rooms):
        if i == 0:
            continue
        spawn_enemies_in_room(grid, room, texture)

    # Reset FOV layer
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            fov_layer.set(x, y, COLOR_UNKNOWN)

    # Update FOV
    update_fov(grid, fov_layer, new_x, new_y)
    pos_display.text = f"Position: ({new_x}, {new_y})"
    status_display.text = "New dungeon generated!"

def handle_keys(key: str, action: str) -> None:
    """Handle keyboard input."""
    global player, grid, fov_layer

    if action != "start":
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
    elif key == "R":
        regenerate_dungeon()
        return
    elif key == "Escape":
        mcrfpy.exit()
        return
    else:
        return

    # Check for blocking entity (potential combat target)
    blocker = get_blocking_entity_at(grid, new_x, new_y)
    if blocker is not None and blocker != player:
        # For now, just report that we bumped into an enemy
        if blocker in entity_data:
            enemy_name = entity_data[blocker]["name"]
            status_display.text = f"A {enemy_name} blocks your path!"
            status_display.fill_color = mcrfpy.Color(200, 150, 100)
        return

    # Check if we can move
    if can_move_to(grid, new_x, new_y):
        player.x = new_x
        player.y = new_y
        pos_display.text = f"Position: ({new_x}, {new_y})"
        status_display.text = "Exploring..."
        status_display.fill_color = mcrfpy.Color(100, 200, 100)

        # Update FOV after movement
        update_fov(grid, fov_layer, new_x, new_y)

scene.on_key = handle_keys

# =============================================================================
# Start the Game
# =============================================================================

scene.activate()
print("Part 5 loaded! Enemies lurk in the dungeon...")