"""UNWRITTEN - battle simulation + screenshots. Owner: Agent B.

Runs 225 scripted headless battles across every pack (both bosses included)
with a level-appropriate party and an auto command policy, asserting:
  - no exceptions,
  - victory is possible for every pack,
  - XP / gold / loot are actually granted,
then prints a balance report (win rate + avg rounds per pack) for Fable.

Finally builds the real BattleScreen and screenshots three states:
  battle_1.png  command menu open on a player turn vs gw_mixed
  battle_2.png  mid-action, floating damage number
  battle_3.png  victory panel

Run:
  cd build && ./mcrogueface --headless --exec ../games/unwritten/tests/test_battle_sim.py
"""
import os
import sys
import random

GAMEROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GAMEROOT)

import mcrfpy
from mcrfpy import automation

from systems.state import GS
from systems import battle
from systems.battle import BattleCore
from data import characters as chardata
from data import items as itemdata

SHOTS = os.path.join(GAMEROOT, "tests", "shots")


# ---------------------------------------------------------------- party setup
_WEAPON = {
    1: {"PIP": "knife", "BRAMBLE": "worn_cudgel", "MOTH": "wick_staff",
        "VERA": "wick_staff", "CANTOR": "worn_cudgel", "NYX": "knife"},
    3: {"PIP": "short_sword", "BRAMBLE": "short_sword", "MOTH": "wick_staff",
        "VERA": "wick_staff", "CANTOR": "short_sword", "NYX": "short_sword"},
    5: {"PIP": "twin_axe", "BRAMBLE": "broad_blade", "MOTH": "tide_rod",
        "VERA": "tide_rod", "CANTOR": "broad_blade", "NYX": "twin_axe"},
}
_TRINKET = {1: "river_stone", 3: "river_stone", 5: "waxed_charm"}


def _gear_tier(level):
    if level >= 5:
        return 5
    if level >= 3:
        return 3
    return 1


def setup(comp, level, points=0, act=1):
    GS.reset()
    GS.act = act
    GS.points = points
    tier = _gear_tier(level)
    for cid in comp:
        GS.recruit(cid, level)
        cs = GS.roster[cid]
        cs.weapon = _WEAPON[tier].get(cid)
        cs.trinket = _TRINKET[tier]
        cs.full_heal()
    GS.gold = 0
    GS.grant("bread", 5)
    GS.grant("red_tonic", 2)
    GS.grant("blue_draught", 2)
    GS.grant("bomb_flask", 1)
    GS.grant("chalk", 1)


# ---------------------------------------------------------------- auto policy
def policy(core, actor):
    skills = chardata.learned_skills(actor.char_id, actor.cstate.level)
    enemies = core.alive_enemies()
    allies = core.alive_party()

    # 1. heal a badly hurt ally
    hurt = [a for a in allies if a.hp < a.max_hp * 0.45]
    if hurt:
        tgt = min(hurt, key=lambda c: c.hp / float(c.max_hp))
        for s in skills:
            if s["special"] in ("kindle", "tonic_toss") and actor.sp >= s["sp"]:
                if s["special"] == "tonic_toss" and tgt.char_id == "NYX":
                    continue
                return {"type": "skill", "skill": s, "target": tgt}

    # 2. occasionally exercise a boss talk option
    if core.is_boss and random.random() < 0.35:
        opts = [o for o in core.boss_talk_options() if o["enabled"]]
        if opts:
            return {"type": "talk", "talk": opts[0]["id"]}

    # 3. occasionally set up buffs (exercise shieldwall / second shadow)
    for s in skills:
        if s["special"] == "shieldwall" and not core.party_guard_active \
                and actor.sp >= s["sp"] and random.random() < 0.25:
            return {"type": "skill", "skill": s, "target": None}
        if s["special"] == "second_shadow" and not actor.guaranteed_crit \
                and actor.sp >= s["sp"] and random.random() < 0.30:
            return {"type": "skill", "skill": s, "target": None}

    # 4. offensive skill (prefer AoE with multiple foes)
    dmg = [s for s in skills
           if s["kind"] in ("phys", "magic") and actor.sp >= s["sp"]]
    if dmg and random.random() < 0.6:
        aoe = [s for s in dmg if s["target"] == "all_enemies"]
        if aoe and len(enemies) >= 2:
            s = random.choice(aoe)
        else:
            s = random.choice(dmg)
        tgt = min(enemies, key=lambda e: e.hp) if enemies else None
        return {"type": "skill", "skill": s, "target": tgt}

    # 5. basic attack, focus the weakest enemy
    if enemies:
        return {"type": "attack", "target": min(enemies, key=lambda e: e.hp)}
    return {"type": "guard"}


