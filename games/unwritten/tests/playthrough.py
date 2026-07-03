"""UNWRITTEN - scripted full playthrough. Owner: Agent D.

THE proof that the three acts wire into one game. Runs headless, deterministic,
driving the REAL systems end to end:
  - the REAL dialogue runner (choices selected by index via
    dialogue.select_choice / dialogue.advance)
  - the REAL battle loop (gw_bats won through the actual command MenuList +
    target-picker via key injection; bosses won through BattleScreen's autopilot
    seam, which drives the same _commit/_resolve path the menu uses, using real
    Talk options)
  - REAL area transitions (overworld.enter_area via the goto_area hook / ferry
    dialogue), the REAL shop and party menu, the REAL epilogue.

Twenty story beats, each screenshotted to tests/shots/pt_NN_<beat>.png and each
followed by GS-state assertions. Prints a beat-by-beat PASS log with the running
Story-Point total. Exits 0 only on a full clean run.

Run:
  cd build && ./mcrogueface --headless --exec ../games/unwritten/tests/playthrough.py
"""
import os
import sys
import random

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import mcrfpy
from mcrfpy import automation

import main
from systems.state import GS
from systems import dialogue, overworld, battle, epilogue, shop, party_menu
from data import characters as chardata

_SHOTS = os.path.join(_ROOT, "tests", "shots")
K = mcrfpy.Key
P = mcrfpy.InputState.PRESSED

_beat_no = [0]


# ------------------------------------------------------------------- utilities
def pump(n):
    for _ in range(n):
        mcrfpy.step(1.0 / 60.0)


def shot(name):
    os.makedirs(_SHOTS, exist_ok=True)
    automation.screenshot(os.path.join(_SHOTS, name))


def beat(title):
    _beat_no[0] += 1
    print("  [beat %02d] %s  |  points=%d gold=%d party=%s"
          % (_beat_no[0], title, GS.points, GS.gold, GS.party), flush=True)


def fail(msg):
    print("FAIL playthrough: %s" % msg, flush=True)
    sys.exit(1)


def need(cond, msg):
    if not cond:
        fail(msg)


# ---- dialogue driving (REAL runner) ----
def reveal():
    """Force the open dialogue's typewriter to complete so its text/choices are
    on screen for a screenshot (presentation only; progression does not need
    it)."""
    c = dialogue.CURRENT
    if c is not None and getattr(c, "box", None) is not None:
        try:
            if c.box._typing:
                c.box._skip()
        except Exception:
            pass
    pump(3)


def advance_to_choices(limit=40):
    for _ in range(limit):
        if dialogue.CURRENT is None:
            return False
        if dialogue.current_choice_labels() is not None:
            return True
        dialogue.advance()
        pump(2)
    return dialogue.current_choice_labels() is not None


def choose_label(substr):
    labels = dialogue.current_choice_labels()
    need(labels is not None, "choose_label(%r): no choice node open" % substr)
    for i, (lab, enabled) in enumerate(labels):
        if substr in lab:
            need(enabled, "choose_label(%r): choice is disabled" % substr)
            dialogue.select_choice(i)
            pump(2)
            return
    fail("choose_label(%r): not found in %r" % (substr, [l for l, _ in labels]))


def finish_dialogue(default=-1, guard=80):
    """Advance/auto-choose (last enabled by default) until the dialogue closes
    or transfers."""
    for _ in range(guard):
        if dialogue.CURRENT is None:
            return
        labels = dialogue.current_choice_labels()
        if labels:
            en = [i for i, (l, e) in enumerate(labels) if e]
            idx = en[default] if en else 0
            dialogue.select_choice(idx)
        else:
            dialogue.advance()
        pump(2)


def open_dialogue(scene_id):
    overworld.WORLD.run_dialogue(scene_id)
    pump(12)


# ---- battle driving ----
def _center_enemies(core):
    return core.alive_enemies()


