"""Unit tests for shade_sprite module."""
import mcrfpy
import sys
import os

# Add project root to path so shade_sprite can be imported
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shade_sprite import (
    AnimatedSprite, CharacterAssembler, Direction,
    PUNY_29, PUNY_24, CREATURE_RPGMAKER, SLIME,
    ALL_FORMATS, detect_format, AnimFrame, AnimDef,
)

errors = []

def test(name, condition, msg=""):
    if not condition:
        errors.append(f"FAIL: {name} - {msg}")
        print(f"  FAIL: {name} {msg}")
    else:
        print(f"  PASS: {name}")


# ---- Format definitions ----
print("=== Format Definitions ===")

test("PUNY_29 dimensions", PUNY_29.tile_w == 32 and PUNY_29.tile_h == 32)
test("PUNY_29 columns", PUNY_29.columns == 29)
test("PUNY_29 rows", PUNY_29.rows == 8)
test("PUNY_29 directions", PUNY_29.directions == 8)
test("PUNY_29 has 10 animations", len(PUNY_29.animations) == 10,
     f"got {len(PUNY_29.animations)}: {list(PUNY_29.animations.keys())}")
test("PUNY_29 idle is looping", PUNY_29.animations["idle"].loop)
test("PUNY_29 death no chain", PUNY_29.animations["death"].chain_to is None)
test("PUNY_29 slash chains to idle", PUNY_29.animations["slash"].chain_to == "idle")

test("PUNY_24 dimensions", PUNY_24.tile_w == 32 and PUNY_24.tile_h == 32)
test("PUNY_24 columns", PUNY_24.columns == 24)
test("PUNY_24 has 8 animations", len(PUNY_24.animations) == 8,
     f"got {len(PUNY_24.animations)}: {list(PUNY_24.animations.keys())}")

test("CREATURE_RPGMAKER tile", CREATURE_RPGMAKER.tile_w == 24 and CREATURE_RPGMAKER.tile_h == 24)
test("CREATURE_RPGMAKER 4-dir", CREATURE_RPGMAKER.directions == 4)

test("SLIME columns", SLIME.columns == 15)
test("SLIME 1-dir", SLIME.directions == 1)

test("ALL_FORMATS count", len(ALL_FORMATS) == 4)


# ---- Format detection ----
print("\n=== Format Detection ===")

test("detect 928x256 -> PUNY_29", detect_format(928, 256) is PUNY_29)
test("detect 768x256 -> PUNY_24", detect_format(768, 256) is PUNY_24)
test("detect 480x32 -> SLIME", detect_format(480, 32) is SLIME)
test("detect 72x96 -> CREATURE_RPGMAKER", detect_format(72, 96) is CREATURE_RPGMAKER)
test("detect unknown -> None", detect_format(100, 100) is None)


# ---- Direction ----
print("\n=== Direction ===")

test("Direction.S == 0", Direction.S == 0)
test("Direction.N == 4", Direction.N == 4)
test("Direction.E == 6", Direction.E == 6)

# 8-dir row mapping
test("8-dir S -> row 0", PUNY_29.direction_row(Direction.S) == 0)
test("8-dir N -> row 4", PUNY_29.direction_row(Direction.N) == 4)
test("8-dir E -> row 6", PUNY_29.direction_row(Direction.E) == 6)

# 4-dir mapping
test("4-dir S -> row 0", CREATURE_RPGMAKER.direction_row(Direction.S) == 0)
test("4-dir W -> row 1", CREATURE_RPGMAKER.direction_row(Direction.W) == 1)
test("4-dir E -> row 2", CREATURE_RPGMAKER.direction_row(Direction.E) == 2)
test("4-dir N -> row 3", CREATURE_RPGMAKER.direction_row(Direction.N) == 3)
test("4-dir SW -> row 0 (rounds to S)", CREATURE_RPGMAKER.direction_row(Direction.SW) == 0)


# ---- Sprite index calculation ----
print("\n=== Sprite Index ===")

