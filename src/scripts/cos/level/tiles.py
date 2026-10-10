"""Tile painting system for Crypt of Sokoban.

# =========================================================================
# COLLABORATION NOTE: This module duplicates the 7DRL's WFC tile rules.
#
# The tile rules were hand-authored during the game jam and shipped with
# known bugs. This is a direct port of the original cos_tiles.py behavior
# so that the remaster renders identically while other systems are upgraded.
#
# PLANNED REPLACEMENT: Wang tiles via engine's WangSet API.
# When a proper .tsx tileset is designed in Tiled with Wang terrain metadata:
#   1. Load the tileset: tileset = mcrfpy.TileSetFile("dungeon.tsj")
#   2. Get the Wang set: wang = tileset.wang_set("dungeon_terrain")
#   3. Build terrain map from BSP room/wall data
#   4. Resolve: tile_ids = wang.resolve(terrain_map)
#   5. Apply to grid layer: wang.apply(terrain_map, tile_layer)
# This will replace the entire WFC system below (~150 lines).
# See tests/demo/screens/tiled_demo.py for a working Wang tile example.
# =========================================================================
"""

import random
from cos.constants import TILE_FALLBACK

# 3x3 neighborhood deltas (row-major: TL, T, TR, L, C, R, BL, B, BR)
DELTAS = [
    (-1, -1), (0, -1), (+1, -1),
    (-1,  0), (0,  0), (+1,  0),
    (-1, +1), (0, +1), (+1, +1),
]

CARDINAL_DIRECTIONS = {
    "N": (0, -1),
    "S": (0, +1),
    "E": (-1, 0),
    "W": (+1, 0),
}


class TileRule:
    """A tile-matching rule: a 3x3 pattern of ground/wall/don't-care.

    Ported from the 7DRL's TileInfo class.
    """
    GROUND = True
    WALL = False
    DONTCARE = None

    CHAR_MAP = {"X": False, "_": True, "?": None}

    def __init__(self, pattern, tile_id, chance=1.0, special_rules=None):
        """
        Args:
            pattern: dict mapping (dx,dy) -> GROUND/WALL/DONTCARE
            tile_id: sprite index to use when this rule matches
            chance: weighted random selection probability
            special_rules: list of (cardinal, required_tile_id) constraints
        """
        self.pattern = pattern
        self.tile_id = tile_id
        self.chance = chance
        self.special_rules = special_rules or []

    @classmethod
    def from_string(cls, pattern_str, tile_id, chance=1.0, special_rules=None):
        """Parse a 9-character pattern string (e.g. '???_X_???')."""
        pattern = {}
        for delta, char in zip(DELTAS, pattern_str):
            pattern[delta] = cls.CHAR_MAP[char]
        return cls(pattern, tile_id, chance, special_rules)

    def matches(self, neighborhood):
        """Check if this rule matches a 3x3 neighborhood."""
        for delta, required in self.pattern.items():
            if required is None:
                continue
            actual = neighborhood.get(delta)
            if actual is None:
                continue
            if required != actual:
                return False
        return True


def _read_neighborhood(grid, x, y):
    """Read the 3x3 walkability neighborhood around (x, y)."""
    gw = int(grid.grid_size.x)
    gh = int(grid.grid_size.y)
    values = {}
    for dx, dy in DELTAS:
        tx, ty = x + dx, y + dy
        if tx < 0 or tx >= gw or ty < 0 or ty >= gh:
            values[(dx, dy)] = True  # out of bounds = ground
        else:
            values[(dx, dy)] = grid.at((tx, ty)).walkable
    return values


def _check_special_rule(rule, grid, x, y, unverified, pass_unverified=False):
    """Check a cardinal-direction tile constraint."""
    cardinal, required_tile = rule
    dx, dy = CARDINAL_DIRECTIONS[cardinal.upper()]
    tx, ty = x + dx, y + dy
    # Lowercase cardinal = check unverified status
    if (tx, ty) in unverified and cardinal in "nsew":
        return pass_unverified
    gw = int(grid.grid_size.x)
    gh = int(grid.grid_size.y)
    if tx < 0 or tx >= gw or ty < 0 or ty >= gh:
        return False
    return grid.at((tx, ty)).tilesprite == required_tile


