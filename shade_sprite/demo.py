"""shade_sprite interactive demo.

Run from the build directory:
    ./mcrogueface --exec ../shade_sprite/demo.py

Or copy the shade_sprite directory into build/scripts/ and run:
    ./mcrogueface --exec scripts/shade_sprite/demo.py

Scenes:
  1 - Animation Viewer: cycle animations and directions
  2 - HSL Recolor: live hue/saturation/lightness shifting
  3 - Creature Gallery: grid of animated characters
  4 - Faction Generator: random faction color schemes

Controls shown on-screen per scene.
"""
import mcrfpy
import sys
import os
import random

# ---------------------------------------------------------------------------
# Asset discovery
# ---------------------------------------------------------------------------

# Search paths for Puny Character sprites
_SEARCH_PATHS = [
    "assets/Puny-Characters",
    "../assets/Puny-Characters",
    # 7DRL dev location
    os.path.expanduser(
        "~/Development/7DRL2026_Liber_Noster_jmccardle/"
        "assets_sources/Puny-Characters"
    ),
]

def _find_asset_dir():
    for p in _SEARCH_PATHS:
        if os.path.isdir(p):
            return p
    return None

ASSET_DIR = _find_asset_dir()

# Character sheets available in the free CC0 pack
_CHARACTER_FILES = [
    "Warrior-Red.png", "Warrior-Blue.png",
    "Soldier-Red.png", "Soldier-Blue.png", "Soldier-Yellow.png",
    "Archer-Green.png", "Archer-Purple.png",
    "Mage-Red.png", "Mage-Cyan.png",
    "Human-Soldier-Red.png", "Human-Soldier-Cyan.png",
    "Human-Worker-Red.png", "Human-Worker-Cyan.png",
    "Orc-Grunt.png", "Orc-Peon-Red.png", "Orc-Peon-Cyan.png",
    "Orc-Soldier-Red.png", "Orc-Soldier-Cyan.png",
    "Character-Base.png",
]

def _available_sheets():
    """Return list of full paths to available character sheets."""
    if not ASSET_DIR:
        return []
    sheets = []
    for f in _CHARACTER_FILES:
        p = os.path.join(ASSET_DIR, f)
        if os.path.isfile(p):
            sheets.append(p)
    return sheets

# Import shade_sprite (handle being run from different locations)
if __name__ == "__main__":
    # Add parent dir to path so shade_sprite can be imported
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from shade_sprite import (
    AnimatedSprite, Direction, PUNY_24, PUNY_29, SLIME,
    detect_format, CharacterAssembler,
)

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
_animated_sprites = []  # all AnimatedSprite instances to tick
_active_scene = None


def _tick_all(timer, runtime):
    """Global animation tick callback."""
    for a in _animated_sprites:
        a.tick(timer.interval)