# PUNY_29: row * 29 + col
test("PUNY_29 col=0 S -> 0", PUNY_29.sprite_index(0, Direction.S) == 0)
test("PUNY_29 col=5 S -> 5", PUNY_29.sprite_index(5, Direction.S) == 5)
test("PUNY_29 col=0 N -> 116", PUNY_29.sprite_index(0, Direction.N) == 4 * 29)
test("PUNY_29 col=5 E -> 6*29+5", PUNY_29.sprite_index(5, Direction.E) == 6 * 29 + 5)

# SLIME: always row 0 (1-dir)
test("SLIME col=3 any dir -> 3", SLIME.sprite_index(3, Direction.E) == 3)


# ---- AnimatedSprite (with mock sprite) ----
print("\n=== AnimatedSprite ===")

# Create a real mcrfpy.Sprite with a from_bytes texture for testing
tex_data = bytes([128, 128, 128, 255] * (768 * 256))
tex = mcrfpy.Texture.from_bytes(tex_data, 768, 256, 32, 32)
sprite = mcrfpy.Sprite(texture=tex, pos=(0, 0))

anim = AnimatedSprite(sprite, PUNY_24, Direction.S)
test("AnimatedSprite created", anim is not None)
test("AnimatedSprite starts with idle", anim.animation_name == "idle")
test("AnimatedSprite direction is S", anim.direction == Direction.S)

# Play walk
anim.play("walk")
test("play walk", anim.animation_name == "walk")
test("walk frame 0", anim.frame_index == 0)

# Tick through first frame (walk frame 0 is col 1, 200ms)
anim.tick(100)  # half of 200ms
test("tick 100ms stays on frame 0", anim.frame_index == 0)

anim.tick(100)  # now 200ms total -> advance to frame 1
test("tick 200ms advances to frame 1", anim.frame_index == 1)

# Sprite index should reflect col 2 (walk frame 1), row 0 (S)
expected_idx = 0 * 24 + 2  # row=0, col=2
test("sprite_index after advance",
     sprite.sprite_index == expected_idx,
     f"got {sprite.sprite_index}, expected {expected_idx}")

# Direction change
anim.set_direction(Direction.E)
test("direction changed to E", anim.direction == Direction.E)
# Same column but different row
expected_idx = 6 * 24 + 2  # row=6 (E), col=2
test("sprite_index after dir change",
     sprite.sprite_index == expected_idx,
     f"got {sprite.sprite_index}, expected {expected_idx}")

# One-shot animation
anim.play("slash")
test("slash starts at frame 0", anim.frame_index == 0)
# Slash: 4 frames of 100ms each, then chains to idle
anim.tick(100)
anim.tick(100)
anim.tick(100)
test("slash frame 3 after 300ms", anim.frame_index == 3)
anim.tick(100)  # finish last frame -> chain to idle
test("slash chains to idle", anim.animation_name == "idle")

# Death animation (no chain)
anim.play("death")
anim.tick(100)  # frame 0
anim.tick(100)  # frame 1 (last frame for PUNY_24 death)
# death has chain_to=None, so it stays finished
# Wait for last frame to expire
anim.tick(1000)  # way past duration
test("death finished", anim.finished)
test("death stays on last frame", anim.frame_index == 1)

# Invalid animation name
try:
    anim.play("nonexistent")
    test("invalid anim raises KeyError", False, "no exception")
except KeyError:
    test("invalid anim raises KeyError", True)


# ---- CharacterAssembler (basic) ----
print("\n=== CharacterAssembler ===")

asm = CharacterAssembler(PUNY_24)
test("assembler created", asm is not None)

# Empty build should fail
try:
    asm.build()
    test("empty build raises", False, "no exception")
except ValueError:
    test("empty build raises ValueError", True)


# ---- Summary ----
print()
if errors:
    print(f"FAILED: {len(errors)} tests failed")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("All tests passed!")
    sys.exit(0)
