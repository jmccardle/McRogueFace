# UNWRITTEN — Architecture & Contracts

Read BIBLE.md (canon) and SYSTEMS.md (numbers) first. This file is the
implementation contract: module boundaries, signatures, engine gotchas, and the
testing/QA harness every agent must use.

## 0. Run instructions

- Game root: `/home/john/Development/McRogueFace/games/unwritten/`
- Windowed: `cd /home/john/Development/McRogueFace/build && ./mcrogueface --exec ../games/unwritten/main.py`
- Headless test: `cd build && ./mcrogueface --headless --exec ../games/unwritten/tests/<test>.py`
- `main.py` must do `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`
  so `import core...`/`import data...`/`import systems...` work. Tests insert the
  game root the same way (they live one level down).
- Asset path is relative to the BUILD dir: `assets/kenney_tinydungeon.png`
  works because cwd is `build/`. Texture: `mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)`
  — construct ONCE in `core/assets.py`, share everywhere.

## 1. Engine gotchas (hard-won; violating these wastes hours)

1. **ASCII ONLY** in every .py file (the --exec loader rejects non-ASCII).
   No em-dash, no curly quotes, no unicode arrows — in code OR string literals.
2. Headless: timers DO NOT fire on their own. Tests drive time with
   `mcrfpy.step(1/60)` (fires each due Timer at most once per call) or call
   game functions directly. `automation.screenshot(path)` is synchronous
   (renders current state immediately). Windowed: timers fire in real time.
3. `mcrfpy.Texture(path, w, h)` — positional, not grid_size kwarg.
4. `Sprite.scale` is a single float. `Caption.font_size` is the text size.
   `Caption.size` is READ-ONLY text dimensions (use it to center:
   `cap.x = cx - cap.size.x / 2` AFTER setting text/font_size).
5. Frames/Captions/Sprites accept constructor kwargs for most properties
   (`fill_color=`, `outline=`, ...). `Color` args: `mcrfpy.Color(r, g, b[, a])`.
