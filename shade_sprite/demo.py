"""shade_sprite interactive demo.

Run from the build directory:
    ./mcrogueface ../shade_sprite/demo.py

Scenes:
  1 - Animation Viewer: cycle through all animations and 8 facing directions
  2 - HSL Recolor: live hue/saturation/lightness shifting side-by-side
  3 - Character Gallery: 4x4 grid of all available character sheets
  4 - Faction Generator: random faction color schemes applied to squads
  5 - Layer Compositing: demonstrates CharacterAssembler layered texture building
  6 - Equipment Customizer: procedural + user-driven layer coloring for gear
  7 - Asset Inventory: browse discovered layer categories and files
  8 - Entity Animation: engine-native Entity.animate() with loop - all formats

Controls shown on-screen per scene.
"""
import mcrfpy
import sys
import os
import random

# ---------------------------------------------------------------------------
# Asset discovery
# ---------------------------------------------------------------------------
_SEARCH_PATHS = [
    "assets/Puny-Characters",
    "../assets/Puny-Characters",
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


def _slime_path():
    """Return path to Slime.png if available."""
    if not ASSET_DIR:
        return None
    p = os.path.join(ASSET_DIR, "Slime.png")
    return p if os.path.isfile(p) else None


def _base_path():
    """Return path to Character-Base.png if available."""
    if not ASSET_DIR:
        return None
    p = os.path.join(ASSET_DIR, "Character-Base.png")
    return p if os.path.isfile(p) else None


# Import shade_sprite
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from shade_sprite import (
    AnimatedSprite, Direction, PUNY_24, PUNY_29, SLIME, CREATURE_RPGMAKER,
    CharacterAssembler,
    AssetLibrary, FactionGenerator,
)

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
BG = mcrfpy.Color(30, 30, 40)
TITLE_COLOR = mcrfpy.Color(220, 220, 255)
LABEL_COLOR = mcrfpy.Color(180, 180, 200)
DIM_COLOR = mcrfpy.Color(120, 120, 140)
WARN_COLOR = mcrfpy.Color(255, 100, 100)
ACCENT_COLOR = mcrfpy.Color(100, 200, 255)
HIGHLIGHT_COLOR = mcrfpy.Color(255, 220, 100)

# ---------------------------------------------------------------------------
# Global animation state
# ---------------------------------------------------------------------------
_animated_sprites = []


def _tick_all(timer, runtime):
    for a in _animated_sprites:
        a.tick(timer.interval)


def _no_assets_fallback(scene, scene_name):
    """Add 'no assets' message and basic navigation to a scene."""
    ui = scene.children
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=BG)
    ui.append(bg)
    title = mcrfpy.Caption(text=f"shade_sprite - {scene_name}",
                           pos=(20, 10), fill_color=TITLE_COLOR)
    ui.append(title)
    msg = mcrfpy.Caption(
        text="No sprite assets found. Place Puny-Characters PNGs in assets/Puny-Characters/",
        pos=(20, 60), fill_color=WARN_COLOR)
    ui.append(msg)
    controls = mcrfpy.Caption(
        text="[1-8] Switch scenes",
        pos=(20, 740), fill_color=DIM_COLOR)
    ui.append(controls)

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        _handle_scene_switch(key)
    scene.on_key = on_key
    return scene


def _handle_scene_switch(key):
    """Common scene switching for number keys."""
    scene_map = {
        mcrfpy.Key.NUM_1: "viewer",
        mcrfpy.Key.NUM_2: "hsl",
        mcrfpy.Key.NUM_3: "gallery",
        mcrfpy.Key.NUM_4: "factions",
        mcrfpy.Key.NUM_5: "layers",
        mcrfpy.Key.NUM_6: "equip",
        mcrfpy.Key.NUM_7: "inventory",
        mcrfpy.Key.NUM_8: "entity_anim",
    }
    name = scene_map.get(key)
    if name:
        mcrfpy.Scene(name).activate()
        return True
    return False


# ---------------------------------------------------------------------------
# Scene 1: Animation Viewer
# ---------------------------------------------------------------------------
def _build_scene_viewer():
    scene = mcrfpy.Scene("viewer")
    sheets = _available_sheets()
    if not sheets:
        return _no_assets_fallback(scene, "Animation Viewer")

    ui = scene.children
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=BG)
    ui.append(bg)

    title = mcrfpy.Caption(text="[1] Animation Viewer",
                           pos=(20, 10), fill_color=TITLE_COLOR)
    ui.append(title)

    fmt = PUNY_24
    anim_names = list(fmt.animations.keys())
    state = {"sheet_idx": 0, "anim_idx": 0, "dir_idx": 0}

    # Load first sheet
    tex = mcrfpy.Texture(sheets[0], fmt.tile_w, fmt.tile_h)

    # Main sprite (large)
    sprite = mcrfpy.Sprite(texture=tex, pos=(80, 180), scale=6.0)
    ui.append(sprite)
    anim = AnimatedSprite(sprite, fmt, Direction.S)
    anim.play("idle")
    _animated_sprites.append(anim)

    # Info labels
    sheet_label = mcrfpy.Caption(
        text=f"Sheet: {os.path.basename(sheets[0])}",
        pos=(20, 50), fill_color=LABEL_COLOR)
    ui.append(sheet_label)
    anim_label = mcrfpy.Caption(
        text="Animation: idle", pos=(20, 80), fill_color=LABEL_COLOR)
    ui.append(anim_label)
    dir_label = mcrfpy.Caption(
        text="Direction: S (0)", pos=(20, 110), fill_color=LABEL_COLOR)
    ui.append(dir_label)
    frame_info = mcrfpy.Caption(
        text="", pos=(20, 140), fill_color=ACCENT_COLOR)
    ui.append(frame_info)

    # 8 directional previews in a compass layout
    compass_cx, compass_cy = 620, 350
    compass_offsets = {
        Direction.N:  (0, -120),
        Direction.NE: (100, -85),
        Direction.E:  (140, 0),
        Direction.SE: (100, 85),
        Direction.S:  (0, 120),
        Direction.SW: (-100, 85),
        Direction.W:  (-140, 0),
        Direction.NW: (-100, -85),
    }

    dir_sprites = []
    dir_anims = []
    dir_labels = []
    for d in Direction:
        ox, oy = compass_offsets[d]
        x = compass_cx + ox - 16  # center 32px * 2 scale
        y = compass_cy + oy - 16
        s = mcrfpy.Sprite(texture=tex, pos=(x, y), scale=2.0)
        ui.append(s)
        a = AnimatedSprite(s, fmt, d)
        a.play("idle")
        _animated_sprites.append(a)
        dir_sprites.append(s)
        dir_anims.append(a)

        lbl = mcrfpy.Caption(text=d.name, pos=(x + 5, y - 18),
                             fill_color=DIM_COLOR)
        ui.append(lbl)
        dir_labels.append(lbl)

    # Compass center label
    compass_title = mcrfpy.Caption(text="8-Dir Compass",
                                   pos=(compass_cx - 50, compass_cy - 10),
                                   fill_color=DIM_COLOR)
    ui.append(compass_title)

    # Slime demo (different format)
    slime_path = _slime_path()
    slime_anim = None
    if slime_path:
        slime_lbl = mcrfpy.Caption(text="Slime (1-dir, SLIME format):",
                                   pos=(80, 520), fill_color=LABEL_COLOR)
        ui.append(slime_lbl)
        slime_tex = mcrfpy.Texture(slime_path, SLIME.tile_w, SLIME.tile_h)
        slime_spr = mcrfpy.Sprite(texture=slime_tex, pos=(80, 550), scale=4.0)
        ui.append(slime_spr)
        slime_anim = AnimatedSprite(slime_spr, SLIME, Direction.S)
        slime_anim.play("walk")
        _animated_sprites.append(slime_anim)

    # Animation list reference
    anim_ref_y = 520 if not slime_path else 640
    anim_ref = mcrfpy.Caption(
        text="Animations: " + ", ".join(anim_names),
        pos=(20, anim_ref_y), fill_color=DIM_COLOR)
    ui.append(anim_ref)

    controls = mcrfpy.Caption(
        text="[Q/E] Sheet  [A/D] Animation  [W/S] Direction  [1-8] Scenes",
        pos=(20, 740), fill_color=DIM_COLOR)
    ui.append(controls)

    def _update_frame_info():
        a = fmt.animations[anim_names[state["anim_idx"]]]
        nf = len(a.frames)
        loop_str = "loop" if a.loop else "one-shot"
        chain_str = f" -> {a.chain_to}" if a.chain_to else ""
        frame_info.text = f"Frames: {nf}  ({loop_str}{chain_str})"

    _update_frame_info()

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
        _update_frame_info()

    def _update_dir():
        d = Direction(state["dir_idx"])
        anim.direction = d
        dir_label.text = f"Direction: {d.name} ({d.value})"

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if _handle_scene_switch(key):
            return
        if key == mcrfpy.Key.Q:
            state["sheet_idx"] = (state["sheet_idx"] - 1) % len(sheets)
            _reload_sheet()
        elif key == mcrfpy.Key.E:
            state["sheet_idx"] = (state["sheet_idx"] + 1) % len(sheets)
            _reload_sheet()
        elif key == mcrfpy.Key.A:
            state["anim_idx"] = (state["anim_idx"] - 1) % len(anim_names)
            _update_anim()
        elif key == mcrfpy.Key.D:
            state["anim_idx"] = (state["anim_idx"] + 1) % len(anim_names)
            _update_anim()
        elif key == mcrfpy.Key.W:
            state["dir_idx"] = (state["dir_idx"] - 1) % 8
            _update_dir()
        elif key == mcrfpy.Key.S:
            state["dir_idx"] = (state["dir_idx"] + 1) % 8
            _update_dir()

    scene.on_key = on_key
    return scene


