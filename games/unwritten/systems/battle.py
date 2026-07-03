"""UNWRITTEN - turn engine + battle screen. Owner: Agent B.

Public surface:
    start_battle(pack_id, on_victory=None, on_defeat=None)

Two layers, deliberately separable so the tests can run thousands of fights
with no UI:
    BattleCore   - pure mechanics (SYSTEMS sections 2-4, BIBLE section 4 bosses).
                   Touches no mcrfpy objects. Combatant.view is set by the screen
                   but never read by the core.
    BattleScreen - the 1024x768 presentation that drives a BattleCore turn by
                   turn, animating each result the core hands back.

Registers systems.dialogue.HOOKS["battle"] = start_battle at import.
ASCII only. "Fail early": unknown packs/skills/items raise.
"""
import random

import mcrfpy
from core import palette, ui, tween, assets
from core.inputstack import InputStack
from systems.state import GS
from data import characters as chardata
from data import items as itemdata
from data import enemies as enemydata
from data.barks import BARKS
from data.maps import BATTLE_BACKDROPS


# =============================================================================
# constants / layout
# =============================================================================
FLOOR_Y = 430
SCREEN_W = 1024
SCREEN_H = 768

# enemy sprite-center x positions by count (left half of the screen)
_ENEMY_SLOTS = {
    1: [300],
    2: [180, 400],
    3: [130, 300, 470],
}
# extra slots used when the Custodian / Gatekeeper summon reinforcements
_SUMMON_SLOTS = [120, 470, 60, 520, 240]

_MAX_ROUNDS = 60   # safety valve for the headless simulator


# =============================================================================
# barks
# =============================================================================
class Barker:
    """Picks a battle bark line, never repeating the immediately previous one."""

    def __init__(self):
        self.last = None

    def line(self, char_id, event):
        opts = BARKS.get(char_id, {}).get(event)
        if not opts:
            return None
        pool = [o for o in opts if o != self.last] or list(opts)
        pick = random.choice(pool)
        self.last = pick
        return pick


# =============================================================================
# combatant
# =============================================================================
class Combatant:
    def __init__(self, side, key, name, base, max_hp, max_sp, labels,
                 crit_base, sprite_index, tex, scale, ai,
                 char_id=None, enemy_id=None, cstate=None):
        self.side = side               # "party" | "enemy"
        self.key = key
        self.name = name
        self.base = dict(base)         # ATK/MAG/DEF/SPD (and HP/SP nominal)
        self._max_hp = int(max_hp)
        self._max_sp = int(max_sp)
        self.labels = set(labels or ())
        self.crit_base = crit_base
        self.sprite_index = sprite_index
        self.tex = tex
        self.scale = scale
        self.ai = ai
        self.char_id = char_id
        self.enemy_id = enemy_id
        self.cstate = cstate

        self._hp = cstate.hp if cstate is not None else int(max_hp)
        self._sp = cstate.sp if cstate is not None else int(max_sp)

        self.mods = []                 # [{"stat","add","mult","turns","tag"}]
        self.guarding = False
        self.stun_turns = 0
        self.redact_turns = 0
        self.guaranteed_crit = False
        self.picked = set()            # pickpocket: enemy keys already robbed
        self.ai_counter = 0
        self.view = None               # BattleScreen sets/reads its own dict

    # ---- pools -------------------------------------------------------------
    @property
    def max_hp(self):
        return self._max_hp

    @property
    def max_sp(self):
        return self._max_sp

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, v):
        self._hp = max(0, min(int(v), self._max_hp))
        if self.cstate is not None:
            self.cstate.hp = self._hp

    @property
    def sp(self):
        return self._sp

    @sp.setter
    def sp(self, v):
        self._sp = max(0, min(int(v), self._max_sp))
        if self.cstate is not None:
            self.cstate.sp = self._sp

    @property
    def alive(self):
        return self._hp > 0

    # ---- effective stats ---------------------------------------------------
    def stat(self, k):
        v = self.base.get(k, 0)
        add = 0
        mult = 1.0
        for m in self.mods:
            if m["stat"] == k:
                add += m.get("add", 0)
                mult += m.get("mult", 0.0)
        return max(0, int(round((v + add) * mult)))

    def add_mod(self, stat, mult=0.0, add=0, turns=None, tag=None):
        self.mods.append({"stat": stat, "mult": mult, "add": add,
                          "turns": turns, "tag": tag})

    def remove_mods_tagged(self, tag):
        self.mods = [m for m in self.mods if m.get("tag") != tag]

    def clear_debuffs(self):
        self.mods = [m for m in self.mods if m.get("mult", 0.0) >= 0
                     and m.get("add", 0) >= 0]


