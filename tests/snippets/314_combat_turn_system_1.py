# mcrf: objects=[Caption,Color,Entity,Frame,Grid,InputState,Key,Scene] verified=0.3.6 status=ok
# region: turn_manager
import mcrfpy

class TurnManager:
    """Manages turn order for actors in a turn-based game."""

    def __init__(self):
        self.actors = []      # List of (actor, speed) tuples
        self.current = 0      # Index of current actor
        self.turn_number = 0  # Global turn counter
        self.state = "waiting"  # waiting, player_turn, enemy_turn

    def add_actor(self, actor, speed=100):
        """Add an actor with a speed value (higher = acts first)."""
        self.actors.append({"actor": actor, "speed": speed, "energy": 0})
        self._sort_by_speed()

    def remove_actor(self, actor):
        """Remove an actor from the turn order."""
        self.actors = [a for a in self.actors if a["actor"] != actor]
        if self.current >= len(self.actors):
            self.current = 0

    def _sort_by_speed(self):
        """Sort actors by speed (descending)."""
        self.actors.sort(key=lambda a: a["speed"], reverse=True)

    def current_actor(self):
        """Get the actor whose turn it is."""
        if not self.actors:
            return None
        return self.actors[self.current]["actor"]

    def end_turn(self):
        """End the current actor's turn and advance to next."""
        if not self.actors:
            return None

        self.current = (self.current + 1) % len(self.actors)

        # Increment turn number when we wrap around
        if self.current == 0:
            self.turn_number += 1

        return self.current_actor()

    def is_player_turn(self, player):
        """Check if it's the player's turn."""
        return self.current_actor() == player
# endregion


# region: energy_manager
class EnergyTurnManager:
    """Turn manager using energy accumulation for speed differences."""

    ENERGY_THRESHOLD = 100  # Energy needed to take a turn

    def __init__(self):
        self.actors = []
        self.current_actor_data = None

    def add_actor(self, actor, speed=100):
        """Add actor with speed (determines energy gain per tick)."""
        self.actors.append({
            "actor": actor,
            "speed": speed,
            "energy": 0
        })

    def remove_actor(self, actor):
        """Remove an actor from the system."""
        self.actors = [a for a in self.actors if a["actor"] != actor]

    def tick(self):
        """Advance time and return next actor ready to act, or None."""
        # Give energy to all actors
        for actor_data in self.actors:
            actor_data["energy"] += actor_data["speed"]

        # Find actor with most energy above threshold
        ready = [a for a in self.actors if a["energy"] >= self.ENERGY_THRESHOLD]

        if ready:
            # Highest energy acts first
            ready.sort(key=lambda a: a["energy"], reverse=True)
            self.current_actor_data = ready[0]
            return self.current_actor_data["actor"]

        return None

    def end_turn(self):
        """Spend energy for the current actor's turn."""
        if self.current_actor_data:
            self.current_actor_data["energy"] -= self.ENERGY_THRESHOLD
            self.current_actor_data = None

    def get_next_actor(self):
        """Get next actor to act, ticking time if needed."""
        # Keep ticking until someone can act
        for _ in range(1000):  # Safety limit
            actor = self.tick()
            if actor:
                return actor
        return None
# endregion


# region: game_loop
import mcrfpy

# Game state
class GameState:
    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn"
    ANIMATING = "animating"
    GAME_OVER = "game_over"

# Scene the turn-based loop runs in
scene = mcrfpy.Scene("game")
mcrfpy.current_scene = scene

# Initialize turn manager
turn_manager = TurnManager()
game_state = GameState.PLAYER_TURN

# Track player and enemies
player = None
enemies = []

def setup_game(grid, player_entity, enemy_entities):
    """Initialize the turn system with game entities."""
    global player, enemies

    player = player_entity
    enemies = enemy_entities

    # Add player first (or with high speed)
    turn_manager.add_actor(player, speed=100)

    # Add enemies
    for enemy in enemies:
        turn_manager.add_actor(enemy, speed=80)

def process_turn():
    """Process the current actor's turn."""
    global game_state

    current = turn_manager.current_actor()

    if current == player:
        # Player's turn - wait for input
        game_state = GameState.PLAYER_TURN
    else:
        # Enemy turn - run AI
        game_state = GameState.ENEMY_TURN
        process_enemy_turn(current)

def process_enemy_turn(enemy):
    """Execute enemy AI and end their turn."""
    # Enemy AI logic here (see combat_enemy_ai.md)
    # ...

    # End turn after action
    end_current_turn()

def end_current_turn():
    """End current turn and advance to next actor."""
    global game_state

    # Check for dead actors
    cleanup_dead_actors()

    # Advance to next
    turn_manager.end_turn()

    # Check win/lose conditions
    if not enemies:
        game_state = GameState.GAME_OVER
        show_victory()
    elif player_is_dead():
        game_state = GameState.GAME_OVER
        show_defeat()
    else:
        # Continue to next turn
        process_turn()