# ---------------------------------------------------------------------------
# Scene 2: HSL Recolor Demo
# ---------------------------------------------------------------------------
def _build_scene_hsl():
    scene = mcrfpy.Scene("hsl")
    sheets = _available_sheets()
    if not sheets:
        return _no_assets_fallback(scene, "HSL Recoloring")

    ui = scene.children
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=BG)
    ui.append(bg)

    title = mcrfpy.Caption(text="[2] HSL Recoloring",
                           pos=(20, 10), fill_color=TITLE_COLOR)
    ui.append(title)

    fmt = PUNY_24
    state = {"hue": 0.0, "sat": 0.0, "lit": 0.0, "sheet_idx": 0}

    # Original (left)
    orig_tex = mcrfpy.Texture(sheets[0], fmt.tile_w, fmt.tile_h)
    orig_sprite = mcrfpy.Sprite(texture=orig_tex, pos=(120, 200), scale=6.0)
    ui.append(orig_sprite)
    orig_anim = AnimatedSprite(orig_sprite, fmt, Direction.S)
    orig_anim.play("walk")
    _animated_sprites.append(orig_anim)
    orig_label = mcrfpy.Caption(text="Original", pos=(145, 170),
                                fill_color=LABEL_COLOR)
    ui.append(orig_label)

    # Shifted (center)
    shifted_sprite = mcrfpy.Sprite(texture=orig_tex, pos=(420, 200), scale=6.0)
    ui.append(shifted_sprite)
    shifted_anim = AnimatedSprite(shifted_sprite, fmt, Direction.S)
    shifted_anim.play("walk")
    _animated_sprites.append(shifted_anim)
    shifted_label = mcrfpy.Caption(text="HSL Shifted", pos=(430, 170),
                                   fill_color=LABEL_COLOR)
    ui.append(shifted_label)

    # Hue wheel preview: show 6 hue rotations at once (right side)
    wheel_label = mcrfpy.Caption(text="Hue Wheel (60-degree steps):",
                                 pos=(700, 80), fill_color=LABEL_COLOR)
    ui.append(wheel_label)

    wheel_sprites = []
    wheel_anims = []
    for i in range(6):
        hue = i * 60.0
        y = 110 + i * 90
        shifted_tex = orig_tex.hsl_shift(hue)
        s = mcrfpy.Sprite(texture=shifted_tex, pos=(730, y), scale=2.5)
        ui.append(s)
        a = AnimatedSprite(s, fmt, Direction.S)
        a.play("walk")
        _animated_sprites.append(a)
        wheel_sprites.append(s)
        wheel_anims.append(a)
        lbl = mcrfpy.Caption(text=f"{hue:.0f} deg", pos=(810, y + 20),
                             fill_color=DIM_COLOR)
        ui.append(lbl)

    # HSL value displays
    hue_label = mcrfpy.Caption(text="Hue: 0", pos=(120, 440),
                               fill_color=mcrfpy.Color(255, 180, 180))
    ui.append(hue_label)
    sat_label = mcrfpy.Caption(text="Sat: 0.0", pos=(120, 470),
                               fill_color=mcrfpy.Color(180, 255, 180))
    ui.append(sat_label)
    lit_label = mcrfpy.Caption(text="Lit: 0.0", pos=(120, 500),
                               fill_color=mcrfpy.Color(180, 180, 255))
    ui.append(lit_label)

    # Explanation
    explain = mcrfpy.Caption(
        text="Hue rotates color wheel. Sat adjusts vibrancy. Lit adjusts brightness.",
        pos=(120, 540), fill_color=DIM_COLOR)
    ui.append(explain)
    explain2 = mcrfpy.Caption(
        text="tex.hsl_shift(hue, sat, lit) returns a NEW texture (original unchanged)",
        pos=(120, 565), fill_color=DIM_COLOR)
    ui.append(explain2)

    controls = mcrfpy.Caption(
        text="[Left/Right] Hue +/-30  [Up/Down] Sat +/-0.1  [Z/X] Lit +/-0.1  [Q/E] Sheet  [1-8] Scenes",
        pos=(20, 740), fill_color=DIM_COLOR)
    ui.append(controls)

    def _rebuild_shifted():
        path = sheets[state["sheet_idx"]]
        base = mcrfpy.Texture(path, fmt.tile_w, fmt.tile_h)
        shifted = base.hsl_shift(state["hue"], state["sat"], state["lit"])
        shifted_sprite.texture = shifted
        hue_label.text = f"Hue: {state['hue']:.0f}"
        sat_label.text = f"Sat: {state['sat']:.1f}"
        lit_label.text = f"Lit: {state['lit']:.1f}"

    def _reload():
        path = sheets[state["sheet_idx"]]
        new_tex = mcrfpy.Texture(path, fmt.tile_w, fmt.tile_h)
        orig_sprite.texture = new_tex
        # Update hue wheel with new base
        for i, s in enumerate(wheel_sprites):
            hue = i * 60.0
            s.texture = new_tex.hsl_shift(hue)
        _rebuild_shifted()

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if _handle_scene_switch(key):
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
        if changed:
            _rebuild_shifted()

    scene.on_key = on_key
    return scene


