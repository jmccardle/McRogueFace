"""Sheet layout definitions for Merchant Shade sprite packs.

Data-driven animation format descriptions. Each SheetFormat defines the
tile dimensions, direction layout, and animation frame sequences for a
specific sprite sheet layout.
"""
from dataclasses import dataclass, field
from enum import IntEnum


class Direction(IntEnum):
    """8-directional facing. Row index matches Puny Character sheet layout."""
    S = 0
    SW = 1
    W = 2
    NW = 3
    N = 4
    NE = 5
    E = 6
    SE = 7


@dataclass
class AnimFrame:
    """A single frame in an animation sequence."""
    col: int        # Column index in the sheet
    duration: int   # Duration in milliseconds


@dataclass
class AnimDef:
    """Definition of a single animation type."""
    name: str
    frames: list  # list of AnimFrame
    loop: bool = True
    chain_to: str = None  # animation to play after one-shot finishes


@dataclass
class SheetFormat:
    """Complete definition of a sprite sheet layout."""
    name: str
    tile_w: int             # Pixel width of each frame
    tile_h: int             # Pixel height of each frame
    columns: int            # Total columns in the sheet
    rows: int               # Total rows (directions)
    directions: int         # Number of directional rows (4 or 8)
    animations: dict = field(default_factory=dict)  # name -> AnimDef
    grid_cell: tuple = (16, 16)   # Target grid cell size
    render_offset: tuple = (0, 0) # Pixel offset for rendering on grid

    def direction_row(self, d):
        """Get row index for a direction, wrapping for 4-dir and 1-dir sheets."""
        if self.directions == 1:
            return 0
        if self.directions == 8:
            return int(d)
        # 4-dir: S=0, W=1, E=2, N=3
        mapping = {
            Direction.S: 0, Direction.SW: 0,
            Direction.W: 1, Direction.NW: 1,
            Direction.N: 3, Direction.NE: 3,
            Direction.E: 2, Direction.SE: 2,
        }
        return mapping.get(d, 0)

    def sprite_index(self, col, direction):
        """Get the flat sprite index for a column and direction."""
        row = self.direction_row(direction)
        return row * self.columns + col


def _make_anim(name, start_col, count, ms_per_frame, loop=True, chain_to="idle"):
    """Helper to create a simple sequential animation."""
    frames = [AnimFrame(col=start_col + i, duration=ms_per_frame)
              for i in range(count)]
    if loop:
        return AnimDef(name=name, frames=frames, loop=True)
    return AnimDef(name=name, frames=frames, loop=False, chain_to=chain_to)


# =============================================================================
# 29-column paid Puny Character format (928x256 @ 32x32)
# =============================================================================
_puny29_anims = {}

# idle: cols 0-1, 300ms each, loop
_puny29_anims["idle"] = AnimDef("idle", [
    AnimFrame(0, 300), AnimFrame(1, 300),
], loop=True)

# walk: cols 1-4, 200ms each, loop
_puny29_anims["walk"] = AnimDef("walk", [
    AnimFrame(1, 200), AnimFrame(2, 200), AnimFrame(3, 200), AnimFrame(4, 200),
], loop=True)

# slash: cols 5-8, 100ms each, one-shot
_puny29_anims["slash"] = _make_anim("slash", 5, 4, 100, loop=False)

# bow: cols 9-12, 100ms each, one-shot
_puny29_anims["bow"] = _make_anim("bow", 9, 4, 100, loop=False)

# thrust: cols 13-15 + repeat last, 100ms each, one-shot
_puny29_anims["thrust"] = AnimDef("thrust", [
    AnimFrame(13, 100), AnimFrame(14, 100), AnimFrame(15, 100), AnimFrame(15, 100),
], loop=False, chain_to="idle")

# spellcast: cols 16-18 + repeat last, 100ms each, one-shot
_puny29_anims["spellcast"] = AnimDef("spellcast", [
    AnimFrame(16, 100), AnimFrame(17, 100), AnimFrame(18, 100), AnimFrame(18, 100),
], loop=False, chain_to="idle")

# hurt: cols 19-21, 100ms each, one-shot
_puny29_anims["hurt"] = _make_anim("hurt", 19, 3, 100, loop=False)

# death: cols 22-24, 100ms + 800ms hold, one-shot (no chain)
_puny29_anims["death"] = AnimDef("death", [
    AnimFrame(22, 100), AnimFrame(23, 100), AnimFrame(24, 800),
], loop=False, chain_to=None)

# dodge: bounce pattern 25,26,25,27, 200ms each, one-shot
_puny29_anims["dodge"] = AnimDef("dodge", [
    AnimFrame(25, 200), AnimFrame(26, 200), AnimFrame(25, 200), AnimFrame(27, 200),
], loop=False, chain_to="idle")

