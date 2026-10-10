"""Player entity for Crypt of Sokoban."""

from cos.entities.base import GameEntity
from cos.constants import SPRITE_PLAYER, DRAW_ORDER_PLAYER


class PlayerEntity(GameEntity):
    """The player character.

    Handles combat stats, equipment, inventory, and receiving items.
    Movement and collision are handled by the base class.
    """

    draw_order = DRAW_ORDER_PLAYER

    def __init__(self, *, game):
        super().__init__(game.grid, 0, 0, SPRITE_PLAYER, game=game)
        self.hp = 10
        self.max_hp = 10
        self.base_damage = 1
        self.base_defense = 0
        self.luck = 0
        self.archetype = None
        self.equipped = []   # list of Equippable (weapons/shields)
        self.inventory = []  # list of Equippable (consumables), max 3
        self.base_zap_damage = 0
        self.base_zap_cooldown = 0
        self.base_zap_range = 4

    def calc_damage(self):
        return self.base_damage + sum(e.damage for e in self.equipped)

    def calc_defense(self):
        return self.base_defense + sum(e.defense for e in self.equipped)

    def tick_equipment(self):
        """Advance cooldowns on all equipped items. Called each turn."""
        for item in self.equipped:
            item.tick()

    def do_zap(self):
        """Fire the first ready zap-capable equipped item."""
        from cos.entities.enemies import EnemyEntity
        enemies = [e for e in self.game.entities if isinstance(e, EnemyEntity)]
        for item in self.equipped:
            if item.zap_damage and item.zap_cooldown_remaining == 0:
                if item.do_zap(self, enemies):
                    return True
        return False

    def bump(self, other, dx, dy, test=False):
        """Player is bumped by another entity (takes damage)."""
        from cos.entities.objects import BoulderEntity
        if isinstance(other, BoulderEntity):
            # Boulder knocked into player = knockback the boulder
            return self.game.pull_boulder_move((-dx, -dy), other)
        # Take damage from attacker
        incoming = max(other.base_damage - self.calc_defense(), 0)
        self.hp = max(self.hp - incoming, 0)
        return False  # attacker doesn't move into our tile

    def receive(self, equip):
        """Try to add an item to equipment or inventory.

        Returns True if the item was accepted, False if full.
        """
        if equip.hands == 0:
            # Consumable -> inventory (max 3 slots)
            active_items = [i for i in self.inventory if i is not None]
            if len(active_items) < 3:
                if None in self.inventory:
                    self.inventory[self.inventory.index(None)] = equip
                else:
                    self.inventory.append(equip)
                return True
            return False
        elif equip.hands == 1:
            if len(self.equipped) < 2:
                self.equipped.append(equip)
                return True
            return False
        else:  # 2-handed
            if len(self.equipped) == 0:
                self.equipped.append(equip)
                return True
            return False

    def consume_item(self, slot_index):
        """Use a consumable from inventory by slot index (0-2).

        Returns True if an item was consumed, False if slot is empty.
        """
        if slot_index >= len(self.inventory):
            return False
        item = self.inventory[slot_index]
        if item is None:
            return False
        item.consume(self)
        self.inventory[slot_index] = None
        return True
