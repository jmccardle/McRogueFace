"""Item template definitions for Crypt of Sokoban.

Clean data module from the original 7DRL - no changes needed.
Each entry defines a loot-table item with level range, drop weight,
sprite, base stats, archetype affinity, and handedness.
"""

from dataclasses import dataclass


@dataclass
class ItemData:
    min_lv: int
    max_lv: int
    base_wt: float
    sprite: int
    base_value: int  # int for weapons/armor/potions, tuple(dmg, cd) for magic
    base_name: str
    affinity: str   # player archetype that boosts drop rate ("knight"/"viking"/"wizard"/None)
    handedness: int  # 0=consumable, 1=one-handed, 2=two-handed


ITEM_DATA = {
    # -- Shields --
    "buckler":     ItemData(1, 10, 0.25, 101, 1, "Buckler",        "knight", 1),
    "shield":      ItemData(2, 99, 0.15, 102, 2, "Shield",         "knight", 1),

    # -- Swords --
    "sword":       ItemData(1, 10, 0.25, 103, 1, "Shortsword",     "knight", 1),
    "sword2":      ItemData(2, 16, 0.15, 104, 2, "Longsword",      "knight", 1),
    "sword3":      ItemData(5, 99, 0.08, 105, 5, "Claymore",       "knight", 2),

    # -- Axes --
    "axe":         ItemData(1, 10, 0.25, 119, 1, "Hatchet",        "viking", 1),
    "axe2":        ItemData(2, 16, 0.15, 120, 4, "Broad Axe",      "viking", 2),
    "axe3":        ItemData(5, 99, 0.08, 121, 6, "Bearded Axe",    "viking", 2),

    # -- Magic weapons (base_value is (damage, cooldown) tuple) --
    "wand":        ItemData(1, 10, 0.25, 132, (1, 10), "Wand",           "wizard", 1),
    "staff":       ItemData(2, 16, 0.15, 130, (2, 8),  "Sceptre",        "wizard", 2),
    "staff2":      ItemData(5, 99, 0.08, 131, (3, 7),  "Wizard's Staff", "wizard", 2),

    # -- Potions (handedness=0 = consumable) --
    "red_pot":     ItemData(1, 99, 0.25, 115, 1, "Health Potion",   None,     0),
    "blue_pot":    ItemData(1, 99, 0.10, 116, 1, "Sorcery Potion",  "wizard", 0),
    "green_pot":   ItemData(1, 99, 0.10, 114, 1, "Strength Potion", "viking", 0),
    "grey_pot":    ItemData(1, 99, 0.10, 113, 1, "Defense Potion",  "knight", 0),
    "sm_grey_pot": ItemData(1, 99, 0.05, 125, 1, "Luck Potion",    None,     0),
}
