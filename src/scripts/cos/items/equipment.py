"""Equipment and consumable item instances.

Extracted from the original cos_entities.py where it was mixed in
with entity definitions. Equippable represents a concrete item
instance (with rolled stats), as opposed to ItemData (the template).
"""

import random
from cos.items.data import ITEM_DATA


# Bonus stat color tiers (bonus_stats -> text color)
BONUS_COLORS = {
    1: (192, 255, 192),
    2: (128, 128, 192),
    3: (255, 192, 255),
    4: (255, 192, 192),
    5: (255, 0, 0),
}


class Equippable:
    """A concrete item instance with rolled stats.

    Attributes:
        hands: 0=consumable, 1=one-handed, 2=two-handed
        hp_healing: HP restored on consume (consumables only)
        damage: melee damage bonus (weapons)
        defense: defense bonus (shields/armor)
        zap_damage: ranged magic damage
        zap_cooldown: turns between zaps
        zap_cooldown_remaining: current cooldown counter
        sprite: tileset sprite index
        text: display name (may include bonus suffix)
        text_color: display color (tinted by bonus tier)
        boost: potion boost type key (e.g. "green_pot") or None
        value: boost magnitude for consumables
    """

    def __init__(self, *, hands=0, hp_healing=0, damage=0, defense=0,
                 zap_damage=0, zap_cooldown=10, sprite=129,
                 boost=None, text="", text_color=(255, 255, 255), value=0):
        self.hands = hands
        self.hp_healing = hp_healing
        self.damage = damage
        self.defense = defense
        self.zap_damage = zap_damage
        self.zap_cooldown = zap_cooldown
        self.zap_cooldown_remaining = 0
        self.sprite = sprite
        self.text = text
        self.text_color = text_color
        self.boost = boost
        self.value = value

    def tick(self):
        """Advance cooldown by one turn."""
        if self.zap_cooldown_remaining > 0:
            self.zap_cooldown_remaining -= 1

    def classify(self):
        """Return a human-readable item category string."""
        if self.hands == 0:
            return "consumable"
        if self.damage > 0:
            return f"{self.hands}-handed weapon"
        if self.defense > 0:
            return "defense"
        if self.zap_damage > 0:
            return f"{self.hands}-handed magic weapon"
        return "unclassifiable"

    def consume(self, consumer):
        """Apply consumable effect to the consumer (PlayerEntity)."""
        if self.boost == "green_pot":
            consumer.base_damage += self.value
        elif self.boost == "blue_pot":
            for _ in range(self.value):
                bonus = random.choice(["damage", "cooldown", "range"])
                if bonus == "damage":
                    consumer.base_zap_damage += 1
                elif bonus == "cooldown":
                    consumer.base_zap_cooldown += 1
                else:
                    consumer.base_zap_range += 1
        elif self.boost == "grey_pot":
            consumer.base_defense += self.value
        elif self.boost == "sm_grey_pot":
            consumer.luck += self.value
        elif self.hp_healing:
            consumer.hp = min(consumer.hp + self.hp_healing, consumer.max_hp)

    def do_zap(self, caster, enemies):
        """Fire a ranged zap at the nearest enemy in range.

        Args:
            caster: the entity casting (needs draw_pos, base_zap_range)
            enemies: iterable of enemy entities to target

        Returns:
            True if a target was hit, False otherwise.
        """
        if self.zap_damage == 0:
            return False
        if self.zap_cooldown_remaining > 0:
            return False

        cx, cy = int(caster.draw_pos.x), int(caster.draw_pos.y)
        targets = []
        for e in enemies:
            if e.hp <= 0:
                continue
            dist = abs(int(e.draw_pos.x) - cx) + abs(int(e.draw_pos.y) - cy)
            if dist <= caster.base_zap_range:
                targets.append(e)

        if not targets:
            return False

        target = random.choice(targets)
        target.receive_damage(self.zap_damage, source="zap")
        self.zap_cooldown_remaining = self.zap_cooldown
        return True

    def __repr__(self):
        parts = [f"text={self.text!r}", f"hands={self.hands}"]
        if self.damage:
            parts.append(f"damage={self.damage}")
        if self.defense:
            parts.append(f"defense={self.defense}")
        if self.zap_damage:
            parts.append(f"zap={self.zap_damage}/{self.zap_cooldown}")
        if self.hp_healing:
            parts.append(f"heal={self.hp_healing}")
        return f"<Equippable {', '.join(parts)}>"


def generate_treasure(treasure_table, depth, luck):
    """Roll a random item from the treasure table.

    Args:
        treasure_table: dict of item_key -> weight
        depth: current dungeon depth (affects bonus stats)
        luck: player luck stat (affects bonus stats)

    Returns:
        An Equippable instance with rolled stats.
    """
    items = list(treasure_table.keys())
    weights = [treasure_table[k] for k in items]
    item_key = random.choices(items, weights=weights)[0]

    bonus_max = int((depth + luck * 2) * 0.66)
    bonus = random.randint(0, bonus_max) if bonus_max > 0 else 0

    data = ITEM_DATA[item_key]
    equip = _create_base_item(item_key, data, bonus)

    if bonus > 0:
        equip.text = f"{equip.text} (+{bonus})"
        tier = min(bonus, 5)
        equip.text_color = BONUS_COLORS[tier]

    return equip


def build_treasure_table(depth, archetype=None):
    """Build a weighted loot table for the given depth and player archetype.

    Args:
        depth: current dungeon depth
        archetype: player archetype ("knight"/"viking"/"wizard"/None)

    Returns:
        dict of item_key -> weight
    """
    table = {}
    for key, data in ITEM_DATA.items():
        if data.min_lv > depth or depth > data.max_lv:
            continue
        weight = data.base_wt
        if archetype is not None and data.affinity == archetype:
            weight *= 3
        table[key] = weight
    return table


def _create_base_item(item_key, data, bonus):
    """Create an Equippable from item data + bonus stats."""
    # Melee weapons
    if item_key in ("sword", "sword2", "sword3", "axe", "axe2", "axe3"):
        return Equippable(
            hands=data.handedness, sprite=data.sprite,
            damage=data.base_value + bonus, text=data.base_name,
        )
    # Shields
    if item_key in ("buckler", "shield"):
        return Equippable(
            hands=data.handedness, sprite=data.sprite,
            defense=data.base_value + bonus, text=data.base_name,
        )
    # Magic weapons
    if item_key in ("wand", "staff", "staff2"):
        base_dmg, base_cd = data.base_value
        equip = Equippable(
            hands=data.handedness, sprite=data.sprite,
            zap_damage=base_dmg, zap_cooldown=base_cd, text=data.base_name,
        )
        for _ in range(bonus):
            if equip.zap_cooldown <= 2 or random.random() > 0.66:
                equip.zap_damage += 1
            else:
                equip.zap_cooldown -= 1
        return equip
    # Health potion
    if item_key == "red_pot":
        return Equippable(
            hands=data.handedness, sprite=data.sprite,
            hp_healing=data.base_value + bonus, text=data.base_name,
        )
    # Stat-boost potions
    if item_key in ("blue_pot", "green_pot", "grey_pot", "sm_grey_pot"):
        return Equippable(
            hands=data.handedness, sprite=data.sprite,
            text=data.base_name, boost=item_key,
            value=data.base_value + bonus,
        )
    # Fallback (should not happen with known item keys)
    return Equippable(text=f"Unknown({item_key})")
