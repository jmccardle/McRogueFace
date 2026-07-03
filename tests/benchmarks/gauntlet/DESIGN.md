# Implementation deviations from the original spec

*(Recorded by the implementer per the spec's instruction below. The original design is
preserved verbatim after this section.)*

1. **`get_metrics()["frame_time"]` is in MILLISECONDS, not seconds.** The spec's "Engine
   API notes" says frame_time is in seconds; runtime probing shows raw values around 16.7
   at 60 fps -- i.e. milliseconds. Scoring and the HUD consume frame_time directly as ms
   (no `* 1000`).
2. **vsync / framerate cap must be disabled to measure.** With default windowed vsync the
   frame_time floors at ~16.7 ms (the 60 Hz budget) regardless of load, so the ramp could
   never observe a genuine failure. `run_gauntlet.py` and `gauntlet_main.py` set
   `mcrfpy.window.vsync = False` and `mcrfpy.window.framerate_limit = 0` at startup.
3. **HUD FPS is derived as `1000 / frame_time`.** The metrics `fps` field is a cumulative
   running average over total runtime (it starts in the thousands and converges slowly),
   not an instantaneous rate, so it is unusable as a live readout. Instantaneous FPS is
   computed from the smoothed frame time instead.
4. **`draw_calls`, `ui_elements`, `visible_elements`, and entity render counters read 0**
   in this build even while a scene is visibly rendering (the engine's own metrics test
   notes these "may be 0 if scene hasn't rendered yet"). They are displayed honestly
   (0 when the engine reports 0) rather than faked; `metrics_at_peak` still stores the full
   dict. frame_time is the sole scoring signal.
5. **`tick(dt_ms)` runs on a dedicated 100 ms simulation Timer**, separate from the 16 ms
   scoring sampler and the 100 ms HUD refresh. The spec described tick as "optional
   per-sample work"; each trial's periodic load (grid.step, path queries, color-region
   rewrites, z-shuffles, FOV recompute) runs on this sim cadence, matching each trial's own
   description ("driven on a 100 ms Timer", "every tick", etc.).
6. **Headless full runs cannot score.** In headless mode frame_time is 0.0 (no real
   rendering) and timers fire one-per-`step()`, so `run_gauntlet.py` only yields a real
   baseline windowed (or under xvfb). The headless unit test exercises
   setup / set_load / teardown directly, not the ramp.
7. Animations use the current `obj.animate(...)` method (the older
   `mcrfpy.Animation(...).start()` seen in some demos is not used).
8. **Hard-cap bail requires 3 over-cap samples per window, not 1.** The spec's "bail
   immediately if any sample > 100 ms" was observed zeroing entire trials on a live
   desktop: a single stray compositor/GC frame >100 ms ended trials whose held p95 was
   6-9 ms, producing 10x-100x run-to-run score variance. A genuinely overloaded engine
   accumulates 3 strikes within ~50 ms of wall time, so the bail still triggers almost
   immediately under true overload; lone hiccups still count toward the window's p95.
9. **Pathfinder Rush starts its ramp at 1 query/tick** (spec table implied a larger
   start via the shared default). Queries burst on one 100 ms tick, so even a handful
   spike a single frame; starting at 1 lets the ramp find the true sustainable level.

---

# THE GAUNTLET — McRogueFace Interactive Stress Benchmark

**Design spec (Fable, 2026-07-02).** Implementer: follow this spec; where the engine
API disagrees with an assumption here, prefer the engine and note the deviation at the
top of the committed copy of this file.

## Concept

An on-screen benchmark the user *watches*: six themed "trials", each stress-testing one
engine subsystem with steadily ramping load until the frame budget breaks. The maximum
sustained load is that trial's score. Scores are written as a JSON baseline so future
engine changes can be diffed (regression = red, improvement = green) right on screen.

Two ways to run:
- **Interactive** (`gauntlet_main.py`): menu, watch any trial, drive load manually or auto-ramp.
- **Baseline run** (`run_gauntlet.py`): runs all six trials back-to-back with auto-ramp,
  shows the results screen, writes `baseline/gauntlet/latest.json` (and promotes to
  `baseline.json` if none exists).

## File layout

```
tests/benchmarks/gauntlet/
├── DESIGN.md            # this file (committed with the code)
├── gauntlet_main.py     # interactive entry point (menu scene + trial scenes + results)
├── run_gauntlet.py      # unattended full run -> results screen -> baseline JSON
├── hud.py               # shared HUD overlay (see Visual Identity)
├── scoring.py           # RampController: hold-window sampling, p50/p95, pass/fail, grades
├── baseline_io.py       # read/write/compare baseline JSON (schema below)
└── trials/
    ├── __init__.py      # Trial base class + TRIALS registry (ordered)
    ├── entity_swarm.py
    ├── animation_storm.py
    ├── grid_titan.py
    ├── pathfinder_rush.py
    ├── ui_avalanche.py
    └── sightline_siege.py
```

