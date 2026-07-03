"""UNWRITTEN - bootstrap and title screen. Owner: Agent A.

Run windowed:
  cd build && ./mcrogueface --exec ../games/unwritten/main.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mcrfpy
from core import palette, ui, tween
from core.inputstack import InputStack
from systems import dialogue
from systems.state import GS

# Boot wiring (Agent D): importing each system registers its dialogue HOOKS at
# import time. main.py used to import none of them, so goto_area/battle/shop/
# swap_menu/epilogue were never registered and _enter_world raised. Import them
# here, once, so the whole game is wired the moment main is loaded.
from systems import overworld    # noqa: F401  registers HOOKS["goto_area"]
from systems import battle       # noqa: F401  registers HOOKS["battle"]
from systems import shop         # noqa: F401  registers HOOKS["shop"]
from systems import party_menu   # noqa: F401  registers HOOKS["swap_menu"]
from systems import epilogue     # noqa: F401  registers HOOKS["epilogue"]


# ----------------------------------------------------------------- chapter presets
def _preset_act1():
    GS.reset()
    GS.act = 1
    GS.recruit("PIP", 1)
    GS.gold = 30
    GS.grant("bread", 2)
    GS.grant("red_tonic", 1)
    roster = GS.roster.get("PIP")
    if roster is not None:
        roster.weapon = "knife"


def _preset_act2():
    GS.reset()
    GS.act = 2
    for f in ("door_open", "bramble_joined", "moth_joined", "quill_confident",
              "griselda_friend", "vera_grudge", "shrine_chest_open"):
        GS.add_flag(f)
    GS.recruit("PIP", 3)
    GS.recruit("BRAMBLE", 3)
    GS.recruit("MOTH", 3)
    GS.gold = 120
    GS.grant("bread", 3)
    GS.grant("red_tonic", 2)
    GS.grant("blue_draught", 1)
    GS.grant("brass_key", 1)


def _preset_act3():
    _preset_act2()
    GS.act = 3
    for f in ("cantor_joined", "gatekeeper_slain", "vera_reconciled",
              "asked_unwoken", "touched_sketch"):
        GS.add_flag(f)
    GS.recruit("CANTOR", 5)
    for cid in ("PIP", "BRAMBLE", "MOTH", "CANTOR"):
        c = GS.roster.get(cid)
        if c is not None:
            c.level = 5
            c.xp = 10 * 5 * 4
            c.full_heal()
    GS.points = 8
    GS.grant("gatekeepers_tooth", 1)
    GS.add_key_item("gatekeepers_tooth")


# -------------------------------------------------------------------- title scene
def build_title():
    scene = mcrfpy.Scene("title")
    mcrfpy.current_scene = scene
    ch = scene.children

    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=palette.INK)
    ch.append(bg)

    # slow gold pulse behind the title
    ring = mcrfpy.Circle(radius=90, center=(512, 250),
                         fill_color=palette.C(palette.GOLD_T, 18),
                         outline=1, outline_color=palette.C(palette.GOLD_T, 40))
    ch.append(ring)
    ring.animate("radius", 130, 2.6, mcrfpy.Easing.EASE_IN_OUT, loop=True)

    title = ui.Label(ch, "UNWRITTEN", (512, 250), color=palette.PARCH,
                     size=palette.TITLE_SIZE, center=True, outline=2)

    rule = mcrfpy.Frame(pos=(512 - 220, 316), size=(440, 3),
                        fill_color=palette.GOLD)
    ch.append(rule)

    ui.Label(ch, "the world is finished. the story is not.", (512, 350),
             color=palette.DIM, size=palette.BODY_SIZE, center=True)

    press = ui.Label(ch, "press ENTER", (512, 600), color=palette.DIM,
                     size=palette.BODY_SIZE, center=True)
    press.animate("opacity", 0.15, 0.8, mcrfpy.Easing.EASE_IN_OUT, loop=True)

    stack = InputStack(scene)

    def on_key(key, state):
        if state != mcrfpy.InputState.PRESSED:
            return True
        K = mcrfpy.Key
        if key == K.ENTER:
            start_new_game(stack)
        elif key == K.NUM_1:
            _preset_act1()
            _enter_world("hollowbrook", "start")
        elif key == K.NUM_2:
            _preset_act2()
            _enter_world("undercroft", "enter")
        elif key == K.NUM_3:
            _preset_act3()
            _enter_world("hollowbrook", "from_ferry")
        return True

    stack.push(on_key, "title")
    return scene


def start_new_game(stack):
    _preset_act1()
    # intro monologue, then hand off to the overworld
    dialogue.run_scene("intro", on_done=lambda: _enter_world("hollowbrook", "start"),
                       stack=stack)


def _enter_world(area, spawn):
    hook = dialogue.HOOKS.get("goto_area")
    if hook is None:
        raise RuntimeError(
            "cannot enter world: systems.dialogue.HOOKS['goto_area'] is not "
            "registered yet (Agent C's overworld must register it)")
    hook(area, spawn)


def main():
    build_title()


if __name__ == "__main__":
    main()
