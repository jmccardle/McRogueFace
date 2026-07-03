# UNWRITTEN
### a McRogueFace RPG
**Tagline:** *The world is finished. The story is not.*

Creative bible. Authored by Fable (creative director). Implementation agents: this
document is canon. Where code and bible disagree, the bible wins unless SYSTEMS.md
or ARCHITECTURE.md overrides with a concrete number or contract.

---

## 1. Premise

The Maker finished the vale on a Tuesday. Every gear meshed. Every door hung true.
The sun ran on rails and the seasons turned on a mainspring, and when the last
cobblestone was set the Maker sat down at a desk in the Study, opened a book,
and prepared to write down *what should happen here*.

And could not think of a single thing.

The world was perfect, and pending. The Maker built a Custodian to keep it that
way — to sweep up any accident that might accidentally become a story — and then
the Maker rested, and has rested for three hundred years. The people of the vale
walk their routes. The shopkeeper polishes the same axe. The mayor rehearses a
speech for a festival that has never been scheduled. Nothing has ever happened,
because nothing has ever been *decided*.

Then one morning PIP wakes up holding a blank book that was not there yesterday,
and discovers they can do something no one in the vale has ever done:
**choose.**

The game is the vale's first story. Dialogue choices are diegetic — every time
the player picks an option, the Blank Book "hums" and writes it down. The
epilogue is that book read back: an enumeration of what the player actually
chose, framed as the story the Maker couldn't write.

**Tone:** warm, wry, a little melancholy. Terry Pratchett shaking hands with
Earthbound. The comedy comes from a world of perfectly maintained pointlessness;
the ache comes from characters who suspect they were sketched and never finished.
Never cynical. Never winking at the player so hard it forgets to be a place.

**Theme (the payload):** a made thing does not need its maker to know what it is
for. The stage is the artifact; the story is whoever shows up. Final line of the
game, non-negotiable: **"The Maker built the vale. You were what happened."**

---

## 2. The Party (6 playable, active party of 3)

Swapping: at Hollowbrook's fountain, at shrine camps, and via the party menu
outside battle. Battle offers SWAP as a full-turn action.
All sprite indices reference `assets/kenney_tinydungeon.png` (16px, 12 cols).