# =============================================================================
# battle core (pure logic)
# =============================================================================
class BattleCore:
    def __init__(self, pack_id):
        self.pack_id = pack_id
        self.is_boss = pack_id.startswith("boss_")
        self.log = []
        self.round = 0
        self.order = []
        self.turn_index = 0
        self.deferred = []
        self.result = None             # "victory" | "defeat" | "flee"

        # shieldwall
        self.party_guard_active = False
        self.party_guard_owner = None

        # boss state
        self.gk_inhale = False
        self.cust_phase2 = False
        self.cust_skip_next = False
        self.revert_disabled = False
        self.talk_used = set()

        # custodian revert bookkeeping
        self.actions_last_round = set()
        self.actions_this_round = set()
        self.cust_damage_this_round = 0

        self.stolen_gold = 0
        self._used_slots = []
        self._initial_pack = len(enemydata.pack(pack_id))

        self.party = self._build_party()
        self.enemies = self._build_enemies()

    # ---- construction ------------------------------------------------------
    def _build_party(self):
        out = []
        for cid in GS.party[:3]:
            cs = GS.roster.get(cid)
            if cs is None:
                raise KeyError("party member %r has no CharState" % (cid,))
            st = cs.stats()
            out.append(Combatant(
                "party", "p_" + cid, cid, st, cs.max_hp, cs.max_sp,
                labels=(), crit_base=chardata.CRIT_BASE.get(cid, 0.06),
                sprite_index=chardata.CHAR_SPRITES[cid], tex=None,
                scale=2.5, ai=None, char_id=cid, cstate=cs))
        if not out:
            raise RuntimeError("cannot start battle with an empty party")
        return out

    def _make_enemy(self, enemy_id, idx):
        rec = enemydata.enemy(enemy_id)
        c = Combatant(
            "enemy", "e%d_%s" % (idx, enemy_id), rec["name"],
            {"ATK": rec["ATK"], "MAG": rec["MAG"], "DEF": rec["DEF"],
             "SPD": rec["SPD"]},
            rec["HP"], 0, labels=rec["labels"], crit_base=0.04,
            sprite_index=rec["sprite"], tex=rec["tex"], scale=rec["scale"],
            ai=rec["ai"], enemy_id=enemy_id)
        c.reward_xp = rec["XP"]
        c.reward_gold = rec["gold"]
        c.drop = rec["drop"]
        return c

    def _build_enemies(self):
        out = []
        ids = enemydata.pack(self.pack_id)
        for i, eid in enumerate(ids):
            c = self._make_enemy(eid, i)
            out.append(c)
            if eid == "gatekeeper":
                c.add_mod("DEF", add=5, turns=None, tag="ward")  # the Ward
        self._enemy_seq = len(ids)
        return out

    def _spawn_enemy(self, enemy_id, result):
        c = self._make_enemy(enemy_id, self._enemy_seq)
        self._enemy_seq += 1
        self.enemies.append(c)
        result["fx"].append({"kind": "summon", "target": c})
        return c

    # ---- roster helpers ----------------------------------------------------
    def all(self):
        return self.party + self.enemies

    def alive_party(self):
        return [c for c in self.party if c.alive]

    def alive_enemies(self):
        return [c for c in self.enemies if c.alive]

    def opponents(self, actor):
        return self.alive_enemies() if actor.side == "party" else self.alive_party()

    def allies(self, actor):
        return self.alive_party() if actor.side == "party" else self.alive_enemies()

    def _rand(self, lst):
        return random.choice(lst) if lst else None

    def _find_enemy(self, enemy_id):
        for e in self.enemies:
            if e.enemy_id == enemy_id:
                return e
        return None

    def _active_boss(self):
        if self.pack_id == "boss_gatekeeper":
            return self._find_enemy("gatekeeper")
        if self.pack_id == "boss_custodian":
            return self._find_enemy("custodian")
        return None

    # ---- round flow --------------------------------------------------------
    def begin_round(self):
        self.round += 1
        self.actions_last_round = self.actions_this_round
        self.actions_this_round = set()
        self.cust_damage_this_round = 0
        if self.party_guard_owner is not None and not self.party_guard_owner.alive:
            self.party_guard_active = False
            self.party_guard_owner = None
        alive = [c for c in self.all() if c.alive]
        alive.sort(key=lambda c: (-c.stat("SPD"), random.random()))
        self.order = alive
        self.turn_index = 0

    def next_actor(self):
        """Return (actor, forced_action) or None when the round is exhausted.
        forced_action is None for a normal turn, {"type":"skip"} when stunned,
        or a stored action for a deferred (Bass Drop) resolution."""
        while self.turn_index < len(self.order):
            c = self.order[self.turn_index]
            self.turn_index += 1
            if not c.alive:
                continue
            skip = self._turn_start(c)
            if skip:
                return (c, {"type": "skip", "reason": skip})
            return (c, None)
        while self.deferred:
            c, act = self.deferred.pop(0)
            if c.alive:
                return (c, act)
        return None

    def _turn_start(self, c):
        c.guarding = False
        if self.party_guard_owner is c:
            self.party_guard_active = False
            self.party_guard_owner = None
        if c.stun_turns > 0:
            c.stun_turns -= 1
            return "stun"
        if c.enemy_id == "custodian" and self.cust_skip_next:
            self.cust_skip_next = False
            return "book"
        return None

    def end_round(self):
        """Custodian Revert + duration ticks. Returns a result-like dict."""
        result = {"actor": None, "log": [], "fx": []}
        self._custodian_revert(result)
        for c in self.all():
            self._tick_durations(c)
        return result

    def _tick_durations(self, c):
        keep = []
        for m in c.mods:
            if m.get("turns") is None:
                keep.append(m)
            else:
                m["turns"] -= 1
                if m["turns"] > 0:
                    keep.append(m)
        c.mods = keep

    # ---- end detection -----------------------------------------------------
    def check_end(self):
        if not self.alive_enemies():
            self.result = "victory"
            return True
        if not self.alive_party():
            self.result = "defeat"
            return True
        return False

    # =====================================================================
    # action resolution
    # =====================================================================
    def resolve(self, actor, action):
        result = {"actor": actor, "log": [], "fx": [], "deferred": False,
                  "bark": None, "flee": False, "swap": None, "end_turn": True}
        t = action.get("type")
        if t == "skip":
            if action.get("reason") == "book":
                pass  # the talk option already narrated the skip
            elif action.get("reason") == "stun":
                result["log"].append("%s cannot move." % actor.name)
            else:
                result["log"].append("%s flutters past." % actor.name)
        elif t == "attack":
            self._do_attack(actor, action, result)
        elif t == "skill":
            self._do_skill(actor, action, result)
        elif t == "item":
            self._do_item(actor, action, result)
        elif t == "guard":
            self._do_guard(actor, result)
        elif t == "eweb":
            self._do_eweb(actor, action, result)
        elif t == "swap":
            self._do_swap(actor, action, result)
        elif t == "talk":
            self._do_talk(actor, action, result)
        elif t == "flee":
            self._do_flee(actor, result)
        elif t == "boss":
            self._do_boss_move(actor, action, result)
        else:
            raise ValueError("unknown battle action type %r" % (t,))

        # custodian revert bookkeeping: record party action tokens
        if actor.side == "party" and not result["deferred"]:
            tok = self._action_token(t, action)
            if tok:
                self.actions_this_round.add(tok)

        self._maybe_phase2(result)

        # end-of-turn duration bookkeeping for the actor
        if not result["deferred"]:
            if actor.redact_turns > 0:
                actor.redact_turns -= 1
        return result

    def _action_token(self, t, action):
        if t == "attack":
            return "attack"
        if t == "skill":
            return "skill:" + action["skill"]["id"]
        if t == "item":
            return "item:" + action["item"]
        if t == "guard":
            return "guard"
        return None

    # ---- damage primitives -------------------------------------------------
    def _strike(self, attacker, target, mult, magical, crit_chance, result,
                force_crit=False):
        if not target.alive:
            return 0
        # Nyx evasion (incoming)
        if target.char_id == "NYX" and random.random() < chardata.NYX_EVASION:
            result["fx"].append({"kind": "miss", "target": target})
            result["log"].append("Nyx is not where the blow lands.")
            return 0
        # Nyx guaranteed-crit consumption
        if attacker.char_id == "NYX" and attacker.guaranteed_crit:
            force_crit = True
            attacker.guaranteed_crit = False
        atk = attacker.stat("MAG" if magical else "ATK")
        dfn = target.stat("DEF")
        if magical:
            dfn = dfn // 2
        var = random.uniform(0.85, 1.15)
        dmg = max(1, int(round((atk * mult - dfn) * var)))
        crit = force_crit or (random.random() < crit_chance)
        if crit:
            dmg = int(round(dmg * 1.5))
        # guard + shieldwall mitigation
        if target.guarding:
            dmg = max(1, dmg // 2)
        if target.side == "party" and self.party_guard_active:
            dmg = max(1, dmg // 2)
        target.hp = target.hp - dmg
        result["fx"].append({"kind": "hit", "target": target, "amount": dmg,
                             "crit": crit, "magical": magical})
        if attacker.side == "party" and target.enemy_id == "custodian":
            self.cust_damage_this_round += dmg
        if not target.alive:
            result["fx"].append({"kind": "death", "target": target})
            # Hedge Slime splits once at death in packs of <= 2 (SYSTEMS section 4)
            if (target.enemy_id == "hedge_slime"
                    and self._initial_pack <= 2
                    and not getattr(target, "_split_done", False)):
                target._split_done = True
                self._spawn_enemy("slimelet", result)
                result["log"].append("The Hedge Slime splits.")
        return dmg

    def _heal(self, target, amount, result):
        amount = int(amount)
        before = target.hp
        target.hp = target.hp + amount
        gained = target.hp - before
        result["fx"].append({"kind": "heal", "target": target, "amount": gained})
        return gained

    # ---- basic attack ------------------------------------------------------
    def _do_attack(self, actor, action, result):
        target = action.get("target")
        if target is None or not target.alive:
            opp = self.opponents(actor)
            target = self._rand(opp)
        if target is None:
            return
        magical = action.get("magical", False)
        crit = actor.crit_base
        result["fx"].append({"kind": "lunge", "actor": actor, "target": target})
        self._strike(actor, target, 1.0, magical, crit, result)

    # ---- skills ------------------------------------------------------------
    def _do_skill(self, actor, action, result):
        skill = action["skill"]
        special = skill["special"]

        # Bass Drop defers to the end of the round the first time it is chosen.
        if special == "bass_drop" and not action.get("_deferred"):
            actor.sp = actor.sp - skill["sp"]
            self.deferred.append((actor, dict(action, _deferred=True)))
            result["deferred"] = True
            result["log"].append("Cantor holds the note. It will land last.")
            return

        if not action.get("_deferred"):
            actor.sp = actor.sp - skill["sp"]

        if actor.side == "party":
            evt = "skill_a" if skill["unlock"] == 1 else "skill_b"
            result["bark"] = (actor.char_id, evt)

        if special == "twinstrike":
            target = self._pick_enemy_target(actor, action)
            result["fx"].append({"kind": "lunge", "actor": actor, "target": target})
            for _ in range(skill["hits"]):
                if target.alive:
                    self._strike(actor, target, skill["mult"], False,
                                 actor.crit_base, result)
        elif special == "pickpocket":
            target = self._pick_enemy_target(actor, action)
            result["fx"].append({"kind": "lunge", "actor": actor, "target": target})
            self._strike(actor, target, skill["mult"], False, actor.crit_base,
                         result)
            if target.key not in actor.picked and target.alive:
                actor.picked.add(target.key)
                loot = random.randint(8, 20)
                self.stolen_gold += loot
                GS.add_gold(loot)
                result["log"].append("Pip lifts %d cogs." % loot)
        elif special == "shieldwall":
            self.party_guard_active = True
            self.party_guard_owner = actor
            result["log"].append("Bramble braces. The party takes half damage.")
        elif special == "vow_strike":
            target = self._pick_enemy_target(actor, action)
            missing = 1.0 - (actor.hp / float(actor.max_hp))
            mult = min(2.0, 1.0 + 0.1 * int(missing * 10))
            result["fx"].append({"kind": "lunge", "actor": actor, "target": target})
            self._strike(actor, target, mult, False, actor.crit_base, result)
        elif special == "kindle":
            target = action.get("target") or self._lowest_ally(actor)
            amt = 24 + 2 * actor.stat("MAG")
            self._heal(target, amt, result)
            result["log"].append("Moth kindles %s." % target.name)
        elif special == "moonflare":
            for e in self.alive_enemies():
                self._strike(actor, e, skill["mult"], True, actor.crit_base,
                             result)
            result["fx"].append({"kind": "shake"})
        elif special == "acid_flask":
            for e in self.alive_enemies():
                self._strike(actor, e, skill["mult"], True, actor.crit_base,
                             result)
                d = skill["debuff"]
                e.add_mod(d["stat"], mult=d["mult"], turns=d["turns"], tag="acid")
                result["fx"].append({"kind": "debuff", "target": e})
        elif special == "tonic_toss":
            target = action.get("target") or self._lowest_ally(actor)
            if target.char_id == "NYX":
                result["log"].append("The tonic passes through her.")
            else:
                amt = 16 + actor.stat("MAG")
                target.clear_debuffs()
                self._heal(target, amt, result)
                result["log"].append("Vera tosses a tonic to %s." % target.name)
        elif special == "resonate":
            target = self._pick_enemy_target(actor, action)
            result["fx"].append({"kind": "lunge", "actor": actor, "target": target})
            self._strike(actor, target, skill["mult"], True, actor.crit_base,
                         result)
            if target.alive and target.labels & {"construct", "undead"}:
                target.stun_turns = max(target.stun_turns, 1)
                result["log"].append("%s is stunned by the chord." % target.name)
        elif special == "bass_drop":
            target = self._pick_enemy_target(actor, action)
            result["fx"].append({"kind": "lunge", "actor": actor, "target": target})
            self._strike(actor, target, skill["mult"], False, actor.crit_base,
                         result)
            result["fx"].append({"kind": "shake"})
        elif special == "grave_chill":
            target = self._pick_enemy_target(actor, action)
            self._strike(actor, target, skill["mult"], True, actor.crit_base,
                         result)
            if target.alive:
                d = skill["debuff"]
                target.add_mod(d["stat"], mult=d["mult"], turns=d["turns"],
                               tag="chill")
                result["fx"].append({"kind": "debuff", "target": target})
        elif special == "second_shadow":
            actor.guaranteed_crit = True
            result["log"].append("Nyx steps into her own shadow.")
        else:
            raise ValueError("unhandled skill special %r" % (special,))

    def _pick_enemy_target(self, actor, action):
        target = action.get("target")
        if target is None or not target.alive:
            target = self._rand(self.opponents(actor))
        return target

    def _lowest_ally(self, actor):
        allies = self.allies(actor)
        return min(allies, key=lambda c: c.hp / float(c.max_hp)) if allies else actor

    # ---- items -------------------------------------------------------------
    def _do_item(self, actor, action, result):
        iid = action["item"]
        rec = itemdata.item(iid)
        eff = rec["effect"]
        target = action.get("target")

        if eff == "aoe_damage":
            GS.take(iid, 1)
            for e in self.alive_enemies():
                dmg = max(1, rec["amount"])
                if e.guarding:
                    dmg = max(1, dmg // 2)
                e.hp = e.hp - dmg
                result["fx"].append({"kind": "hit", "target": e, "amount": dmg,
                                     "crit": False, "magical": True})
                if e.enemy_id == "custodian":
                    self.cust_damage_this_round += dmg
                if not e.alive:
                    result["fx"].append({"kind": "death", "target": e})
            result["fx"].append({"kind": "shake"})
            result["log"].append("%s throws a Bomb Flask." % actor.name)
            return

        if target is None:
            target = self._lowest_ally(actor)

        # Nyx cannot be restored by items (HP-restoring effects only).
        if target.char_id == "NYX" and eff in ("heal", "cleanse_heal", "revive"):
            result["log"].append("The tonic passes through her.")
            return

        GS.take(iid, 1)
        if eff == "heal":
            self._heal(target, rec["amount"], result)
            result["log"].append("%s uses %s." % (actor.name, rec["name"]))
        elif eff == "sp":
            target.sp = target.sp + rec["amount"]
            result["fx"].append({"kind": "sp", "target": target,
                                 "amount": rec["amount"]})
            result["log"].append("%s restores SP with %s." % (actor.name, rec["name"]))
        elif eff == "cleanse_heal":
            target.clear_debuffs()
            self._heal(target, rec["amount"], result)
            result["log"].append("%s uses %s." % (actor.name, rec["name"]))
        elif eff == "revive":
            if target.alive:
                result["log"].append("%s is already standing." % target.name)
            else:
                target.hp = int(target.max_hp * rec["amount"])
                result["fx"].append({"kind": "revive", "target": target})
                result["log"].append("%s is written back with Chalk." % target.name)
        else:
            raise ValueError("unhandled item effect %r" % (eff,))

    # ---- guard / swap / eweb ----------------------------------------------
    def _do_guard(self, actor, result):
        actor.guarding = True
        actor.sp = actor.sp + 2
        result["fx"].append({"kind": "guard", "target": actor})
        result["log"].append("%s guards." % actor.name)

    def _do_eweb(self, actor, action, result):
        target = action.get("target") or self._rand(self.alive_party())
        if target is None:
            return
        target.add_mod("SPD", mult=-0.30, turns=2, tag="web")
        result["fx"].append({"kind": "debuff", "target": target})
        result["log"].append("The Loom Spider webs %s. It slows." % target.name)

    def _do_swap(self, actor, action, result):
        new_id = action["swap_to"]
        cs = GS.roster.get(new_id)
        if cs is None:
            raise KeyError("cannot swap to %r: not in roster" % (new_id,))
        st = cs.stats()
        newc = Combatant(
            "party", "p_" + new_id, new_id, st, cs.max_hp, cs.max_sp,
            labels=(), crit_base=chardata.CRIT_BASE.get(new_id, 0.06),
            sprite_index=chardata.CHAR_SPRITES[new_id], tex=None,
            scale=2.5, ai=None, char_id=new_id, cstate=cs)
        idx = self.party.index(actor)
        self.party[idx] = newc
        # update the active party ordering in GS
        if actor.char_id in GS.party:
            gi = GS.party.index(actor.char_id)
            GS.party[gi] = new_id
        result["swap"] = (actor, newc)
        result["log"].append("%s steps back; %s steps in." % (actor.name, newc.name))

    def _do_flee(self, actor, result):
        if self.is_boss:
            result["log"].append("There is no fleeing this.")
            return
        if random.random() < 0.70:
            result["flee"] = True
            result["log"].append("The party slips away.")
        else:
            result["log"].append("Couldn't get away!")

    # =====================================================================
    # enemy / boss AI
    # =====================================================================
    def ai_action(self, actor):
        ai = actor.ai
        if ai == "gatekeeper":
            return self._gk_action(actor)
        if ai == "custodian":
            return self._cust_action(actor)
        if ai == "bat" and random.random() < 0.25:
            return {"type": "skip", "reason": "flutter"}
        if ai == "scarab" and actor.hp < actor.max_hp * 0.5:
            return {"type": "guard"}
        if ai == "spider":
            actor.ai_counter += 1
            if actor.ai_counter % 3 == 0:
                return {"type": "eweb", "target": self._rand(self.alive_party())}
        magical = (ai == "echo")
        return {"type": "attack", "target": self._rand(self.alive_party()),
                "magical": magical}

    def _gk_action(self, actor):
        if self.gk_inhale:
            self.gk_inhale = False
            return {"type": "boss", "move": "toll"}
        alive_imps = [e for e in self.enemies
                      if e.enemy_id == "chime_imp" and e.alive]
        if len(alive_imps) < 2 and random.random() < 0.45:
            return {"type": "boss", "move": "summon"}
        r = random.random()
        if r < 0.35:
            self.gk_inhale = True
            return {"type": "boss", "move": "inhale"}
        return {"type": "boss", "move": "stone_stare"}

    def _cust_action(self, actor):
        r = random.random()
        if r < 0.45:
            return {"type": "boss", "move": "sweep"}
        if r < 0.75:
            return {"type": "boss", "move": "redact"}
        if actor.hp < actor.max_hp:
            return {"type": "boss", "move": "polish"}
        return {"type": "boss", "move": "sweep"}

    def _do_boss_move(self, actor, action, result):
        move = action["move"]
        if move == "stone_stare":
            target = self._rand(self.alive_party())
            if target:
                result["fx"].append({"kind": "lunge", "actor": actor,
                                     "target": target})
                self._strike(actor, target, 1.6, False, 0.05, result)
                result["log"].append(
                    "The Gatekeeper's stare files %s under HURT." % target.name)
        elif move == "toll":
            result["log"].append("THE TOLL. The whole room rings.")
            for p in self.alive_party():
                self._strike(actor, p, 1.2, False, 0.03, result)
            result["fx"].append({"kind": "shake"})
        elif move == "inhale":
            result["log"].append("The Gatekeeper inhales.")
        elif move == "summon":
            self._spawn_enemy("chime_imp", result)
            result["log"].append("The Gatekeeper summons a Chime-Imp to its side.")
        elif move == "sweep":
            result["log"].append(
                "The Custodian sweeps. Everything is briefly, painfully, neat.")
            for p in self.alive_party():
                self._strike(actor, p, 1.0, True, 0.03, result)
            result["fx"].append({"kind": "shake"})
        elif move == "redact":
            candidates = [p for p in self.alive_party() if p.redact_turns == 0]
            target = self._rand(candidates or self.alive_party())
            if target:
                target.redact_turns = 2
                result["fx"].append({"kind": "debuff", "target": target})
                result["log"].append(
                    "%s is Redacted. 'You are simpler now.'" % target.name)
        elif move == "polish":
            self._heal(actor, 12, result)
            result["log"].append(
                "The Custodian polishes itself. Small scratches vanish.")
        else:
            raise ValueError("unknown boss move %r" % (move,))

    # =====================================================================
    # boss reactions
    # =====================================================================
    def _maybe_phase2(self, result):
        cust = self._find_enemy("custodian")
        if (cust is None or not cust.alive or self.cust_phase2
                or cust.hp > cust.max_hp * 0.5):
            return
        self.cust_phase2 = True
        result["log"].append(
            "The Custodian opens. Inside: filed silence. Bell is summoned to "
            "its side - and a grey echo of Pip.")
        self._spawn_enemy("bell", result)
        self._spawn_enemy("grey_echo", result)

    def _custodian_revert(self, result):
        cust = self._find_enemy("custodian")
        if (cust is None or not cust.alive or not self.cust_phase2
                or self.revert_disabled):
            return
        if self.cust_damage_this_round <= 0:
            return
        new_types = self.actions_this_round - self.actions_last_round
        if new_types:
            result["log"].append(
                "The Custodian reaches to smooth the page - and hesitates. "
                "It has never seen THAT before.")
        else:
            healed = self.cust_damage_this_round
            cust.hp = cust.hp + healed
            result["fx"].append({"kind": "heal", "target": cust, "amount": healed})
            result["log"].append(
                "The Custodian smooths the page flat. What happened, un-happens.")

    # =====================================================================
    # boss talk options
    # =====================================================================
    def boss_talk_options(self):
        """List of {"id","label","enabled","reason"} for the active boss, or []."""
        boss = self._active_boss()
        if boss is None or not boss.alive:
            return []
        opts = []
        if boss.enemy_id == "gatekeeper":
            if "oath_relieve" not in self.talk_used:
                en = GS.in_party("BRAMBLE")
                opts.append(("oath_relieve",
                             "[OATH] Relieve the Gatekeeper of its post",
                             en, "" if en else "needs Bramble"))
        elif boss.enemy_id == "custodian":
            if "liturgy_name" not in self.talk_used:
                en = GS.in_party("MOTH")
                opts.append(("liturgy_name",
                             "[LITURGY] Name the light at it",
                             en, "" if en else "needs Moth"))
            if "resonance_bell" not in self.talk_used:
                bell = self._find_enemy("bell")
                en = (GS.in_party("CANTOR") and GS.points >= 6
                      and self.cust_phase2 and bell is not None and bell.alive)
                opts.append(("resonance_bell",
                             "[RESONANCE] Ring Bell backward",
                             en, "" if en else "needs Cantor, 6 pts, Bell"))
            if "book_open" not in self.talk_used:
                en = GS.points >= 8
                opts.append(("book_open",
                             "Hold up the Book, open",
                             en, "" if en else "needs 8 points"))
        return [{"id": o[0], "label": o[1], "enabled": o[2], "reason": o[3]}
                for o in opts]

    def _do_talk(self, actor, action, result):
        tid = action["talk"]
        self.talk_used.add(tid)
        if tid == "oath_relieve":
            gk = self._find_enemy("gatekeeper")
            if gk:
                gk.remove_mods_tagged("ward")
            GS.add_flag("gatekeeper_relieved")
            GS.add_points(1)
            result["log"].append(
                "Bramble: By the order that posted you: your watch is "
                "COMPLETE. Stand down, soldier.")
            result["log"].append(
                "The Gatekeeper's Ward crumbles. Its face, for the first "
                "time, rests.")
        elif tid == "liturgy_name":
            cust = self._find_enemy("custodian")
            if cust:
                cust.add_mod("MAG", mult=-0.30, turns=None, tag="liturgy")
            result["log"].append(
                "Moth names the light. The Custodian's edges blur, as if "
                "embarrassed.")
        elif tid == "resonance_bell":
            bell = self._find_enemy("bell")
            if bell and bell.alive:
                bell.hp = 0
                result["fx"].append({"kind": "death", "target": bell})
            self.revert_disabled = True
            GS.add_flag("bell_defected")
            GS.add_points(1)
            result["log"].append(
                "Bell rings BACKWARD. The note un-announces the Custodian. "
                "'I have SUCH a backlog,' Bell says, and stands with YOU.")
        elif tid == "book_open":
            self.cust_skip_next = True
            result["log"].append(
                "You hold up the Book, open. The Custodian reads. Margins do "
                "not usually get to read.")
        else:
            raise ValueError("unknown talk option %r" % (tid,))

    # =====================================================================
    # rewards
    # =====================================================================
    def collect_rewards(self):
        xp = 0
        gold = 0
        drops = []
        for e in self.enemies:
            if e.alive:
                continue
            xp += getattr(e, "reward_xp", 0)
            gold += getattr(e, "reward_gold", 0)
            drop = getattr(e, "drop", None)
            if drop and random.random() < drop[1]:
                drops.append(drop[0])
        return xp, gold, drops


# =============================================================================
# battle screen (presentation)
# =============================================================================
VICTORY_SCENES = {
    "uc_mimic": "mimic_post",
    "boss_gatekeeper": "gatekeeper_post",
    "boss_custodian": "custodian_post",
}

_CMD = ["Attack", "Skill", "Item", "Guard", "Talk", "Swap", "Flee"]


class BattleScreen:
    def __init__(self, pack_id, prev_scene, on_victory=None, on_defeat=None):
        self.core = BattleCore(pack_id)
        self.pack_id = pack_id
        self.prev_scene = prev_scene
        self.on_victory = on_victory
        self.on_defeat = on_defeat
        self.barker = Barker()

        self.area = getattr(GS, "current_area", "hollowbrook")
        if self.area not in BATTLE_BACKDROPS:
            self.area = "hollowbrook"

        self.timers = []
        self.log_lines = []
        self.menus = []            # live modal widgets to destroy on teardown
        self.state = "boot"
        self.cur_actor = None
        self.cur_forced = None
        self._ended = False
        self._auto = None          # test seam: policy(screen, actor)->action dict

        self.scene = mcrfpy.Scene("battle")
        self.ch = self.scene.children
        mcrfpy.current_scene = self.scene
        self.stack = InputStack(self.scene)

        self._build_backdrop()
        self._build_enemies()
        self._build_party_cards()
        self._build_ribbon()
        self._build_log_panel()

        # kick off
        self.core.begin_round()
        self._schedule(self._advance, 350)

    # ---- timer helper ------------------------------------------------------
    def _schedule(self, fn, ms):
        name = "bat_%d" % (len(self.timers) + random.randint(0, 1 << 20))

        def cb(timer, runtime):
            timer.stop()
            if self._ended and fn not in (self._teardown,):
                return
            fn()
        t = mcrfpy.Timer(name, cb, ms)
        self.timers.append(t)
        return t

    def _stop_timers(self):
        for t in self.timers:
            try:
                t.stop()
            except Exception:
                pass
        self.timers = []

    # =====================================================================
    # scene construction
    # =====================================================================
    def _build_backdrop(self):
        bands = BATTLE_BACKDROPS[self.area]
        band_h = SCREEN_H / len(bands)
        for i, col in enumerate(bands):
            f = mcrfpy.Frame(pos=(0, int(i * band_h)),
                             size=(SCREEN_W, int(band_h) + 1),
                             fill_color=palette.C(col))
            f.z_index = -100
            self.ch.append(f)
        floor = mcrfpy.Frame(pos=(0, FLOOR_Y), size=(SCREEN_W, 3),
                             fill_color=palette.C((20, 20, 26)))
        floor.z_index = -90
        self.ch.append(floor)

    def _enemy_base_x(self, n):
        return list(_ENEMY_SLOTS.get(n, _ENEMY_SLOTS[3]))

    def _build_enemies(self):
        n = len(self.core.enemies)
        xs = self._enemy_base_x(n)
        self.core._used_slots = list(xs)
        for i, e in enumerate(self.core.enemies):
            cx = xs[i] if i < len(xs) else _SUMMON_SLOTS[i % len(_SUMMON_SLOTS)]
            self._make_enemy_view(e, cx)

    def _make_enemy_view(self, e, cx):
        tex = e.tex if e.tex is not None else assets.TEX
        px = int(cx - 8 * e.scale)
        top = int(FLOOR_Y - 16 * e.scale)
        halos = []
        if e.enemy_id == "custodian":
            halos = self._custodian_halos(cx, top + int(8 * e.scale))
        spr = mcrfpy.Sprite(pos=(px, top), texture=tex,
                            sprite_index=e.sprite_index)
        spr.scale = e.scale
        spr.z_index = 10
        self.ch.append(spr)
        name = ui.Label(self.ch, e.name, (cx, top - 30), color=palette.PARCH,
                        size=palette.SMALL_SIZE, center=True, outline=1)
        bar = ui.Bar(self.ch, (int(cx - 42), top - 16), (84, 10),
                     palette.BLOOD, e.hp, e.max_hp, show_text=False)
        e.view = {"sprite": spr, "name": name, "bar": bar, "cx": cx,
                  "halos": halos}

    def _custodian_halos(self, cx, cy):
        out = []
        for i, r in enumerate((90, 64)):
            h = mcrfpy.Frame(pos=(int(cx - r), int(cy - r)), size=(2 * r, 2 * r),
                             fill_color=palette.C((0, 0, 0, 0)),
                             outline=3, outline_color=palette.C(palette.GOLD_T, 150))
            h.origin = (r, r)
            h.z_index = 5
            self.ch.append(h)
            h.animate("rotation", 360.0, 9.0 + 3 * i, mcrfpy.Easing.LINEAR,
                      loop=True)
            out.append(h)
        return out

    def _build_party_cards(self):
        self.card_y = [84, 246, 408]
        for i in range(3):
            self._make_card(i)
        self._refresh_cards()

    def _make_card(self, i):
        if i >= len(self.core.party):
            self.core.__dict__.setdefault("_cardslots", None)
        y = self.card_y[i]
        panel = ui.Panel(self.ch, (724, y), (284, 150))
        return panel

    def _refresh_cards(self):
        # rebuild party card contents from scratch (simple + robust)
        if hasattr(self, "_cards"):
            for c in self._cards:
                c.destroy()
        self._cards = []
        for i in range(3):
            y = self.card_y[i]
            outline = palette.GOLD if (i < len(self.core.party) and
                                       self.core.party[i] is self.cur_actor) \
                else palette.OUTLINE
            panel = ui.Panel(self.ch, (724, y), (284, 150),
                             outline_color=outline)
            self._cards.append(panel)
            if i >= len(self.core.party):
                ui.Label(panel.children, "(empty)", (142, 70),
                         color=palette.DIM, size=palette.SMALL_SIZE, center=True)
                continue
            c = self.core.party[i]
            chip = mcrfpy.Frame(pos=(12, 12), size=(56, 56),
                                fill_color=palette.INSET, outline=2,
                                outline_color=palette.OUTLINE)
            panel.children.append(chip)
            tex = assets.TEX
            spr = mcrfpy.Sprite(pos=(8, 8), texture=tex,
                                sprite_index=c.sprite_index)
            spr.scale = 2.5
            chip.children.append(spr)
            ui.Label(panel.children, c.name, (80, 14), color=palette.PARCH,
                     size=palette.NAME_SIZE)
            ui.Label(panel.children, "Lv %d" % (c.cstate.level if c.cstate else 1),
                     (228, 14), color=palette.GOLD, size=palette.SMALL_SIZE)
            hp = ui.Bar(panel.children, (80, 46), (192, 18), palette.BLOOD,
                        c.hp, c.max_hp)
            sp = ui.Bar(panel.children, (80, 70), (192, 16), palette.TEAL,
                        c.sp, c.max_sp)
            status = ""
            if not c.alive:
                status = "DOWN"
            elif c.redact_turns > 0:
                status = "Redacted"
            elif c.guarding:
                status = "Guarding"
            ui.Label(panel.children, status, (12, 118), color=palette.DIM,
                     size=palette.SMALL_SIZE)
            c.view = {"panel": panel, "hp": hp, "sp": sp, "spr": spr}

    def _build_ribbon(self):
        self.ribbon_frame = mcrfpy.Frame(pos=(16, 8), size=(690, 52),
                                         fill_color=palette.C(palette.PANEL_T, 180),
                                         outline=2, outline_color=palette.OUTLINE)
        self.ribbon_frame.z_index = 2000
        self.ch.append(self.ribbon_frame)
        self.ribbon_chips = []
        self._refresh_ribbon()

    def _refresh_ribbon(self):
        for c in self.ribbon_chips:
            try:
                self.ribbon_frame.children.remove(c)
            except Exception:
                pass
        self.ribbon_chips = []
        order = self.core.order if self.core.order else \
            sorted([c for c in self.core.all() if c.alive],
                   key=lambda c: -c.stat("SPD"))
        x = 8
        tex = assets.TEX
        for c in order:
            if not c.alive:
                continue
            hot = (c is self.cur_actor)
            chip = mcrfpy.Frame(pos=(x, 6), size=(40, 40),
                                fill_color=palette.INSET, outline=2,
                                outline_color=palette.GOLD if hot else palette.OUTLINE)
            self.ribbon_frame.children.append(chip)
            self.ribbon_chips.append(chip)
            t = c.tex if (c.side == "enemy" and c.tex is not None) else tex
            spr = mcrfpy.Sprite(pos=(4, 4), texture=t, sprite_index=c.sprite_index)
            spr.scale = 2.0
            chip.children.append(spr)
            x += 46
            if x > 660:
                break

    def _build_log_panel(self):
        self.log_panel = ui.Panel(self.ch, (16, 500), (690, 52))
        self.log_caps = []
        for i in range(3):
            cap = ui.Label(self.log_panel.children, "", (12, 6 + i * 15),
                           color=palette.DIM, size=palette.SMALL_SIZE)
            self.log_caps.append(cap)

    # ---- log ---------------------------------------------------------------
    def push_log(self, line):
        if not line:
            return
        self.log_lines.append(line)
        self.log_lines = self.log_lines[-3:]
        for i, cap in enumerate(self.log_caps):
            cap.text = self.log_lines[i] if i < len(self.log_lines) else ""

    # =====================================================================
    # turn loop
    # =====================================================================
    def _advance(self):
        if self._ended:
            return
        na = self.core.next_actor()
        if na is None:
            end_res = self.core.end_round()
            for ln in end_res["log"]:
                self.push_log(ln)
            self._play_fx(end_res["fx"])
            if self.core.check_end():
                self._schedule(self._on_battle_end, 500)
                return
            self.core.begin_round()
            self._refresh_ribbon()
            self._schedule(self._advance, 300)
            return
        self.cur_actor, self.cur_forced = na
        self._refresh_ribbon()
        self._refresh_cards()
        if self.cur_forced is not None:
            self._resolve(self.cur_actor, self.cur_forced)
        elif self.cur_actor.side == "enemy":
            action = self.core.ai_action(self.cur_actor)
            self._resolve(self.cur_actor, action)
        else:
            self._open_command_menu(self.cur_actor)

    def _resolve(self, actor, action):
        result = self.core.resolve(actor, action)
        for ln in result["log"]:
            self.push_log(ln)
        if result["bark"]:
            bl = self.barker.line(*result["bark"])
            if bl:
                self.push_log("%s: %s" % (result["bark"][0].title(), bl))
        if result["swap"]:
            self._refresh_cards()
        self._play_fx(result["fx"])
        if result["flee"]:
            self.core.result = "flee"
            self._schedule(self._on_battle_end, 400)
            return
        # low-HP barks
        for p in self.core.alive_party():
            if p.hp <= p.max_hp * 0.30 and not getattr(p, "_barked_low", False):
                p._barked_low = True
                bl = self.barker.line(p.char_id, "hurt_low")
                if bl:
                    self.push_log("%s: %s" % (p.char_id.title(), bl))
            elif p.hp > p.max_hp * 0.30:
                p._barked_low = False
        if self.core.check_end():
            self._schedule(self._on_battle_end, 550)
            return
        self._schedule(self._advance, 500)

    # ---- fx player ---------------------------------------------------------
    def _play_fx(self, fx):
        for e in fx:
            k = e["kind"]
            if k == "lunge":
                self._lunge(e["actor"], e["target"])
            elif k == "hit":
                self._show_hit(e["target"], e["amount"], e["crit"])
            elif k == "heal":
                self._show_heal(e["target"], e["amount"])
            elif k == "sp":
                self._update_target_bars(e["target"])
            elif k == "miss":
                self._float_over(e["target"], "miss", palette.DIM)
            elif k == "debuff":
                self._float_over(e["target"], "-", palette.TEAL)
            elif k == "guard":
                self._update_target_bars(e["target"])
            elif k == "death":
                self._death(e["target"])
            elif k == "revive":
                self._refresh_cards()
            elif k == "summon":
                self._summon_view(e["target"])
            elif k == "shake":
                self._screen_shake()
        self._update_all_bars()

    def _center_of(self, c):
        if c.side == "enemy" and c.view:
            top = int(FLOOR_Y - 16 * c.scale)
            return (c.view["cx"], top + int(8 * c.scale))
        if c.side == "party" and c.view:
            i = self.core.party.index(c) if c in self.core.party else 0
            return (760, self.card_y[i] + 40)
        return (300, 300)

    def _lunge(self, actor, target):
        if actor.side == "enemy" and actor.view:
            spr = actor.view["sprite"]
            ox = spr.x
            spr.animate("x", ox + 24, 0.12, mcrfpy.Easing.EASE_OUT,
                        callback=lambda *_a: spr.animate("x", ox, 0.12,
                                                         mcrfpy.Easing.EASE_IN))
        elif actor.side == "party" and actor.view:
            spr = actor.view["spr"]
            ox = spr.x
            spr.animate("x", ox - 24, 0.12, mcrfpy.Easing.EASE_OUT,
                        callback=lambda *_a: spr.animate("x", ox, 0.12,
                                                         mcrfpy.Easing.EASE_IN))

    def _show_hit(self, target, amount, crit):
        cx, cy = self._center_of(target)
        color = palette.PARCH if target.side == "enemy" else palette.BLOOD
        tween.float_text(self.ch, str(amount), (cx - 10, cy), color, size=24)
        if crit:
            tween.float_text(self.ch, "CRIT!", (cx - 20, cy - 26), palette.GOLD,
                             size=20)

    def _show_heal(self, target, amount):
        cx, cy = self._center_of(target)
        tween.float_text(self.ch, "+%d" % amount, (cx - 8, cy), palette.GRASS,
                         size=22)

    def _float_over(self, target, text, color):
        cx, cy = self._center_of(target)
        tween.float_text(self.ch, text, (cx, cy), color, size=18)

    def _death(self, target):
        if target.side == "enemy" and target.view:
            spr = target.view["sprite"]
            spr.animate("opacity", 0.0, 0.45, mcrfpy.Easing.EASE_IN)
            for key in ("name",):
                try:
                    self.ch.remove(target.view[key])
                except Exception:
                    pass
            target.view["bar"].destroy()

            def rm(*_a):
                try:
                    self.ch.remove(spr)
                except Exception:
                    pass
            self._schedule(rm, 480)
        else:
            self._refresh_cards()

    def _summon_view(self, e):
        cx = None
        used = getattr(self.core, "_used_slots", [])
        for s in _SUMMON_SLOTS:
            if s not in used:
                cx = s
                break
        if cx is None:
            cx = _SUMMON_SLOTS[len(used) % len(_SUMMON_SLOTS)]
        used.append(cx)
        self.core._used_slots = used
        self._make_enemy_view(e, cx)
        self._refresh_ribbon()

    def _screen_shake(self):
        pass  # backdrop is full-bleed; shake individual party cards instead
        for c in self.core.alive_party():
            if c.view:
                tween.shake(c.view["panel"].frame, mag=6, dur=0.25)

    def _update_target_bars(self, target):
        self._update_all_bars()

    def _update_all_bars(self):
        for e in self.core.enemies:
            if e.view and e.alive:
                e.view["bar"].set(e.hp, e.max_hp)
        for c in self.core.party:
            if c.view:
                c.view["hp"].set(c.hp, c.max_hp)
                c.view["sp"].set(c.sp, c.max_sp)

    # =====================================================================
    # command menu + submenus
    # =====================================================================
    def _clear_menus(self):
        for m in self.menus:
            try:
                m.destroy()
            except Exception:
                pass
        self.menus = []
        for nm in ("cmd", "sub", "target"):
            self.stack.pop(nm)
        if hasattr(self, "_picker") and self._picker:
            self._picker.destroy()
            self._picker = None

    def set_autopilot(self, policy):
        """Test seam: install policy(screen, actor)->action-dict. On each player
        turn the command is taken from the policy and driven through the REAL
        _commit/_resolve path instead of opening the on-screen command menu.
        Returning None falls through to the interactive menu."""
        self._auto = policy

    def _open_command_menu(self, actor):
        if self._auto is not None:
            action = self._auto(self, actor)
            if action is not None:
                self._commit(actor, action)
                return
        self._clear_menus()
        self.state = "command"
        has_skills = bool(chardata.learned_skills(actor.char_id,
                          actor.cstate.level)) and actor.redact_turns == 0
        has_items = any(itemdata.is_consumable(i) and n > 0
                        for i, n in GS.inventory.items())
        talk_opts = self.core.boss_talk_options() if self.core.is_boss else []
        bench = self._bench()
        items = [
            ("Attack", "attack", True, ""),
            ("Skill", "skill", has_skills,
             "redacted" if actor.redact_turns > 0 else "no SP/skills"),
            ("Item", "item", has_items, "none"),
            ("Guard", "guard", True, ""),
        ]
        if talk_opts:
            items.append(("Talk", "talk", True, ""))
        if bench:
            items.append(("Swap", "swap", True, ""))
        items.append(("Flee", "flee", not self.core.is_boss, "no escape"))
        menu = ui.MenuList(self.ch, (16, 560), 240, items,
                           on_pick=lambda v: self._cmd_pick(actor, v),
                           on_cancel=None, title=actor.name)
        self.menus.append(menu)
        self.stack.push(menu.handle, "cmd")

    def _bench(self):
        in_battle = {c.char_id for c in self.core.party}
        return [cid for cid in GS.roster
                if cid not in in_battle and GS.roster[cid].alive]

    def _cmd_pick(self, actor, v):
        if v == "attack":
            self._pick_target(actor, self.core.alive_enemies(),
                              lambda tgt: self._commit(actor,
                                  {"type": "attack", "target": tgt}))
        elif v == "guard":
            self._commit(actor, {"type": "guard"})
        elif v == "flee":
            self._commit(actor, {"type": "flee"})
        elif v == "skill":
            self._open_skill_menu(actor)
        elif v == "item":
            self._open_item_menu(actor)
        elif v == "talk":
            self._open_talk_menu(actor)
        elif v == "swap":
            self._open_swap_menu(actor)

    def _open_skill_menu(self, actor):
        self.stack.pop("cmd")
        skills = chardata.learned_skills(actor.char_id, actor.cstate.level)
        rows = []
        for s in skills:
            afford = actor.sp >= s["sp"]
            label = "%s (%d SP)" % (s["name"], s["sp"])
            rows.append((label, s, afford, "low SP"))
        menu = ui.MenuList(self.ch, (16, 470), 300, rows,
                           on_pick=lambda s: self._skill_chosen(actor, s),
                           on_cancel=lambda: self._back_to_command(actor),
                           title="Skill")
        self.menus.append(menu)
        self.stack.push(menu.handle, "sub")

    def _skill_chosen(self, actor, skill):
        tgt = skill["target"]
        if tgt == "enemy":
            self._pick_target(actor, self.core.alive_enemies(),
                              lambda t: self._commit(actor,
                                  {"type": "skill", "skill": skill, "target": t}))
        elif tgt == "ally":
            self._pick_target(actor, self.core.alive_party(),
                              lambda t: self._commit(actor,
                                  {"type": "skill", "skill": skill, "target": t}))
        else:  # all_enemies / party / self
            self._commit(actor, {"type": "skill", "skill": skill, "target": None})

    def _open_item_menu(self, actor):
        self.stack.pop("cmd")
        rows = []
        for iid, n in GS.inventory.items():
            if not itemdata.is_consumable(iid) or n <= 0:
                continue
            rec = itemdata.item(iid)
            rows.append(("%s x%d" % (rec["name"], n), iid, True, ""))
        if not rows:
            rows = [("(no items)", None, False, "")]
        menu = ui.MenuList(self.ch, (16, 470), 280, rows,
                           on_pick=lambda iid: self._item_chosen(actor, iid),
                           on_cancel=lambda: self._back_to_command(actor),
                           title="Item")
        self.menus.append(menu)
        self.stack.push(menu.handle, "sub")

    def _item_chosen(self, actor, iid):
        if iid is None:
            return
        rec = itemdata.item(iid)
        if rec["effect"] == "aoe_damage":
            self._commit(actor, {"type": "item", "item": iid, "target": None})
        else:
            self._pick_target(actor, self.core.party,   # allow reviving the downed
                              lambda t: self._commit(actor,
                                  {"type": "item", "item": iid, "target": t}))

    def _open_talk_menu(self, actor):
        self.stack.pop("cmd")
        opts = self.core.boss_talk_options()
        rows = [(o["label"], o["id"], o["enabled"], o["reason"]) for o in opts]
        menu = ui.MenuList(self.ch, (16, 430), 470, rows,
                           on_pick=lambda tid: self._commit(actor,
                               {"type": "talk", "talk": tid}),
                           on_cancel=lambda: self._back_to_command(actor),
                           title="Talk")
        self.menus.append(menu)
        self.stack.push(menu.handle, "sub")

    def _open_swap_menu(self, actor):
        self.stack.pop("cmd")
        bench = self._bench()
        rows = [(cid.title(), cid, True, "") for cid in bench]
        menu = ui.MenuList(self.ch, (16, 470), 240, rows,
                           on_pick=lambda cid: self._commit(actor,
                               {"type": "swap", "swap_to": cid}),
                           on_cancel=lambda: self._back_to_command(actor),
                           title="Swap in")
        self.menus.append(menu)
        self.stack.push(menu.handle, "sub")

    def _back_to_command(self, actor):
        self._clear_menus()
        self._open_command_menu(actor)

    # ---- target picker -----------------------------------------------------
    def _pick_target(self, actor, targets, on_done):
        targets = [t for t in targets if t.alive] or list(targets)
        if not targets:
            return
        self.stack.pop("sub")
        self.stack.pop("cmd")
        self._picker = _TargetPicker(self, targets, on_done,
                                     lambda: self._back_to_command(actor))
        self.stack.push(self._picker.handle, "target")

    def _commit(self, actor, action):
        self._clear_menus()
        self.state = "resolving"
        self._resolve(actor, action)

    # =====================================================================
    # end of battle
    # =====================================================================
    def _on_battle_end(self):
        self._clear_menus()
        res = self.core.result
        if res == "victory":
            self._victory()
        elif res == "flee":
            self._teardown_and_restore()
        else:
            self._defeat()

    def _victory(self):
        xp, gold, drops = self.core.collect_rewards()
        events = GS.xp_gain(xp)
        GS.add_gold(gold)
        for d in drops:
            GS.grant(d, 1)
        # panel
        self._clear_menus()
        panel = ui.Panel(self.ch, (312, 220), (400, 300),
                         outline_color=palette.GOLD, z_index=7000)
        self.menus.append(panel)
        ui.Label(panel.children, "VICTORY", (200, 30), color=palette.GOLD,
                 size=palette.BANNER_SIZE, center=True)
        y = 90
        ui.Label(panel.children, "XP  +%d" % xp, (40, y), color=palette.GRASS,
                 size=palette.BODY_SIZE)
        ui.Label(panel.children, "Cogs +%d" % gold, (40, y + 26),
                 color=palette.GOLD, size=palette.BODY_SIZE)
        yy = y + 56
        for d in drops:
            ui.Label(panel.children, "Found %s" % itemdata.item(d)["name"],
                     (40, yy), color=palette.PARCH, size=palette.SMALL_SIZE)
            yy += 22
        for cid, lvl in events:
            ui.Toast(self.ch, "%s reached Lv %d" % (cid.title(), lvl),
                     color=palette.GRASS)
            if lvl == 4:
                ui.Toast(self.ch, "%s: Skill learned!" % cid.title(),
                         color=palette.GOLD)
        ui.Label(panel.children, "press ENTER", (200, 262), color=palette.DIM,
                 size=palette.SMALL_SIZE, center=True)
        self.stack.clear()
        self.stack.push(self._victory_key, "victory")

    def _victory_key(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return True
        if key in (mcrfpy.Key.ENTER, mcrfpy.Key.SPACE):
            self._finish_victory()
        return True

    def _finish_victory(self):
        self._teardown()
        if self.prev_scene is not None:
            mcrfpy.current_scene = self.prev_scene
        if self.pack_id in VICTORY_SCENES:
            self._run_return_scene(VICTORY_SCENES[self.pack_id])
        elif self.on_victory:
            self.on_victory()

    def _run_return_scene(self, scene_id):
        """Run a post-battle dialogue on the restored scene. If we returned to
        the live overworld, reuse ITS input stack - creating a fresh InputStack
        would reassign scene.on_key and orphan overworld movement - and keep the
        overworld frozen for the scene's duration."""
        from systems import dialogue, overworld
        w = overworld.WORLD
        if w is not None and self.prev_scene is w.scene:
            w.frozen = True
            w.held = []

            def _after():
                if overworld.WORLD is w:
                    w.frozen = False
                    w.refresh_theme()
                    w.refresh_hud()
            dialogue.run_scene(scene_id, on_done=_after, stack=w.stack)
        else:
            dialogue.run_scene(scene_id)

    def _defeat(self):
        self._clear_menus()
        cover = mcrfpy.Frame(pos=(0, 0), size=(SCREEN_W, SCREEN_H),
                             fill_color=palette.C(palette.INK_T, 0))
        cover.z_index = 8000
        self.ch.append(cover)
        cover.animate("opacity", 1.0, 0.6, mcrfpy.Easing.EASE_IN_OUT)
        panel = ui.Panel(self.ch, (262, 300), (500, 160),
                         outline_color=palette.BLOOD, z_index=8100)
        self.menus.append(panel)
        ui.Label(panel.children, "The vale goes back to waiting.", (250, 60),
                 color=palette.PARCH, size=palette.BODY_SIZE, center=True)
        ui.Label(panel.children, "press ENTER", (250, 120), color=palette.DIM,
                 size=palette.SMALL_SIZE, center=True)
        self.stack.clear()
        self.stack.push(self._defeat_key, "defeat")

    def _defeat_key(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return True
        if key in (mcrfpy.Key.ENTER, mcrfpy.Key.SPACE):
            self._teardown()
            if self.on_defeat:
                self.on_defeat()
            else:
                import main
                main.build_title()
        return True

    def _teardown_and_restore(self):
        self._teardown()
        if self.prev_scene is not None:
            mcrfpy.current_scene = self.prev_scene

    def _teardown(self):
        self._ended = True
        self._stop_timers()
        self._clear_menus()
        self.stack.clear()


# =============================================================================
# target picker (modal reticle over a candidate target)
# =============================================================================
class _TargetPicker:
    """A modal input handler pushed on the battle InputStack while the player
    chooses a target. Left/Right (or W/S/A/D) cycle candidates, Enter/Space
    confirm (on_done(target)), Esc cancels (on_cancel()). Draws a gold reticle
    over the current candidate. This was referenced by BattleScreen._pick_target
    but never defined - implemented here (Agent D integration)."""

    def __init__(self, screen, targets, on_done, on_cancel):
        self.screen = screen
        self.targets = [t for t in targets if t.alive] or list(targets)
        self.on_done = on_done
        self.on_cancel = on_cancel
        self.idx = 0
        self.reticle = mcrfpy.Frame(pos=(0, 0), size=(10, 10),
                                    fill_color=palette.C((0, 0, 0, 0)),
                                    outline=3, outline_color=palette.GOLD)
        self.reticle.z_index = 6800
        screen.ch.append(self.reticle)
        self._place()

    def _place(self):
        if not self.targets:
            return
        t = self.targets[self.idx]
        cx, cy = self.screen._center_of(t)
        if t.side == "enemy":
            half = int(10 * getattr(t, "scale", 4.0))
        else:
            half = 90
        self.reticle.w = 2 * half
        self.reticle.h = 2 * half
        self.reticle.x = int(cx - half)
        self.reticle.y = int(cy - half)

    def _cycle(self, delta):
        alive = [t for t in self.targets if t.alive]
        if not alive:
            return
        # keep idx pointing at a live target, then step
        cur = self.targets[self.idx] if self.idx < len(self.targets) else None
        if cur not in alive:
            self.targets = alive
            self.idx = 0
        else:
            self.targets = alive
            self.idx = self.targets.index(cur)
        self.idx = (self.idx + delta) % len(self.targets)
        self._place()

    def handle(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return True
        K = mcrfpy.Key
        if key in (K.A, K.LEFT, K.W, K.UP):
            self._cycle(-1)
            return True
        if key in (K.D, K.RIGHT, K.S, K.DOWN):
            self._cycle(1)
            return True
        if key in (K.ENTER, K.SPACE):
            alive = [t for t in self.targets if t.alive]
            if alive:
                tgt = self.targets[self.idx] if self.targets[self.idx].alive \
                    else alive[0]
                self.on_done(tgt)
            return True
        if key == K.ESCAPE:
            if self.on_cancel:
                self.on_cancel()
            return True
        return True

    def destroy(self):
        try:
            self.screen.ch.remove(self.reticle)
        except Exception:
            pass


# =============================================================================
# public entry + hook registration
# =============================================================================
# The most recently created BattleScreen (test seam: a scripted playthrough
# needs a handle on a battle that a dialogue action started internally, since
# the dialogue runner discards start_battle's return value).
_LAST_SCREEN = None

# Test seam: if set, every battle is created with this autopilot already
# installed, so a battle a *dialogue* action starts internally is auto-driven
# from turn one (there is no chance to call set_autopilot before its first
# player turn opens the command menu). None in normal play.
DEFAULT_AUTOPILOT = None


def start_battle(pack_id, on_victory=None, on_defeat=None):
    """Build a battle scene for `pack_id`, run it, restore the previous scene
    on completion. Returns the BattleScreen (mostly useful for tests)."""
    global _LAST_SCREEN
    prev = mcrfpy.current_scene
    _LAST_SCREEN = BattleScreen(pack_id, prev, on_victory, on_defeat)
    if DEFAULT_AUTOPILOT is not None:
        _LAST_SCREEN.set_autopilot(DEFAULT_AUTOPILOT)
    return _LAST_SCREEN


# register the dialogue hook (dialogue calls HOOKS["battle"](pack_id))
from systems import dialogue as _dialogue
_dialogue.HOOKS["battle"] = start_battle