# ---------------------------------------------------------------------------
# Scene 3: Creature Gallery
# ---------------------------------------------------------------------------
def _build_scene_gallery():
    scene = mcrfpy.Scene("gallery")
    sheets = _available_sheets()
    if not sheets:
        return _no_assets_fallback(scene, "Character Gallery")

    ui = scene.children
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=BG)
    ui.append(bg)

    title = mcrfpy.Caption(text="[3] Character Gallery",
                           pos=(20, 10), fill_color=TITLE_COLOR)
    ui.append(title)

    fmt = PUNY_24
    anim_names = list(fmt.animations.keys())
    state = {"dir_idx": 0, "anim_idx": 1}  # start with walk

    # 5-column grid
    cols = 5
    x_start, y_start = 30, 60
    x_spacing, y_spacing = 195, 130
    scale = 2.5

    gallery_anims = []
    count = min(len(sheets), 20)

    for i in range(count):
        col = i % cols
        row = i // cols
        x = x_start + col * x_spacing
        y = y_start + row * y_spacing

        tex = mcrfpy.Texture(sheets[i], fmt.tile_w, fmt.tile_h)
        sprite = mcrfpy.Sprite(texture=tex, pos=(x + 30, y + 25), scale=scale)
        ui.append(sprite)

        a = AnimatedSprite(sprite, fmt, Direction.S)
        a.play("walk")
        _animated_sprites.append(a)
        gallery_anims.append(a)

        name = os.path.basename(sheets[i]).replace(".png", "")
        lbl = mcrfpy.Caption(text=name, pos=(x, y + 5),
                             fill_color=DIM_COLOR)
        ui.append(lbl)

    # Slime in gallery too
    slime_p = _slime_path()
    slime_anim_ref = None
    if slime_p:
        row = count // cols
        col = count % cols
        x = x_start + col * x_spacing
        y = y_start + row * y_spacing
        stex = mcrfpy.Texture(slime_p, SLIME.tile_w, SLIME.tile_h)
        sspr = mcrfpy.Sprite(texture=stex, pos=(x + 30, y + 25), scale=scale)
        ui.append(sspr)
        slime_anim_ref = AnimatedSprite(sspr, SLIME, Direction.S)
        slime_anim_ref.play("walk")
        _animated_sprites.append(slime_anim_ref)
        lbl = mcrfpy.Caption(text="Slime", pos=(x, y + 5), fill_color=DIM_COLOR)
        ui.append(lbl)

    dir_info = mcrfpy.Caption(text="Direction: S  Animation: walk",
                              pos=(20, 700), fill_color=LABEL_COLOR)
    ui.append(dir_info)

    controls = mcrfpy.Caption(
        text="[W/S] Direction  [A/D] Animation  [1-8] Scenes",
        pos=(20, 740), fill_color=DIM_COLOR)
    ui.append(controls)

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if _handle_scene_switch(key):
            return
        if key == mcrfpy.Key.W:
            state["dir_idx"] = (state["dir_idx"] - 1) % 8
            d = Direction(state["dir_idx"])
            for a in gallery_anims:
                a.direction = d
            dir_info.text = f"Direction: {d.name}  Animation: {anim_names[state['anim_idx']]}"
        elif key == mcrfpy.Key.S:
            state["dir_idx"] = (state["dir_idx"] + 1) % 8
            d = Direction(state["dir_idx"])
            for a in gallery_anims:
                a.direction = d
            dir_info.text = f"Direction: {d.name}  Animation: {anim_names[state['anim_idx']]}"
        elif key == mcrfpy.Key.A:
            state["anim_idx"] = (state["anim_idx"] - 1) % len(anim_names)
            name = anim_names[state["anim_idx"]]
            for a in gallery_anims:
                a.play(name)
            dir_info.text = f"Direction: {Direction(state['dir_idx']).name}  Animation: {name}"
        elif key == mcrfpy.Key.D:
            state["anim_idx"] = (state["anim_idx"] + 1) % len(anim_names)
            name = anim_names[state["anim_idx"]]
            for a in gallery_anims:
                a.play(name)
            dir_info.text = f"Direction: {Direction(state['dir_idx']).name}  Animation: {name}"

    scene.on_key = on_key
    return scene


# ---------------------------------------------------------------------------
# Scene 4: Faction Generator
# ---------------------------------------------------------------------------
_FACTION_NAMES = [
    "Iron Guard", "Shadow Pact", "Dawn Order", "Ember Clan",
    "Frost Legion", "Vine Court", "Storm Band", "Ash Wardens",
    "Gold Company", "Crimson Oath", "Azure Fleet", "Jade Circle",
    "Silver Hand", "Night Watch", "Sun Speakers", "Bone Reavers",
]


def _build_scene_factions():
    scene = mcrfpy.Scene("factions")
    sheets = _available_sheets()
    if not sheets:
        return _no_assets_fallback(scene, "Faction Generator")

    ui = scene.children
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=BG)
    ui.append(bg)

    title = mcrfpy.Caption(text="[4] Faction Generator",
                           pos=(20, 10), fill_color=TITLE_COLOR)
    ui.append(title)

    fmt = PUNY_24
    scale = 3.0
    faction_anims = []

    def _populate():
        """Generate 4 random factions with hue-shifted squads."""
        # Remove old faction anims from global list
        for a in faction_anims:
            if a in _animated_sprites:
                _animated_sprites.remove(a)
        faction_anims.clear()

        hues = [random.uniform(0, 360) for _ in range(4)]
        names = random.sample(_FACTION_NAMES, 4)

        y_start = 70
        for fi in range(4):
            y = y_start + fi * 165
            hue = hues[fi]

            # Faction header with colored indicator
            lbl = mcrfpy.Caption(
                text=f"{names[fi]}  (hue {hue:.0f})",
                pos=(20, y), fill_color=HIGHLIGHT_COLOR)
            ui.append(lbl)

            # Pick 5 random characters for this faction
            chosen = random.sample(sheets, min(5, len(sheets)))
            for ci, path in enumerate(chosen):
                x = 30 + ci * 180
                base_tex = mcrfpy.Texture(path, fmt.tile_w, fmt.tile_h)
                shifted_tex = base_tex.hsl_shift(hue)
                s = mcrfpy.Sprite(texture=shifted_tex, pos=(x, y + 30),
                                  scale=scale)
                ui.append(s)
                a = AnimatedSprite(s, fmt, Direction.S)
                a.play("walk")
                _animated_sprites.append(a)
                faction_anims.append(a)

                # Character name below
                cname = os.path.basename(path).replace(".png", "")
                nlbl = mcrfpy.Caption(text=cname, pos=(x, y + 130),
                                      fill_color=DIM_COLOR)
                ui.append(nlbl)

    _populate()

    controls = mcrfpy.Caption(
        text="[Space] Re-roll factions  [1-8] Scenes",
        pos=(20, 740), fill_color=DIM_COLOR)
    ui.append(controls)

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if _handle_scene_switch(key):
            return
        if key == mcrfpy.Key.SPACE:
            # Rebuild scene from scratch
            new_scene = _build_scene_factions()
            new_scene.activate()

    scene.on_key = on_key
    return scene