| # | Name | Sprite | Class / fantasy | Combat identity | Dialogue tag |
|---|------|--------|-----------------|-----------------|--------------|
| 1 | **PIP** | 85 | The Waker. An ordinary person, which in this vale is a miracle. | Fast rogue: high SPD, steals, double hits | `NIMBLE` |
| 2 | **SER BRAMBLE** | 96 | Oathknight who has guarded a door for 40 years because "someone wrote GUARD once and nothing since." | Tank: taunt/guard-party, damage grows as he bleeds | `OATH` |
| 3 | **MOTH** | 84 | Lamplighter of the Order of the Wick. Keeps candles ready for a light no one ever named. | Healer/caster: heal, AoE radiance | `LITURGY` |
| 4 | **VERA** | 111 | Alchemist selling "possibility tonics" that have never worked, because nothing is possible yet. | Debuffer/AoE: acid flasks, tonics | `ALCHEMY` |
| 5 | **CANTOR** | 109 | A chord-golem the Maker built to play the fanfare when the story began. Still holding the first note. | Slow nuker: stuns constructs/undead, huge single hits | `RESONANCE` |
| 6 | **NYX** | 121 | The Unlived. A character the Maker sketched, almost loved, and abandoned. Not dead — *never alive*. | Glass cannon: crits, evasion, cannot be healed by items (only MOTH's Kindle or shrine rest) | `SHADOW` |

**Recruitment paths** (dialogue-driven; see SCRIPT files for the actual scenes):
- **PIP** — starter.
- **BRAMBLE** — Act 1, Hollowbrook north door. Joins when given a *new* oath
  ("guard the people as they walk through it"). An `OATH`-flavored option makes
  it graceful; brute-force option also works but sets `bramble_grumbles`.
- **MOTH** — Act 1, Gearwood Cold Shrine. Joins after the player relights the
  shrine brazier (interaction, no check) and names what the light is for
  (3-way choice; remembered; quoted back in the epilogue).
- **VERA** — Act 1, Griselda's shop dispute. Side with Vera → joins immediately,
  Griselda's prices +25% (`griselda_grudge`). Side with Griselda → Vera storms
  out; she can be recruited in Act 2 outside the Undercroft *only* via an
  apology that passes `ALCHEMY` (gift a Bomb Flask) or `NIMBLE` (return the
  ledger page Pip lifted). If never reconciled, she runs a stall in Act 3 and
  the roster is 5.
- **CANTOR** — Act 2, Undercroft Chord Hall. Dormant. The Book writes his name:
  the first thing the player ever *writes* rather than picks. (Scripted scene;
  the choice is which name to write — "Cantor" / "his serial CH-0RD" / player
  picks silence, which recruits him as CANTOR anyway but sets `cantor_quiet`,
  changing his battle bark and one Custodian line.)
- **NYX** — Act 3, greyed Hollowbrook, only visible standing where no NPC ever
  stands (the empty plinth by the fountain). If the player earlier asked Quill
  about "the ones who never woke" (`asked_unwoken`), she recognizes being
  remembered and joins warmly; otherwise a `SHADOW`-less party must pass a
  harder choice gate (offer her the Book to read → she joins, `nyx_read_book`).
  Missable: if both fail she appears at the epilogue anyway, unrecruited, with
  one devastating gentle line.

## 3. Recurring NPCs (4, non-party)

| Name | Sprite | Role | Arc |
|------|--------|------|-----|
| **FERRYMAN ODD** | 87 | Poles the canal barge between areas. The only fast-travel. | Asks one question per ride about your latest big choice; never comments, just writes your answer on the hull among hundreds of blank planks. Final ride: reveals he was the Maker's *first sketch* — "I only know one route. The Maker never wrote me a second." If the player promises to write him one (`odd_promised`), the epilogue gives him a new river. |
| **MAYOR QUILL** | 100 | Anxious mayor of Hollowbrook. Quest-giver. | Confidence arc: the player either decides *for* him (fast, sets `quill_dependent`) or asks his opinion and endorses it (slower, sets `quill_confident`). In Act 3 a confident Quill organizes the townsfolk into the Chorus (pre-battle buff vs the Custodian); a dependent Quill loops harder than anyone when the town greys. |
| **GRISELDA** | 88 | Smith & shopkeeper. Sells gear and items. | Rival-or-mentor to Vera (see Vera). If befriended (`griselda_friend`: side with her OR reconcile everyone in Act 3), she reforges the Gatekeeper's Tooth into the best weapon, **Toothed Regret**, free. Otherwise it stays a trinket. |
| **BELL** | 110 | The Custodian's herald. Small, red, immaculate, courteous. | Appears exactly 4 times: Gearwood clearing (curious), Undercroft gate (warning), greyed Hollowbrook (apologetic — "I *liked* the bakery. But it was becoming a story."), Custodian battle (component). With `CANTOR` in party + Story Points >= 6, the in-battle `[RESONANCE] Ring Bell backward` option makes Bell defect, skipping Custodian phase 2 and unlocking the "Rung True" epilogue variant. |

## 4. Antagonists / Bosses (2)

- **THE GATEKEEPER** — Act 2 boss. Sprite 20 (gargoyle face) at scale 7, flanked
  by two Chime-Imps (110, hsl-shifted teal). A wall with opinions. It keeps the
  deep vale "pending" and considers adventurers a filing error. Attacks: Stone
  Stare (single, heavy), Toll (AoE, telegraphed one turn ahead — "The Gatekeeper
  inhales."), Summon Chime (replaces dead imps). Talk option: `[OATH]` Bramble
  formally relieves it of duty — removes its DEF buff for the whole fight.
  Drop: **Gatekeeper's Tooth** (key item).
- **THE CUSTODIAN** — final boss, Maker's Study. Sprite 41 (ornate mechanism) at
  scale 8 with two slowly rotating gold Frame halos (`rotation` animate, loop).
  Not evil. It is doing *exactly its job*: keeping the world clean, complete,
  and pending. Phase 1: Sweep (AoE), Redact (removes one party member's skills
  for 2 turns — "You are simpler now"), Polish (self-heal small). Phase 2 (under
  50%): summons Bell + a grey Echo of the starter, gains Revert (undoes the last
  damage dealt unless a NEW action type was used since — mechanically rewards
  variety, thematically: repetition is what it eats).
  Talk options (each once): `[LITURGY]` name the light (MAG down),
  `[RESONANCE]` ring Bell backward (Bell defects, see above), `[points >= 8]`
  "Read it the Book so far" — it hesitates: skips its next turn.
  No drop. The reward is the epilogue.

## 5. Acts, areas, and the trope checklist

**ACT 1 — Hollowbrook & the Gearwood.** Hub town (fountain, shop, mayor's
porch, the North Door, ferry dock). Recruit Bramble, resolve shop dispute
(Vera), ferry to Gearwood: soft encounters (bats, slimes, spiders), Cold Shrine
(recruit Moth, camp/swap point), find the Undercroft stair + Brass Key.
Bell appearance #1.

**ACT 2 — The Undercroft.** Proper dungeon: FOV fog-of-war, wandering visible
encounters (skeletons, echoes, scarabs), loot chests (one is sprite 92, a mimic
— fight it, it drops well), the Chord Hall (recruit Cantor), optional Vera
reconciliation outside the gate. Bell appearance #2. **BOSS: Gatekeeper.**

**ACT 3 — Hollowbrook, Reverted → the Maker's Study.**
The Custodian's answer to the Gatekeeper falling: it *reverts* Hollowbrook.
The player returns to the same map, greyed: desaturated ColorLayers, NPCs
standing at their Act-1 positions repeating one line each, the fountain dry,
Griselda's shop shuttered (unless `griselda_friend`), music/pulse gone.
**This is the "return to a modified area" beat and it must land hard —
identical geometry, drained palette.** Re-wake each NPC with a tag- or
flag-gated choice (each rewake +1 Story Point). Recruit Nyx at the empty
plinth. Bell appearance #3. Ferry to the Study — paper-white surreal area,
ink-hatched walls, floating desk — **BOSS: Custodian** (Bell appearance #4),
then epilogue.

**Trope contract (all must ship):**
- [x] Starter + 5 recruits, active party of 3 → roster above
- [x] 4 recurring non-party NPCs → Odd, Quill, Griselda, Bell
- [x] Return to a modified area → greyed Hollowbrook
- [x] 2 boss fights → Gatekeeper, Custodian
- [x] Items, shops, loot, levels, skills, stats → SYSTEMS.md
- [x] Dialogue drives outcome; skill checks & past choices gate options →
      recruitment paths, rewakes, boss Talk actions, epilogue variants

## 6. Aesthetic direction

**Palette (core/palette.py must define these exactly):**
- `INK      = (11, 12, 16)`      — global background
- `PARCH    = (232, 220, 192)`   — primary text
- `GOLD     = (212, 169, 78)`    — accents, selection, the Book
- `DIM      = (138, 132, 118)`   — secondary text, locked options
- `BLOOD    = (205, 66, 57)`     — damage, HP low
- `TEAL     = (80, 190, 180)`    — SP, magic
- `GRASS    = (96, 160, 92)`     — heals, XP
- `PANEL    = (22, 24, 32)`      — UI panel fill; outline (52, 60, 80), 2px
- Grey-world wash (Act 3): every area color lerped 70% toward (58, 58, 62).

**Area ground palettes (ColorLayer only — NO terrain tiles; per John's
constraint, the tileset is for characters/items/props only):**
- Hollowbrook: umber field (54,44,34), paths (84,66,44), water (38,66,86),
  building footprints (30,32,42) with GOLD doorway cells.
- Gearwood: moss (30,46,32) / (38,58,38) checker-ish variation, canopy-shadow
  cells (22,34,26).
- Undercroft: (16,18,28) / (20,24,36), FOV fog via engine perspective colors.
- Maker's Study: **inverted palette** — parchment floor (214,204,178), ink
  walls (28,26,24), everything UI-outlined in ink not gold. The world here is
  literally paper.

**Sprites:** characters/props at scale 2.0 on the overworld grid (32px cells →
grid zoom handles it; see ARCHITECTURE), scale 4.0 for battle enemies, 5.0 for
dialogue portraits, 7-8 for bosses. Chunky and proud of it.

**Motion:** every UI transition is an easing tween, nothing teleports:
dialogue boxes slide up 12px + fade in; damage numbers float (EASE_OUT, 0.8s);
battle actors lunge 24px toward target and back; scene transitions via
`scene.activate(transition=...)` if available, else 0.25s full-screen INK frame
opacity fade. NPCs idle-bob (draw_pos y +-0.06, 1.6s loop). The Book hum:
a small gold Circle pulse behind the dialogue box whenever a choice is made.

**Sound:** none. The vale is waiting. (Also keeps scope sane.)

## 7. Voice samples (calibration for any text an agent must improvise)

- Quill: "It's a very good door. Best in the vale. We're all very proud of it
  and nobody has ever once been through it."
- Griselda: "Forty years I've sharpened this axe. You want to know what it's
  cut? Time, mostly."
- Bell: "Please don't be alarmed. Alarm is untidy."
- Odd: "One route. There and back. You'd think the water would get bored.
  Water doesn't. I checked."
- Nyx: "You looked at the empty spot. Nobody looks at the empty spot."
- The Custodian: "I am not your enemy. I am your margin."

Improvised text must match: short sentences, concrete nouns, no modern slang,
no fourth-wall winks beyond what the premise already licenses.