def boss_policy(screen, actor):
    """Autopilot: fire an enabled boss Talk once, else heal a badly hurt ally,
    else an offensive skill / basic attack. Drives the REAL _commit path."""
    core = screen.core
    skills = chardata.learned_skills(actor.char_id, actor.cstate.level)
    allies = core.alive_party()
    enemies = core.alive_enemies()
    for o in core.boss_talk_options():
        if o["enabled"]:
            return {"type": "talk", "talk": o["id"]}
    hurt = [a for a in allies if a.hp < a.max_hp * 0.45]
    if hurt:
        tgt = min(hurt, key=lambda c: c.hp / float(c.max_hp))
        for s in skills:
            if s["special"] == "kindle" and actor.sp >= s["sp"]:
                return {"type": "skill", "skill": s, "target": tgt}
            if s["special"] == "tonic_toss" and actor.sp >= s["sp"] \
                    and tgt.char_id != "NYX":
                return {"type": "skill", "skill": s, "target": tgt}
        for iid in ("red_tonic", "bread"):
            if GS.inventory.get(iid, 0) > 0:
                return {"type": "item", "item": iid, "target": tgt}
    dmg = [s for s in skills if s["kind"] in ("phys", "magic")
           and actor.sp >= s["sp"]]
    if dmg and enemies and random.random() < 0.7:
        aoe = [s for s in dmg if s["target"] == "all_enemies"]
        s = random.choice(aoe) if (aoe and len(enemies) >= 2) else random.choice(dmg)
        tgt = min(enemies, key=lambda e: e.hp) if enemies else None
        return {"type": "skill", "skill": s, "target": tgt}
    if enemies:
        return {"type": "attack", "target": min(enemies, key=lambda e: e.hp)}
    return {"type": "guard"}


def battle_ui_win(scr, shot_name=None, max_iter=2000):
    """Drive a battle to victory through the ACTUAL on-screen command menu +
    target picker, by injecting keys (auto: Attack -> first target)."""
    shot_done = False
    for _ in range(max_iter):
        if scr._ended:
            break
        pump(3)
        if not shot_done and shot_name and scr.state == "command":
            shot(shot_name)
            shot_done = True
        if scr.stack.has("victory") or scr.stack.has("defeat"):
            scr.scene.on_key(K.ENTER, P)
            pump(3)
            continue
        if scr.stack.has("target"):
            scr.scene.on_key(K.ENTER, P)
            pump(2)
            continue
        if scr.stack.has("cmd"):
            scr.scene.on_key(K.ENTER, P)   # Attack is the first enabled row
            pump(2)
            continue
    if not shot_done and shot_name:
        shot(shot_name)


def battle_auto_win(scr, shot_name=None, max_iter=8000):
    """Drive a boss battle to victory via the autopilot seam (real command
    dispatch), dismissing the victory/defeat panels with a keypress. The
    autopilot is installed at battle creation via battle.DEFAULT_AUTOPILOT."""
    if scr._auto is None:
        scr.set_autopilot(boss_policy)
    shot_done = False
    for _ in range(max_iter):
        if scr._ended:
            break
        pump(3)
        if not shot_done and shot_name and scr.state in ("resolving", "command"):
            shot(shot_name)
            shot_done = True
        if scr.stack.has("victory") or scr.stack.has("defeat"):
            scr.scene.on_key(K.ENTER, P)
            pump(3)
            continue
    if not shot_done and shot_name:
        shot(shot_name)


def level_party_to(level):
    """Grant the whole roster enough XP to reach `level` and top everyone up.
    Stands in for the encounters a real player fights between story beats."""
    from systems.state import xp_for_level
    target = xp_for_level(level)
    for cs in GS.roster.values():
        if cs.xp < target:
            cs.add_xp(target - cs.xp)
        cs.full_heal()