# ---------------------------------------------------------------- one battle
def run_once(pack_id, comp, level, points=0, act=1):
    setup(comp, level, points, act)
    core = BattleCore(pack_id)
    core.begin_round()
    rounds = 1
    steps = 0
    while True:
        na = core.next_actor()
        if na is None:
            core.end_round()
            if core.check_end():
                break
            core.begin_round()
            rounds += 1
            if rounds > battle._MAX_ROUNDS:
                core.result = "defeat"
                break
            continue
        actor, forced = na
        if forced is not None:
            action = forced
        elif actor.side == "enemy":
            action = core.ai_action(actor)
        else:
            action = policy(core, actor)
        result = core.resolve(actor, action)
        if result["flee"]:
            core.result = "flee"
            break
        if core.check_end():
            break
        steps += 1
        if steps > 6000:
            core.result = "defeat"
            break

    xp = gold = 0
    drops = []
    if core.result == "victory":
        xp, gold, drops = core.collect_rewards()
        GS.xp_gain(xp)
        GS.add_gold(gold)
        for d in drops:
            GS.grant(d, 1)
    return core.result, rounds, xp, gold, drops


# ---------------------------------------------------------------- sim config
# pack_id -> (party comp, level, points, act, label for report)
SIM = [
    ("gw_bats",    (["PIP", "BRAMBLE", "MOTH"], 1, 0, 1)),
    ("gw_mixed",   (["PIP", "BRAMBLE", "MOTH"], 2, 0, 1)),
    ("gw_mixed2",  (["PIP", "BRAMBLE", "MOTH"], 2, 0, 1)),
    ("gw_scarabs", (["PIP", "BRAMBLE", "MOTH"], 2, 0, 1)),
    ("gw_slimes",  (["PIP", "BRAMBLE", "MOTH"], 1, 0, 1)),
    ("uc_bones",   (["PIP", "BRAMBLE", "CANTOR"], 3, 0, 2)),
    ("uc_bones2",  (["PIP", "BRAMBLE", "MOTH"], 4, 0, 2)),
    ("uc_chimes",  (["PIP", "CANTOR", "MOTH"], 4, 0, 2)),
    ("uc_echoes",  (["PIP", "BRAMBLE", "MOTH"], 3, 0, 2)),
    ("uc_mixed",   (["PIP", "CANTOR", "MOTH"], 4, 0, 2)),
    ("uc_mimic",   (["PIP", "BRAMBLE", "MOTH"], 4, 0, 2)),
    ("st_echoes",  (["PIP", "MOTH", "CANTOR"], 5, 0, 3)),
    ("st_echoes2", (["PIP", "MOTH", "CANTOR"], 6, 0, 3)),
    ("boss_gatekeeper", (["PIP", "BRAMBLE", "MOTH"], 5, 4, 2)),
    ("boss_custodian",  (["PIP", "MOTH", "CANTOR"], 7, 8, 3)),
]
TRIALS = 15