def _find_possible_tiles(grid, x, y, rules, unverified=None, pass_unverified=False):
    """Find all tile rules that match at position (x, y)."""
    if unverified is None:
        unverified = set()
    neighborhood = _read_neighborhood(grid, x, y)
    matches = [(r, r.tile_id) for r in rules if r.matches(neighborhood)]

    if not matches:
        return []

    # If no matches have special rules, do a weighted choice immediately
    if not any(r.special_rules for r, _ in matches):
        weights = [r.chance for r, _ in matches]
        _, tile = random.choices(matches, weights=weights)[0]
        return [tile]

    # Check special rules
    possible = []
    for rule, tile in matches:
        if not rule.special_rules:
            possible.append(tile)
            continue
        for sr in rule.special_rules:
            if _check_special_rule(sr, grid, x, y, unverified, pass_unverified):
                possible.append(tile)
                break  # one passing rule is enough

    return list(set(possible))


def _wfc_solve(grid, rules):
    """Run the WFC constraint solver to assign tiles to all cells.

    Multi-pass: first pass assigns unambiguous tiles, subsequent
    passes propagate constraints, and a final collapse step handles
    remaining ambiguities with weighted random choice.
    """
    gw = int(grid.grid_size.x)
    gh = int(grid.grid_size.y)

    # First pass: identify cells with multiple options
    possibilities = {}
    for x in range(gw):
        for y in range(gh):
            matches = _find_possible_tiles(
                grid, x, y, rules, pass_unverified=True,
            )
            if len(matches) == 0:
                grid.at((x, y)).tilesprite = TILE_FALLBACK
            elif len(matches) == 1:
                grid.at((x, y)).tilesprite = matches[0]
            else:
                possibilities[(x, y)] = matches

    # Iterative constraint propagation
    max_iterations = 20
    for _ in range(max_iterations):
        if not possibilities:
            break
        old_count = len(possibilities)
        new_possibilities = {}

        for (x, y) in possibilities:
            matches = _find_possible_tiles(
                grid, x, y, rules,
                unverified=set(possibilities.keys()),
                pass_unverified=True,
            )
            if len(matches) == 0:
                grid.at((x, y)).tilesprite = TILE_FALLBACK
            elif len(matches) == 1:
                grid.at((x, y)).tilesprite = matches[0]
            else:
                grid.at((x, y)).tilesprite = -1
                new_possibilities[(x, y)] = matches

        possibilities = new_possibilities
        if len(possibilities) == old_count:
            # No progress - collapse remaining cells
            _collapse_remaining(grid, rules, possibilities)
            break


def _collapse_remaining(grid, rules, possibilities):
    """Force-collapse remaining undecided tiles."""
    while possibilities:
        # Find cells with fewest options
        min_options = min(len(v) for v in possibilities.values() if v)
        collapsed = False

        for (x, y) in list(possibilities.keys()):
            if len(possibilities[(x, y)]) != min_options:
                continue
            neighborhood = _read_neighborhood(grid, x, y)
            matches = [r for r in rules if r.matches(neighborhood)]
            verifiable = _find_possible_tiles(
                grid, x, y, rules,
                unverified=set(possibilities.keys()),
            )
            if verifiable:
                valid_matches = [
                    (r, r.tile_id) for r in matches if r.tile_id in verifiable
                ]
                if valid_matches:
                    weights = [r.chance for r, _ in valid_matches]
                    _, tile = random.choices(valid_matches, weights=weights)[0]
                    grid.at((x, y)).tilesprite = tile
                    del possibilities[(x, y)]
                    collapsed = True
                    break

        if not collapsed:
            # Quantum collapse: pick any remaining cell at random
            pos = random.choice(list(possibilities.keys()))
            x, y = pos
            neighborhood = _read_neighborhood(grid, x, y)
            matches = [(r, r.tile_id) for r in rules if r.matches(neighborhood)]
            if matches:
                weights = [r.chance for r, _ in matches]
                _, tile = random.choices(matches, weights=weights)[0]
                grid.at((x, y)).tilesprite = tile
            else:
                grid.at((x, y)).tilesprite = TILE_FALLBACK
            del possibilities[pos]


# =========================================================================
# Tile rule definitions - ported directly from simple_tiles.txt
#
# COLLABORATION NOTE: These rules were hand-authored during the 7DRL and
# have known issues (some wall configurations produce the fallback tile).
# They should be replaced with a Wang tile set designed in Tiled.
# =========================================================================

_TILE_RULES = []