# ---------------------------------------------------------------------------
# Scene 1: Animation Viewer
# ---------------------------------------------------------------------------
def _build_scene_viewer():
    scene = mcrfpy.Scene("viewer")
    ui = scene.children

    # Background
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                      fill_color=mcrfpy.Color(30, 30, 40))
    ui.append(bg)

    # Title
    title = mcrfpy.Caption(text="shade_sprite - Animation Viewer",
                           pos=(20, 10),
                           fill_color=mcrfpy.Color(220, 220, 255))
    ui.append(title)

    sheets = _available_sheets()
    if not sheets:
        msg = mcrfpy.Caption(
            text="No sprite assets found. Place Puny-Characters PNGs in assets/Puny-Characters/",
            pos=(20, 60),
            fill_color=mcrfpy.Color(255, 100, 100))
        ui.append(msg)
        return scene

    # State
    state = {
        "sheet_idx": 0,
        "anim_idx": 0,
        "dir_idx": 0,
    }

    # Determine format
    fmt = PUNY_24  # Free pack is 768x256

    anim_names = list(fmt.animations.keys())
    dir_names = [d.name for d in Direction]

    # Load first sheet
    tex = mcrfpy.Texture(sheets[0], fmt.tile_w, fmt.tile_h)

    # Main sprite display (scaled up 4x)
    sprite = mcrfpy.Sprite(texture=tex, pos=(200, 200), scale=6.0)
    ui.append(sprite)

    anim = AnimatedSprite(sprite, fmt, Direction.S)
    anim.play("idle")
    _animated_sprites.append(anim)

    # Info labels
    sheet_label = mcrfpy.Caption(
        text=f"Sheet: {os.path.basename(sheets[0])}",
        pos=(20, 50),
        fill_color=mcrfpy.Color(180, 180, 200))
    ui.append(sheet_label)

    anim_label = mcrfpy.Caption(
        text=f"Animation: idle",
        pos=(20, 80),
        fill_color=mcrfpy.Color(180, 180, 200))
    ui.append(anim_label)

    dir_label = mcrfpy.Caption(
        text=f"Direction: S",
        pos=(20, 110),
        fill_color=mcrfpy.Color(180, 180, 200))
    ui.append(dir_label)

    controls = mcrfpy.Caption(
        text="[Q/E] Sheet  [A/D] Animation  [W/S] Direction  [2] HSL  [3] Gallery  [4] Factions",
        pos=(20, 740),
        fill_color=mcrfpy.Color(120, 120, 140))
    ui.append(controls)

    # Also show all 8 directions as small sprites
    dir_sprites = []
    dir_anims = []
    for i, d in enumerate(Direction):
        dx = 500 + (i % 4) * 80
        dy = 200 + (i // 4) * 100
        s = mcrfpy.Sprite(texture=tex, pos=(dx, dy), scale=3.0)
        ui.append(s)
        a = AnimatedSprite(s, fmt, d)
        a.play("idle")
        _animated_sprites.append(a)
        dir_sprites.append(s)
        dir_anims.append(a)

        # Direction label
        lbl = mcrfpy.Caption(text=d.name, pos=(dx + 10, dy - 18),
                             fill_color=mcrfpy.Color(150, 150, 170))
        ui.append(lbl)

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return

        if key == mcrfpy.Key.Q:
            # Previous sheet
            state["sheet_idx"] = (state["sheet_idx"] - 1) % len(sheets)
            _reload_sheet()
        elif key == mcrfpy.Key.E:
            # Next sheet
            state["sheet_idx"] = (state["sheet_idx"] + 1) % len(sheets)
            _reload_sheet()
        elif key == mcrfpy.Key.A:
            # Previous animation
            state["anim_idx"] = (state["anim_idx"] - 1) % len(anim_names)
            _update_anim()
        elif key == mcrfpy.Key.D:
            # Next animation
            state["anim_idx"] = (state["anim_idx"] + 1) % len(anim_names)
            _update_anim()
        elif key == mcrfpy.Key.W:
            # Previous direction
            state["dir_idx"] = (state["dir_idx"] - 1) % 8
            _update_dir()
        elif key == mcrfpy.Key.S:
            # Next direction
            state["dir_idx"] = (state["dir_idx"] + 1) % 8
            _update_dir()
        elif key == mcrfpy.Key.Num2:
            mcrfpy.Scene("hsl").activate()
        elif key == mcrfpy.Key.Num3:
            mcrfpy.Scene("gallery").activate()
        elif key == mcrfpy.Key.Num4:
            mcrfpy.Scene("factions").activate()

    def _reload_sheet():
        path = sheets[state["sheet_idx"]]
        new_tex = mcrfpy.Texture(path, fmt.tile_w, fmt.tile_h)
        sprite.texture = new_tex
        for s in dir_sprites:
            s.texture = new_tex
        sheet_label.text = f"Sheet: {os.path.basename(path)}"
        _update_anim()

    def _update_anim():
        name = anim_names[state["anim_idx"]]
        anim.play(name)
        for a in dir_anims:
            a.play(name)
        anim_label.text = f"Animation: {name}"

    def _update_dir():
        d = Direction(state["dir_idx"])
        anim.direction = d
        dir_label.text = f"Direction: {d.name}"

    scene.on_key = on_key
    return scene


# ---------------------------------------------------------------------------
# Scene 2: HSL Recolor Demo
# ---------------------------------------------------------------------------
def _build_scene_hsl():
    scene = mcrfpy.Scene("hsl")
    ui = scene.children

    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                      fill_color=mcrfpy.Color(30, 30, 40))
    ui.append(bg)

    title = mcrfpy.Caption(text="shade_sprite - HSL Recoloring",
                           pos=(20, 10),
                           fill_color=mcrfpy.Color(220, 220, 255))
    ui.append(title)

    sheets = _available_sheets()
    if not sheets:
        msg = mcrfpy.Caption(
            text="No sprite assets found.",
            pos=(20, 60),
            fill_color=mcrfpy.Color(255, 100, 100))
        ui.append(msg)

        def on_key(key, action):
            if action == mcrfpy.InputState.PRESSED and key == mcrfpy.Key.Num1:
                mcrfpy.Scene("viewer").activate()
        scene.on_key = on_key
        return scene

    fmt = PUNY_24

    state = {
        "hue": 0.0,
        "sat": 0.0,
        "lit": 0.0,
        "sheet_idx": 0,
    }

    # Original sprite (left)
    orig_tex = mcrfpy.Texture(sheets[0], fmt.tile_w, fmt.tile_h)
    orig_sprite = mcrfpy.Sprite(texture=orig_tex, pos=(150, 250), scale=6.0)
    ui.append(orig_sprite)
    orig_anim = AnimatedSprite(orig_sprite, fmt, Direction.S)
    orig_anim.play("walk")
    _animated_sprites.append(orig_anim)

    orig_label = mcrfpy.Caption(text="Original", pos=(170, 220),
                                fill_color=mcrfpy.Color(180, 180, 200))
    ui.append(orig_label)

    # Shifted sprite (right)
    shifted_sprite = mcrfpy.Sprite(texture=orig_tex, pos=(550, 250), scale=6.0)
    ui.append(shifted_sprite)
    shifted_anim = AnimatedSprite(shifted_sprite, fmt, Direction.S)
    shifted_anim.play("walk")
    _animated_sprites.append(shifted_anim)

    shifted_label = mcrfpy.Caption(text="Shifted", pos=(570, 220),
                                   fill_color=mcrfpy.Color(180, 180, 200))
    ui.append(shifted_label)

    # HSL value displays
    hue_label = mcrfpy.Caption(text="Hue: 0.0", pos=(20, 500),
                               fill_color=mcrfpy.Color(255, 180, 180))
    ui.append(hue_label)
    sat_label = mcrfpy.Caption(text="Sat: 0.0", pos=(20, 530),
                               fill_color=mcrfpy.Color(180, 255, 180))
    ui.append(sat_label)
    lit_label = mcrfpy.Caption(text="Lit: 0.0", pos=(20, 560),
                               fill_color=mcrfpy.Color(180, 180, 255))
    ui.append(lit_label)

    controls = mcrfpy.Caption(
        text="[Left/Right] Hue +/-30  [Up/Down] Sat +/-0.1  [Z/X] Lit +/-0.1  [Q/E] Sheet  [1] Viewer",
        pos=(20, 740),
        fill_color=mcrfpy.Color(120, 120, 140))
    ui.append(controls)

    def _rebuild_shifted():
        path = sheets[state["sheet_idx"]]
        base = mcrfpy.Texture(path, fmt.tile_w, fmt.tile_h)
        shifted = base.hsl_shift(state["hue"], state["sat"], state["lit"])
        shifted_sprite.texture = shifted
        hue_label.text = f"Hue: {state['hue']:.0f}"
        sat_label.text = f"Sat: {state['sat']:.1f}"
        lit_label.text = f"Lit: {state['lit']:.1f}"

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return

        changed = False
        if key == mcrfpy.Key.LEFT:
            state["hue"] = (state["hue"] - 30.0) % 360.0
            changed = True
        elif key == mcrfpy.Key.RIGHT:
            state["hue"] = (state["hue"] + 30.0) % 360.0
            changed = True
        elif key == mcrfpy.Key.UP:
            state["sat"] = min(1.0, state["sat"] + 0.1)
            changed = True
        elif key == mcrfpy.Key.DOWN:
            state["sat"] = max(-1.0, state["sat"] - 0.1)
            changed = True
        elif key == mcrfpy.Key.Z:
            state["lit"] = max(-1.0, state["lit"] - 0.1)
            changed = True
        elif key == mcrfpy.Key.X:
            state["lit"] = min(1.0, state["lit"] + 0.1)
            changed = True
        elif key == mcrfpy.Key.Q:
            state["sheet_idx"] = (state["sheet_idx"] - 1) % len(sheets)
            _reload()
        elif key == mcrfpy.Key.E:
            state["sheet_idx"] = (state["sheet_idx"] + 1) % len(sheets)
            _reload()
        elif key == mcrfpy.Key.Num1:
            mcrfpy.Scene("viewer").activate()
            return
        elif key == mcrfpy.Key.Num3:
            mcrfpy.Scene("gallery").activate()
            return
        elif key == mcrfpy.Key.Num4:
            mcrfpy.Scene("factions").activate()
            return

        if changed:
            _rebuild_shifted()

    def _reload():
        path = sheets[state["sheet_idx"]]
        new_tex = mcrfpy.Texture(path, fmt.tile_w, fmt.tile_h)
        orig_sprite.texture = new_tex
        _rebuild_shifted()

    scene.on_key = on_key
    _rebuild_shifted()
    return scene


