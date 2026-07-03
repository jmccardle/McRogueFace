"""UNWRITTEN - shared assets. Owner: Agent A.

The ONE Texture for the whole game and the speaker->portrait sprite map.
Constructed once here; import TEX everywhere else (never re-create the Texture).
Asset path is relative to the build/ working directory (see ARCHITECTURE section 0).
"""
import mcrfpy

TEX = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Speaker id -> sprite index (BIBLE sections 2/3/4). NARRATOR has no portrait.
PORTRAITS = {
    "PIP":        85,
    "BRAMBLE":    96,
    "MOTH":       84,
    "VERA":       111,
    "CANTOR":     109,
    "NYX":        121,
    "QUILL":      100,
    "GRISELDA":   88,
    "ODD":        87,
    "BELL":       110,
    "GATEKEEPER": 20,
    "CUSTODIAN":  41,
    "NARRATOR":   None,
}


def portrait_index(speaker):
    """Return the sprite index for a speaker id, or None for NARRATOR.

    Fail early: an unknown speaker id is a content/authoring error, not a
    thing to paper over with a placeholder sprite.
    """
    if speaker not in PORTRAITS:
        raise KeyError(
            "unknown speaker id %r - add it to core.assets.PORTRAITS" % (speaker,))
    return PORTRAITS[speaker]
