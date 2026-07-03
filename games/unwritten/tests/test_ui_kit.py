"""UNWRITTEN - UI kit headless test. Owner: Agent A.

Builds a scene, exercises every widget (DialogueBox with a real node from
script_act1 'intro', a MenuList with a disabled row, a Bar at 30%, a Toast, a
TitleBanner), drives mcrfpy.step to advance the typewriter, and screenshots two
meaningful states.

Run:
  cd build && ./mcrogueface --headless --exec ../games/unwritten/tests/test_ui_kit.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mcrfpy
from core import palette, ui
from data import script_act1

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")


def step_n(n):
    for _ in range(n):
        mcrfpy.step(1.0 / 60.0)


def main():
    os.makedirs(SHOTS, exist_ok=True)
    scene = mcrfpy.Scene("uikit")
    mcrfpy.current_scene = scene
    ch = scene.children

    # background
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=palette.INK)
    ch.append(bg)

    # --- MenuList with one disabled row (top-left) ---
    menu = ui.MenuList(
        ch, (60, 150), 300,
        items=[
            ("Attack", "attack", True),
            ("Skill", "skill", True),
            ("Item", "item", False, "no items"),
            ("Guard", "guard", True),
        ],
        title="COMMAND")

    # --- Bar at 30% (right) ---
    bar_panel = ui.Panel(ch, (600, 150), (340, 70), outline_color=palette.OUTLINE)
    ui.Label(bar_panel.children, "HP", (16, 14), color=palette.PARCH,
             size=palette.SMALL_SIZE)
    hp_bar = ui.Bar(bar_panel.children, (16, 34), (300, 22), palette.BLOOD,
                    cur=30, maxv=100)

    # --- Toast (top-right) ---
    ui.Toast(ch, "+1 Story Point", color=palette.GOLD)

    # --- TitleBanner (top center) ---
    ui.TitleBanner(ch, "THE GEARWOOD", cx=512, cy=70)

    # --- DialogueBox: a real NARRATOR node from 'intro', mid-typewriter ---
    box = ui.DialogueBox(ch)
    intro_n1 = script_act1.SCENES["intro"]["nodes"]["n1"]
    box.show_node("NARRATOR", intro_n1["text"], on_advance=lambda: None)

    # let the entrance settle and reveal part of the body
    step_n(16)
    ok1 = mcrfpy.automation.screenshot(os.path.join(SHOTS, "uikit_1.png"))
    assert ok1, "screenshot 1 failed"
    partial = box.body.text
    assert 0 < len(partial) < len(box._full), \
        "typewriter should be mid-reveal (%d/%d)" % (len(partial), len(box._full))

    # --- DialogueBox choice mode: a real node with a disabled [ALCHEMY] choice ---
    disp = script_act1.SCENES["shop_dispute"]["nodes"]["n3"]
    # empty active party -> the [ALCHEMY] tag choice is locked (disabled), the
    # two plain choices are enabled. This is the design pillar: shown but DIM.
    choices = []
    for c in disp["choices"]:
        enabled = c.get("req") is None
        choices.append((c["label"], enabled))
    box.show_node("VERA", disp["text"], choices=choices,
                  on_choice=lambda i: None)

    # fully reveal the prompt so the choice list appears
    step_n(180)
    disabled_count = sum(1 for _lbl, en in choices if not en)
    assert disabled_count == 1, "expected exactly one disabled choice"
    assert len(box.choice_caps) == len(choices), "all choices should render"
    ok2 = mcrfpy.automation.screenshot(os.path.join(SHOTS, "uikit_2.png"))
    assert ok2, "screenshot 2 failed"

    box.destroy()
    menu.destroy()

    print("uikit_1.png:", os.path.join(SHOTS, "uikit_1.png"), flush=True)
    print("uikit_2.png:", os.path.join(SHOTS, "uikit_2.png"), flush=True)
    print("PASS test_ui_kit", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
