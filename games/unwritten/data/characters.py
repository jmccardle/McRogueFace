"""UNWRITTEN - party data tables. Owner: Agent B.

BASE (level-1 stats), GROWTH (per-level growth dicts, index i applied when a
character REACHES level i+2, so 7 entries cover levels 2..8), SKILLS (per-char
[skillA, skillB]) and CHAR_SPRITES. Numbers are canon from SYSTEMS sections 1
and 3. ASCII only.

state.CharState reads BASE[cid] and GROWTH[cid]; battle.py reads SKILLS and
CHAR_SPRITES. "Fail early": unknown ids raise KeyError at the call site.
"""

# --------------------------------------------------------------- sprite indices
CHAR_SPRITES = {
    "PIP": 85,
    "BRAMBLE": 96,
    "MOTH": 84,
    "VERA": 111,
    "CANTOR": 109,
    "NYX": 121,
}

# --------------------------------------------------------------- base stats (L1)
BASE = {
    "PIP":     {"HP": 34, "SP": 10, "ATK": 7, "MAG": 3, "DEF": 4, "SPD": 9},
    "BRAMBLE": {"HP": 46, "SP": 8,  "ATK": 6, "MAG": 2, "DEF": 7, "SPD": 4},
    "MOTH":    {"HP": 28, "SP": 16, "ATK": 3, "MAG": 8, "DEF": 3, "SPD": 6},
    "VERA":    {"HP": 31, "SP": 12, "ATK": 5, "MAG": 6, "DEF": 4, "SPD": 6},
    "CANTOR":  {"HP": 40, "SP": 12, "ATK": 8, "MAG": 6, "DEF": 6, "SPD": 2},
    "NYX":     {"HP": 22, "SP": 12, "ATK": 9, "MAG": 5, "DEF": 2, "SPD": 10},
}


def _const(g):
    return [dict(g) for _ in range(7)]


def _alt(base, extra):
    """7 growth dicts. Even reached-levels (2,4,6,8 -> index 0,2,4,6) get the
    `extra` +1s on top of `base`; odd levels get only `base`."""
    out = []
    for i in range(7):
        d = dict(base)
        if i % 2 == 0:
            for k, v in extra.items():
                d[k] = d.get(k, 0) + v
        out.append(d)
    return out


# --------------------------------------------------------------- per-level growth
GROWTH = {
    "PIP":     _const({"HP": 6, "SP": 2, "ATK": 2, "DEF": 1, "SPD": 1}),
    "BRAMBLE": _const({"HP": 9, "SP": 1, "ATK": 1, "DEF": 2}),
    "MOTH":    _alt({"HP": 4, "SP": 4, "MAG": 2}, {"DEF": 1, "SPD": 1}),
    "VERA":    _alt({"HP": 5, "SP": 3}, {"ATK": 1, "MAG": 1, "DEF": 1, "SPD": 1}),
    "CANTOR":  _const({"HP": 7, "SP": 2, "ATK": 2, "MAG": 1, "DEF": 1}),
    "NYX":     _const({"HP": 3, "SP": 3, "ATK": 3, "SPD": 1}),
}

# --------------------------------------------------------------- crit base (%/100)
CRIT_BASE = {
    "PIP": 0.06, "BRAMBLE": 0.06, "MOTH": 0.06,
    "VERA": 0.06, "CANTOR": 0.06, "NYX": 0.18,
}

# NYX passive evasion (SYSTEMS section 3)
NYX_EVASION = 0.20

