"""Play scene - the main game loop for Crypt of Sokoban.

Replaces the 7DRL's Crypt god object. Responsibilities are now split:
- PlayScene: scene lifecycle, input handling, turn sequencing
- Level: dungeon generation (level/generator.py)
- HUD: display updates (ui/hud.py)
- GameEntity subclasses: entity behavior (entities/*.py)

Key modernizations:
- Uses Key/InputState enums instead of string comparisons
- Uses grid.center_camera() instead of manual pixel math
- Entities register/unregister themselves (no manual list rebuilding)
- Dijkstra maps cleared when walkability changes (boulder moves)
"""

import random
import mcrfpy
from cos import Resources
from cos.constants import (
    GRID_ZOOM, LEVEL_PLANS, ENEMY_PRESETS,
)
from cos.level.generator import Level
from cos.entities.player import PlayerEntity
from cos.entities.enemies import EnemyEntity
from cos.entities.objects import BoulderEntity, ExitEntity, TreasureEntity
from cos.items.equipment import build_treasure_table
from cos.ui.hud import HUD
from cos.ui.widgets import SweetButton


class PlayScene:
    """The main gameplay scene.

    Manages the turn-based game loop: player input -> entity actions ->
    HUD update. Owns the current level, entity registry, and HUD.

    The entity registry (self.entities) replaces the 7DRL's dual-tracking
    pattern where entities lived in both a Python list and the engine's
    grid.entities collection. Now entities add themselves to the engine
    grid on creation and register with us for turn processing.
    """

    def __init__(self):
        self.scene = mcrfpy.Scene("play")
        self.ui = self.scene.children

        self.entities = []  # all GameEntity instances for turn processing
        self.depth = 1
        self.player = None
        self.level = None
        self.grid = None
        self.hud = HUD()

        # "Stuck" button for level regeneration
        self.stuck_btn = SweetButton(
            (810, 700), "Stuck", icon=19,
            box_width=150, box_height=60, click=self._on_stuck,
        )

        # Create initial level
        self._create_liminal_void()
        self.player = PlayerEntity(game=self)
        self._generate_level(self.depth)
        self._swap_to_level()

    # -- Entity registry --------------------------------------------------
    # Replaces the 7DRL's add_entity() which sorted, cleared, and rebuilt
    # the engine's entity list every time an entity was added.

    def register_entity(self, entity):
        """Called by GameEntity.__init__ to register for turn processing."""
        self.entities.append(entity)

    def unregister_entity(self, entity):
        """Called by GameEntity.die() to remove from turn processing."""
        if entity in self.entities:
            self.entities.remove(entity)

    # -- Scene lifecycle --------------------------------------------------

    def activate(self):
        res = Resources()
        res.play_sfx(1)
        self.scene.on_key = self._on_key
        self.scene.activate()

    # -- Level management -------------------------------------------------

    def _create_liminal_void(self):
        """Create a 1x1 grid for entity initialization before level gen."""
        res = Resources()
        self.grid = mcrfpy.Grid(
            grid_size=(1, 1), texture=res.tileset,
            pos=(0, 0), size=(16, 16),
        )

    def _generate_level(self, depth):
        """Generate a new level and populate it with entities."""
        self.level = Level(20, 20)
        self.grid = self.level.grid

        # Get the level plan
        if depth in LEVEL_PLANS:
            plan = LEVEL_PLANS[depth]
        else:
            plan = self._procedural_plan(depth)

        # Generate the level layout and get feature positions
        coords = self.level.generate(plan)

        # Clear entity registry (player persists across levels)
        self.entities = []

        # Spawn entities from feature coordinates
        self.spawn_point = (0, 0)
        self._spawn_entities(coords)

    def _spawn_entities(self, coords):
        """Spawn entities from (feature_name, position) pairs.

        Sorted alphabetically so "button" comes before "exit",
        ensuring the button exists when the exit references it.
        """
        buttons = []
        for name, pos in sorted(coords, key=lambda c: c[0]):
            if name == "spawn":
                if self.player:
                    self.register_entity(self.player)
                    self.spawn_point = pos
            elif name == "boulder":
                BoulderEntity(pos[0], pos[1], game=self)
            elif name == "treasure":
                table = build_treasure_table(
                    self.depth,
                    self.player.archetype if self.player else None,
                )
                TreasureEntity(pos[0], pos[1], game=self, treasure_table=table)
            elif name == "button":
                buttons.append(pos)
            elif name == "exit":
                btn = buttons.pop(0)
                ExitEntity(pos[0], pos[1], btn[0], btn[1], game=self)
            elif name in ENEMY_PRESETS:
                EnemyEntity.from_preset(name, pos[0], pos[1], game=self)

    def _swap_to_level(self):
        """Switch the scene to display the current level."""
        self.grid = self.level.grid
        self.grid.zoom = GRID_ZOOM

        # Center camera on the grid using tile coordinates
        gw = int(self.grid.grid_size.x)
        gh = int(self.grid.grid_size.y)
        self.grid.center_camera((gw / 2.0, gh / 2.0))

        # Move player to spawn point
        if self.player:
            self.player.grid = self.grid
            self.player.draw_pos = self.spawn_point

        # Rebuild scene UI
        # Clear and repopulate (no more try/except workaround needed)
        while len(self.ui) > 0:
            self.ui.pop(0)
        self.ui.append(self.grid)
        self.ui.append(self.stuck_btn.base_frame)
        self.ui.append(self.hud.headsup)
        self.ui.append(self.hud.sidebar)

        self.hud.update(self.player, self.depth)

    def descend(self):
        """Called by ExitEntity when the player enters an unlocked exit."""
        self.depth += 1
        self._generate_level(self.depth)
        self._swap_to_level()

    # -- Turn sequencing ---------------------------------------------------

    def _enemy_turn(self):
        """Process one turn for all entities, then update HUD.

        Fixes 7DRL bug: consuming items in slots 2-3 now costs a turn.
        """
        for entity in sorted(self.entities, key=lambda e: e.draw_order):
            entity.act()
        if self.player:
            self.player.tick_equipment()
        self.hud.update(self.player, self.depth)

    # -- Input handling ---------------------------------------------------

    def _on_key(self, key, action):
        """Keyboard handler using Key/InputState enums.

        Replaces the 7DRL's string-based comparisons:
          Old: if key == "W" and state == "end": ...
          New: if key == mcrfpy.Key.W and action == mcrfpy.InputState.PRESSED: ...
        """
        if action != mcrfpy.InputState.PRESSED:
            return

        direction = None

        # Movement (WASD)
        if key == mcrfpy.Key.W:
            direction = (0, -1)
        elif key == mcrfpy.Key.A:
            direction = (-1, 0)
        elif key == mcrfpy.Key.S:
            direction = (0, 1)
        elif key == mcrfpy.Key.D:
            direction = (1, 0)

        # Zap
        elif key == mcrfpy.Key.Z:
            self.player.do_zap()
            self._enemy_turn()
            return

        # Consume items (all slots now cost a turn - fixes 7DRL bug)
        elif key == mcrfpy.Key.Num1:
            if self.player.consume_item(0):
                self._enemy_turn()
            return
        elif key == mcrfpy.Key.Num2:
            if self.player.consume_item(1):
                self._enemy_turn()
            return
        elif key == mcrfpy.Key.Num3:
            if self.player.consume_item(2):
                self._enemy_turn()
            return

        # Wait (skip turn)
        elif key == mcrfpy.Key.PERIOD:
            self._enemy_turn()
            return

        # Pull boulder
        elif key == mcrfpy.Key.X:
            self._pull_boulder_search()
            return

        # Debug: skip to next level
        elif key == mcrfpy.Key.P:
            self.descend()
            return

        # Debug: interactive console (native builds only)
        elif key == mcrfpy.Key.GRAVE:
            try:
                import code
                code.InteractiveConsole(locals=globals()).interact()
            except ImportError:
                pass
            return

        # Execute movement
        if direction:
            self.player.try_move(*direction)
            self._enemy_turn()

    # -- Boulder pulling --------------------------------------------------

    def _pull_boulder_search(self):
        """Find an adjacent boulder and pull it."""
        px, py = self.player.grid_x, self.player.grid_y
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            for entity in self.entities:
                if not isinstance(entity, BoulderEntity):
                    continue
                if entity.grid_x == px + dx and entity.grid_y == py + dy:
                    self.pull_boulder_move((dx, dy), entity)
                    self._enemy_turn()
                    return

    def pull_boulder_move(self, direction, boulder):
        """Pull a boulder: player moves away, boulder follows.

        Args:
            direction: (dx, dy) from player to boulder
            boulder: the BoulderEntity to pull
        """
        dx, dy = direction
        # Player moves opposite to the boulder direction
        if self.player.try_move(-dx, -dy, test=True):
            old_x, old_y = self.player.grid_x, self.player.grid_y
            self.player.try_move(-dx, -dy)
            boulder.do_move(old_x, old_y)

    # -- Callbacks --------------------------------------------------------

    def _on_stuck(self, btn, args):
        """Regenerate the current level (Stuck button)."""
        if args[3] == mcrfpy.InputState.RELEASED:
            return
        self._generate_level(self.depth)
        self._swap_to_level()

    # -- Procedural level planning ----------------------------------------

    def _procedural_plan(self, depth):
        """Generate a level plan for depths beyond the hand-authored plans."""
        monsters = (depth - 6) // 2
        target_rooms = min(depth // 2, 6)
        target_treasure = min(depth // 3, 4)

        rooms = [[] for _ in range(target_rooms)]

        # Required features go in random rooms
        for feature in ("spawn", "boulder", "button", "exit"):
            rooms[random.randint(0, target_rooms - 1)].append(feature)

        # Monster spawns
        monster_weights = {
            "rat": int(monsters * 0.8) + 2,
            "big rat": max(int(monsters * 0.2) - 2, 0),
            "cyclops": max(int(monsters * 0.1) - 3, 0),
        }
        monster_weights = {k: v for k, v in monster_weights.items() if v > 0}
        names = list(monster_weights.keys())
        weights = [monster_weights[k] for k in names]
        for _ in range(monsters):
            r = random.randint(0, target_rooms - 1)
            rooms[r].append(random.choices(names, weights=weights)[0])

        # Treasure
        for _ in range(target_treasure):
            rooms[random.randint(0, target_rooms - 1)].append("treasure")

        return [tuple(room) for room in rooms]