def cleanup_dead_actors():
    """Remove dead actors from turn order."""
    global enemies

    # Remove dead enemies
    for enemy in enemies[:]:
        if enemy.hp <= 0:
            turn_manager.remove_actor(enemy)
            enemies.remove(enemy)

def handle_player_input(key, action):
    """Handle keyboard input during player's turn."""
    if action == mcrfpy.InputState.RELEASED:
        return
    if action == mcrfpy.InputState.REPEATED and key not in (mcrfpy.Key.W, mcrfpy.Key.UP, mcrfpy.Key.S, mcrfpy.Key.DOWN, mcrfpy.Key.A, mcrfpy.Key.LEFT, mcrfpy.Key.D, mcrfpy.Key.RIGHT):
        return  # held movement keys keep moving; Space (wait) needs a fresh press (#549)

    if game_state != GameState.PLAYER_TURN:
        return  # Not player's turn

    # Movement keys
    dx, dy = 0, 0
    if key in (mcrfpy.Key.W, mcrfpy.Key.UP):
        dy = -1
    elif key in (mcrfpy.Key.S, mcrfpy.Key.DOWN):
        dy = 1
    elif key in (mcrfpy.Key.A, mcrfpy.Key.LEFT):
        dx = -1
    elif key in (mcrfpy.Key.D, mcrfpy.Key.RIGHT):
        dx = 1
    elif key == mcrfpy.Key.SPACE:
        # Wait/skip turn
        end_current_turn()
        return

    if dx != 0 or dy != 0:
        # Try to move or attack
        if try_move_or_attack(player, dx, dy):
            end_current_turn()

scene.on_key = handle_player_input
# endregion


# What the recipe assumes the rest of the game provides.
class Actor:
    """A combatant: a grid entity with a name and hit points."""

    def __init__(self, grid, name, x, y, sprite_index, hp):
        self.name = name
        self.hp = hp
        self.entity = mcrfpy.Entity((x, y), mcrfpy.default_texture, sprite_index)
        grid.entities.append(self.entity)


def player_is_dead():
    return player.hp <= 0


def show_victory():
    scene.children.append(mcrfpy.Caption(text="Victory!", pos=(20, 20)))


def show_defeat():
    scene.children.append(mcrfpy.Caption(text="Defeat", pos=(20, 20)))


def try_move_or_attack(actor, dx, dy):
    """Attack an enemy standing in the way, otherwise step onto the cell."""
    tx = actor.entity.cell_x + dx
    ty = actor.entity.cell_y + dy
    for enemy in enemies:
        if (enemy.entity.cell_x, enemy.entity.cell_y) == (tx, ty):
            enemy.hp -= 5
            return True
    if 0 <= tx < 16 and 0 <= ty < 12:
        actor.entity.cell_pos = (tx, ty)
        return True
    return False


grid = mcrfpy.Grid(grid_size=(16, 12), pos=(0, 0), size=(640, 480))
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

hero = Actor(grid, "Hero", 3, 6, 84, hp=20)
goblin = Actor(grid, "Goblin", 8, 6, 112, hp=10)
orc = Actor(grid, "Orc", 10, 4, 108, hp=15)

setup_game(grid, hero, [goblin, orc])
process_turn()


# region: turn_order_ui
def create_turn_order_ui(scene, turn_manager, x=800, y=50):
    """Create a visual turn order display."""
    # Background frame
    frame = mcrfpy.Frame(pos=(x, y), size=(200, 300))
    frame.fill_color = mcrfpy.Color(30, 30, 30, 200)
    frame.outline = 2
    frame.outline_color = mcrfpy.Color(100, 100, 100)
    scene.children.append(frame)

    # Title
    title = mcrfpy.Caption(text="Turn Order", x=x + 10, y=y + 10)
    title.fill_color = mcrfpy.Color(255, 255, 255)
    scene.children.append(title)

    return frame

def update_turn_order_display(scene, frame, turn_manager, x=800, y=50):
    """Update the turn order display."""

    # Clear old entries (keep frame and title)
    # In practice, store references to caption objects and update them

    for i, actor_data in enumerate(turn_manager.actors):
        actor = actor_data["actor"]
        is_current = (i == turn_manager.current)

        # Actor name/type
        name = getattr(actor, 'name', f"Actor {i}")
        color = mcrfpy.Color(255, 255, 0) if is_current else mcrfpy.Color(200, 200, 200)

        caption = mcrfpy.Caption(text=name, pos=(x + 10, y + 40 + i * 25))
        caption.fill_color = color
        scene.children.append(caption)
# endregion

order_frame = create_turn_order_ui(scene, turn_manager)
update_turn_order_display(scene, order_frame, turn_manager)

base_speed = 80

# region: tip_initiative
import random
speed = base_speed + random.randint(-10, 10)
# endregion