def run_sim():
    random.seed(20260703)
    report = []
    total_xp = total_gold = total_drops = 0
    total_battles = 0
    for pack_id, (comp, level, points, act) in SIM:
        wins = 0
        round_sum = 0
        win_rounds = 0
        for _ in range(TRIALS):
            res, rounds, xp, gold, drops = run_once(
                pack_id, comp, level, points, act)
            total_battles += 1
            total_xp += xp
            total_gold += gold
            total_drops += len(drops)
            round_sum += rounds
            if res == "victory":
                wins += 1
                win_rounds += rounds
        win_rate = 100.0 * wins / TRIALS
        avg_rounds = (win_rounds / wins) if wins else round_sum / TRIALS
        report.append((pack_id, level, win_rate, avg_rounds, wins))
    return report, total_battles, total_xp, total_gold, total_drops


def print_report(report, total_battles, total_xp, total_gold, total_drops):
    print("", flush=True)
    print("=" * 64, flush=True)
    print("UNWRITTEN - BATTLE BALANCE REPORT (%d battles, %d per pack)"
          % (total_battles, TRIALS), flush=True)
    print("=" * 64, flush=True)
    print("%-18s %3s %8s %10s" % ("pack", "Lv", "win%", "avg rounds"),
          flush=True)
    print("-" * 64, flush=True)
    for pack_id, level, wr, ar, wins in report:
        print("%-18s %3d %7.0f%% %10.1f" % (pack_id, level, wr, ar), flush=True)
    print("-" * 64, flush=True)
    print("totals: XP granted %d | cogs granted %d | drops %d"
          % (total_xp, total_gold, total_drops), flush=True)
    print("=" * 64, flush=True)


def assert_sim(report, total_xp, total_gold, total_drops):
    problems = []
    for pack_id, level, wr, ar, wins in report:
        if wins == 0:
            problems.append("pack %s never won (win rate 0%%)" % pack_id)
    if total_xp <= 0:
        problems.append("no XP was ever granted")
    if total_gold <= 0:
        problems.append("no gold was ever granted")
    if total_drops <= 0:
        problems.append("no loot drops occurred")
    if problems:
        for p in problems:
            print("FAIL: %s" % p, flush=True)
        return False
    return True


# ---------------------------------------------------------------- screenshots
def step(seconds):
    n = int(seconds / (1.0 / 60.0))
    for _ in range(max(1, n)):
        mcrfpy.step(1.0 / 60.0)


def take_screenshots():
    if not os.path.isdir(SHOTS):
        os.makedirs(SHOTS)
    random.seed(7)

    # --- shot 1: command menu open vs gw_mixed ---
    setup(["PIP", "BRAMBLE", "MOTH"], 2)
    GS.current_area = "gearwood"
    screen = battle.start_battle("gw_mixed")
    tries = 0
    while screen.state != "command" and tries < 400:
        step(0.05)
        tries += 1
    step(0.05)
    automation.screenshot(os.path.join(SHOTS, "battle_1.png"))
    print("shot 1 (command menu, state=%s) saved" % screen.state, flush=True)

    # --- shot 2: mid-action floating damage ---
    actor = screen.cur_actor
    target = screen.core.alive_enemies()[0]
    if actor is not None and actor.side == "party":
        screen._commit(actor, {"type": "attack", "target": target})
    step(0.15)
    automation.screenshot(os.path.join(SHOTS, "battle_2.png"))
    print("shot 2 (mid-action) saved", flush=True)

    # --- shot 3: victory panel ---
    for e in screen.core.enemies:
        e.hp = 0
    screen.core.result = "victory"
    screen._on_battle_end()
    step(0.1)
    automation.screenshot(os.path.join(SHOTS, "battle_3.png"))
    print("shot 3 (victory panel) saved", flush=True)
    screen._teardown()


# ---------------------------------------------------------------- main
def main():
    report, total_battles, total_xp, total_gold, total_drops = run_sim()
    print_report(report, total_battles, total_xp, total_gold, total_drops)
    ok = assert_sim(report, total_xp, total_gold, total_drops)

    take_screenshots()

    if ok:
        print("PASS test_battle_sim", flush=True)
        sys.exit(0)
    else:
        print("FAIL test_battle_sim", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