# item_use: col 28, mixed timing, one-shot
_puny29_anims["item_use"] = AnimDef("item_use", [
    AnimFrame(28, 300),
], loop=False, chain_to="idle")

PUNY_29 = SheetFormat(
    name="puny_29",
    tile_w=32, tile_h=32,
    columns=29, rows=8,
    directions=8,
    animations=_puny29_anims,
    grid_cell=(16, 16),
    render_offset=(-8, -16),
)


# =============================================================================
# 24-column free Puny Character format (768x256 @ 32x32)
# =============================================================================
_puny24_anims = {}

# Same layout but without dodge, item_use, and death has fewer frames
_puny24_anims["idle"] = AnimDef("idle", [
    AnimFrame(0, 300), AnimFrame(1, 300),
], loop=True)

_puny24_anims["walk"] = AnimDef("walk", [
    AnimFrame(1, 200), AnimFrame(2, 200), AnimFrame(3, 200), AnimFrame(4, 200),
], loop=True)

_puny24_anims["slash"] = _make_anim("slash", 5, 4, 100, loop=False)
_puny24_anims["bow"] = _make_anim("bow", 9, 4, 100, loop=False)

_puny24_anims["thrust"] = AnimDef("thrust", [
    AnimFrame(13, 100), AnimFrame(14, 100), AnimFrame(15, 100), AnimFrame(15, 100),
], loop=False, chain_to="idle")

_puny24_anims["spellcast"] = AnimDef("spellcast", [
    AnimFrame(16, 100), AnimFrame(17, 100), AnimFrame(18, 100), AnimFrame(18, 100),
], loop=False, chain_to="idle")

_puny24_anims["hurt"] = _make_anim("hurt", 19, 3, 100, loop=False)

_puny24_anims["death"] = AnimDef("death", [
    AnimFrame(22, 100), AnimFrame(23, 100),
], loop=False, chain_to=None)

PUNY_24 = SheetFormat(
    name="puny_24",
    tile_w=32, tile_h=32,
    columns=24, rows=8,
    directions=8,
    animations=_puny24_anims,
    grid_cell=(16, 16),
    render_offset=(-8, -16),
)


# =============================================================================
# RPG Maker creature format (288x192, 3x4 per character, 4 chars per sheet)
# =============================================================================
_creature_rpg_anims = {}

# Walk: 3 columns (left-step, stand, right-step), 200ms each, loop
_creature_rpg_anims["idle"] = AnimDef("idle", [
    AnimFrame(1, 400),
], loop=True)

_creature_rpg_anims["walk"] = AnimDef("walk", [
    AnimFrame(0, 200), AnimFrame(1, 200), AnimFrame(2, 200), AnimFrame(1, 200),
], loop=True)

CREATURE_RPGMAKER = SheetFormat(
    name="creature_rpgmaker",
    tile_w=24, tile_h=24,
    columns=3, rows=4,
    directions=4,
    animations=_creature_rpg_anims,
    grid_cell=(16, 16),
    render_offset=(-4, -8),
)


# =============================================================================
# Slime format (480x32, 15x1, non-directional)
# =============================================================================
_slime_anims = {}

_slime_anims["idle"] = AnimDef("idle", [
    AnimFrame(0, 300), AnimFrame(1, 300),
], loop=True)

_slime_anims["walk"] = AnimDef("walk", [
    AnimFrame(0, 200), AnimFrame(1, 200), AnimFrame(2, 200), AnimFrame(3, 200),
], loop=True)

SLIME = SheetFormat(
    name="slime",
    tile_w=32, tile_h=32,
    columns=15, rows=1,
    directions=1,
    animations=_slime_anims,
    grid_cell=(16, 16),
    render_offset=(-8, -16),
)


# =============================================================================
# Format auto-detection
# =============================================================================
_FORMAT_TABLE = {
    (928, 256): PUNY_29,
    (768, 256): PUNY_24,
    (480, 32): SLIME,
    # RPG Maker sheets: 288x192 is 4 characters, each 72x192 / 3x4
    # Individual characters extracted: 72x96 (3 cols x 4 rows of 24x24)
    (72, 96): CREATURE_RPGMAKER,
    (288, 192): CREATURE_RPGMAKER,  # Full sheet (need sub-region extraction)
}


def detect_format(width, height):
    """Auto-detect sheet format from pixel dimensions.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        SheetFormat or None if no match found
    """
    return _FORMAT_TABLE.get((width, height))


# All predefined formats for iteration
ALL_FORMATS = [PUNY_29, PUNY_24, CREATURE_RPGMAKER, SLIME]