def _define_rules():
    """Parse tile rules from inline definitions.

    These are identical to the original simple_tiles.txt content,
    just expressed as Python data instead of a text file read at
    import time.
    """
    # Format: (tile_id, chance, pattern_string, [special_rules])
    # Pattern: 9 chars, row-major. X=wall, _=ground, ?=don't care
    # Special rules: list of ("cardinal_char", tile_id) tuples
    #   Uppercase cardinal = always check. Lowercase = skip if unverified.
    defs = [
        # Open ground
        (145, 1.0,   "????_????", []),
        (184, 0.03,  "????_????", []),  # variant

        # Lone wall / pillar
        (146, 1.0,   "____X____", []),

        # Top-left corner
        (132, 1.0,   "?_?_XX?X?", []),

        # Horizontal walls
        (133, 1.0,   "???XXX?_?", []),
        (182, 0.04,  "???XXX?_?", []),  # variant
        (183, 0.04,  "???XXX?_?", []),  # variant
        (157, 0.01,  "???XXX?_?", []),  # variant

        # Top-right corner
        (135, 1.0,   "?_?XX_?X?", []),

        # Left side wall
        (144, 1.0, "?X??X_?X?",
         [("N", 132), ("s", 144), ("n", 144), ("n", 192),
          ("s", 192), ("S", 156), ("n", 171), ("s", 169), ("n", 180)]),

        # Right side wall
        (147, 1.0, "?X?_X??X?",
         [("N", 135), ("s", 147), ("n", 147), ("n", 193),
          ("s", 193), ("S", 159), ("n", 170), ("s", 168), ("n", 181)]),

        # Bottom-left corner
        (156, 1.0,   "?X?_XX?_?", []),

        # Bottom-right corner
        (159, 1.0,   "?X?XX_?_?", []),

        # Vertical T, left wall
        (192, 1.0, "?X??XX?X?",
         [("n", 144), ("s", 144), ("s", 169)]),

        # Vertical T, right wall
        (193, 1.0, "?X?XX??X?",
         [("n", 147), ("s", 147), ("s", 168)]),

        # Horizontal T, left wall
        (180, 1.0, "???XXX?X?",
         [("s", 144), ("s", 144), ("s", 169)]),

        # Horizontal T, right wall
        (181, 1.0, "???XXX?X?",
         [("s", 147), ("s", 147), ("s", 168)]),

        # Wall edge-of-gap (left variants)
        (195, 1.0, "??_XX_?__",
         [("W", 133), ("W", 182), ("W", 183), ("W", 157)]),
        (195, 1.0, "?__XX_?__", []),
        (195, 1.0, "?__XX_??_",
         [("W", 133), ("W", 182), ("W", 183), ("W", 157)]),
        (195, 1.0, "??_XX_?__",
         [("W", 133), ("W", 182), ("W", 183), ("W", 157)]),

        # Wall edge-of-gap (right variants)
        (194, 1.0, "_??_XX__?",
         [("E", 133), ("E", 182), ("E", 183), ("E", 157)]),
        (194, 1.0, "__?_XX__?", []),
        (194, 1.0, "__?_XX_??",
         [("E", 133), ("E", 182), ("E", 183), ("E", 157)]),
        (194, 1.0, "_??_XX__?",
         [("E", 133), ("E", 182), ("E", 183), ("E", 157)]),

        # Right vertical wall, gap below
        (168, 1.0, "?X?_X_?_?",
         [("n", 147), ("n", 170), ("n", 135), ("n", 181), ("n", 193)]),

        # Left vertical wall, gap below
        (169, 1.0, "?X?_X_?_?",
         [("n", 144), ("n", 171), ("n", 132), ("n", 192), ("n", 180)]),

        # Right vertical wall, gap above
        (170, 1.0, "?_?_X_?X?",
         [("s", 147), ("s", 168), ("s", 133), ("s", 182),
          ("s", 183), ("s", 157), ("s", 193), ("s", 181)]),

        # Left vertical wall, gap above
        (171, 1.0, "?_?_X_?X?",
         [("s", 144), ("s", 169), ("s", 133), ("s", 182),
          ("s", 183), ("s", 157), ("s", 171), ("s", 180)]),
    ]

    for tile_id, chance, pattern, special in defs:
        _TILE_RULES.append(
            TileRule.from_string(pattern, tile_id, chance, special)
        )


# Initialize rules on module load
_define_rules()


def paint_tiles(grid):
    """Apply WFC tile painting to the entire grid.

    This is the main entry point called by the level generator.
    """
    _wfc_solve(grid, _TILE_RULES)
