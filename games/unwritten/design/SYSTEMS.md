# UNWRITTEN — Systems Spec (numbers are canon)

Playtime target: 30–45 minutes. Grind is abbreviated by design: XP is generous,
maps are small, encounters are visible (bump to fight, avoidable), and every
number below is tuned for "one sitting, slightly under-leveled feels tense but
fair."

## 1. Stats & leveling

Stats: `HP, SP, ATK, MAG, DEF, SPD`. Levels 1–8. XP to next level = `20 * level`
(cumulative table: 20/60/120/200/300/420/560). Whole party (all 6, benched
included) gains full XP — swapping is never punished.

Per-character base (level 1) and per-level growth:

| Char    | HP  | SP | ATK | MAG | DEF | SPD | growth (per level)            |
|---------|-----|----|-----|-----|-----|-----|-------------------------------|
| PIP     | 34  | 10 | 7   | 3   | 4   | 9   | +6 HP +2 SP +2 ATK +1 DEF +1 SPD |
| BRAMBLE | 46  | 8  | 6   | 2   | 7   | 4   | +9 HP +1 SP +1 ATK +2 DEF     |
| MOTH    | 28  | 16 | 3   | 8   | 3   | 6   | +4 HP +4 SP +2 MAG +1 DEF +1 SPD (alt levels) |
| VERA    | 31  | 12 | 5   | 6   | 4   | 6   | +5 HP +3 SP +1 ATK +1 MAG +1 DEF +1 SPD (alt) |
| CANTOR  | 40  | 12 | 8   | 6   | 6   | 2   | +7 HP +2 SP +2 ATK +1 MAG +1 DEF |
| NYX     | 22  | 12 | 9   | 5   | 2   | 10  | +3 HP +3 SP +3 ATK +1 SPD     |

("alt levels": the +1s marked (alt) apply on even levels only. Keep it simple in
code: a per-char list of 7 growth dicts is fine.)

NYX joins at the party's average level; everyone else joins at their scene's
scripted level (Bramble 1, Moth 2, Vera 2, Cantor 4).

## 2. Damage model

- Physical: `dmg = max(1, round((ATK * mult - DEF) * var))`, `var` uniform in
  [0.85, 1.15].
- Magical: same with MAG and `DEF//2`.
- Crit: chance per skill (base 6%, NYX base 18%), crit = dmg * 1.5, gold flash.
- Guard: incoming dmg halved until next turn, +2 SP on guarding.
- Turn order: sort by SPD desc, ties random, recomputed each round. Shown as a
  portrait ribbon top of battle screen.

## 3. Skills (unlock L1 unless noted; SP cost in parens)

| Char | Skill A | Skill B (unlocks L4) |
|------|---------|----------------------|
| PIP | **Twinstrike** (3): two hits at 0.7x each | **Pickpocket** (2): 0.6x dmg + steal bonus gold (8-20), once per enemy |
| BRAMBLE | **Shieldwall** (3): party takes half dmg until his next turn | **Vow Strike** (4): mult 1.0 + 0.1 per 10% HP Bramble is missing (max 2.0) |
| MOTH | **Kindle** (4): heal one ally `24 + 2*MAG`; works on NYX | **Moonflare** (6): AoE magic 1.1x |
| VERA | **Acid Flask** (4): AoE 0.7x + DEF -25% (2 turns) | **Tonic Toss** (3): heal one `16 + MAG` and clear debuffs (NOT Nyx) |
| CANTOR | **Resonate** (4): 1.2x magic; vs construct/undead also stun 1 turn | **Bass Drop** (7): single 2.2x, acts last that round |
| NYX | **Grave Chill** (3): 1.0x magic + SPD -30% (2 turns) | **Second Shadow** (5): her next attack this battle is a guaranteed crit; using it does not end her evasion |

NYX passive: 20% evasion. NYX cannot be healed by items (silently blocked with
battle log line "The tonic passes through her."); Kindle and shrine rest work.

## 4. Enemies

`hue` = hsl_shift degrees applied to the base sprite for area variants.

| Enemy | Sprite | HP | ATK | MAG | DEF | SPD | XP | Gold | Notes |
|-------|--------|----|-----|-----|-----|-----|----|------|-------|
| Gloom Bat | 120 | 14 | 5 | 0 | 1 | 8 | 6 | 4 | 25% chance to skip (flutters) |
| Hedge Slime | 108 | 20 | 4 | 0 | 3 | 2 | 7 | 5 | splits once at death into 1 Slimelet (8 HP) in Gearwood packs of <=2 |
| Loom Spider | 122 | 16 | 6 | 0 | 2 | 6 | 8 | 6 | Web: SPD-30% 2 turns, every 3rd action |
| Waxwing Scarab | 123 | 24 | 6 | 0 | 5 | 3 | 10 | 8 | guards when under 50% |
| Unwoken Skeleton | 86 | 26 | 8 | 0 | 3 | 5 | 13 | 10 | undead (Resonate stuns) |
| Pale Echo | 121, hue -40 | 18 | 0 | 8 | 1 | 7 | 12 | 0 | magic attack; drops no gold, drops Chalk (see items) 40% |
| Chime-Imp | 110, hue +160 | 22 | 7 | 4 | 3 | 7 | 14 | 12 | construct (Resonate stuns) |
| Mimic | 92 | 45 | 10 | 0 | 6 | 1 | 30 | 60 | the Undercroft chest that bites; always drops Second Trinket |
| **GATEKEEPER** | 20 | 150 | 11 | 6 | 8 (13 buffed) | 3 | 80 | 100 | boss, see BIBLE §4; starts with Ward (+5 DEF) until [OATH] talk |
| **CUSTODIAN** | 41 | 210 | 9 | 12 | 7 | 6 | 0 | 0 | boss, two phases, see BIBLE §4 |