6. Scene: `s = mcrfpy.Scene(name)`; `s.children` collection; activate via
   `mcrfpy.current_scene = s`. Keyboard: `s.on_key = fn(key, state)` with
   `mcrfpy.Key.*` / `mcrfpy.InputState.PRESSED/RELEASED`. Compare enums with
   `==` (a quirk in `!=` was fixed but don't tempt it).
7. Grid: `mcrfpy.Grid(grid_size=(w,h), pos=..., size=...)` (no texture needed
   when only ColorLayers draw terrain). `grid.zoom`, `grid.center` (pixels;
   cell = 16px pre-zoom), `grid.center_camera((tx, ty))` for tile coords.
   Layers: `mcrfpy.ColorLayer(name=..., z_index=...)` then `grid.add_layer(l)`,
   `l.set((x,y), color)`, `l.fill(color)`. Negative z renders under entities.
8. Entities: `mcrfpy.Entity(grid_pos=(x,y), texture=TEX, sprite_index=i)` then
   `grid.entities.append(e)`. Remove with `e.die()`. `e.draw_pos` is the
   fractional render position (use for bob/lerp), `e.grid_pos` is logic.
9. Everything animatable: `obj.animate("x", 500.0, 0.3, mcrfpy.Easing.EASE_OUT)`;
   callback kwarg receives `(target, prop, value)`; `loop=True` for idle bobs.
   Animate color components via property paths like `"fill_color.a"` — but NOT
   `frame.fill_color.r = x` directly (Color reads are copies; whole-value
   assignment or animate() only).
10. `clip_children=True` on Frame for panels that scroll/slide; explicit
    `z_index` whenever two siblings overlap (ties break unpredictably).
11. Timer: `mcrfpy.Timer(name, cb, ms)`, cb = `(timer, runtime_ms)`. Names are
    global — prefix with your system (`"bat_"`, `"dlg_"`, `"ow_"`). `.stop()`
    dangling timers in every teardown; a timer holding a dead scene's objects
    is the #1 crash source.
12. Scene-level Frames at 1024x768; design for exactly that resolution.
13. `automation.keyDown/keyUp/typewrite` exist for input-injection tests, but
    prefer calling game functions directly in headless tests (deterministic).

## 2. File layout & ownership

```
games/unwritten/
  main.py                     # bootstrap, title screen, chapter select   [Agent A]
  core/
    palette.py                # ALL colors/fonts consts from BIBLE §6     [Agent A]
    assets.py                 # the one Texture; SPRITES dict of indices  [Agent A]
    ui.py                     # widget kit (below)                        [Agent A]
    inputstack.py             # modal input dispatch (below)              [Agent A]
    tween.py                  # helpers: fade_scene, float_text, shake    [Agent A]
  data/
    script_act1.py ... act3.py, epilogue.py   # dialogue trees   [FABLE - already written, DO NOT EDIT text]
    characters.py             # party tables from SYSTEMS §1/§3           [Agent B]
    enemies.py                # enemy tables/packs from SYSTEMS §4        [Agent B]
    items.py                  # items/equipment from SYSTEMS §5           [Agent B]
    maps.py                   # ASCII maps + placements  [FABLE - written, DO NOT EDIT layouts]
  systems/
    state.py                  # GameState singleton (below)               [Agent A]
    dialogue.py               # dialogue runner (below)                   [Agent A]
    overworld.py              # grid areas, movement, NPCs, encounters    [Agent C]
    battle.py                 # turn engine + battle screen               [Agent B]
    party_menu.py             # party/equip/items/stats menu              [Agent C]
    shop.py                   # Griselda's shop                           [Agent C]
    epilogue.py               # Book pages                                [Agent C]
  tests/
    shots/                    # screenshot output (gitignored ok)
    test_ui_kit.py            # [Agent A]
    test_battle_sim.py        # [Agent B]
    test_overworld.py         # [Agent C]
    test_script_integrity.py  # [Agent A] validates all dialogue refs
    playthrough.py            # [Agent D] scripted full run
```

Ownership is exclusive: never edit another agent's file; integration issues go
in your report instead. `data/script_*.py` and `data/maps.py` text/layout are
authored content — you may fix a syntax error, never rewrite content.

## 3. Core contracts (Agent A implements; B/C code against these)

### systems/state.py
```python
class GameState:            # singleton: state.GS
    party: list[str]        # active char ids in order, max 3, e.g. ["PIP","BRAMBLE","MOTH"]
    roster: dict[str, CharState]  # all recruited chars
    flags: set[str]
    points: int
    gold: int
    inventory: dict[str, int]     # item_id -> count
    key_items: list[str]
    act: int                # 1..3
    def has(self, flag) -> bool
    def add_flag(self, flag)          # idempotent
    def add_points(self, n)           # also triggers Book-hum UI hook if set
    def recruit(self, char_id, level) # adds to roster (and party if space)
    def party_tags(self) -> set[str]  # dialogue tags of ACTIVE party
    def grant(self, item_id, n=1); def spend_gold(self, n) -> bool
    def xp_gain(self, amount)         # whole roster, handles level-ups, returns list of levelup events

class CharState:  # hp, sp, level, xp, equipped weapon/trinket ids, stats() -> dict (base+growth+equipment)
```

### core/ui.py  (all widgets take a parent collection, absolute pixel pos)
```python
class Panel:        # Frame with PANEL fill + outline; .frame, .children
class Label:        # Caption factory with palette defaults; centered variant
class MenuList:     # vertical keyboard menu: items=[(label, value, enabled)], on_pick(value), on_cancel()
                    # gold '>' cursor, W/S or arrows, Enter/Space pick, Esc cancel; disabled rows DIM with lock reason
class Bar:          # stat bar: bg + fill + optional caption "12/34"; .set(cur, max); color param
class DialogueBox:  # bottom box 940x190 at (42, 556): portrait chip (sprite scale 5 in 96px frame),
                    # name tag, typewriter body (45 chars/sec via Timer, space skips), blinking 'v' when done,
                    # choice list mode (gold arrows; locked choices DIM prefixed by their [TAG]);
                    # .show_node(node, on_choice) drives one node; hum() pulses the gold circle
class Toast:        # top-right slide-in note ("Got 3x Bread", "+1 Story Point"), auto-dismiss 2.2s, stacks
class TitleBanner:  # area-entry banner: big centered caption, fade in/out 1.8s total
```

### core/inputstack.py
```python
class InputStack:   # scene.on_key -> stack dispatch
    def push(self, handler, name=""); def pop(self, name=""); def replace(...)
    # handler: fn(key, state) -> bool (True = consumed). Top-most first.
    # Overworld pushes movement; DialogueBox pushes itself while open; menus likewise.
```

### systems/dialogue.py
```python
def run_scene(scene_id, on_done=None)
# Loads node dict from data.script_actN (see schema below), drives DialogueBox,
# applies effects to GS, executes actions. MUST support being started from
# overworld (freezes movement via InputStack) and from battle (Talk).
```

**Dialogue node schema (already used by the script files):**
```python
SCENES = {
  "scene_id": {
    "start": "n1",
    "nodes": {
      "n1": {
        "speaker": "QUILL",         # char/npc id, or "NARRATOR" (no portrait, italic-dim style)
        "text": "one paragraph",
        "next": "n2",               # OR "choices": [...]
        "choices": [
          {"label": "...", "next": "n3",
           "req": ("tag","OATH") | ("flag","x") | ("flag_not","x") | ("party","NYX") | ("points",6),
           "effects": [("flag","x"), ("points",1), ("gold",-20), ("item","bread",2)]},
        ],
        "effects": [...],           # applied on node ENTER
        "action": "recruit:VERA:2" | "battle:pack_id" | "shop" | "heal_party"
                  | "swap_menu" | "end" | "act:3" | "goto_area:gearwood:12,4",
      },
    },
  },
}
```
Unmet `req` choices are SHOWN but disabled (DIM + tag visible) — this is a
design pillar, not optional. `speaker` id -> portrait sprite via
`core.assets.PORTRAITS`.

### systems/battle.py (Agent B) — public surface
```python
def start_battle(pack_id, on_victory, on_defeat, boss_scene_hooks=None)
# builds battle scene, runs to completion, restores previous scene after.
# boss_scene_hooks: {"talk_options": [...], "phase2_at": 0.5, ...} per BIBLE §4.
```
Battle screen layout (1024x768): turn ribbon top (portrait chips in order);
enemies left half standing on a floor line (y=430), party status cards right
column (3 cards: name, HP Bar, SP Bar, level); command panel bottom-left
(MenuList: Attack/Skill/Item/Guard/Talk?/Swap/Flee); battle log (last 3 lines,
DIM) above the command panel; area-tinted gradient backdrop (6 horizontal
bands, palette per area). Damage numbers float via tween. Actors lunge on
attack. Defeated enemies fade (opacity tween) then die().

### systems/overworld.py (Agent C) — public surface
```python
def enter_area(area_id, spawn=None)   # builds/reuses Grid scene from data.maps
def refresh_area()                    # re-applies palette/NPCs after flag changes (act 3 grey!)
```
Movement: WASD/arrows, 8ms repeat via held-key Timer, bump into NPC entity =
run its dialogue scene; bump into encounter entity = start_battle; walk onto
door/exit cell = area transition (fade). Player is an Entity (sprite 85).
Encounter entities wander 1 cell every 900ms within a radius-2 leash.
Act 3 grey: `refresh_area` lerps every ColorLayer cell 70% toward (58,58,62)
when `GS.act == 3 and area == hollowbrook and not flags["town_rewoken"]`.

## 4. Testing & QA harness (every agent)

- Each owned system ships a headless test that: builds its screen with fake
  state, `automation.screenshot("tests/shots/<name>_1.png")` at 2+ meaningful
  states, prints "PASS <name>", `sys.exit(0)`. Drive timers with
  `mcrfpy.step(1/60)` in a loop when needed (e.g., 120 steps = 2 simulated sec).
- `test_script_integrity.py`: walks ALL scenes in data/script_*: every `next`
  and choice target resolves; every req/effect tuple well-formed; every speaker
  has a portrait; every action string parses; every battle pack exists; prints
  counts. This test protects the authored content — run it after ANY change.
- `test_battle_sim.py`: run 200 scripted battles headless w/o UI sleeps
  (auto-pick first command) across packs incl. both bosses; assert no
  exceptions, victory possible, XP/loot granted; print win rates + avg turns
  (balance report for Fable).
- Visual bar: screenshots must look like a finished game: no overlapping text,
  no default-white anything, palette exactly from core/palette.py. Fable
  art-directs from your screenshots and WILL send notes.

## 5. Performance & hygiene

- The whole game is <15k cells and <100 entities — nothing here can challenge
  the engine (it holds 10k entities at 60fps). Do not prematurely optimize;
  DO stop Timers and clear scene references on teardown.
- No global mutable state outside systems/state.py. No prints in the game path
  except the debug chapter-select (title screen keys 1/2/3 preset GS per act —
  Agent D wires the presets from SYSTEMS §6 flag combos).
- "Fail Early" (John's law): no silent fallbacks. Missing sprite id, unknown
  flag, unresolved dialogue target = raise with a clear message. Never ship a
  placeholder that pretends to work.
