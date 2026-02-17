"""shade_sprite - Sprite animation and compositing for Merchant Shade sprite packs.

A standalone module for McRogueFace that loads, composites, and animates
layered pixel art character sheets. Supports multiple sprite sheet formats
including the Puny Characters pack (paid & free), RPG Maker creatures,
and slime sheets.

Quick start:
    from shade_sprite import AnimatedSprite, Direction, PUNY_29
    import mcrfpy

    tex = mcrfpy.Texture("Warrior-Red.png", 32, 32)
    sprite = mcrfpy.Sprite(texture=tex, pos=(100, 100), scale=2.0)
    scene.children.append(sprite)

    anim = AnimatedSprite(sprite, PUNY_29)
    anim.play("walk")
    anim.direction = Direction.E

    def tick_anims(timer, runtime):
        anim.tick(timer.interval)
    mcrfpy.Timer("anim", tick_anims, 50)

For layered characters:
    from shade_sprite import CharacterAssembler, PUNY_29

    assembler = CharacterAssembler(PUNY_29)
    assembler.add_layer("skins/Human1.png")
    assembler.add_layer("clothes/BasicBlue-Body.png", hue_shift=120.0)
    assembler.add_layer("hair/M-Hairstyle1-Black.png")
    texture = assembler.build("my_character")
"""

from .formats import (
    Direction,
    AnimFrame,
    AnimDef,
    SheetFormat,
    PUNY_29,
    PUNY_24,
    CREATURE_RPGMAKER,
    SLIME,
    ALL_FORMATS,
    detect_format,
)
from .animation import AnimatedSprite
from .assembler import CharacterAssembler

__all__ = [
    # Core classes
    "AnimatedSprite",
    "CharacterAssembler",
    # Format definitions
    "Direction",
    "AnimFrame",
    "AnimDef",
    "SheetFormat",
    # Predefined formats
    "PUNY_29",
    "PUNY_24",
    "CREATURE_RPGMAKER",
    "SLIME",
    "ALL_FORMATS",
    # Utilities
    "detect_format",
]