Encounter packs (visible wandering entities on the map; bump = battle):
- Gearwood: 2-3 of {bat, slime, spider}; one fixed scarab pair guarding the shrine chest.
- Undercroft: 2-3 of {skeleton, echo, scarab}; chime-imp pairs near the boss door.
- Act 3 Study approach: 2x pale echo packs only (the world is running out of things).
Respawn: none. ~9-11 packs total in the game. Flee: 70% base, never from bosses.

## 5. Items & equipment

Consumables (usable in battle or menu):

| Item | Sprite | Cost | Effect |
|------|--------|------|--------|
| Bread | 66 | 8 | heal 12 |
| Red Tonic | 115 | 20 | heal 30 |
| Green Salve | 114 | 25 | clear debuffs + heal 10 |
| Blue Draught | 116 | 30 | restore 15 SP |
| Bomb Flask | 113 | 35 | 22 AoE damage (item, anyone can throw) |
| Chalk | 102 | — (drop only) | revive fallen ally at 40% HP. Rare: Echoes drop it. Griselda sells ONE, 90g. |

Equipment: one weapon + one trinket per character. No armor slot (DEF comes
from trinkets); keep the equip screen simple.

| Weapon | Sprite | Cost | Effect | Notes |
|--------|--------|------|--------|-------|
| Knife | 105 | 15 | +2 ATK | starter tier |
| Short Sword | 103 | 40 | +4 ATK | |
| Broad Blade | 106 | 90 | +7 ATK | Act 2 shop unlock |
| Worn Cudgel | 117 | 15 | +2 ATK | Bramble/Cantor flavor |
| Twin Axe | 119 | 90 | +6 ATK, +2 SPD | |
| Wick Staff | 129 | 45 | +4 MAG | |
| Tide Rod | 130 | 95 | +7 MAG | Act 2 shop unlock |
| **Toothed Regret** | 118 | — | +10 ATK, +6 MAG | Griselda reforges the Gatekeeper's Tooth, free, only if `griselda_friend` |

| Trinket | Sprite | Cost | Effect |
|---------|--------|------|--------|
| River Stone | 101 | 25 | +2 DEF |
| Waxed Charm | 56 | 60 | +3 DEF, +5 max HP |
| Second Trinket | 91 | — | +2 all stats (Mimic drop; the name is the joke) |
| Gatekeeper's Tooth | 107 | — | +3 ATK trinket until/unless reforged |

Key items (menu tab, not usable): Blank Book, Brass Key, Gatekeeper's Tooth
(moves to equipment if reforged), The Wick (Moth's candle, set during her
recruitment naming choice).

Shop (Griselda): Act 1 stock through Broad-Blade tier locked; Act 2 unlocks the
90+ tier. Prices x1.25 if `griselda_grudge`. Buyback at half price. Gold is
called **cogs**.

Starting kit: Pip L1, Knife equipped, 2 Bread, 1 Red Tonic, 30 cogs.

## 6. Flags & Story Points (single source of truth for the writing)

`state.flags: set[str]`, `state.points: int` (Story Points, shown as small gold
tally "the Book grows heavier": +1 each on the moments marked below).

Canonical flags (agents: use EXACTLY these names):
`quill_confident | quill_dependent | vera_joined_early | vera_grudge |
vera_reconciled | griselda_friend | griselda_grudge | bramble_grumbles |
asked_unwoken | cantor_quiet | odd_promised | nyx_read_book | nyx_missed |
moth_light_name_dark / _lost / _small (one of three) | mimic_slain |
gatekeeper_relieved | bell_defected | rewoke_quill | rewoke_griselda |
rewoke_odd | book_read_custodian`

Story Points (+1 each): recruiting each of the 5, each of the 3 rewakes,
`odd_promised`, `asked_unwoken`, resolving the shop dispute either way,
`gatekeeper_relieved`. (Max realistic ~12; thresholds: Bell defect needs >= 6
plus Cantor present; "Read the Book" battle option needs >= 8.)

## 7. Epilogue matrix

The epilogue is the Book read aloud: 6-10 short pages (full-screen INK panels,
centered PARCH text, one keypress each). Assembled from:
1. Fixed opening ("This is the story of the vale, as it actually happened.").
2. One page per major choice: the door, the dispute, Moth's light-name, Cantor's
   name, the rewakes, Odd's promise (new river page), Bell's fate.
3. Nyx page: recruited-warm / recruited-late / **missed** ("There was someone
   else, almost. Look for her, next time. She waits by the fountain.").
4. Quill arc page (confident: he schedules the festival, finally; dependent: he
   waits for you to say it's time, and you do, and that's alright too).
5. Fixed closing: "The Maker built the vale. You were what happened." then the
   title card UNWRITTEN — except now stamped WRITTEN in gold.
