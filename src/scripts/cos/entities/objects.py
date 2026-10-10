"""Static/interactive game objects for Crypt of Sokoban.

Boulder, Button, Exit, and Treasure entities.
"""

from cos.entities.base import GameEntity
from cos.entities.player import PlayerEntity
from cos.items.equipment import generate_treasure, build_treasure_table
from cos.constants import (
    SPRITE_BOULDER, SPRITE_BUTTON,
    SPRITE_EXIT_LOCKED, SPRITE_EXIT_UNLOCKED,
    SPRITE_TREASURE_CLOSED, SPRITE_TREASURE_OPEN,
    DRAW_ORDER_BOULDER, DRAW_ORDER_BUTTON,
    DRAW_ORDER_EXIT, DRAW_ORDER_TREASURE,
)


class BoulderEntity(GameEntity):
    """A pushable boulder - the core Sokoban mechanic.

    Can be pushed by the player (and push-capable enemies).
    Cannot be pushed by other boulders.
    """

    draw_order = DRAW_ORDER_BOULDER

    def __init__(self, x, y, *, game):
        super().__init__(game.grid, x, y, SPRITE_BOULDER, game=game)

    def bump(self, other, dx, dy, test=False):
        # Boulders can't push boulders
        if isinstance(other, BoulderEntity):
            return False

        # Only push-capable enemies can push boulders
        from cos.entities.enemies import EnemyEntity
        if isinstance(other, EnemyEntity) and not other.can_push:
            return False

        # Can the boulder move in the push direction?
        old_x, old_y = self.grid_x, self.grid_y
        if self.try_move(dx, dy, test=test):
            if not test:
                other.do_move(old_x, old_y)
            return True
        return False


class ButtonEntity(GameEntity):
    """A pressure plate that unlocks its paired exit.

    Triggers on ev_enter (anything steps on it) and
    untriggers on ev_exit (anything leaves it).
    """

    draw_order = DRAW_ORDER_BUTTON

    def __init__(self, x, y, exit_entity, *, game):
        super().__init__(game.grid, x, y, SPRITE_BUTTON, game=game)
        self.exit = exit_entity

    def ev_enter(self, other):
        self.exit.unlock()

    def ev_exit(self, other):
        self.exit.lock()

    def bump(self, other, dx, dy, test=False):
        # Buttons are always walkable - entities pass through
        if not test:
            other.do_move(self.grid_x, self.grid_y)
        return True


class ExitEntity(GameEntity):
    """A locked exit that opens when its paired button is pressed.

    When the player walks through an unlocked exit, the game
    advances to the next level.
    """

    draw_order = DRAW_ORDER_EXIT

    def __init__(self, x, y, button_x, button_y, *, game):
        super().__init__(game.grid, x, y, SPRITE_EXIT_LOCKED, game=game)
        self.my_button = ButtonEntity(button_x, button_y, self, game=game)
        self.unlocked = False

    def unlock(self):
        self.sprite_number = SPRITE_EXIT_UNLOCKED
        self.unlocked = True

    def lock(self):
        self.sprite_number = SPRITE_EXIT_LOCKED
        self.unlocked = False

    def bump(self, other, dx, dy, test=False):
        # Boulders can't go through exits
        if isinstance(other, BoulderEntity):
            return False

        if not self.unlocked:
            return False

        if not test:
            other.do_move(self.grid_x + dx, self.grid_y + dy)

        # Player descends to the next level
        if isinstance(other, PlayerEntity):
            self.game.descend()

        return True


class TreasureEntity(GameEntity):
    """A treasure chest that generates a random item when opened.

    Only the player can open chests. Once opened, they remain
    as visual decoration (open sprite) but can't be looted again.
    """

    draw_order = DRAW_ORDER_TREASURE

    def __init__(self, x, y, *, game, treasure_table=None):
        super().__init__(game.grid, x, y, SPRITE_TREASURE_CLOSED, game=game)
        self.opened = False
        self.treasure_table = treasure_table or {}

    def bump(self, other, dx, dy, test=False):
        if not isinstance(other, PlayerEntity):
            return False

        if self.opened:
            return True  # already opened, just walk through

        if not test:
            self.sprite_number = SPRITE_TREASURE_OPEN
            self.opened = True
            if self.treasure_table:
                item = generate_treasure(
                    self.treasure_table,
                    self.game.depth,
                    other.luck,
                )
                other.receive(item)

        return False  # player doesn't move onto the chest
