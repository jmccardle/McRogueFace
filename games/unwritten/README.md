# UNWRITTEN

*The world is finished. The story is not.*

A complete short-form RPG (30-45 minutes) built on McRogueFace: turn-based
battle-screen combat, a six-character roster with an active party of three,
choice-driven dialogue with skill checks, shops, loot, levels, two bosses,
and an epilogue assembled from the choices you actually made.

The Maker built a perfect vale, sat down to write what should happen in it,
and couldn't think of a single thing. Three hundred years later, someone
wakes up holding a blank book.

## Run it

```bash
cd build
./mcrogueface --exec ../games/unwritten/main.py
```

## Controls

- **WASD / arrows** - move (bump into people to talk, into enemies to fight)
- **Enter / Space** - advance dialogue, confirm menus (Space also skips the typewriter)
- **Esc** - back out of menus / open the party menu from the overworld
- **E / Enter** - interact (camps, props)
- **Tab** - party menu (swap, equip, items, stats, key items)
- Title screen: **1 / 2 / 3** jump to Act 1/2/3 with appropriate preset state (debug)

## What to look for

- Every dialogue choice is remembered; several are gated by WHO is in your
  active party (each character carries a dialogue tag) or by what you chose
  hours earlier. Locked options stay visible - that "what would that have
  been?" itch is intentional.
- Both bosses can be TALKED to mid-battle if you brought the right people.
- After the first boss, go home. The way the town comes back is the game's
  favorite trick.
- Whether you find the sixth party member at all depends on questions you
  did or didn't ask in Act 1.

## Layout

- `design/` - creative bible, systems spec, architecture contracts
- `data/` - authored content: dialogue scripts (33 scenes / 171 nodes),
  maps, items, enemies, epilogue pages, battle barks
- `core/` - UI kit (dialogue box, menus, bars, toasts), palette, input stack
- `systems/` - state, dialogue runner, overworld, battle, shop, menus, epilogue
- `tests/` - unit tests per system + `playthrough.py`, a scripted headless
  run of the entire game (20 beats, title card to WRITTEN stamp):
  `cd build && ./mcrogueface --headless --exec ../games/unwritten/tests/playthrough.py`

## Credits

Made overnight, on request, as an answer to a question.

- Creative direction, story, dialogue, systems & encounter design: **Fable** (Claude)
- Implementation: Claude Opus subagents (framework / battle / overworld / integration)
- Engine: **McRogueFace** by John McCardle
- Tileset: Kenney's Tiny Dungeon (characters and items only - the terrain
  is nothing but colored cells, on purpose)

The Maker built the vale. You were what happened.