# ------------------------------------------------------------------------ SKILLS
# Each skill: id, name, sp, unlock (skill A = 1, skill B = 4), desc for the
# submenu, and mechanical fields the battle engine dispatches on via "special".
#   kind:   phys | magic | heal | buff | selfbuff
#   target: enemy | all_enemies | ally | party | self
#   mult:   damage/heal multiplier (semantics per special)
#   hits:   number of strikes (phys)
#   debuff: {"stat","mult","turns"} applied to target(s)
SKILLS = {
    "PIP": [
        {"id": "twinstrike", "name": "Twinstrike", "sp": 3, "unlock": 1,
         "kind": "phys", "target": "enemy", "mult": 0.7, "hits": 2,
         "special": "twinstrike",
         "desc": "Two quick hits at 0.7x each."},
        {"id": "pickpocket", "name": "Pickpocket", "sp": 2, "unlock": 4,
         "kind": "phys", "target": "enemy", "mult": 0.6, "hits": 1,
         "special": "pickpocket",
         "desc": "0.6x hit; steal 8-20 cogs, once per foe."},
    ],
    "BRAMBLE": [
        {"id": "shieldwall", "name": "Shieldwall", "sp": 3, "unlock": 1,
         "kind": "buff", "target": "party", "special": "shieldwall",
         "desc": "Party takes half damage until Bramble's next turn."},
        {"id": "vow_strike", "name": "Vow Strike", "sp": 4, "unlock": 4,
         "kind": "phys", "target": "enemy", "mult": 1.0, "hits": 1,
         "special": "vow_strike",
         "desc": "Grows stronger the more HP Bramble is missing."},
    ],
    "MOTH": [
        {"id": "kindle", "name": "Kindle", "sp": 4, "unlock": 1,
         "kind": "heal", "target": "ally", "special": "kindle",
         "heals_nyx": True,
         "desc": "Heal one ally 24 + 2*MAG. Works on Nyx."},
        {"id": "moonflare", "name": "Moonflare", "sp": 6, "unlock": 4,
         "kind": "magic", "target": "all_enemies", "mult": 1.1,
         "special": "moonflare",
         "desc": "Radiant AoE, 1.1x magic to all foes."},
    ],
    "VERA": [
        {"id": "acid_flask", "name": "Acid Flask", "sp": 4, "unlock": 1,
         "kind": "magic", "target": "all_enemies", "mult": 0.7,
         "special": "acid_flask",
         "debuff": {"stat": "DEF", "mult": -0.25, "turns": 2},
         "desc": "AoE 0.7x and DEF -25% (2 turns)."},
        {"id": "tonic_toss", "name": "Tonic Toss", "sp": 3, "unlock": 4,
         "kind": "heal", "target": "ally", "special": "tonic_toss",
         "heals_nyx": False,
         "desc": "Heal one 16 + MAG, clear debuffs. Not Nyx."},
    ],
    "CANTOR": [
        {"id": "resonate", "name": "Resonate", "sp": 4, "unlock": 1,
         "kind": "magic", "target": "enemy", "mult": 1.2,
         "special": "resonate",
         "desc": "1.2x magic; stuns constructs/undead 1 turn."},
        {"id": "bass_drop", "name": "Bass Drop", "sp": 7, "unlock": 4,
         "kind": "phys", "target": "enemy", "mult": 2.2, "hits": 1,
         "special": "bass_drop",
         "desc": "Massive 2.2x single hit; acts last this round."},
    ],
    "NYX": [
        {"id": "grave_chill", "name": "Grave Chill", "sp": 3, "unlock": 1,
         "kind": "magic", "target": "enemy", "mult": 1.0,
         "special": "grave_chill",
         "debuff": {"stat": "SPD", "mult": -0.30, "turns": 2},
         "desc": "1.0x magic and SPD -30% (2 turns)."},
        {"id": "second_shadow", "name": "Second Shadow", "sp": 5, "unlock": 4,
         "kind": "selfbuff", "target": "self", "special": "second_shadow",
         "desc": "Her next attack is a guaranteed crit."},
    ],
}


def learned_skills(char_id, level):
    """Skills available to char_id at `level` (unlock <= level)."""
    if char_id not in SKILLS:
        raise KeyError("no skills for %r in data.characters.SKILLS" % (char_id,))
    return [s for s in SKILLS[char_id] if level >= s["unlock"]]


def skill_by_id(skill_id):
    for lst in SKILLS.values():
        for s in lst:
            if s["id"] == skill_id:
                return s
    raise KeyError("unknown skill id %r" % (skill_id,))