# ---------------------------------------------------------------------------
# Scene 3: Creature Gallery
# ---------------------------------------------------------------------------
def _build_scene_gallery():
    scene = mcrfpy.Scene("gallery")
    ui = scene.children

    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                      fill_color=mcrfpy.Color(30, 30, 40))
    ui.append(bg)

    title = mcrfpy.Caption(text="shade_sprite - Character Gallery",
                           pos=(20, 10),
                           fill_color=mcrfpy.Color(220, 220, 255))
    ui.append(title)

    sheets = _available_sheets()
    if not sheets:
        msg = mcrfpy.Caption(
            text="No sprite assets found.",
            pos=(20, 60),
            fill_color=mcrfpy.Color(255, 100, 100))
        ui.append(msg)

        def on_key(key, action):
            if action == mcrfpy.InputState.PRESSED and key == mcrfpy.Key.Num1:
                mcrfpy.Scene("viewer").activate()
        scene.on_key = on_key
        return scene

    fmt = PUNY_24
    directions = [Direction.S, Direction.SW, Direction.W, Direction.NW,
                  Direction.N, Direction.NE, Direction.E, Direction.SE]

    # Layout: grid of characters, 4 columns
    cols = 4
    x_start, y_start = 40, 60
    x_spacing, y_spacing = 240, 130
    scale = 3.0

    gallery_anims = []
    count = min(len(sheets), 16)  # max 4x4 grid

    for i in range(count):
        col = i % cols
        row = i // cols
        x = x_start + col * x_spacing
        y = y_start + row * y_spacing

        tex = mcrfpy.Texture(sheets[i], fmt.tile_w, fmt.tile_h)
        sprite = mcrfpy.Sprite(texture=tex, pos=(x + 20, y + 20),
                               scale=scale)
        ui.append(sprite)

        a = AnimatedSprite(sprite, fmt, Direction.S)
        a.play("walk")
        _animated_sprites.append(a)
        gallery_anims.append(a)

        name = os.path.basename(sheets[i]).replace(".png", "")
        lbl = mcrfpy.Caption(text=name, pos=(x, y),
                             fill_color=mcrfpy.Color(150, 150, 170))
        ui.append(lbl)

    state = {"dir_idx": 0, "anim_idx": 1}  # start with walk
    anim_names = list(fmt.animations.keys())

    controls = mcrfpy.Caption(
        text="[W/S] Direction  [A/D] Animation  [1] Viewer  [2] HSL  [4] Factions",
        pos=(20, 740),
        fill_color=mcrfpy.Color(120, 120, 140))
    ui.append(controls)

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if key == mcrfpy.Key.W:
            state["dir_idx"] = (state["dir_idx"] - 1) % 8
            d = Direction(state["dir_idx"])
            for a in gallery_anims:
                a.direction = d
        elif key == mcrfpy.Key.S:
            state["dir_idx"] = (state["dir_idx"] + 1) % 8
            d = Direction(state["dir_idx"])
            for a in gallery_anims:
                a.direction = d
        elif key == mcrfpy.Key.A:
            state["anim_idx"] = (state["anim_idx"] - 1) % len(anim_names)
            name = anim_names[state["anim_idx"]]
            for a in gallery_anims:
                a.play(name)
        elif key == mcrfpy.Key.D:
            state["anim_idx"] = (state["anim_idx"] + 1) % len(anim_names)
            name = anim_names[state["anim_idx"]]
            for a in gallery_anims:
                a.play(name)
        elif key == mcrfpy.Key.Num1:
            mcrfpy.Scene("viewer").activate()
        elif key == mcrfpy.Key.Num2:
            mcrfpy.Scene("hsl").activate()
        elif key == mcrfpy.Key.Num4:
            mcrfpy.Scene("factions").activate()

    scene.on_key = on_key
    return scene