# ===========================================================================
# the playthrough
# ===========================================================================
def run():
    random.seed(20260703)
    os.makedirs(_SHOTS, exist_ok=True)
    print("=== UNWRITTEN full playthrough ===", flush=True)

    # ------------------------------------------------------------ 1. TITLE
    main.build_title()
    title_scene = mcrfpy.current_scene
    pump(20)
    shot("pt_01_title.png")
    need(title_scene.name == "title", "title scene not active")
    beat("title screen")

    # ---------------------------------------- 2. intro dialogue mid-typewriter
    # press ENTER on the real title handler: starts a new game -> intro monologue
    title_scene.on_key(K.ENTER, P)
    pump(10)          # entrance + a few characters of the typewriter
    need(dialogue.CURRENT is not None, "intro dialogue did not start")
    need(dialogue.CURRENT.box._typing, "intro should be mid-typewriter")
    shot("pt_02_intro_typewriter.png")
    beat("intro monologue (mid-typewriter)")

    # advance the whole intro; its terminal 'end' hands off to the overworld
    finish_dialogue(guard=40)
    pump(30)          # enter_area("hollowbrook", "start")

    # ---------------------------------------------- 3. Hollowbrook, Act 1
    w = overworld.WORLD
    need(w is not None and w.area_id == "hollowbrook", "not in hollowbrook")
    need(abs(w.zoom - 2.0) < 1e-6 and abs(w.grid.zoom - 2.0) < 1e-6,
         "overworld must render at zoom 2.0 (got %r)" % w.grid.zoom)
    need(GS.act == 1 and GS.party == ["PIP"], "act1 start state wrong")
    pump(10)
    shot("pt_03_hollowbrook_act1.png")
    beat("Hollowbrook Act 1 (zoom 2)")

    # -------------------------------------------- 4. quill_first choice list
    open_dialogue("quill_first")
    need(advance_to_choices(), "quill_first reached no choice node")
    reveal()
    shot("pt_04_quill_choices.png")
    need(len(dialogue.current_choice_labels()) == 2, "quill choices missing")
    choose_label("What do YOU think")          # -> quill_confident (+1)
    need(advance_to_choices(), "quill_first second choice missing")
    choose_label("Did everyone wake up")       # -> asked_unwoken (+1)
    finish_dialogue()
    need(GS.has("quill_confident"), "quill_confident not set")
    need(GS.has("asked_unwoken"), "asked_unwoken not set")
    need(not w.frozen, "overworld should unfreeze after quill dialogue")
    beat("Quill: confident + asked about the unwoken")

    # ---------------------------------- 5. Bramble recruit + North Door opens
    open_dialogue("bramble_door")
    need(advance_to_choices(), "bramble_door reached no choices")
    choose_label("[OATH]")                     # graceful recruit
    finish_dialogue()
    pump(6)
    shot("pt_05_bramble_door_open.png")
    need("BRAMBLE" in GS.party, "Bramble not recruited")
    need(GS.has("bramble_joined") and GS.has("door_open"),
         "bramble_joined/door_open not set")
    beat("Ser Bramble joins; North Door opens (door_open)")

    # --------------------------------------- 6. shop dispute (side with Vera)
    open_dialogue("shop_dispute")
    need(advance_to_choices(), "shop_dispute reached no choices")
    reveal()
    shot("pt_06_shop_dispute.png")
    labels = dialogue.current_choice_labels()
    # [ALCHEMY] choice must be shown-but-disabled (no ALCHEMY in party)
    need(any(("ALCHEMY" in l and not e) for l, e in labels),
         "the [ALCHEMY] choice should be visible but locked")
    choose_label("Come with me and prove it")  # side with Vera
    finish_dialogue()
    need("VERA" in GS.party, "Vera not recruited")
    need(GS.has("vera_joined_early") and GS.has("griselda_grudge"),
         "vera_joined_early/griselda_grudge not set")
    beat("Shop dispute resolved siding with Vera")

    # ------------------------------------------- 7. Griselda's shop (buy bread)
    GS.gold = 80
    bread0 = GS.inventory.get("bread", 0)
    open_dialogue("griselda_shop")
    choose_label("see your wares")             # -> n_shop (text node)
    dialogue.advance()                         # fire its 'shop' action
    pump(10)
    need(shop._MENU is not None, "shop did not open")
    shot("pt_07_shop_open.png")
    gold0 = GS.gold
    shop._MENU._buy("bread")                   # real buy path
    need(GS.inventory.get("bread", 0) == bread0 + 1, "bread not bought")
    need(GS.gold < gold0, "cogs not spent on bread")
    shop._MENU._leave()
    pump(6)
    need(not w.frozen, "overworld should resume after leaving shop")
    beat("Griselda's shop open; bought Bread")

    # ------------------------------------------------------- 8. ferry ride node
    open_dialogue("odd_ferry_1")
    reveal()
    shot("pt_08_ferry.png")
    need(advance_to_choices(), "ferry reached no choices")
    choose_label("Take the ferry")             # req door_open (met)
    # advance to Odd's mid-ride question, answer it, ride triggers goto_area
    need(advance_to_choices(), "ferry ride question missing")
    choose_label("For the town")
    finish_dialogue()                          # n6 -> goto_area:gearwood
    pump(40)                                   # fade + enter_area(gearwood)
    beat("Ferry ride with Odd -> Gearwood")

    # --------------------------------------------- 9. Gearwood arrival banner
    w = overworld.WORLD
    need(w.area_id == "gearwood", "did not arrive in gearwood")
    pump(8)
    shot("pt_09_gearwood_arrival.png")
    beat("Gearwood arrival banner")

    # -------------------------------- 10. real battle vs gw_bats via UI loop
    level_party_to(3)                          # stand in for early encounters
    GS.current_area = "gearwood"
    won = {"v": False}
    scr = battle.start_battle("gw_bats", on_victory=lambda: won.__setitem__("v", True))
    battle_ui_win(scr, shot_name="pt_10_battle_gw_bats.png")
    need(scr.core.result == "victory", "gw_bats battle not won (%r)"
         % scr.core.result)
    need(won["v"], "gw_bats on_victory callback never fired")
    need(mcrfpy.current_scene is w.scene, "battle did not restore the overworld")
    beat("gw_bats battle WON through the command menu + target picker")

    # ------------------------------------ 11. Moth shrine (name 'small things')
    open_dialogue("moth_shrine")
    need(advance_to_choices(), "moth_shrine reached no choices")
    reveal()
    shot("pt_11_moth_shrine.png")
    choose_label("small things")               # moth_light_name_small
    finish_dialogue()
    need(GS.has("moth_light_name_small"), "moth light-name not recorded")
    need("MOTH" in GS.roster, "Moth not recruited")
    beat("Moth's light named for small things; Moth joins the roster")

    # -------------------- (bridge) open the shrine chest + descend the stair
    open_dialogue("shrine_chest")
    finish_dialogue()
    need(GS.has("shrine_chest_open") and GS.inventory.get("brass_key", 0) >= 1,
         "shrine chest did not yield the brass key")
    open_dialogue("gearwood_stair")
    need(advance_to_choices(), "stair reached no choices")
    choose_label("Unlock it with the brass key")
    finish_dialogue()                          # -> act 2, goto_area:undercroft
    pump(40)

    # ---------------------------------------------- 12. Undercroft with FOV
    w = overworld.WORLD
    need(w.area_id == "undercroft", "did not descend into the undercroft")
    need(w.fov is not None, "undercroft should build an FOV overlay")
    need(GS.act == 2, "act should be 2 in the undercroft")
    pump(10)
    shot("pt_12_undercroft_fov.png")
    beat("Undercroft with fog-of-war (FOV)")

    # --------------------------------------------- 13. Cantor wake (write CANTOR)
    open_dialogue("cantor_wake")
    need(advance_to_choices(), "cantor_wake reached no choices")
    reveal()
    shot("pt_13_cantor_wake.png")
    choose_label("Write CANTOR")
    finish_dialogue()
    need("CANTOR" in GS.roster, "Cantor not recruited")
    need(GS.has("cantor_joined"), "cantor_joined not set")
    beat("Cantor woken by writing his name")

    # ---------------------- 14. Gatekeeper boss WON incl. the [OATH] Talk option
    need("BRAMBLE" in GS.party, "Bramble must be active for the OATH talk")
    level_party_to(6)
    GS.grant("red_tonic", 3)
    GS.current_area = "undercroft"
    battle.DEFAULT_AUTOPILOT = boss_policy      # auto-drive the dialogue-started boss
    open_dialogue("gatekeeper_pre")
    need(advance_to_choices(), "gatekeeper_pre reached no choices")
    choose_label("going through")               # -> battle:boss_gatekeeper
    finish_dialogue()                           # advance n6 -> starts the battle
    pump(4)
    scr = _active_battle()
    need(scr is not None, "gatekeeper battle did not start")
    battle_auto_win(scr, shot_name="pt_14_gatekeeper_battle.png")
    battle.DEFAULT_AUTOPILOT = None
    need(scr.core.result == "victory", "gatekeeper not defeated (%r)"
         % scr.core.result)
    need(GS.has("gatekeeper_relieved"), "the [OATH] Talk option was not used")
    need(GS.has("gatekeeper_slain"), "gatekeeper_post did not run")
    beat("Gatekeeper WON using [OATH] Relieve; the vale reverts")

    # gatekeeper_post is now open on the overworld stack; it ends by fading to
    # the greyed Hollowbrook (act 3), which auto-runs the Bell #3 arrival scene.
    finish_dialogue()
    pump(45)

    # ---------------------------------------- 15. grey Hollowbrook (Bell #3)
    w = overworld.WORLD
    need(w.area_id == "hollowbrook" and GS.act == 3, "did not revert to hollowbrook")
    need(w._grey_factor() is not None, "grey wash should be active on arrival")
    need(dialogue.CURRENT is not None, "the Bell #3 arrival scene did not auto-run")
    reveal()
    shot("pt_15_grey_hollowbrook.png")
    finish_dialogue()
    need(GS.has("bell_3_done"), "bell_3 arrival did not complete")
    beat("Reverted Hollowbrook; Bell's apology (bell_3_done)")

    # -------------------------------- 16. one rewake (Quill) -> partial color
    full_wash = w._grey_factor()
    open_dialogue("rewake_quill")
    need(advance_to_choices(), "rewake_quill reached no choices")
    choose_label("What is a door FOR")          # req quill_confident
    finish_dialogue()
    pump(10)
    need(GS.has("rewoke_quill"), "rewoke_quill not set")
    eased = w._grey_factor()
    need(eased is not None and eased < full_wash - 0.1,
         "color should return as Quill rewakes (%.2f -> %.2f)" % (full_wash, eased))
    shot("pt_16_rewake_quill_partial.png")
    beat("Quill rewoken; color begins to return")

    # ---------------------- 17. all three rewoken + Nyx recruited at the plinth
    open_dialogue("rewake_griselda")
    need(advance_to_choices(), "rewake_griselda reached no choices")
    choose_label("put me in your LEDGER")       # req party VERA (active)
    finish_dialogue()                           # -> hold the line
    need(GS.has("rewoke_griselda"), "rewoke_griselda not set")

    open_dialogue("rewake_odd")
    need(advance_to_choices(), "rewake_odd reached no choices")
    choose_label("NEW route into his hand")     # press the fare
    need(advance_to_choices(), "rewake_odd follow-up choice missing")
    choose_label("I'll write you one")          # odd_promised (+1)
    finish_dialogue()
    need(GS.has("rewoke_odd") and GS.has("odd_promised"), "odd rewake incomplete")
    need(GS.has("town_rewoken"), "town_rewoken should set after all 3 rewakes")
    pump(10)

    # Nyx stands on the empty plinth now; we asked about the unwoken in beat 4
    open_dialogue("nyx_plinth")
    need(advance_to_choices(), "nyx_plinth reached no choices")
    choose_label("I've been looking for you")   # req asked_unwoken -> warm join
    finish_dialogue()
    need("NYX" in GS.roster and GS.has("nyx_joined"), "Nyx not recruited")
    pump(6)
    shot("pt_17_all_rewoken_nyx.png")
    beat("All three rewoken + Nyx joins at the plinth (town_rewoken)")

    # -------------------------------------------------- 18. Study arrival
    open_dialogue("odd_ferry_study")
    need(advance_to_choices(), "odd_ferry_study reached no choices")
    choose_label("pale channel to the Study")
    finish_dialogue()                           # goto_area:study
    pump(45)
    w = overworld.WORLD
    need(w.area_id == "study", "did not reach the Study")
    pump(8)
    shot("pt_18_study_arrival.png")
    beat("The Maker's Study (paper palette)")

    # ----- put the recommended team forward for the finale (REAL party swap) -
    pm = party_menu.open_menu(w.scene, w.stack, on_close=lambda: None)
    if "MOTH" not in GS.party:
        pm._do_swap("BRAMBLE", "MOTH")
    if "CANTOR" not in GS.party:
        pm._do_swap("VERA", "CANTOR")
    pm.destroy()
    pump(4)
    need("MOTH" in GS.party and "CANTOR" in GS.party,
         "party swap for the finale failed: %s" % GS.party)

    # --------------------- 19. Custodian boss WON using a Talk option
    need(GS.points >= 8, "need >= 8 Story Points for the finale talk options")
    level_party_to(8)
    GS.grant("red_tonic", 4)
    GS.grant("blue_draught", 3)
    GS.current_area = "study"
    battle.DEFAULT_AUTOPILOT = boss_policy
    open_dialogue("custodian_pre")
    need(advance_to_choices(), "custodian_pre reached no choices")
    choose_label("Pending isn't perfect")       # -> battle:boss_custodian
    finish_dialogue()
    pump(4)
    scr = _active_battle()
    need(scr is not None, "custodian battle did not start")
    battle_auto_win(scr, shot_name="pt_19_custodian_battle.png")
    battle.DEFAULT_AUTOPILOT = None
    need(scr.core.result == "victory", "custodian not defeated (%r)"
         % scr.core.result)
    need(len(scr.core.talk_used) >= 1, "no Talk option was used vs the Custodian")
    print("      custodian talk options used: %s"
          % sorted(scr.core.talk_used), flush=True)
    beat("Custodian WON using Talk (%s)" % ",".join(sorted(scr.core.talk_used)))

    # --------------------------------------- 20. epilogue + final WRITTEN card
    # custodian_post is open on the overworld stack; choose to read it the Book
    need(dialogue.CURRENT is not None, "custodian_post did not run")
    need(advance_to_choices(), "custodian_post reached no choices")
    choose_label("let it read")                 # req points >= 8
    finish_dialogue()                           # -> action epilogue
    pump(30)
    ep = epilogue.CURRENT
    need(ep is not None, "epilogue did not start")
    need(ep.pages, "epilogue collected no pages")
    shot("pt_20a_epilogue_page.png")
    # page through to the final card, injecting a keypress per page
    for _ in range(len(ep.pages) + 4):
        if ep.final:
            break
        ep.scene.on_key(K.ENTER, P)
        pump(20)
    need(ep.final, "epilogue never reached the final card")
    pump(120)                                   # stamp + WRITTEN thunk timers
    shot("pt_20b_written.png")
    need(GS.has("book_read_custodian"), "book_read_custodian not set")
    beat("Epilogue read; UNWRITTEN stamped WRITTEN")

    # ------------------------------------------------------------- summary
    print("", flush=True)
    print("=== PLAYTHROUGH COMPLETE ===", flush=True)
    print("Story Points: %d" % GS.points, flush=True)
    print("Roster: %s" % sorted(GS.roster), flush=True)
    print("Active party: %s" % GS.party, flush=True)
    key_flags = ["quill_confident", "asked_unwoken", "bramble_joined",
                 "door_open", "vera_joined_early", "griselda_grudge",
                 "moth_light_name_small", "moth_joined", "cantor_joined",
                 "gatekeeper_relieved", "gatekeeper_slain", "bell_3_done",
                 "rewoke_quill", "rewoke_griselda", "rewoke_odd", "odd_promised",
                 "town_rewoken", "nyx_joined", "book_read_custodian"]
    have = [f for f in key_flags if GS.has(f)]
    print("Flags set (%d/%d): %s" % (len(have), len(key_flags), have), flush=True)
    missing = [f for f in key_flags if not GS.has(f)]
    need(not missing, "expected story flags missing: %s" % missing)
    need(GS.points >= 12, "story points unexpectedly low: %d" % GS.points)
    need(len(GS.roster) == 6, "expected all 6 recruited, got %s" % sorted(GS.roster))
    print("PASS playthrough", flush=True)
    sys.exit(0)


def _active_battle():
    """The BattleScreen that start_battle just created is referenced by the
    dialogue hook only transiently; grab it via current_scene's owner."""
    return battle._LAST_SCREEN


if __name__ == "__main__":
    run()
