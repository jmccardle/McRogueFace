"""UNWRITTEN - overworld / menus / epilogue headless test. Owner: Agent C.

Run:
  cd build && ./mcrogueface --headless --exec ../games/unwritten/tests/test_overworld.py

Drives the overworld through its meaningful states and screenshots each:
  ow_hollowbrook  ow_dialogue  ow_undercroft  ow_grey  ow_grey_partial  ow_epilogue
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import mcrfpy
from mcrfpy import automation

import main
from systems.state import GS
from systems import overworld
from systems import epilogue
from systems import shop            # noqa: F401  (registers HOOKS["shop"])
from systems import party_menu      # noqa: F401  (registers HOOKS["swap_menu"])

_SHOTS = os.path.join(_ROOT, "tests", "shots")


def _shot(name):
    os.makedirs(_SHOTS, exist_ok=True)
    automation.screenshot(os.path.join(_SHOTS, name))
    print("  shot", name, flush=True)


def _pump(n):
    for _ in range(n):
        mcrfpy.step(1.0 / 60.0)


def main_test():
    # encounters have no data.enemies yet (Agent B, parallel): use a placeholder
    overworld.TEST_ENEMY_FALLBACK = 86

    # ---- 1. Hollowbrook, Act 1, fresh -------------------------------------
    main._preset_act1()
    overworld.enter_area("hollowbrook", "start")
    w = overworld.WORLD
    assert w is not None and w.area_id == "hollowbrook", "world not built"
    assert GS.current_area == "hollowbrook", "GS.current_area not set"
    # a few real movement steps
    for _ in range(3):
        w.try_step(0, -1)
        _pump(10)
    w.try_step(-1, 0)
    _pump(20)
    _shot("ow_hollowbrook.png")
    print("PASS hollowbrook build + movement", flush=True)

    # ---- 2. Bump SER BRAMBLE -> dialogue opens ----------------------------
    assert "BRAMBLE" in w.npc_entities, "Bramble NPC missing in Act 1"
    w.player.grid_pos = (11, 5)
    w.player.draw_pos = (11, 5)
    w.try_step(0, -1)                 # step up into Bramble at (11,4)
    assert w.frozen, "bumping an NPC should freeze movement (dialogue open)"
    _pump(40)                        # let the box slide up + typewriter run
    _shot("ow_dialogue.png")
    print("PASS bramble bump opens dialogue", flush=True)

    # ---- 3. Undercroft with FOV -------------------------------------------
    main._preset_act2()
    overworld.enter_area("undercroft", "enter")
    w2 = overworld.WORLD
    assert w2.fov is not None, "undercroft should build an FOV overlay"
    assert w2.grid.perspective is w2.player, "grid.perspective not the player"
    w2.try_step(1, 0)
    _pump(15)
    w2.try_step(0, 1)
    _pump(20)
    _shot("ow_undercroft.png")
    print("PASS undercroft FOV", flush=True)

    # ---- 4. Act 3 greyed Hollowbrook --------------------------------------
    main._preset_act3()
    assert not GS.has("rewoke_quill"), "preset should start with no rewakes"
    overworld.enter_area("hollowbrook", "from_ferry")
    w3 = overworld.WORLD
    assert w3._grey_factor() is not None, "grey wash should be active in Act 3"
    _pump(20)
    _shot("ow_grey.png")
    print("PASS grey town (full wash)", flush=True)

    # ---- 5. Two rewakes -> color returns ----------------------------------
    GS.add_flag("rewoke_quill")
    GS.add_flag("rewoke_griselda")
    overworld.refresh_area()
    f = w3._grey_factor()
    assert f is not None and abs(f - 0.24) < 0.01, "wash should ease to ~0.24"
    _pump(15)
    _shot("ow_grey_partial.png")
    print("PASS grey partial (color returning)", flush=True)

    # ---- 6. Epilogue page 1 -----------------------------------------------
    # a real Moth recruit always records a light-name; the act-3 preset omits it
    GS.add_flag("moth_light_name_small")
    ep = epilogue.start_epilogue()
    assert GS.has("nyx_missed"), "epilogue must set nyx_missed when Nyx absent"
    _pump(40)                        # 240ms schedule + fade-in
    assert ep.pages, "epilogue collected no pages"
    _shot("ow_epilogue.png")
    print("PASS epilogue renders", flush=True)

    print("PASS test_overworld", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main_test()