# ---------------------------------------------------------------------------
# Scene 5: Layer Compositing
# ---------------------------------------------------------------------------
def _build_scene_layers():
    scene = mcrfpy.Scene("layers")
    sheets = _available_sheets()
    base_p = _base_path()
    if not sheets or not base_p:
        return _no_assets_fallback(scene, "Layer Compositing")

    ui = scene.children
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=BG)
    ui.append(bg)

    title = mcrfpy.Caption(text="[5] Layer Compositing (CharacterAssembler)",
                           pos=(20, 10), fill_color=TITLE_COLOR)
    ui.append(title)

    fmt = PUNY_24
    scale = 5.0

    # Explanation
    explain = mcrfpy.Caption(
        text="CharacterAssembler composites multiple texture layers with HSL shifts.",
        pos=(20, 45), fill_color=LABEL_COLOR)
    ui.append(explain)
    explain2 = mcrfpy.Caption(
        text="Base layer (skin) + overlay (equipment) with color variation = unique characters.",
        pos=(20, 70), fill_color=LABEL_COLOR)
    ui.append(explain2)

    # Find sheets that aren't Character-Base for overlay
    overlay_sheets = [s for s in sheets
                      if "Character-Base" not in os.path.basename(s)]

    # --- Column 1: Show the base layer alone ---
    col1_x = 30
    base_lbl = mcrfpy.Caption(text="Base Layer", pos=(col1_x, 110),
                              fill_color=ACCENT_COLOR)
    ui.append(base_lbl)

    base_tex = mcrfpy.Texture(base_p, fmt.tile_w, fmt.tile_h)
    base_spr = mcrfpy.Sprite(texture=base_tex, pos=(col1_x + 10, 140), scale=scale)
    ui.append(base_spr)
    base_anim = AnimatedSprite(base_spr, fmt, Direction.S)
    base_anim.play("walk")
    _animated_sprites.append(base_anim)
    base_note = mcrfpy.Caption(text="Character-Base.png", pos=(col1_x, 310),
                               fill_color=DIM_COLOR)
    ui.append(base_note)

    # --- Column 2: Show an overlay alone ---
    col2_x = 250
    overlay_lbl = mcrfpy.Caption(text="Overlay Layer", pos=(col2_x, 110),
                                 fill_color=ACCENT_COLOR)
    ui.append(overlay_lbl)

    state = {"overlay_idx": 0, "hue": 0.0}
    overlay_tex = mcrfpy.Texture(overlay_sheets[0], fmt.tile_w, fmt.tile_h)
    overlay_spr = mcrfpy.Sprite(texture=overlay_tex, pos=(col2_x + 10, 140),
                                scale=scale)
    ui.append(overlay_spr)
    overlay_anim = AnimatedSprite(overlay_spr, fmt, Direction.S)
    overlay_anim.play("walk")
    _animated_sprites.append(overlay_anim)
    overlay_name_lbl = mcrfpy.Caption(
        text=os.path.basename(overlay_sheets[0]),
        pos=(col2_x, 310), fill_color=DIM_COLOR)
    ui.append(overlay_name_lbl)

    # --- Column 3: Composite result ---
    col3_x = 470
    comp_lbl = mcrfpy.Caption(text="Composite Result", pos=(col3_x, 110),
                              fill_color=ACCENT_COLOR)
    ui.append(comp_lbl)

    # Build initial composite
    assembler = CharacterAssembler(fmt)
    assembler.add_layer(base_p)
    assembler.add_layer(overlay_sheets[0])
    comp_tex = assembler.build("demo_composite")

    comp_spr = mcrfpy.Sprite(texture=comp_tex, pos=(col3_x + 10, 140),
                             scale=scale)
    ui.append(comp_spr)
    comp_anim = AnimatedSprite(comp_spr, fmt, Direction.S)
    comp_anim.play("walk")
    _animated_sprites.append(comp_anim)

    comp_note = mcrfpy.Caption(text="Base + Overlay composited",
                               pos=(col3_x, 310), fill_color=DIM_COLOR)
    ui.append(comp_note)

    # --- Column 4: Composite with hue shift ---
    col4_x = 690
    shifted_lbl = mcrfpy.Caption(text="Shifted Composite", pos=(col4_x, 110),
                                 fill_color=ACCENT_COLOR)
    ui.append(shifted_lbl)

    assembler2 = CharacterAssembler(fmt)
    assembler2.add_layer(base_p)
    assembler2.add_layer(overlay_sheets[0], hue_shift=120.0)
    shifted_comp_tex = assembler2.build("demo_shifted")

    shifted_comp_spr = mcrfpy.Sprite(texture=shifted_comp_tex,
                                     pos=(col4_x + 10, 140), scale=scale)
    ui.append(shifted_comp_spr)
    shifted_comp_anim = AnimatedSprite(shifted_comp_spr, fmt, Direction.S)
    shifted_comp_anim.play("walk")
    _animated_sprites.append(shifted_comp_anim)

    hue_note = mcrfpy.Caption(text=f"Overlay hue: {state['hue']:.0f}",
                              pos=(col4_x, 310), fill_color=DIM_COLOR)
    ui.append(hue_note)

    # --- Row 2: Show multiple hue-shifted composites ---
    row2_y = 370
    row2_lbl = mcrfpy.Caption(
        text="Same base + overlay, 6 hue rotations (60-degree increments):",
        pos=(30, row2_y), fill_color=LABEL_COLOR)
    ui.append(row2_lbl)

    row2_anims = []
    for i in range(6):
        hue = i * 60.0
        x = 30 + i * 160
        y = row2_y + 30

        asm = CharacterAssembler(fmt)
        asm.add_layer(base_p)
        asm.add_layer(overlay_sheets[0], hue_shift=hue)
        tex = asm.build(f"row2_{i}")

        s = mcrfpy.Sprite(texture=tex, pos=(x + 20, y), scale=3.0)
        ui.append(s)
        a = AnimatedSprite(s, fmt, Direction.S)
        a.play("walk")
        _animated_sprites.append(a)
        row2_anims.append((s, a))

        lbl = mcrfpy.Caption(text=f"hue={hue:.0f}", pos=(x + 10, y + 100),
                             fill_color=DIM_COLOR)
        ui.append(lbl)

    # Code example
    code_lbl = mcrfpy.Caption(
        text='asm = CharacterAssembler(PUNY_24)',
        pos=(30, 600), fill_color=mcrfpy.Color(150, 200, 150))
    ui.append(code_lbl)
    code_lbl2 = mcrfpy.Caption(
        text='asm.add_layer("Character-Base.png")',
        pos=(30, 625), fill_color=mcrfpy.Color(150, 200, 150))
    ui.append(code_lbl2)
    code_lbl3 = mcrfpy.Caption(
        text='asm.add_layer("Warrior-Red.png", hue_shift=120.0)',
        pos=(30, 650), fill_color=mcrfpy.Color(150, 200, 150))
    ui.append(code_lbl3)
    code_lbl4 = mcrfpy.Caption(
        text='texture = asm.build("my_character")',
        pos=(30, 675), fill_color=mcrfpy.Color(150, 200, 150))
    ui.append(code_lbl4)

    controls = mcrfpy.Caption(
        text="[Q/E] Overlay sheet  [Left/Right] Overlay hue +/-30  [1-8] Scenes",
        pos=(20, 740), fill_color=DIM_COLOR)
    ui.append(controls)

    def _rebuild():
        path = overlay_sheets[state["overlay_idx"]]
        hue = state["hue"]

        # Update overlay preview
        new_overlay_tex = mcrfpy.Texture(path, fmt.tile_w, fmt.tile_h)
        overlay_spr.texture = new_overlay_tex
        overlay_name_lbl.text = os.path.basename(path)

        # Rebuild unshifted composite
        asm = CharacterAssembler(fmt)
        asm.add_layer(base_p)
        asm.add_layer(path)
        comp_spr.texture = asm.build("demo_composite")

        # Rebuild shifted composite
        asm2 = CharacterAssembler(fmt)
        asm2.add_layer(base_p)
        asm2.add_layer(path, hue_shift=hue)
        shifted_comp_spr.texture = asm2.build("demo_shifted")
        hue_note.text = f"Overlay hue: {hue:.0f}"

        # Rebuild row2
        for i, (s, a) in enumerate(row2_anims):
            h = i * 60.0
            asm3 = CharacterAssembler(fmt)
            asm3.add_layer(base_p)
            asm3.add_layer(path, hue_shift=h)
            s.texture = asm3.build(f"row2_{i}")

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if _handle_scene_switch(key):
            return
        if key == mcrfpy.Key.Q:
            state["overlay_idx"] = (state["overlay_idx"] - 1) % len(overlay_sheets)
            _rebuild()
        elif key == mcrfpy.Key.E:
            state["overlay_idx"] = (state["overlay_idx"] + 1) % len(overlay_sheets)
            _rebuild()
        elif key == mcrfpy.Key.LEFT:
            state["hue"] = (state["hue"] - 30.0) % 360.0
            _rebuild()
        elif key == mcrfpy.Key.RIGHT:
            state["hue"] = (state["hue"] + 30.0) % 360.0
            _rebuild()

    scene.on_key = on_key
    return scene