# ---------------------------------------------------------------------------
# Scene 4: Faction Generator
# ---------------------------------------------------------------------------
def _build_scene_factions():
    scene = mcrfpy.Scene("factions")
    ui = scene.children

    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                      fill_color=mcrfpy.Color(30, 30, 40))
    ui.append(bg)

    title = mcrfpy.Caption(text="shade_sprite - Faction Generator",
                           pos=(20, 10),
                           fill_color=mcrfpy.Color(220, 220, 255))
    ui.append(title)

    sheets = _available_sheets()
    if not sheets:
        msg = mcrfpy.Caption(
            text="No sprite assets found.",
            pos=(20, 60),
            fill_color=mcrfpy.Color(255, 100, 100))
        ui.append(msg)

        def on_key(key, action):
            if action == mcrfpy.InputState.PRESSED and key == mcrfpy.Key.Num1:
                mcrfpy.Scene("viewer").activate()
        scene.on_key = on_key
        return scene

    fmt = PUNY_24
    scale = 3.0

    # State for generated factions
    faction_anims = []  # store references for animation ticking
    faction_sprites = []  # sprites to update on re-roll
    faction_labels = []

    # Faction colors (HSL hue values)
    faction_hues = [0, 60, 120, 180, 240, 300]
    faction_names_pool = [
        "Iron Guard", "Shadow Pact", "Dawn Order", "Ember Clan",
        "Frost Legion", "Vine Court", "Storm Band", "Ash Wardens",
        "Gold Company", "Crimson Oath", "Azure Fleet", "Jade Circle",
    ]

    def _generate_factions():
        # Clear old faction animations from global list
        for a in faction_anims:
            if a in _animated_sprites:
                _animated_sprites.remove(a)
        faction_anims.clear()

        # Pick 4 factions with random hues and characters
        hues = random.sample(faction_hues, min(4, len(faction_hues)))
        names = random.sample(faction_names_pool, 4)

        # We'll create sprites dynamically
        # Clear old sprites (rebuild scene content below bg/title/controls)
        while len(ui) > 3:  # keep bg, title, controls
            # Can't easily remove from UICollection, so we rebuild the scene
            pass
        # Actually, just position everything and update textures
        return hues, names

    def _build_faction_display():
        for a in faction_anims:
            if a in _animated_sprites:
                _animated_sprites.remove(a)
        faction_anims.clear()
        faction_sprites.clear()
        faction_labels.clear()

        hues = [random.uniform(0, 360) for _ in range(4)]
        names = random.sample(faction_names_pool, 4)

        y_start = 80
        for fi in range(4):
            y = y_start + fi * 160
            hue = hues[fi]

            # Faction name
            lbl = mcrfpy.Caption(
                text=f"{names[fi]} (hue {hue:.0f})",
                pos=(20, y),
                fill_color=mcrfpy.Color(200, 200, 220))
            ui.append(lbl)
            faction_labels.append(lbl)

            # Pick 4 random character sheets for this faction
            chosen = random.sample(sheets, min(4, len(sheets)))
            for ci, path in enumerate(chosen):
                x = 40 + ci * 200

                # Apply faction hue shift
                base_tex = mcrfpy.Texture(path, fmt.tile_w, fmt.tile_h)
                shifted_tex = base_tex.hsl_shift(hue)

                s = mcrfpy.Sprite(texture=shifted_tex, pos=(x, y + 30),
                                  scale=scale)
                ui.append(s)
                faction_sprites.append(s)

                a = AnimatedSprite(s, fmt, Direction.S)
                a.play("walk")
                _animated_sprites.append(a)
                faction_anims.append(a)

    controls = mcrfpy.Caption(
        text="[Space] Re-roll factions  [1] Viewer  [2] HSL  [3] Gallery",
        pos=(20, 740),
        fill_color=mcrfpy.Color(120, 120, 140))
    ui.append(controls)

    _build_faction_display()

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if key == mcrfpy.Key.SPACE:
            # Rebuild scene
            _rebuild_factions_scene()
        elif key == mcrfpy.Key.Num1:
            mcrfpy.Scene("viewer").activate()
        elif key == mcrfpy.Key.Num2:
            mcrfpy.Scene("hsl").activate()
        elif key == mcrfpy.Key.Num3:
            mcrfpy.Scene("gallery").activate()

    def _rebuild_factions_scene():
        # Easiest: rebuild the whole scene
        new_scene = _build_scene_factions()
        new_scene.activate()

    scene.on_key = on_key
    return scene


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not ASSET_DIR:
        print("WARNING: No Puny-Characters asset directory found.")
        print("Searched:", _SEARCH_PATHS)
        print("The demo will show placeholder messages.")
        print()

    # Build all scenes
    _build_scene_viewer()
    _build_scene_hsl()
    _build_scene_gallery()
    _build_scene_factions()

    # Start animation timer (20fps animation updates)
    mcrfpy.Timer("shade_anim", _tick_all, 50)

    # Activate first scene
    mcrfpy.Scene("viewer").activate()


if __name__ == "__main__":
    main()
    sys.exit(0)