**All source files ASCII-only** (the `--exec` loader rejects non-ASCII). No unicode
glyphs anywhere, including Caption text: use `^` / `v` for deltas, `*` for accents.

## Visual identity

Dark, instrument-panel aesthetic. The benchmark should feel like a cockpit gauge
cluster bolted over a chaotic arena.

Palette (mcrfpy.Color):
- Background `#0d0f14` (13,15,20); HUD panel fill `#161a22` (22,26,34) with 1px outline `#2a3140` (42,49,64)
- Primary text `#e8eaf0` (232,234,240); dim text `#8a93a6` (138,147,166)
- Frame-budget colors: OK (< 16.7 ms) mint `#38d996` (56,217,150); warn (16.7-33 ms)
  amber `#f5b83d` (245,184,61); fail (> 33 ms) red `#e5484d` (229,72,77)

Trial accent colors (used for the trial banner, its menu row, its arena flavor, and
its row on the results screen):

| # | Trial            | Subsystem                 | Accent                    |
|---|------------------|---------------------------|---------------------------|
| 1 | ENTITY SWARM     | entity step/render        | amber   (245,165,36)      |
| 2 | ANIMATION STORM  | animation manager         | magenta (229,85,157)      |
| 3 | GRID TITAN       | grid render + layer writes| cyan    (53,193,214)      |
| 4 | PATHFINDER RUSH  | Dijkstra/A* queries       | green   (76,194,110)      |
| 5 | UI AVALANCHE     | UI hierarchy + draw calls | violet  (154,110,245)     |
| 6 | SIGHTLINE SIEGE  | FOV + perspective         | crimson (229,72,77)       |

### HUD (hud.py) — identical overlay on every trial scene

Top strip, full width, panel-filled:
- Left: trial name in its accent color, plus one-line description in dim text.
- Center: **frame-time sparkline** — 60 thin Frame bars (4 px wide, 2 px gap),
  bar height = frame_time clamped to [0, 50] ms mapped to [2, 48] px, colored by the
  budget colors above. A 1px horizontal hairline marks the 16.7 ms budget.
- Right: big FPS readout (large Caption, budget-colored), under it
  `frame p95: NN.N ms`, `draw calls: N`, and the load line `LOAD: <value> <unit>`
  with ramp state tag `[RAMP k]` / `[HOLD]` / `[MANUAL]`.

Bottom strip: key legend in dim text
`[SPACE] pause  [LEFT/RIGHT] trial  [-/+] load  [A] auto-ramp  [R] run gauntlet  [S] shot  [ESC] menu/quit`

HUD refreshes on a 100 ms Timer (10 Hz), NOT per frame; metric samples for scoring are
taken on their own 16 ms Timer. HUD cost is constant across trials — that is fine, it
is part of the harness and identical everywhere.

### Menu scene

Title `THE GAUNTLET` centered large, subtitle `McRogueFace stress benchmark` in dim
text; engine version + commit short-hash bottom-left (read version from
`mcrfpy.__version__` if present, else omit; commit passed in by run script or read
lazily via `subprocess` is NOT allowed inside the engine — obtain it in baseline_io
with `git rev-parse --short HEAD` guarded by try/except when writing JSON only).
Six menu rows, one per trial: number, name in accent, unit, and — if a baseline
exists — its baseline max_load in dim text. A slow color-cycle animation on the title
(animate fill_color through the six accents, 12 s loop) gives the screen life without
costing measurable frame time.

### Results scene

Table, one row per trial: name (accent), `max_load unit`, `p95 ms at peak`, and when a
baseline exists: delta column `^ +12%` (mint) / `v -8%` (red) / `= same` (dim).
Footer: **GAUNTLET SCORE** = geometric mean of per-trial `max_load / baseline_max_load`
ratios, displayed as `xNN.N%` vs baseline (=100% at parity); when no baseline exists show
`FIRST RUN -- baseline recorded` instead. Below it, letter grade per trial vs baseline:
S >= 150%, A >= 100%, B >= 80%, C >= 60%, D below; overall grade from the geomean.

## Trials

Common contract (`trials/__init__.py`):

```python
class Trial:
    name = "ENTITY SWARM"; unit = "entities"; accent = (245,165,36)
    description = "one line"
    base_load = 50          # starting load
    growth = 1.6            # geometric ramp factor: load_k = round(base * growth**k)
    def setup(self, scene, ui): ...      # build arena, return nothing
    def set_load(self, level_value): ... # create/destroy stress objects to match
    def tick(self, dt_ms): ...           # optional per-sample work (default no-op)
    def teardown(self): ...
```

1. **ENTITY SWARM** — one Grid (~40x25 visible), N entities with SEEK behavior toward a
   wandering target using a Dijkstra map, `grid.step()` driven on a 100 ms Timer;
   entities render with sprites. Load = entity count.
2. **ANIMATION STORM** — N small Frames scattered on screen, each running two concurrent
   animations (position with random easing, fill_color pulse), re-launched from the
   animation-complete callback so the storm is self-sustaining. Load = live animations (2N).
