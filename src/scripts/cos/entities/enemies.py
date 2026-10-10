"""Enemy entities for Crypt of Sokoban.

Major change from 7DRL: uses engine's Dijkstra pathfinding instead of
manual Manhattan-distance pursuit. Enemies now path around walls correctly.
"""

from cos.entities.base import GameEntity
from cos.entities.player import PlayerEntity
from cos.constants import (
    SPRITE_DEAD_OFFSET, DRAW_ORDER_ENEMY, DRAW_ORDER_DEAD_ENEMY,
    ENEMY_PRESETS,
)


class EnemyEntity(GameEntity):
    """A hostile creature that pursues and attacks the player.

    AI behavior (act()):
    - If adjacent to player: attack
    - If player is in sight range: pathfind toward player using Dijkstra
    - Otherwise: wander randomly

    The original 7DRL had two bugs in direction checking:
    - Checked (1,0) twice, never checked (0,-1) - enemies couldn't see north
    - towards[0] crashed with IndexError when no walkable neighbors existed
    Both are fixed here.
    """

    draw_order = DRAW_ORDER_ENEMY
    CARDINAL_DIRS = ((1, 0), (0, 1), (-1, 0), (0, -1))

    def __init__(self, x, y, *, game, hp=2, base_damage=1, base_defense=0,
                 sprite=123, can_push=False, crushable=True, sight=8,
                 move_cooldown=1):
        super().__init__(game.grid, x, y, sprite, game=game)
        self.hp = hp
        self.base_damage = base_damage
        self.base_defense = base_defense
        self.base_sprite = sprite
        self.can_push = can_push
        self.crushable = crushable
        self.sight = sight
        self.move_cooldown = move_cooldown
        self.moved_last = 0

    @classmethod
    def from_preset(cls, name, x, y, *, game):
        """Create an enemy from a named preset (e.g. 'rat', 'cyclops')."""
        preset = ENEMY_PRESETS[name]
        return cls(x, y, game=game, **preset)

    @property
    def alive(self):
        return self.hp > 0

    def _mark_dead(self):
        """Visual indicator: swap to dead sprite, drop draw order."""
        self.sprite_number = self.base_sprite + SPRITE_DEAD_OFFSET
        self.draw_order = DRAW_ORDER_DEAD_ENEMY

    def receive_damage(self, amount, source="melee"):
        """Take damage and die if HP reaches 0."""
        self.hp = max(self.hp - amount, 0)
        if self.hp == 0:
            self._mark_dead()

    def bump(self, other, dx, dy, test=False):
        """Handle being bumped by another entity."""
        # Dead enemies are walkable
        if not self.alive:
            if not test:
                other.do_move(self.grid_x, self.grid_y)
            return True

        if isinstance(other, PlayerEntity):
            damage = other.calc_damage()
            self.receive_damage(damage, source="melee")
            return False  # player doesn't move into enemy tile

        from cos.entities.objects import BoulderEntity
        if isinstance(other, BoulderEntity):
            if not self.crushable:
                return False
            # Crushed by boulder
            self.receive_damage(self.hp, source="crush")
            if not test:
                other.do_move(self.grid_x, self.grid_y)
            return True

        return False

    def act(self):
        """Turn-based AI using Dijkstra pathfinding.

        Replaces the 7DRL's manual Manhattan-distance pursuit that
        couldn't path around walls and had direction-checking bugs.
        """
        if not self.alive:
            return

        player = self.game.player
        px, py = player.grid_x, player.grid_y
        x, y = self.grid_x, self.grid_y

        # Adjacent to player? Attack directly.
        for dx, dy in self.CARDINAL_DIRS:
            if x + dx == px and y + dy == py:
                self.try_move(dx, dy)
                return

        # Movement cooldown (doesn't affect melee attacks)
        if self.moved_last > 0:
            self.moved_last -= 1
            return
        self.moved_last = self.move_cooldown

        distance = abs(x - px) + abs(y - py)

        # Can-push enemies: charge in a line toward player
        if self.can_push:
            if x == px:
                self.try_move(0, 1 if y < py else -1)
                return
            if y == py:
                self.try_move(1 if x < px else -1, 0)
                return

        # Out of sight? Wander randomly.
        if distance > self.sight:
            import random
            dx, dy = random.choice(self.CARDINAL_DIRS)
            self.try_move(dx, dy)
            return

        # In sight: use Dijkstra pathfinding to pursue player.
        # The engine caches Dijkstra maps per root position, so
        # multiple enemies sharing the same target are efficient.
        grid = self.entity.grid
        if grid is None:
            return
        dijkstra = grid.get_dijkstra_map((px, py))
        next_step = dijkstra.step_from((x, y))
        if next_step is not None:
            dx = int(next_step.x) - x
            dy = int(next_step.y) - y
            self.try_move(dx, dy)
