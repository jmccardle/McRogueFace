"""Base entity class for Crypt of Sokoban.

The original 7DRL used a COSEntity wrapper around mcrfpy.Entity via
composition (self._entity) to work around engine bugs #72 and #76.
Those bugs are fixed. This remaster uses mcrfpy.Entity directly,
with game logic stored in a parallel GameEntity object that holds
a reference to the engine entity.

Design decision: We still use composition rather than inheritance
because mcrfpy.Entity is a C extension type. Subclassing C extension
types in Python works but has caveats with __init__ signatures and
tp_alloc. Composition is explicit and avoids those edge cases.
The key difference from the 7DRL version is that we no longer need
workarounds for iteration, removal, or property access.
"""

import mcrfpy
from cos import Resources
from cos.constants import SPRITE_EMPTY, DRAW_ORDER_PLAYER


class GameEntity:
    """Base class for all game entities with turn-based logic.

    Each GameEntity owns an mcrfpy.Entity for rendering and provides
    game logic (movement, collision, events). The entity registry on
    the Game object tracks all GameEntities for turn processing.

    Attributes:
        entity: the underlying mcrfpy.Entity for rendering
        game: reference to the Game (play scene) for entity registry
        draw_order: rendering priority (lower = behind)
    """

    draw_order = 0

    def __init__(self, grid, x, y, sprite, *, game):
        res = Resources()
        self.entity = mcrfpy.Entity(
            grid_pos=(x, y), texture=res.tileset, sprite_index=sprite,
        )
        self.entity.grid = grid
        self.game = game
        game.register_entity(self)

    # -- Position access (no more proxied properties) ---------------------

    @property
    def grid_x(self):
        return int(self.entity.draw_pos.x)

    @property
    def grid_y(self):
        return int(self.entity.draw_pos.y)

    @property
    def pos(self):
        """Integer (x, y) tile position."""
        return (self.grid_x, self.grid_y)

    @property
    def draw_pos(self):
        return self.entity.draw_pos

    @draw_pos.setter
    def draw_pos(self, value):
        self.entity.draw_pos = value

    @property
    def sprite_number(self):
        return self.entity.sprite_number

    @sprite_number.setter
    def sprite_number(self, value):
        self.entity.sprite_number = value

    @property
    def grid(self):
        return self.entity.grid

    @grid.setter
    def grid(self, value):
        self.entity.grid = value

    # -- Core mechanics ---------------------------------------------------

    def die(self):
        """Remove this entity from the game.

        Uses the engine's native entity.die() instead of the 7DRL's
        manual index-based removal workaround.
        """
        self.entity.die()
        self.game.unregister_entity(self)

    def try_move(self, dx, dy, test=False):
        """Attempt to move by (dx, dy). Returns True if movement succeeded.

        Checks for entity collisions first (via bump()), then grid
        walkability. If test=True, only checks feasibility without moving.
        """
        grid = self.entity.grid
        if grid is None:
            return False
        gw, gh = int(grid.grid_size.x), int(grid.grid_size.y)
        tx, ty = self.grid_x + dx, self.grid_y + dy

        if tx < 0 or tx >= gw or ty < 0 or ty >= gh:
            return False

        # Check entity collisions (sorted by draw_order descending so
        # boulders are tested before buttons when overlapping)
        for other in sorted(self.game.entities, key=lambda e: e.draw_order, reverse=True):
            if other.grid_x == tx and other.grid_y == ty:
                return other.bump(self, dx, dy, test=test)

        if grid.at((tx, ty)).walkable:
            if not test:
                self.do_move(tx, ty)
            return True
        return False

    def do_move(self, tx, ty):
        """Execute a move to (tx, ty), firing enter/exit events.

        The original used draw_pos for all position logic. We maintain
        that for now but use grid_x/grid_y for integer comparisons.
        """
        old_x, old_y = self.grid_x, self.grid_y
        self.draw_pos = (tx, ty)

        for e in self.game.entities:
            if e is self:
                continue
            if e.grid_x == old_x and e.grid_y == old_y:
                e.ev_exit(self)

        for e in self.game.entities:
            if e is self:
                continue
            if e.grid_x == tx and e.grid_y == ty:
                e.ev_enter(self)

    # -- Overridable hooks ------------------------------------------------

    def act(self):
        """Called each turn. Override in subclasses for AI/behavior."""
        pass

    def bump(self, other, dx, dy, test=False):
        """Called when another entity tries to move into our tile.

        Returns True if the mover is allowed to enter, False otherwise.
        """
        return False

    def ev_enter(self, other):
        """Called when another entity moves onto our tile."""
        pass

    def ev_exit(self, other):
        """Called when another entity leaves our tile."""
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} ({self.grid_x}, {self.grid_y})>"
