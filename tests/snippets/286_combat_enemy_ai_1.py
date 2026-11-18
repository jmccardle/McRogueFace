# mcrf: objects=[Easing,Entity,Grid,Scene] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("enemy_ai")
mcrfpy.current_scene = scene

# 32x24 cells at zoom 2: every cell walkable and transparent, with a few pillars.
grid = mcrfpy.Grid(
    grid_size=(32, 24),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=2.0,
)
scene.children.append(grid)

for gy in range(24):
    for gx in range(32):
        cell = grid.at(gx, gy)
        cell.tilesprite = 48 if (gx + gy) % 2 == 0 else 49
        cell.walkable = True
        cell.transparent = True

for px_, py_ in [(8, 6), (8, 7), (12, 9), (13, 9), (7, 12)]:
    pillar = grid.at(px_, py_)
    pillar.tilesprite = 0
    pillar.walkable = False
    pillar.transparent = False

player = mcrfpy.Entity(grid_pos=(10, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)
enemy_texture = mcrfpy.default_texture


def attack(attacker, target):
    print("attack!")


def move_with_animation(entity, new_x, new_y, duration=0.2):
    entity.grid_pos = (new_x, new_y)
    entity.animate("draw_pos", (new_x, new_y), duration, mcrfpy.Easing.EASE_IN_OUT)


# region: chase
import mcrfpy

def enemy_ai(enemy, player, grid):
    """Simple AI: chase the player and attack if adjacent."""
    # Get positions (tile coordinates, not pixel x/y)
    ex, ey = enemy.grid_x, enemy.grid_y
    px, py = player.grid_x, player.grid_y

    # Check if adjacent (can attack)
    distance = abs(ex - px) + abs(ey - py)
    if distance == 1:
        # Attack the player
        attack(enemy, player)
        return

    # Not adjacent - try to path toward player
    path = enemy.path_to(px, py)

    if path and len(path) > 0:
        # Move to first step in path
        next_x, next_y = path[0]

        # Check if tile is walkable and not occupied
        if is_walkable(grid, next_x, next_y) and not is_occupied(next_x, next_y):
            enemy.grid_x = next_x
            enemy.grid_y = next_y
# endregion


# region: sight
def enemy_ai_with_sight(enemy, player, grid, sight_range=8):
    """Chase player only when in sight range."""
    ex, ey = enemy.grid_x, enemy.grid_y
    px, py = player.grid_x, player.grid_y

    # Calculate distance
    distance = abs(ex - px) + abs(ey - py)

    # Check if player is in sight range
    if distance > sight_range:
        # Player not visible - wander or idle
        wander(enemy, grid)
        return

    # Optional: Check line of sight (no walls blocking)
    if not has_line_of_sight(grid, ex, ey, px, py):
        wander(enemy, grid)
        return

    # Player is visible - chase or attack
    if distance == 1:
        attack(enemy, player)
    else:
        path = enemy.path_to(px, py)
        if path:
            next_x, next_y = path[0]
            if is_walkable(grid, next_x, next_y):
                enemy.grid_x = next_x
                enemy.grid_y = next_y

def has_line_of_sight(grid, x1, y1, x2, y2):
    """Simple line of sight check using Bresenham's line."""
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    x, y = x1, y1

    while True:
        if x == x2 and y == y2:
            return True

        # Check if current tile blocks sight
        point = grid.at(x, y)
        if not point.transparent and (x != x1 or y != y1):
            return False

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

    return True
# endregion


# region: wander
import random

def wander(enemy, grid):
    """Move randomly to an adjacent walkable tile."""
    ex, ey = enemy.grid_x, enemy.grid_y

    # Get valid adjacent tiles
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    random.shuffle(directions)

    for dx, dy in directions:
        new_x, new_y = ex + dx, ey + dy

        if is_walkable(grid, new_x, new_y) and not is_occupied(new_x, new_y):
            enemy.grid_x = new_x
            enemy.grid_y = new_y
            return

    # No valid moves - stay in place

def is_walkable(grid, x, y):
    """Check if a tile can be walked on."""
    grid_w, grid_h = grid.grid_size
    if x < 0 or x >= grid_w or y < 0 or y >= grid_h:
        return False
    return grid.at(x, y).walkable

def is_occupied(x, y, entities=None):
    """Check if a tile is occupied by another entity."""
    if entities is None:
        return False

    for entity in entities:
        if entity.grid_x == x and entity.grid_y == y:
            return True
    return False
# endregion


# region: behaviors
class AIBehavior:
    """Base class for AI behaviors."""

    def execute(self, enemy, player, grid, entities):
        raise NotImplementedError


class ChaseAI(AIBehavior):
    """Always chase the player."""

    def execute(self, enemy, player, grid, entities):
        ex, ey = enemy.grid_x, enemy.grid_y
        px, py = player.grid_x, player.grid_y

        if abs(ex - px) + abs(ey - py) == 1:
            return ("attack", player)

        path = enemy.path_to(px, py)
        if path:
            return ("move", path[0])

        return ("wait", None)


class CowardAI(AIBehavior):
    """Run away from the player."""

    def execute(self, enemy, player, grid, entities):
        ex, ey = enemy.grid_x, enemy.grid_y
        px, py = player.grid_x, player.grid_y

        # Find direction away from player
        dx = 1 if ex > px else -1 if ex < px else 0
        dy = 1 if ey > py else -1 if ey < py else 0

        # Try to move away
        for new_x, new_y in [(ex + dx, ey), (ex, ey + dy), (ex + dx, ey + dy)]:
            if is_walkable(grid, new_x, new_y) and not is_occupied(new_x, new_y, entities):
                return ("move", (new_x, new_y))

        return ("wait", None)


class PatrolAI(AIBehavior):
    """Patrol between waypoints, chase if player spotted."""

    def __init__(self, waypoints):
        self.waypoints = waypoints
        self.current_waypoint = 0
        self.alert = False
        self.sight_range = 6

    def execute(self, enemy, player, grid, entities):
        ex, ey = enemy.grid_x, enemy.grid_y
        px, py = player.grid_x, player.grid_y
        distance = abs(ex - px) + abs(ey - py)

        # Check for player
        if distance <= self.sight_range:
            self.alert = True

        if self.alert:
            # Chase behavior
            if distance == 1:
                return ("attack", player)
            path = enemy.path_to(px, py)
            if path:
                return ("move", path[0])
            return ("wait", None)

        # Patrol behavior
        if not self.waypoints:
            return ("wait", None)

        target = self.waypoints[self.current_waypoint]

        if (ex, ey) == target:
            # Reached waypoint, go to next
            self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
            target = self.waypoints[self.current_waypoint]

        # Path to waypoint. grid.find_path() takes (start, end) tuples and
        # returns an AStarPath (or None) -- use peek() for the next step,
        # not path[0] (AStarPath doesn't support indexing).
        path = grid.find_path((ex, ey), target)
        if path:
            return ("move", path.peek().int)

        return ("wait", None)


class HunterAI(AIBehavior):
    """Wait until player is close, then chase aggressively."""

    def __init__(self, trigger_range=4, chase_range=12):
        self.trigger_range = trigger_range
        self.chase_range = chase_range
        self.hunting = False

    def execute(self, enemy, player, grid, entities):
        ex, ey = enemy.grid_x, enemy.grid_y
        px, py = player.grid_x, player.grid_y
        distance = abs(ex - px) + abs(ey - py)

        # Trigger hunting mode
        if distance <= self.trigger_range:
            self.hunting = True

        # Stop hunting if player escapes
        if distance > self.chase_range:
            self.hunting = False

        if not self.hunting:
            return ("wait", None)

        # Hunting - chase aggressively
        if distance == 1:
            return ("attack", player)

        path = enemy.path_to(px, py)
        if path:
            return ("move", path[0])

        return ("wait", None)
# endregion


# region: actions
def process_ai_action(enemy, action, target, player, grid):
    """Execute an AI action."""
    if action == "attack":
        attack(enemy, target)
    elif action == "move":
        new_x, new_y = target
        # Move with animation
        move_with_animation(enemy, new_x, new_y)
    elif action == "wait":
        pass  # Do nothing

def run_all_enemy_ai(enemies, player, grid):
    """Run AI for all enemies."""
    all_entities = [player] + [e.entity for e in enemies]

    for enemy_obj in enemies:
        if enemy_obj.hp <= 0:
            continue

        behavior = enemy_obj.ai
        action, target = behavior.execute(
            enemy_obj.entity,
            player,
            grid,
            all_entities
        )

        process_ai_action(enemy_obj.entity, action, target, player, grid)
# endregion


class Enemy:
    """Enemy with health, AI, and entity representation."""

    def __init__(self, grid, x, y, texture, sprite_index, ai_behavior):
        self.entity = mcrfpy.Entity((x, y), texture, sprite_index)
        grid.entities.append(self.entity)
        self.grid = grid
        self.hp = 10
        self.max_hp = 10
        self.attack_power = 3
        self.defense = 1
        self.ai = ai_behavior

    def take_turn(self, player, all_entities):
        """Execute AI and take action."""
        if self.hp <= 0:
            return

        action, target = self.ai.execute(
            self.entity, player, self.grid, all_entities
        )

        if action == "attack":
            damage = max(0, self.attack_power - target.defense)
            target.hp -= damage
        elif action == "move":
            new_x, new_y = target
            self.entity.grid_x = new_x
            self.entity.grid_y = new_y

    def destroy(self):
        """Remove from game."""
        self.entity.die()


# Usage
patrol_ai = PatrolAI([(5, 5), (15, 5), (15, 15), (5, 15)])
guard = Enemy(grid, 5, 5, enemy_texture, 0, patrol_ai)

hunter_ai = HunterAI(trigger_range=3, chase_range=10)
lurker = Enemy(grid, 20, 20, enemy_texture, 1, hunter_ai)


ex, ey = guard.entity.grid_x, guard.entity.grid_y
path = guard.entity.path_to(player.grid_x, player.grid_y)
# region: cardinal
# Filter to cardinal directions only
path = [p for p in path if abs(p[0] - ex) + abs(p[1] - ey) == 1]
# endregion


# region: alert
def alert_nearby(x, y, radius, enemies):
    for enemy in enemies:
        dist = abs(enemy.entity.grid_x - x) + abs(enemy.entity.grid_y - y)
        if dist <= radius and hasattr(enemy.ai, 'alert'):
            enemy.ai.alert = True
# endregion


# What a reader does with the pieces above: the guard has spotted the player, so one
# round of AI sends it chasing while the lurker waits; two helper enemies use the
# stand-alone chase and sight behaviours.
alert_nearby(player.grid_x, player.grid_y, 8, [guard, lurker])
run_all_enemy_ai([guard, lurker], player, grid)

raider = mcrfpy.Entity(grid_pos=(16, 8), texture=enemy_texture, sprite_index=112)
watcher = mcrfpy.Entity(grid_pos=(24, 14), texture=enemy_texture, sprite_index=113)
grid.entities.append(raider)
grid.entities.append(watcher)
enemy_ai(raider, player, grid)
enemy_ai_with_sight(watcher, player, grid)