3. **GRID TITAN** — square Grid of side S with a TileLayer + ColorLayer; every tick,
   rewrite a 32x32 ColorLayer region (rolling window) and animate the camera center in a
   slow orbit so chunks keep invalidating. Load = S (grid side; cells = S*S). growth 1.4.
4. **PATHFINDER RUSH** — static maze grid (BSP or simple rooms); each tick issue Q
   `grid.find_path` / Dijkstra queries between random walkable pairs. Load = queries/tick.
5. **UI AVALANCHE** — nested Frame trees (depth 5) each with Captions and Sprites, plus a
   z-order shuffle of the top-level frames every tick to defeat caching. Load = total
   UI elements.
6. **SIGHTLINE SIEGE** — Grid with scattered walls; N entities each with an active FOV
   (`compute_fov`, radius 10) recomputed on a 100 ms step as they random-walk, exercising
   perspective writeback (#316). Load = FOV entities.

Trials must create everything under their own Scene and fully dispose in `teardown()`
(remove entities, stop timers, drop references) so trials do not contaminate each other.

## Ramp + scoring (scoring.py)

- Auto-ramp: set load, **settle 1.0 s** (discard samples), then **hold 2.0 s** collecting
  `get_metrics()["frame_time"]` samples on the 16 ms sampler Timer.
- Pass: p95 <= 16.67 ms -> next ramp step. Fail: stop; trial score = last PASSING load
  and its held p50/p95. Also bail immediately if any sample > 100 ms (hard cap).
- Record per trial: `unit, max_load, p50_ms, p95_ms, samples, metrics_at_peak`
  (metrics_at_peak = the full get_metrics() dict from the last passing window).

## Baseline JSON (baseline_io.py)

Path: `tests/benchmarks/baseline/gauntlet/`. Schema:

```json
{ "schema": 1, "version": "0.2.8", "commit": "abc1234", "date": "2026-07-02",
  "platform": "<platform.platform()>", "budget_ms": 16.67,
  "trials": { "entity_swarm": { "unit": "entities", "max_load": 3200,
               "p50_ms": 9.1, "p95_ms": 15.8, "samples": 122,
               "metrics_at_peak": { "...": "full get_metrics dict" } } },
  "gauntlet_score_vs_baseline": 1.0 }
```

Every full run writes `latest.json`; if `baseline.json` is absent, copy it there.
`baseline_io.compare(latest, baseline)` returns per-trial ratios + geomean for the
results screen. Never overwrite `baseline.json` automatically once it exists.

## Engine API notes for the implementer (verified against this codebase)

- `mcrfpy.get_metrics()` -> dict with `frame_time` (s), `avg_frame_time`, `fps`,
  `draw_calls`, `ui_elements`, `visible_elements`, `current_frame`, `runtime`,
  `grid_render_time`, `entity_render_time`, `fov_overlay_time`, `python_time`,
  `animation_time`, `grid_cells_rendered`, `entities_rendered`, `total_entities`.
- Scenes: `s = mcrfpy.Scene("name")`; children via `s.children`; activate with
  `mcrfpy.current_scene = s` or `s.activate()`; keyboard `s.on_key = fn(key, state)`
  with `mcrfpy.Key` / `mcrfpy.InputState` enums.
- Timers: `mcrfpy.Timer("name", cb, interval_ms)`, callback `(timer, runtime_ms)`;
  methods stop/pause/resume/restart. In headless, timers fire only via `mcrfpy.step(dt)`,
  ONE event per step.
- Animation: `obj.animate("x", 500.0, 2.0, mcrfpy.Easing.EASE_IN_OUT, callback=fn)`;
  callback receives `(target, property, final_value)`.
- Captions: keyword args (`Caption(text=..., pos=...)`); Grid center is in pixels,
  `grid.center_camera((tx, ty))` for tile coords; `grid.at(x,y)` GridPoint has
  walkable/transparent; layers: construct `ColorLayer(name=..., z_index=...)` then
  `grid.add_layer(layer)`; `entity.set_behavior(mcrfpy.Behavior.SEEK, pathfinder=...)`.
- Check `tests/demo/screens/*.py` and `tests/benchmarks/*.py` for working idioms before
  writing each trial; `stubs/mcrfpy.pyi` is the API contract.

## Verification expected from the implementer

1. Each trial runs standalone headless (`--headless --exec`) driving `mcrfpy.step()`:
   setup, set_load at two levels, teardown — asserting object counts and no errors.
   Commit as `tests/unit/gauntlet_trials_test.py` (fast, suite-friendly).
2. Screenshot of the menu, one mid-trial scene, and the results scene via
   `automation.screenshot()` under headless timers; eyeball-check layout matches this
   spec (attach paths in your report).
3. A real baseline attempt: run `run_gauntlet.py` windowed if a display is available,
   else under `xvfb-run` if installed. If neither works, say so in your report and
   leave baseline capture to the operator — do NOT ship a fake baseline.json.
