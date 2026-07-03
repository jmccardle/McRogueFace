"""UNWRITTEN - enemy tables and encounter packs. Owner: Agent B.

Numbers canon from SYSTEMS section 4; boss behavior from BIBLE section 4.
Area/variant textures (Pale Echo, Chime-Imp, Grey Echo) are hue/sat-shifted
copies of the shared atlas, built ONCE here at import via TEX.hsl_shift.

ENEMIES : id -> record used by systems.battle to build combatants.
PACKS   : pack_id -> list of enemy ids (order = left-to-right on screen).
ASCII only. "Fail early": unknown ids raise.
"""
from core.assets import TEX

# ------------------------------------------------- variant textures (built once)
# Pale Echo: sprite 121 hue -40 deg (hsl_shift takes [0,360) so -40 -> 320).
PALE_ECHO_TEX = TEX.hsl_shift(320.0, 0.0, 0.0)
# Chime-Imp: sprite 110 hue +160 deg (teal).
CHIME_TEX = TEX.hsl_shift(160.0, 0.0, 0.0)
# Grey Echo (Custodian summon): starter sprite 85, drained of color.
GREY_ECHO_TEX = TEX.hsl_shift(0.0, -0.85, 0.02)


def _e(name, sprite, hp, atk, mag, dfn, spd, xp, gold, ai="basic",
       labels=None, tex=None, scale=4.0, drop=None):
    return {
        "name": name, "sprite": sprite,
        "HP": hp, "ATK": atk, "MAG": mag, "DEF": dfn, "SPD": spd,
        "XP": xp, "gold": gold, "ai": ai,
        "labels": set(labels or ()), "tex": tex, "scale": scale, "drop": drop,
    }


ENEMIES = {
    "gloom_bat":       _e("Gloom Bat", 120, 14, 5, 0, 1, 8, 6, 4, ai="bat"),
    "hedge_slime":     _e("Hedge Slime", 108, 20, 4, 0, 3, 2, 7, 5, ai="slime"),
    "slimelet":        _e("Slimelet", 108, 8, 3, 0, 1, 3, 0, 0, ai="basic",
                          scale=3.0),
    "loom_spider":     _e("Loom Spider", 122, 16, 6, 0, 2, 6, 8, 6, ai="spider"),
    "waxwing_scarab":  _e("Waxwing Scarab", 123, 24, 6, 0, 5, 3, 10, 8,
                          ai="scarab"),
    "unwoken_skeleton": _e("Unwoken Skeleton", 86, 26, 8, 0, 3, 5, 13, 10,
                           ai="skeleton", labels=("undead",)),
    "pale_echo":       _e("Pale Echo", 121, 18, 0, 8, 1, 7, 12, 0, ai="echo",
                          tex=PALE_ECHO_TEX,
                          drop=("chalk", 0.40)),
    "chime_imp":       _e("Chime-Imp", 110, 22, 7, 4, 3, 7, 14, 12, ai="chime",
                          labels=("construct",), tex=CHIME_TEX),
    "mimic":           _e("Mimic", 92, 45, 10, 0, 6, 1, 30, 60, ai="mimic"),

    # ---------------------------------------------------------------- bosses
    "gatekeeper":      _e("The Gatekeeper", 20, 150, 11, 6, 8, 3, 80, 100,
                          ai="gatekeeper", labels=("construct",), scale=7.0),
    "custodian":       _e("The Custodian", 41, 210, 9, 12, 7, 6, 0, 0,
                          ai="custodian", labels=("construct",), scale=8.0),

    # -------------------------------------------------------- boss summons/misc
    # Bell: Chime-Imp stats but the base (red) sprite, unshifted.
    "bell":            _e("Bell", 110, 22, 7, 4, 3, 7, 0, 0, ai="chime",
                          labels=("construct",)),
    # Grey Echo: Pale Echo stats +50%, desaturated starter sprite.
    "grey_echo":       _e("Grey Echo", 85, 27, 0, 12, 2, 7, 0, 0, ai="echo",
                          labels=("construct",), tex=GREY_ECHO_TEX),
}


# ------------------------------------------------------------------------ packs
PACKS = {
    # Gearwood (Act 1): soft encounters. gw_slimes is size 2 so slimes split.
    "gw_bats":    ["gloom_bat", "gloom_bat", "gloom_bat"],
    "gw_mixed":   ["gloom_bat", "hedge_slime", "loom_spider"],
    "gw_mixed2":  ["loom_spider", "gloom_bat", "hedge_slime"],
    "gw_scarabs": ["waxwing_scarab", "waxwing_scarab"],
    "gw_slimes":  ["hedge_slime", "hedge_slime"],

    # Undercroft (Act 2): proper dungeon. uc_mimic is solo.
    "uc_bones":   ["unwoken_skeleton", "unwoken_skeleton"],
    "uc_bones2":  ["unwoken_skeleton", "unwoken_skeleton", "waxwing_scarab"],
    "uc_chimes":  ["chime_imp", "chime_imp"],
    "uc_echoes":  ["pale_echo", "pale_echo", "unwoken_skeleton"],
    "uc_mixed":   ["unwoken_skeleton", "pale_echo", "waxwing_scarab"],
    "uc_mimic":   ["mimic"],

    # Act 3 Study approach: pale echoes only (the world is running out).
    "st_echoes":  ["pale_echo", "pale_echo"],
    "st_echoes2": ["pale_echo", "pale_echo", "pale_echo"],

    # Bosses (BIBLE section 4). Gatekeeper flanked by two Chime-Imps.
    "boss_gatekeeper": ["chime_imp", "gatekeeper", "chime_imp"],
    "boss_custodian":  ["custodian"],
}


def pack(pack_id):
    if pack_id not in PACKS:
        raise KeyError("unknown battle pack %r in data.enemies.PACKS" % (pack_id,))
    return list(PACKS[pack_id])


def enemy(enemy_id):
    if enemy_id not in ENEMIES:
        raise KeyError("unknown enemy id %r in data.enemies.ENEMIES" % (enemy_id,))
    return ENEMIES[enemy_id]