# ---------------------------------------------------------------------------
# Scene 6: Equipment Customizer
# ---------------------------------------------------------------------------
def _build_scene_equip():
    scene = mcrfpy.Scene("equip")
    sheets = _available_sheets()
    base_p = _base_path()
    if not sheets or not base_p:
        return _no_assets_fallback(scene, "Equipment Customizer")

    ui = scene.children
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=BG)
    ui.append(bg)

    title = mcrfpy.Caption(text="[6] Equipment Customizer",
                           pos=(20, 10), fill_color=TITLE_COLOR)
    ui.append(title)

    fmt = PUNY_24
    overlay_sheets = [s for s in sheets
                      if "Character-Base" not in os.path.basename(s)]

    # Three independent equipment "slots" - each selects overlay + hue
    # Simulates: Body armor, Weapon style, Trim/accent
    slot_names = ["Body Armor", "Weapon Style", "Accent Layer"]
    slot_defaults = [
        {"sheet_idx": 0, "hue": 0.0, "sat": 0.0, "lit": 0.0, "enabled": True},
        {"sheet_idx": min(2, len(overlay_sheets) - 1), "hue": 120.0,
         "sat": 0.0, "lit": 0.0, "enabled": True},
        {"sheet_idx": min(4, len(overlay_sheets) - 1), "hue": 240.0,
         "sat": 0.0, "lit": -0.3, "enabled": False},
    ]
    slots = [dict(d) for d in slot_defaults]
    state = {"active_slot": 0, "dir_idx": 0}

    # Main character preview (large)
    preview_spr = mcrfpy.Sprite(pos=(400, 150), scale=8.0)
    ui.append(preview_spr)
    preview_anim = AnimatedSprite(preview_spr, fmt, Direction.S)
    preview_anim.play("walk")
    _animated_sprites.append(preview_anim)

    # Direction label
    dir_lbl = mcrfpy.Caption(text="Direction: S", pos=(400, 420),
                             fill_color=LABEL_COLOR)
    ui.append(dir_lbl)

    # Slot panels (left side)
    slot_labels = []
    slot_info_labels = []
    slot_indicators = []

    for i, sname in enumerate(slot_names):
        y = 80 + i * 180

        # Slot header
        indicator = mcrfpy.Caption(
            text=f">>> {sname} <<<" if i == 0 else f"    {sname}",
            pos=(20, y),
            fill_color=HIGHLIGHT_COLOR if i == 0 else LABEL_COLOR)
        ui.append(indicator)
        slot_indicators.append(indicator)

        # Status
        slot = slots[i]
        enabled_str = "ON" if slot["enabled"] else "OFF"
        sheet_name = os.path.basename(overlay_sheets[slot["sheet_idx"]]).replace(".png", "")
        info = mcrfpy.Caption(
            text=f"[{enabled_str}] {sheet_name}  H:{slot['hue']:.0f} S:{slot['sat']:.1f} L:{slot['lit']:.1f}",
            pos=(20, y + 30),
            fill_color=ACCENT_COLOR if slot["enabled"] else mcrfpy.Color(80, 80, 100))
        ui.append(info)
        slot_info_labels.append(info)

        # Small preview for this slot
        slot_tex = mcrfpy.Texture(overlay_sheets[slot["sheet_idx"]],
                                  fmt.tile_w, fmt.tile_h)
        if slot["hue"] != 0.0 or slot["sat"] != 0.0 or slot["lit"] != 0.0:
            slot_tex = slot_tex.hsl_shift(slot["hue"], slot["sat"], slot["lit"])
        slot_spr = mcrfpy.Sprite(texture=slot_tex, pos=(20, y + 55), scale=3.0)
        ui.append(slot_spr)
        slot_labels.append(slot_spr)

    # Row of procedurally generated variants at bottom
    row_y = 550
    row_lbl = mcrfpy.Caption(
        text="Procedural Variants (randomized per slot):",
        pos=(20, row_y), fill_color=LABEL_COLOR)
    ui.append(row_lbl)

    variant_sprites = []
    variant_anims = []
    for i in range(6):
        x = 30 + i * 155
        s = mcrfpy.Sprite(pos=(x + 20, row_y + 30), scale=3.0)
        ui.append(s)
        a = AnimatedSprite(s, fmt, Direction.S)
        a.play("walk")
        _animated_sprites.append(a)
        variant_sprites.append(s)
        variant_anims.append(a)

    def _build_composite():
        """Build composite texture from current slot settings."""
        asm = CharacterAssembler(fmt)
        asm.add_layer(base_p)
        for slot in slots:
            if slot["enabled"]:
                path = overlay_sheets[slot["sheet_idx"]]
                asm.add_layer(path, hue_shift=slot["hue"],
                             sat_shift=slot["sat"], lit_shift=slot["lit"])
        return asm.build("equip_preview")

    def _update_preview():
        """Rebuild main preview and slot info."""
        tex = _build_composite()
        preview_spr.texture = tex

        for i, slot in enumerate(slots):
            enabled_str = "ON" if slot["enabled"] else "OFF"
            sheet_name = os.path.basename(
                overlay_sheets[slot["sheet_idx"]]).replace(".png", "")
            slot_info_labels[i].text = (
                f"[{enabled_str}] {sheet_name}  "
                f"H:{slot['hue']:.0f} S:{slot['sat']:.1f} L:{slot['lit']:.1f}")
            if slot["enabled"]:
                slot_info_labels[i].fill_color = ACCENT_COLOR
            else:
                slot_info_labels[i].fill_color = mcrfpy.Color(80, 80, 100)

            # Update slot preview sprite
            stex = mcrfpy.Texture(overlay_sheets[slot["sheet_idx"]],
                                  fmt.tile_w, fmt.tile_h)
            if slot["hue"] != 0.0 or slot["sat"] != 0.0 or slot["lit"] != 0.0:
                stex = stex.hsl_shift(slot["hue"], slot["sat"], slot["lit"])
            slot_labels[i].texture = stex

        # Update slot indicators
        for i, ind in enumerate(slot_indicators):
            sname = slot_names[i]
            if i == state["active_slot"]:
                ind.text = f">>> {sname} <<<"
                ind.fill_color = HIGHLIGHT_COLOR
            else:
                ind.text = f"    {sname}"
                ind.fill_color = LABEL_COLOR

    def _generate_variants():
        """Create 6 random procedural variants."""
        for i in range(6):
            asm = CharacterAssembler(fmt)
            asm.add_layer(base_p)
            # Each variant gets 1-2 random layers with random hues
            n_layers = random.randint(1, 2)
            for _ in range(n_layers):
                path = random.choice(overlay_sheets)
                hue = random.uniform(0, 360)
                sat = random.uniform(-0.3, 0.3)
                lit = random.uniform(-0.2, 0.1)
                asm.add_layer(path, hue_shift=hue, sat_shift=sat, lit_shift=lit)
            variant_sprites[i].texture = asm.build(f"variant_{i}")

    _update_preview()
    _generate_variants()

    controls = mcrfpy.Caption(
        text="[Tab] Slot  [Q/E] Sheet  [Left/Right] Hue  [Up/Down] Sat  [Z/X] Lit  [T] Toggle  [R] Randomize  [1-8] Scenes",
        pos=(20, 740), fill_color=DIM_COLOR)
    ui.append(controls)

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if _handle_scene_switch(key):
            return

        slot = slots[state["active_slot"]]

        if key == mcrfpy.Key.TAB:
            state["active_slot"] = (state["active_slot"] + 1) % len(slots)
            _update_preview()
        elif key == mcrfpy.Key.T:
            slot["enabled"] = not slot["enabled"]
            _update_preview()
        elif key == mcrfpy.Key.Q:
            slot["sheet_idx"] = (slot["sheet_idx"] - 1) % len(overlay_sheets)
            _update_preview()
        elif key == mcrfpy.Key.E:
            slot["sheet_idx"] = (slot["sheet_idx"] + 1) % len(overlay_sheets)
            _update_preview()
        elif key == mcrfpy.Key.LEFT:
            slot["hue"] = (slot["hue"] - 30.0) % 360.0
            _update_preview()
        elif key == mcrfpy.Key.RIGHT:
            slot["hue"] = (slot["hue"] + 30.0) % 360.0
            _update_preview()
        elif key == mcrfpy.Key.UP:
            slot["sat"] = min(1.0, slot["sat"] + 0.1)
            _update_preview()
        elif key == mcrfpy.Key.DOWN:
            slot["sat"] = max(-1.0, slot["sat"] - 0.1)
            _update_preview()
        elif key == mcrfpy.Key.Z:
            slot["lit"] = max(-1.0, slot["lit"] - 0.1)
            _update_preview()
        elif key == mcrfpy.Key.X:
            slot["lit"] = min(1.0, slot["lit"] + 0.1)
            _update_preview()
        elif key == mcrfpy.Key.R:
            _generate_variants()
        elif key == mcrfpy.Key.W:
            state["dir_idx"] = (state["dir_idx"] - 1) % 8
            d = Direction(state["dir_idx"])
            preview_anim.direction = d
            for a in variant_anims:
                a.direction = d
            dir_lbl.text = f"Direction: {d.name}"
        elif key == mcrfpy.Key.S:
            state["dir_idx"] = (state["dir_idx"] + 1) % 8
            d = Direction(state["dir_idx"])
            preview_anim.direction = d
            for a in variant_anims:
                a.direction = d
            dir_lbl.text = f"Direction: {d.name}"

    scene.on_key = on_key
    return scene


