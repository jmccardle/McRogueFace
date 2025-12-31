"""McRogueFace - Part 6: Combat System

Documentation: https://mcrogueface.github.io/tutorial/part_06_combat
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/tutorials/part_06_combat/part_06_combat.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy
import random
from dataclasses import dataclass
from typing import Optional

# =============================================================================
# Constants
# =============================================================================

# Sprite indices for CP437 tileset
SPRITE_WALL = 35    # '#' - wall
SPRITE_FLOOR = 46   # '.' - floor
SPRITE_PLAYER = 64  # '@' - player
SPRITE_CORPSE = 37  # '%' - remains

# Enemy sprites
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

# Message log settings
MAX_MESSAGES = 5

# =============================================================================
# Fighter Component
# =============================================================================

@dataclass
class Fighter:
    """Combat stats for an entity."""
    hp: int
    max_hp: int
    attack: int
    defense: int
    name: str
    is_player: bool = False

    @property
    def is_alive(self) -> bool:
        """Check if this fighter is still alive."""
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        """Apply damage and return actual damage taken."""
        actual_damage = min(self.hp, amount)
        self.hp -= actual_damage
        return actual_damage

    def heal(self, amount: int) -> int:
        """Heal and return actual amount healed."""
        actual_heal = min(self.max_hp - self.hp, amount)
        self.hp += actual_heal
        return actual_heal

# =============================================================================
# Enemy Templates
# =============================================================================

ENEMY_TEMPLATES = {
    "goblin": {
        "sprite": SPRITE_GOBLIN,
        "hp": 6,
        "attack": 3,
        "defense": 0,
        "color": mcrfpy.Color(100, 200, 100)
    },
    "orc": {
        "sprite": SPRITE_ORC,
        "hp": 10,
        "attack": 4,
        "defense": 1,
        "color": mcrfpy.Color(100, 150, 100)
    },
    "troll": {
        "sprite": SPRITE_TROLL,
        "hp": 16,
        "attack": 6,
        "defense": 2,
        "color": mcrfpy.Color(50, 150, 50)
    }
}

# =============================================================================
# Global State
# =============================================================================

# Entity data storage
entity_data: dict[mcrfpy.Entity, Fighter] = {}

# Global references
player: Optional[mcrfpy.Entity] = None
grid: Optional[mcrfpy.Grid] = None
fov_layer = None
texture: Optional[mcrfpy.Texture] = None

# Game state
game_over: bool = False

# Message log
messages: list[tuple[str, mcrfpy.Color]] = []

# =============================================================================
# Room Class
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
# Exploration Tracking
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
# Message Log
# =============================================================================

def add_message(text: str, color: mcrfpy.Color = None) -> None:
    """Add a message to the log.

    Args:
        text: The message text
        color: Optional color (defaults to white)
    """
    if color is None:
        color = mcrfpy.Color(255, 255, 255)

    messages.append((text, color))

    # Keep only the most recent messages
    while len(messages) > MAX_MESSAGES:
        messages.pop(0)

    # Update the message display
    update_message_display()

def update_message_display() -> None:
    """Update the message log UI."""
    if message_log_caption is None:
        return

    # Combine messages into a single string
    lines = []
    for text, color in messages:
        lines.append(text)

    message_log_caption.text = "\n".join(lines)

def clear_messages() -> None:
    """Clear all messages."""
    global messages
    messages = []
    update_message_display()

# =============================================================================
# Dungeon Generation
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
# Entity Management
# =============================================================================

def spawn_enemy(target_grid: mcrfpy.Grid, x: int, y: int, enemy_type: str, tex: mcrfpy.Texture) -> mcrfpy.Entity:
    """Spawn an enemy at the given position."""
    template = ENEMY_TEMPLATES[enemy_type]

    enemy = mcrfpy.Entity(
        grid_pos=(x, y),
        texture=tex,
        sprite_index=template["sprite"]
    )

    enemy.visible = False

    target_grid.entities.append(enemy)

    # Create Fighter component for this enemy
    entity_data[enemy] = Fighter(
        hp=template["hp"],
        max_hp=template["hp"],
        attack=template["attack"],
        defense=template["defense"],
        name=enemy_type.capitalize(),
        is_player=False
    )

    return enemy

def spawn_enemies_in_room(target_grid: mcrfpy.Grid, room: RectangularRoom, tex: mcrfpy.Texture) -> None:
    """Spawn random enemies in a room."""
    num_enemies = random.randint(0, MAX_ENEMIES_PER_ROOM)

    for _ in range(num_enemies):
        inner_x, inner_y = room.inner
        x = random.randint(inner_x.start, inner_x.stop - 1)
        y = random.randint(inner_y.start, inner_y.stop - 1)

        if get_entity_at(target_grid, x, y) is not None:
            continue

        roll = random.random()
        if roll < 0.6:
            enemy_type = "goblin"
        elif roll < 0.9:
            enemy_type = "orc"
        else:
            enemy_type = "troll"

        spawn_enemy(target_grid, x, y, enemy_type, tex)

def get_entity_at(target_grid: mcrfpy.Grid, x: int, y: int) -> Optional[mcrfpy.Entity]:
    """Get any entity at the given position."""
    for entity in target_grid.entities:
        if int(entity.x) == x and int(entity.y) == y:
            # Check if this entity is alive (or is a non-Fighter entity)
            if entity in entity_data:
                if entity_data[entity].is_alive:
                    return entity
            else:
                return entity
    return None

def get_blocking_entity_at(target_grid: mcrfpy.Grid, x: int, y: int, exclude: mcrfpy.Entity = None) -> Optional[mcrfpy.Entity]:
    """Get any living entity that blocks movement at the given position."""
    for entity in target_grid.entities:
        if entity == exclude:
            continue
        if int(entity.x) == x and int(entity.y) == y:
            if entity in entity_data and entity_data[entity].is_alive:
                return entity
    return None

def remove_entity(target_grid: mcrfpy.Grid, entity: mcrfpy.Entity) -> None:
    """Remove an entity from the grid and data storage."""
    # Find and remove from grid
    for i, e in enumerate(target_grid.entities):
        if e == entity:
            target_grid.entities.remove(i)
            break

    # Remove from entity data
    if entity in entity_data:
        del entity_data[entity]

def clear_enemies(target_grid: mcrfpy.Grid) -> None:
    """Remove all enemies from the grid."""
    enemies_to_remove = []

    for entity in target_grid.entities:
        if entity in entity_data and not entity_data[entity].is_player:
            enemies_to_remove.append(entity)

    for enemy in enemies_to_remove:
        remove_entity(target_grid, enemy)

# =============================================================================
# Combat System
# =============================================================================

def calculate_damage(attacker: Fighter, defender: Fighter) -> int:
    """Calculate damage dealt from attacker to defender.

    Args:
        attacker: The attacking Fighter
        defender: The defending Fighter

    Returns:
        The amount of damage to deal (minimum 0)
    """
    damage = max(0, attacker.attack - defender.defense)
    return damage

def perform_attack(attacker_entity: mcrfpy.Entity, defender_entity: mcrfpy.Entity) -> None:
    """Execute an attack from one entity to another.

    Args:
        attacker_entity: The entity performing the attack
        defender_entity: The entity being attacked
    """
    global game_over

    attacker = entity_data.get(attacker_entity)
    defender = entity_data.get(defender_entity)

    if attacker is None or defender is None:
        return

    # Calculate and apply damage
    damage = calculate_damage(attacker, defender)
    defender.take_damage(damage)

    # Generate combat message
    if damage > 0:
        if attacker.is_player:
            add_message(
                f"You hit the {defender.name} for {damage} damage!",
                mcrfpy.Color(200, 200, 200)
            )
        else:
            add_message(
                f"The {attacker.name} hits you for {damage} damage!",
                mcrfpy.Color(255, 150, 150)
            )
    else:
        if attacker.is_player:
            add_message(
                f"You hit the {defender.name} but deal no damage.",
                mcrfpy.Color(150, 150, 150)
            )
        else:
            add_message(
                f"The {attacker.name} hits you but deals no damage.",
                mcrfpy.Color(150, 150, 200)
            )

    # Check for death
    if not defender.is_alive:
        handle_death(defender_entity, defender)

def handle_death(entity: mcrfpy.Entity, fighter: Fighter) -> None:
    """Handle the death of an entity.

    Args:
        entity: The entity that died
        fighter: The Fighter component of the dead entity
    """
    global game_over, grid

    if fighter.is_player:
        # Player death
        add_message("You have died!", mcrfpy.Color(255, 50, 50))
        add_message("Press R to restart or Escape to quit.", mcrfpy.Color(200, 200, 200))
        game_over = True

        # Change player sprite to corpse
        entity.sprite_index = SPRITE_CORPSE
    else:
        # Enemy death
        add_message(f"The {fighter.name} dies!", mcrfpy.Color(100, 255, 100))

        # Replace with corpse
        entity.sprite_index = SPRITE_CORPSE

        # Mark as dead (hp is already 0)
        # Remove blocking but keep visual corpse
        # Actually remove the entity and its data
        remove_entity(grid, entity)

    # Update HP display
    update_hp_display()

# =============================================================================
# Field of View
# =============================================================================

def update_entity_visibility(target_grid: mcrfpy.Grid) -> None:
    """Update visibility of all entities based on FOV."""
    global player

    for entity in target_grid.entities:
        if entity == player:
            entity.visible = True
            continue

        ex, ey = int(entity.x), int(entity.y)
        entity.visible = target_grid.is_in_fov(ex, ey)

def update_fov(target_grid: mcrfpy.Grid, target_fov_layer, player_x: int, player_y: int) -> None:
    """Update the field of view visualization."""
    target_grid.compute_fov(player_x, player_y, FOV_RADIUS, mcrfpy.FOV.SHADOW)

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if target_grid.is_in_fov(x, y):
                mark_explored(x, y)
                target_fov_layer.set(x, y, COLOR_VISIBLE)
            elif is_explored(x, y):
                target_fov_layer.set(x, y, COLOR_DISCOVERED)
            else:
                target_fov_layer.set(x, y, COLOR_UNKNOWN)

    update_entity_visibility(target_grid)

# =============================================================================
# Movement and Actions
# =============================================================================

def can_move_to(target_grid: mcrfpy.Grid, x: int, y: int, mover: mcrfpy.Entity = None) -> bool:
    """Check if a position is valid for movement."""
    if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
        return False

    if not target_grid.at(x, y).walkable:
        return False

    blocker = get_blocking_entity_at(target_grid, x, y, exclude=mover)
    if blocker is not None:
        return False

    return True

def try_move_or_attack(dx: int, dy: int) -> None:
    """Attempt to move the player or attack if blocked by enemy.

    Args:
        dx: Change in X position (-1, 0, or 1)
        dy: Change in Y position (-1, 0, or 1)
    """
    global player, grid, fov_layer, game_over

    if game_over:
        return

    px, py = int(player.x), int(player.y)
    target_x = px + dx
    target_y = py + dy

    # Check bounds
    if target_x < 0 or target_x >= GRID_WIDTH or target_y < 0 or target_y >= GRID_HEIGHT:
        return

    # Check for blocking entity
    blocker = get_blocking_entity_at(grid, target_x, target_y, exclude=player)

    if blocker is not None:
        # Attack the blocking entity
        perform_attack(player, blocker)
        # After player attacks, enemies take their turn
        enemy_turn()
    elif grid.at(target_x, target_y).walkable:
        # Move to the empty tile
        player.x = target_x
        player.y = target_y
        pos_display.text = f"Position: ({target_x}, {target_y})"

        # Update FOV after movement
        update_fov(grid, fov_layer, target_x, target_y)

        # Enemies take their turn after player moves
        enemy_turn()

    # Update HP display
    update_hp_display()

# =============================================================================
# Enemy AI
# =============================================================================

def enemy_turn() -> None:
    """Execute enemy actions."""
    global player, grid, game_over

    if game_over:
        return

    player_x, player_y = int(player.x), int(player.y)

    # Collect enemies that can act
    enemies = []
    for entity in grid.entities:
        if entity == player:
            continue
        if entity in entity_data and entity_data[entity].is_alive:
            enemies.append(entity)

    for enemy in enemies:
        fighter = entity_data.get(enemy)
        if fighter is None or not fighter.is_alive:
            continue

        ex, ey = int(enemy.x), int(enemy.y)

        # Only act if in player's FOV (aware of player)
        if not grid.is_in_fov(ex, ey):
            continue

        # Check if adjacent to player
        dx = player_x - ex
        dy = player_y - ey

        if abs(dx) <= 1 and abs(dy) <= 1 and (dx != 0 or dy != 0):
            # Adjacent - attack!
            perform_attack(enemy, player)
        else:
            # Not adjacent - try to move toward player
            move_toward_player(enemy, ex, ey, player_x, player_y)

def move_toward_player(enemy: mcrfpy.Entity, ex: int, ey: int, px: int, py: int) -> None:
    """Move an enemy one step toward the player.

    Uses simple greedy movement - not true pathfinding.
    """
    global grid

    # Calculate direction to player
    dx = 0
    dy = 0

    if px < ex:
        dx = -1
    elif px > ex:
        dx = 1

    if py < ey:
        dy = -1
    elif py > ey:
        dy = 1

    # Try to move in the desired direction
    # First try the combined direction
    new_x = ex + dx
    new_y = ey + dy

    if can_move_to(grid, new_x, new_y, enemy):
        enemy.x = new_x
        enemy.y = new_y
    elif dx != 0 and can_move_to(grid, ex + dx, ey, enemy):
        # Try horizontal only
        enemy.x = ex + dx
    elif dy != 0 and can_move_to(grid, ex, ey + dy, enemy):
        # Try vertical only
        enemy.y = ey + dy
    # If all fail, enemy stays in place

# =============================================================================
# UI Updates
# =============================================================================

def update_hp_display() -> None:
    """Update the HP display in the UI."""
    global player

    if hp_display is None or player is None:
        return

    if player in entity_data:
        fighter = entity_data[player]
        hp_display.text = f"HP: {fighter.hp}/{fighter.max_hp}"

        # Color based on health percentage
        hp_percent = fighter.hp / fighter.max_hp
        if hp_percent > 0.6:
            hp_display.fill_color = mcrfpy.Color(100, 255, 100)
        elif hp_percent > 0.3:
            hp_display.fill_color = mcrfpy.Color(255, 255, 100)
        else:
            hp_display.fill_color = mcrfpy.Color(255, 100, 100)

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
    size=(800, 480),
    grid_size=(GRID_WIDTH, GRID_HEIGHT),
    texture=texture
)
grid.zoom = 1.0

# Generate initial dungeon structure
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

# Create player Fighter component
entity_data[player] = Fighter(
    hp=30,
    max_hp=30,
    attack=5,
    defense=2,
    name="Player",
    is_player=True
)

# Spawn enemies in all rooms except the first
for i, room in enumerate(rooms):
    if i == 0:
        continue
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
    text="Part 6: Combat System"
)
title.fill_color = mcrfpy.Color(255, 255, 255)
title.font_size = 24
scene.children.append(title)

instructions = mcrfpy.Caption(
    pos=(50, 50),
    text="WASD/Arrows: Move/Attack | R: Restart | Escape: Quit"
)
instructions.fill_color = mcrfpy.Color(180, 180, 180)
instructions.font_size = 16
scene.children.append(instructions)

# Position display
pos_display = mcrfpy.Caption(
    pos=(50, 580),
    text=f"Position: ({int(player.x)}, {int(player.y)})"
)
pos_display.fill_color = mcrfpy.Color(200, 200, 100)
pos_display.font_size = 16
scene.children.append(pos_display)

# HP display
hp_display = mcrfpy.Caption(
    pos=(300, 580),
    text="HP: 30/30"
)
hp_display.fill_color = mcrfpy.Color(100, 255, 100)
hp_display.font_size = 16
scene.children.append(hp_display)

# Message log (positioned below the grid)
message_log_caption = mcrfpy.Caption(
    pos=(50, 610),
    text=""
)
message_log_caption.fill_color = mcrfpy.Color(200, 200, 200)
message_log_caption.font_size = 14
scene.children.append(message_log_caption)

# Initial message
add_message("Welcome to the dungeon! Find and defeat the enemies.", mcrfpy.Color(100, 100, 255))

# =============================================================================
# Input Handling
# =============================================================================

def restart_game() -> None:
    """Restart the game with a new dungeon."""
    global player, grid, fov_layer, game_over, entity_data, rooms

    game_over = False

    # Clear all entities and data
    entity_data.clear()

    # Remove all entities from grid
    while len(grid.entities) > 0:
        grid.entities.remove(0)

    # Regenerate dungeon
    fill_with_walls(grid)
    init_explored()
    clear_messages()

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

    # Get new player starting position
    if rooms:
        new_x, new_y = rooms[0].center
    else:
        new_x, new_y = GRID_WIDTH // 2, GRID_HEIGHT // 2

    # Recreate player
    player = mcrfpy.Entity(
        grid_pos=(new_x, new_y),
        texture=texture,
        sprite_index=SPRITE_PLAYER
    )
    grid.entities.append(player)

    entity_data[player] = Fighter(
        hp=30,
        max_hp=30,
        attack=5,
        defense=2,
        name="Player",
        is_player=True
    )

    # Spawn enemies
    for i, room in enumerate(rooms):
        if i == 0:
            continue
        spawn_enemies_in_room(grid, room, texture)

    # Reset FOV layer
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            fov_layer.set(x, y, COLOR_UNKNOWN)

    # Update displays
    update_fov(grid, fov_layer, new_x, new_y)
    pos_display.text = f"Position: ({new_x}, {new_y})"
    update_hp_display()

    add_message("A new adventure begins!", mcrfpy.Color(100, 100, 255))

def handle_keys(key: str, action: str) -> None:
    """Handle keyboard input."""
    global game_over

    if action != "start":
        return

    # Handle restart
    if key == "R":
        restart_game()
        return

    if key == "Escape":
        mcrfpy.exit()
        return

    # Ignore other input if game is over
    if game_over:
        return

    # Movement and attack
    if key == "W" or key == "Up":
        try_move_or_attack(0, -1)
    elif key == "S" or key == "Down":
        try_move_or_attack(0, 1)
    elif key == "A" or key == "Left":
        try_move_or_attack(-1, 0)
    elif key == "D" or key == "Right":
        try_move_or_attack(1, 0)

scene.on_key = handle_keys

# =============================================================================
# Start the Game
# =============================================================================

scene.activate()
print("Part 6 loaded! Combat is now active. Good luck!")