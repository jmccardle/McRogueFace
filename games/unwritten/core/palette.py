"""UNWRITTEN - palette and font constants. Owner: Agent A.

Colors from BIBLE section 6, defined EXACTLY. Each color is provided as both a
mcrfpy.Color constant (for constructor kwargs) and a raw (r,g,b) tuple with a
_T suffix (for lerping / passing to color math at call sites).
"""
import mcrfpy

# ----------------------------------------------------------------- raw tuples
INK_T     = (11, 12, 16)      # global background
PARCH_T   = (232, 220, 192)   # primary text
GOLD_T    = (212, 169, 78)    # accents, selection, the Book
DIM_T     = (138, 132, 118)   # secondary text, locked options
BLOOD_T   = (205, 66, 57)     # damage, HP low
TEAL_T    = (80, 190, 180)    # SP, magic
GRASS_T   = (96, 160, 92)     # heals, XP
PANEL_T   = (22, 24, 32)      # UI panel fill
OUTLINE_T = (52, 60, 80)      # panel outline (2px)
GREY_T    = (58, 58, 62)      # Act 3 grey-world wash target

# a slightly darker fill used behind portrait chips / insets
INSET_T   = (14, 15, 20)


def C(t, a=255):
    """Build a mcrfpy.Color from a 3-tuple (plus optional alpha)."""
    return mcrfpy.Color(t[0], t[1], t[2], a)


def to_color(c, a=None):
    """Coerce a Color OR (r,g,b[,a]) tuple/list into a fresh mcrfpy.Color.

    Some call sites (lerps, animations) hand us tuples; others hand Colors.
    Never blind-cast; always produce a new Color so shared constants are safe.
    """
    if isinstance(c, mcrfpy.Color):
        if a is None:
            return mcrfpy.Color(c.r, c.g, c.b, c.a)
        return mcrfpy.Color(c.r, c.g, c.b, a)
    r, g, b = c[0], c[1], c[2]
    if a is not None:
        alpha = a
    elif len(c) > 3:
        alpha = c[3]
    else:
        alpha = 255
    return mcrfpy.Color(int(r), int(g), int(b), int(alpha))


def lerp_t(a, b, t):
    """Linear interpolation between two raw (r,g,b) tuples -> (r,g,b) tuple."""
    t = max(0.0, min(1.0, t))
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


# ----------------------------------------------------------------- Color consts
INK     = C(INK_T)
PARCH   = C(PARCH_T)
GOLD    = C(GOLD_T)
DIM     = C(DIM_T)
BLOOD   = C(BLOOD_T)
TEAL    = C(TEAL_T)
GRASS   = C(GRASS_T)
PANEL   = C(PANEL_T)
OUTLINE = C(OUTLINE_T)
GREY    = C(GREY_T)
INSET   = C(INSET_T)

# ----------------------------------------------------------------- fonts/sizes
FONT = mcrfpy.default_font

TITLE_SIZE   = 72
BANNER_SIZE  = 44
NAME_SIZE    = 17
BODY_SIZE    = 16
CHOICE_SIZE  = 15
SMALL_SIZE   = 14