# ---------------------------------------------------------------------------
# Scene 7: Asset Inventory Browser
# ---------------------------------------------------------------------------
def _build_scene_inventory():
    scene = mcrfpy.Scene("inventory")
    ui = scene.children
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=BG)
    ui.append(bg)

    title = mcrfpy.Caption(text="[7] Asset Inventory",
                           pos=(20, 10), fill_color=TITLE_COLOR)
    ui.append(title)

    lib = AssetLibrary()
    if not lib.available:
        msg = mcrfpy.Caption(
            text="No paid Puny Characters v2.1 pack found.",
            pos=(20, 60), fill_color=WARN_COLOR)
        ui.append(msg)
        msg2 = mcrfpy.Caption(
            text="The AssetLibrary scans the 'Individual Spritesheets' directory.",
            pos=(20, 90), fill_color=DIM_COLOR)
        ui.append(msg2)
        controls = mcrfpy.Caption(text="[1-8] Switch scenes",
                                  pos=(20, 740), fill_color=DIM_COLOR)
        ui.append(controls)

        def on_key(key, action):
            if action != mcrfpy.InputState.PRESSED:
                return
            _handle_scene_switch(key)
        scene.on_key = on_key
        return scene

    # Build category data
    categories = lib.categories
    cat_data = []  # list of (key, label, count, subcats_with_counts)
    for cat_key in categories:
        files = lib.layers(cat_key)
        subcats = lib.subcategories(cat_key)
        sub_info = []
        for sc in subcats:
            sc_files = lib.layers_in(cat_key, sc)
            label = sc if sc else "(root)"
            sub_info.append((label, len(sc_files), [f.name for f in sc_files]))
        display_name = cat_key.replace("_", " ").title()
        cat_data.append((cat_key, display_name, len(files), sub_info))

    state = {"cat_idx": 0, "sub_idx": 0, "scroll": 0}
    MAX_VISIBLE_FILES = 18

    # Summary header
    summary = lib.summary()
    total = sum(summary.values())
    species_list = ", ".join(lib.species)
    summary_lbl = mcrfpy.Caption(
        text=f"Found {total} layer files in {len(categories)} categories. Species: {species_list}",
        pos=(20, 45), fill_color=LABEL_COLOR)
    ui.append(summary_lbl)

    # Left panel: category list
    left_x = 20
    cat_labels = []
    for i, (key, display, count, _) in enumerate(cat_data):
        y = 85 + i * 28
        prefix = ">>>" if i == 0 else "   "
        lbl = mcrfpy.Caption(
            text=f"{prefix} {display} ({count})",
            pos=(left_x, y),
            fill_color=HIGHLIGHT_COLOR if i == 0 else LABEL_COLOR)
        ui.append(lbl)
        cat_labels.append(lbl)

    # Center panel: subcategory list
    center_x = 280
    sub_header = mcrfpy.Caption(text="Subcategories:",
                                pos=(center_x, 85), fill_color=ACCENT_COLOR)
    ui.append(sub_header)

    # We'll dynamically create labels for subcategories
    sub_labels = []
    sub_label_pool = []  # pre-allocated caption objects
    for i in range(12):
        lbl = mcrfpy.Caption(text="", pos=(center_x, 110 + i * 25),
                             fill_color=LABEL_COLOR)
        ui.append(lbl)
        sub_label_pool.append(lbl)

    # Right panel: file list
    right_x = 560
    file_header = mcrfpy.Caption(text="Files:",
                                 pos=(right_x, 85), fill_color=ACCENT_COLOR)
    ui.append(file_header)

    file_label_pool = []
    for i in range(MAX_VISIBLE_FILES):
        lbl = mcrfpy.Caption(text="", pos=(right_x, 110 + i * 25),
                             fill_color=DIM_COLOR)
        ui.append(lbl)
        file_label_pool.append(lbl)

    scroll_info = mcrfpy.Caption(text="", pos=(right_x, 110 + MAX_VISIBLE_FILES * 25),
                                 fill_color=DIM_COLOR)
    ui.append(scroll_info)

    def _refresh():
        cat_key, display, count, sub_info = cat_data[state["cat_idx"]]

        # Update category highlights
        for i, lbl in enumerate(cat_labels):
            key, disp, cnt, _ = cat_data[i]
            if i == state["cat_idx"]:
                lbl.text = f">>> {disp} ({cnt})"
                lbl.fill_color = HIGHLIGHT_COLOR
            else:
                lbl.text = f"    {disp} ({cnt})"
                lbl.fill_color = LABEL_COLOR

        # Update subcategory list
        for i, lbl in enumerate(sub_label_pool):
            if i < len(sub_info):
                sc_label, sc_count, _ = sub_info[i]
                prefix = ">" if i == state["sub_idx"] else " "
                lbl.text = f"{prefix} {sc_label} ({sc_count})"
                lbl.fill_color = ACCENT_COLOR if i == state["sub_idx"] else LABEL_COLOR
            else:
                lbl.text = ""

        # Update file list for selected subcategory
        if state["sub_idx"] < len(sub_info):
            _, _, file_names = sub_info[state["sub_idx"]]
        else:
            file_names = []

        scroll = state["scroll"]
        visible = file_names[scroll:scroll + MAX_VISIBLE_FILES]
        for i, lbl in enumerate(file_label_pool):
            if i < len(visible):
                lbl.text = visible[i]
            else:
                lbl.text = ""

        if len(file_names) > MAX_VISIBLE_FILES:
            scroll_info.text = f"({scroll + 1}-{min(scroll + MAX_VISIBLE_FILES, len(file_names))} of {len(file_names)}, PgUp/PgDn)"
        else:
            scroll_info.text = ""

    _refresh()

    controls = mcrfpy.Caption(
        text="[W/S] Category  [A/D] Subcategory  [PgUp/PgDn] Scroll files  [1-8] Scenes",
        pos=(20, 740), fill_color=DIM_COLOR)
    ui.append(controls)

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if _handle_scene_switch(key):
            return

        _, _, _, sub_info = cat_data[state["cat_idx"]]

        if key == mcrfpy.Key.W:
            state["cat_idx"] = (state["cat_idx"] - 1) % len(cat_data)
            state["sub_idx"] = 0
            state["scroll"] = 0
            _refresh()
        elif key == mcrfpy.Key.S:
            state["cat_idx"] = (state["cat_idx"] + 1) % len(cat_data)
            state["sub_idx"] = 0
            state["scroll"] = 0
            _refresh()
        elif key == mcrfpy.Key.A:
            if sub_info:
                state["sub_idx"] = (state["sub_idx"] - 1) % len(sub_info)
                state["scroll"] = 0
            _refresh()
        elif key == mcrfpy.Key.D:
            if sub_info:
                state["sub_idx"] = (state["sub_idx"] + 1) % len(sub_info)
                state["scroll"] = 0
            _refresh()
        elif key == mcrfpy.Key.PAGEDOWN:
            if state["sub_idx"] < len(sub_info):
                _, _, file_names = sub_info[state["sub_idx"]]
                max_scroll = max(0, len(file_names) - MAX_VISIBLE_FILES)
                state["scroll"] = min(state["scroll"] + MAX_VISIBLE_FILES, max_scroll)
            _refresh()
        elif key == mcrfpy.Key.PAGEUP:
            state["scroll"] = max(0, state["scroll"] - MAX_VISIBLE_FILES)
            _refresh()

    scene.on_key = on_key
    return scene


