"""UNWRITTEN - items and equipment. Owner: Agent B.

Numbers canon from SYSTEMS section 5. Three views over one source of truth:
  ITEMS   : id -> full record (name, sprite, cost, kind, effect/equip fields)
  EQUIP   : id -> stat-delta dict  (read by systems.state.CharState)
  SHOP_STOCK : act -> list of item ids Griselda stocks

Gold is called "cogs" in prose (BIBLE). "Fail early": unknown ids raise.
ASCII only.
"""

# kind values: "consumable", "weapon", "trinket", "key"

ITEMS = {
    # --------------------------------------------------------- consumables
    "bread": {"name": "Bread", "sprite": 66, "cost": 8, "kind": "consumable",
              "effect": "heal", "amount": 12,
              "desc": "Restores 12 HP."},
    "red_tonic": {"name": "Red Tonic", "sprite": 115, "cost": 20,
                  "kind": "consumable", "effect": "heal", "amount": 30,
                  "desc": "Restores 30 HP."},
    "green_salve": {"name": "Green Salve", "sprite": 114, "cost": 25,
                    "kind": "consumable", "effect": "cleanse_heal", "amount": 10,
                    "desc": "Clears debuffs and restores 10 HP."},
    "blue_draught": {"name": "Blue Draught", "sprite": 116, "cost": 30,
                     "kind": "consumable", "effect": "sp", "amount": 15,
                     "desc": "Restores 15 SP."},
    "bomb_flask": {"name": "Bomb Flask", "sprite": 113, "cost": 35,
                   "kind": "consumable", "effect": "aoe_damage", "amount": 22,
                   "target": "all_enemies",
                   "desc": "22 damage to all foes. Anyone can throw it."},
    "chalk": {"name": "Chalk", "sprite": 102, "cost": 90, "kind": "consumable",
              "effect": "revive", "amount": 0.40, "shop_limit": 1,
              "desc": "Revive a fallen ally at 40% HP."},

    # --------------------------------------------------------------- weapons
    "knife": {"name": "Knife", "sprite": 105, "cost": 15, "kind": "weapon",
              "equip": {"ATK": 2}, "desc": "+2 ATK. Starter tier."},
    "short_sword": {"name": "Short Sword", "sprite": 103, "cost": 40,
                    "kind": "weapon", "equip": {"ATK": 4}, "desc": "+4 ATK."},
    "broad_blade": {"name": "Broad Blade", "sprite": 106, "cost": 90,
                    "kind": "weapon", "equip": {"ATK": 7},
                    "desc": "+7 ATK. Act 2 unlock."},
    "worn_cudgel": {"name": "Worn Cudgel", "sprite": 117, "cost": 15,
                    "kind": "weapon", "equip": {"ATK": 2},
                    "desc": "+2 ATK. Bramble/Cantor flavor."},
    "twin_axe": {"name": "Twin Axe", "sprite": 119, "cost": 90, "kind": "weapon",
                 "equip": {"ATK": 6, "SPD": 2}, "desc": "+6 ATK, +2 SPD."},
    "wick_staff": {"name": "Wick Staff", "sprite": 129, "cost": 45,
                   "kind": "weapon", "equip": {"MAG": 4}, "desc": "+4 MAG."},
    "tide_rod": {"name": "Tide Rod", "sprite": 130, "cost": 95, "kind": "weapon",
                 "equip": {"MAG": 7}, "desc": "+7 MAG. Act 2 unlock."},
    "toothed_regret": {"name": "Toothed Regret", "sprite": 118, "cost": 0,
                       "kind": "weapon", "equip": {"ATK": 10, "MAG": 6},
                       "desc": "+10 ATK, +6 MAG. Griselda's reforge."},

    # -------------------------------------------------------------- trinkets
    "river_stone": {"name": "River Stone", "sprite": 101, "cost": 25,
                    "kind": "trinket", "equip": {"DEF": 2}, "desc": "+2 DEF."},
    "waxed_charm": {"name": "Waxed Charm", "sprite": 56, "cost": 60,
                    "kind": "trinket", "equip": {"DEF": 3, "HP": 5},
                    "desc": "+3 DEF, +5 max HP."},
    "second_trinket": {"name": "Second Trinket", "sprite": 91, "cost": 0,
                       "kind": "trinket",
                       "equip": {"HP": 2, "SP": 2, "ATK": 2, "MAG": 2,
                                 "DEF": 2, "SPD": 2},
                       "desc": "+2 to all stats. The name is the joke."},
    "gatekeepers_tooth": {"name": "Gatekeeper's Tooth", "sprite": 107,
                          "cost": 0, "kind": "trinket", "equip": {"ATK": 3},
                          "desc": "+3 ATK until reforged."},

    # ------------------------------------------------------------- key items
    "blank_book": {"name": "Blank Book", "sprite": 94, "cost": 0, "kind": "key",
                   "desc": "The book that was not there yesterday."},
    "brass_key": {"name": "Brass Key", "sprite": 104, "cost": 0, "kind": "key",
                  "desc": "Opens the Undercroft stair."},
}

# ----------------------------------------------------- stat-delta view for state
EQUIP = {iid: rec["equip"] for iid, rec in ITEMS.items() if "equip" in rec}

# -------------------------------------------------------------------- shop stock
# Act 1: sub-90-cog tier only. Act 2 unlocks the 90+ gear. Act 3 = Act 2 stock.
_ACT1 = ["knife", "short_sword", "worn_cudgel", "wick_staff",
         "river_stone", "waxed_charm",
         "bread", "red_tonic", "green_salve", "blue_draught", "bomb_flask",
         "chalk"]
_ACT2 = _ACT1 + ["broad_blade", "twin_axe", "tide_rod"]

SHOP_STOCK = {1: list(_ACT1), 2: list(_ACT2), 3: list(_ACT2)}


def item(item_id):
    if item_id not in ITEMS:
        raise KeyError("unknown item id %r in data.items.ITEMS" % (item_id,))
    return ITEMS[item_id]


def is_consumable(item_id):
    return ITEMS.get(item_id, {}).get("kind") == "consumable"