# ---------------------------------------------------------------------------
# Scene 8: Entity Animation (engine-native, all formats)
# ---------------------------------------------------------------------------
def _format_frame_list(fmt, anim_name, direction):
    """Convert animation def to flat sprite index list for Entity.animate()."""
    anim = fmt.animations[anim_name]
    return [fmt.sprite_index(f.col, direction) for f in anim.frames]


def _format_duration(fmt, anim_name):
    """Total duration in seconds."""
    anim = fmt.animations[anim_name]
    return sum(f.duration for f in anim.frames) / 1000.0


def _build_scene_entity_anim():
    scene = mcrfpy.Scene("entity_anim")
    sheets = _available_sheets()
    if not sheets:
        return _no_assets_fallback(scene, "Entity Animation")

    ui = scene.children
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=BG)
    ui.append(bg)

    title = mcrfpy.Caption(text="[8] Entity Animation (engine-native loop)",
                           pos=(20, 10), fill_color=TITLE_COLOR)
    ui.append(title)

    explain = mcrfpy.Caption(
        text="Entity.animate('sprite_index', [frames], duration, loop=True) - no Python timer needed",
        pos=(20, 40), fill_color=LABEL_COLOR)
    ui.append(explain)

    # Collect all format sections
    # Each section: format, texture path, available animations, grid + entities
    sections = []  # (fmt, name, tex, grid, entities, anim_names)

    state = {"anim_idx": 0, "dir_idx": 0}

    section_y = 80
    grid_w, grid_h = 200, 160

    # --- PUNY_24 ---
    puny24_lbl = mcrfpy.Caption(text="PUNY_24 (8-dir, free)",
                                pos=(20, section_y), fill_color=ACCENT_COLOR)
    ui.append(puny24_lbl)

    fmt24 = PUNY_24
    tex24 = mcrfpy.Texture(sheets[0], fmt24.tile_w, fmt24.tile_h)
    grid24 = mcrfpy.Grid(grid_size=(8, 1), texture=tex24,
                         pos=(20, section_y + 25), size=(grid_w * 2, grid_h))
    grid24.zoom = 0.25
    ui.append(grid24)

    entities24 = []
    anim_names24 = list(fmt24.animations.keys())
    for i, d in enumerate(Direction):
        e = mcrfpy.Entity(grid_pos=(i, 0), texture=tex24, sprite_index=0)
        grid24.entities.append(e)
        entities24.append(e)
    sections.append((fmt24, "PUNY_24", tex24, grid24, entities24, anim_names24))

    # Direction labels for compass
    for i, d in enumerate(Direction):
        lbl = mcrfpy.Caption(text=d.name, pos=(20 + i * 50, section_y + 25 + grid_h + 2),
                             fill_color=DIM_COLOR)
        ui.append(lbl)

    # --- PUNY_29 (if paid sheets exist with 29 cols) ---
    # PUNY_29 uses 928px wide sheets; check if any available are that size
    puny29_sheet = None
    for s in sheets:
        try:
            # Try loading as PUNY_29 to check
            t = mcrfpy.Texture(s, PUNY_29.tile_w, PUNY_29.tile_h)
            # Check column count via sprite count (29 cols * 8 rows = 232)
            puny29_sheet = s
            break
        except Exception:
            pass

    section_y2 = section_y + grid_h + 45
    if puny29_sheet:
        puny29_lbl = mcrfpy.Caption(text="PUNY_29 (8-dir, paid - extra anims)",
                                    pos=(20, section_y2), fill_color=ACCENT_COLOR)
        ui.append(puny29_lbl)

        fmt29 = PUNY_29
        tex29 = mcrfpy.Texture(puny29_sheet, fmt29.tile_w, fmt29.tile_h)
        grid29 = mcrfpy.Grid(grid_size=(8, 1), texture=tex29,
                             pos=(20, section_y2 + 25), size=(grid_w * 2, grid_h))
        grid29.zoom = 0.25
        ui.append(grid29)

        entities29 = []
        anim_names29 = list(fmt29.animations.keys())
        for i, d in enumerate(Direction):
            e = mcrfpy.Entity(grid_pos=(i, 0), texture=tex29, sprite_index=0)
            grid29.entities.append(e)
            entities29.append(e)
        sections.append((fmt29, "PUNY_29", tex29, grid29, entities29, anim_names29))
    else:
        puny29_lbl = mcrfpy.Caption(text="PUNY_29 (not available - need 928px wide sheet)",
                                    pos=(20, section_y2), fill_color=DIM_COLOR)
        ui.append(puny29_lbl)

    # --- SLIME ---
    section_y3 = section_y2 + grid_h + 45
    slime_p = _slime_path()
    if slime_p:
        slime_lbl = mcrfpy.Caption(text="SLIME (1-dir, non-directional)",
                                   pos=(20, section_y3), fill_color=ACCENT_COLOR)
        ui.append(slime_lbl)

        fmt_slime = SLIME
        tex_slime = mcrfpy.Texture(slime_p, fmt_slime.tile_w, fmt_slime.tile_h)
        grid_slime = mcrfpy.Grid(grid_size=(2, 1), texture=tex_slime,
                                 pos=(20, section_y3 + 25), size=(120, grid_h))
        grid_slime.zoom = 0.25
        ui.append(grid_slime)

        entities_slime = []
        anim_names_slime = list(fmt_slime.animations.keys())
        for i, aname in enumerate(anim_names_slime):
            e = mcrfpy.Entity(grid_pos=(i, 0), texture=tex_slime, sprite_index=0)
            grid_slime.entities.append(e)
            entities_slime.append(e)

        slime_note = mcrfpy.Caption(
            text="idle / walk", pos=(20, section_y3 + 25 + grid_h + 2),
            fill_color=DIM_COLOR)
        ui.append(slime_note)

        sections.append((fmt_slime, "SLIME", tex_slime, grid_slime,
                         entities_slime, anim_names_slime))
    else:
        slime_lbl = mcrfpy.Caption(text="SLIME (not available)",
                                   pos=(20, section_y3), fill_color=DIM_COLOR)
        ui.append(slime_lbl)

    # --- Info panel (right side) ---
    info_x = 500
    anim_info = mcrfpy.Caption(text="Animation: idle", pos=(info_x, 80),
                               fill_color=HIGHLIGHT_COLOR)
    ui.append(anim_info)
    dir_info = mcrfpy.Caption(text="Direction: S (0)", pos=(info_x, 110),
                              fill_color=LABEL_COLOR)
    ui.append(dir_info)
    frame_info = mcrfpy.Caption(text="", pos=(info_x, 140),
                                fill_color=ACCENT_COLOR)
    ui.append(frame_info)

    # Code example
    code_y = 200
    code_lines = [
        "# Engine-native sprite frame animation:",
        "frames = [fmt.sprite_index(f.col, dir)",
        "          for f in fmt.animations['walk'].frames]",
        "entity.animate('sprite_index', frames,",
        "               duration, loop=True)",
        "",
        "# No Python Timer or AnimatedSprite needed!",
        "# The C++ AnimationManager handles the loop.",
    ]
    for i, line in enumerate(code_lines):
        c = mcrfpy.Caption(text=line, pos=(info_x, code_y + i * 25),
                           fill_color=mcrfpy.Color(150, 200, 150))
        ui.append(c)

    # Show all available animation names per format
    names_y = code_y + len(code_lines) * 25 + 20
    for fmt, name, _, _, _, anim_names in sections:
        albl = mcrfpy.Caption(
            text=f"{name}: {', '.join(anim_names)}",
            pos=(info_x, names_y), fill_color=DIM_COLOR)
        ui.append(albl)
        names_y += 25

    def _apply_anims():
        """Apply current animation to all entities in all sections."""
        d = Direction(state["dir_idx"])
        for fmt, name, tex, grid, entities, anim_names in sections:
            idx = state["anim_idx"] % len(anim_names)
            anim_name = anim_names[idx]
            frames = _format_frame_list(fmt, anim_name, d)
            dur = _format_duration(fmt, anim_name)
            is_loop = fmt.animations[anim_name].loop

            for e in entities:
                e.animate("sprite_index", frames, dur, loop=is_loop)

        # Use first section for info display
        if sections:
            fmt0, _, _, _, _, anames0 = sections[0]
            idx0 = state["anim_idx"] % len(anames0)
            aname = anames0[idx0]
            adef = fmt0.animations[aname]
            nf = len(adef.frames)
            loop_str = "loop" if adef.loop else "one-shot"
            chain_str = f" -> {adef.chain_to}" if adef.chain_to else ""
            anim_info.text = f"Animation: {aname}"
            frame_info.text = f"Frames: {nf}  ({loop_str}{chain_str})"
        dir_info.text = f"Direction: {d.name} ({d.value})"

    _apply_anims()

    controls = mcrfpy.Caption(
        text="[A/D] Animation  [W/S] Direction  [1-8] Scenes",
        pos=(20, 740), fill_color=DIM_COLOR)
    ui.append(controls)

    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if _handle_scene_switch(key):
            return
        if key == mcrfpy.Key.A:
            state["anim_idx"] -= 1
            _apply_anims()
        elif key == mcrfpy.Key.D:
            state["anim_idx"] += 1
            _apply_anims()
        elif key == mcrfpy.Key.W:
            state["dir_idx"] = (state["dir_idx"] - 1) % 8
            _apply_anims()
        elif key == mcrfpy.Key.S:
            state["dir_idx"] = (state["dir_idx"] + 1) % 8
            _apply_anims()

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

    _build_scene_viewer()
    _build_scene_hsl()
    _build_scene_gallery()
    _build_scene_factions()
    _build_scene_layers()
    _build_scene_equip()
    _build_scene_inventory()
    _build_scene_entity_anim()

    # Start animation timer (20fps animation updates)
    # Keep a reference so the Python cache lookup works and (timer, runtime) is passed
    global _anim_timer
    _anim_timer = mcrfpy.Timer("shade_anim", _tick_all, 50)

    # Activate first scene
    mcrfpy.Scene("viewer").activate()


if __name__ == "__main__":
    main()
    # Do NOT call sys.exit(0) here - let the game loop run
