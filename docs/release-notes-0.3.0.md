# McRogueFace 0.3.0 — release notes (DRAFT)

> Draft assembled from the 109 commits between the `0.2.8` tag and master `678ef74`.
> Not final: the scope below may still gain the fixes listed under "Under consideration".

## Headline: Python 3.15

McRogueFace now embeds **CPython 3.15.0** (was 3.14), on every platform:

- **Linux**: built from the `modules/cpython` submodule, pinned at the `v3.15.0` tag.
  `sys.version` reports the tag exactly, with no `-dirty` suffix.
- **Windows**: the python.org 3.15 embeddable build. Packages now ship the `.pyd`
  extension modules. Before this, `socket`, `ssl`, `asyncio`, `ctypes` and `sqlite3`
  could not be imported in Windows builds, 0.2.8 included (#419).
- **Web (WASM)**: CPython 3.15 is built for Emscripten. The browser stdlib bundle gains
  `_colorize`, `pathlib`, `email` and the full `importlib`, which repairs REPL
  tracebacks (#392).
- The `mcrfpy` module now uses multi-phase initialization. It **refuses to load in a
  subinterpreter**, consistent with the 1.x compatibility policy that excludes
  subinterpreters.
- Like CPython 3.15 (PEP 831), the engine is built with **frame pointers**, so `perf`,
  eBPF profilers and gdb can unwind from Python through the engine to `main`. The
  overhead is within wall-clock noise (#421). See `docs/profiling.md`.

Your game scripts now run on 3.15; check CPython's *What's New in 3.15* for stdlib
removals that affect your code.

## Breaking changes and upgrade notes

| Change | What to do |
|---|---|
| **`UIGrid` is gone; `GridData` is public and is not drawable.** `mcrfpy.Grid` is the same type as `mcrfpy.GridView`. Camera, position, size, input callbacks, overlay `children` and `animate()` belong to the **view**; cells, layers, entities, FOV and pathfinding belong to the **data** (#355, #359–#371). | Code that only uses `Grid(...)` keeps working. Code that reached drawable properties through a map object must go through a view. |
| **`entity.grid` returns a `GridData`**, not the view. The setter still accepts a view. | Use `view.grid_data` / the view you hold for camera or position work. |
| `GridData.apply_ranges()` / `apply_threshold()` return `GridData` (were `Grid`). | Chained calls are unaffected. |
| **Headless `mcrfpy.step()` is a full simulation frame**: `Scene.update(dt)` fires, scene transitions progress and complete, and `current_frame` advances. Rendering and input are still excluded (#350). | Headless tests that relied on `step()` skipping these may change behaviour. |
| **Headless timers count from simulation time**, not the wall clock, so their first firing is deterministic (#383). | — |
| **`DijkstraMap.path_from()` used to return the path reversed**, and `step_from()` returned a cell that wasn't adjacent to the query (#375). | Remove any `reversed()` workaround. |
| `Sound.play_varied()` returns the `(pitch, volume)` it used (was `None`), and plays it on its own overlapping voice. The sound's `pitch`/`volume` and `.playing` aren't affected; `stop()` stops the extra voices too (#407). | — |
| **`--headless` and `--audio-off` now turn audio off.** Both flags used to be ignored. Now no audio device is opened: `play()` does nothing and `.playing` stays `False`. Loading, `duration` and `SoundBuffer` work as before, and `play_varied()` still draws its random values (#406). | Pass `--audio-on` (in either order with `--headless`) for real playback in headless runs. |
| `mcrfpy.step()` / `advance()` raise `RuntimeError` when called from a thread that holds `mcrfpy.lock()`; previously this deadlocked. | — |
| **One thread drives the clock** (#411). The first thread to run a frame owns it until it exits: the main thread once the engine loop starts (always, when windowed), otherwise the first caller of `step()`/`advance()`. Other threads' calls raise `RuntimeError` (they used to run a second frame body concurrently). `mcrfpy.lock()` is a no-op on the owner and a real barrier everywhere else, including the main thread when a background thread drives. Headless `--run-forever` refuses to start its loop if a background thread owns the clock. | Run frames from one thread and hand work to it; other threads apply changes inside `with mcrfpy.lock():`. |
| **Timers catch up** (#397). When a frame comes late (a wide `step()`, or a stalled windowed frame), a repeating timer fires once per elapsed interval, and each call's `runtime` is that firing's own deadline, not the frame time. The timer keeps its phase: `step(10.5)` fires a 1000 ms timer at 1000…10000 and leaves 500 ms to the next. Animations get the whole frame time too (a step of 10 s or more, or a windowed frame of 1 s or more, used to skip them). | A callback that used `runtime` as "now" gets the scheduled time. A timer much faster than the frame rate now fires several times per frame instead of once. |
| **`animate()` names are attributes, in the attribute's units** (#423, #426). Every name `animate()` accepts is a readable attribute, and animating it ends where assigning it would. **Entity `"x"`/`"y"` are now pixels** (they animated tile coordinates, so `animate("x", 64)` sent the entity to 1024 px); `"pos"` (pixels) and `"draw_pos"` (tiles, a Vector) are new, as is `"opacity"`. GridView animates `x`, `y`, `w`, `h`, `pos`, `size`, `opacity`, `rotation`, `origin`, `z_index` and `fill_color` again (lost in the type split). Every type takes `Color` and `Vector` targets (only tuples worked), and `z_index` animates on every drawable. Arc, Circle and Line gain `x`/`y` attributes; Frame and Viewport3D gain `size`. A Line's `pos` is its midpoint and moving it moves the line (it used to move nothing, so aligning a Line didn't place it). Assigning a Frame's `w`/`h`/`size` resizes its clipping/cache texture, as animating it did. Wrong-typed targets raise `TypeError`. | Animate an entity's tile position with `"draw_pos"`: `e.animate("draw_pos", (5, 3), 0.2)`. Removed names raise `ValueError` naming the replacement: Entity `draw_x`/`draw_y` (use `draw_pos`) and `sprite_scale` (it never had an effect); `position` (use `pos`); `origin_x`/`origin_y` (use `origin`); Line `start_x`/`start_y`/`end_x`/`end_y` (use `start`/`end`); Caption `size` (use `font_size`). |
| `step()` rejects a negative, NaN or infinite `dt` with `ValueError`, and one that would overflow the clock with `OverflowError`; `advance()` likewise for overflow. A negative `dt` used to mean "next event", and NaN/inf wrapped the clock negative. | Use `step()` / `step(None)` for "next event". |
| `--exec` / `-c` scripts run in UTF-8 mode. A bare `open()` reads UTF-8 on every platform; it used to be ASCII on Linux and the ANSI code page on Windows (#378). | — |
| `get_metrics()` counters (`draw_calls`, `ui_elements`, the grid counters) are no longer always 0 (#341). | — |
| **An entity no longer keeps its grid alive** (the back-reference is weak; the strong one leaked every grid with entities, #437). `e = Entity(grid=Grid(...))` with no other reference to the grid leaves `e.grid` as `None`. | Keep a reference to the grid (or view) you're using. |
| **Every accessor returns the same Python object** for the same engine object: `grid.layer(name)`, `grid.layers`, `.texture`, `.font`, `.children`, `.entities`, `entity.perspective_map`, `get_dijkstra_map(root)`, `mcrfpy.timers`, find(), and more (#430). An object you constructed comes back as itself. | Code that relied on getting a *fresh* wrapper (e.g. mutating it as a private copy) must copy explicitly. |
| `entity.perspective_map = m` then reading it back returns `m` itself, with `m`'s own `enum_type` (previously a fresh map always typed with `mcrfpy.Perspective`). | — |
| **`get_dijkstra_map()` never returns a stale map.** A cached map is rebuilt on the next request after a walkability edit, or after an entity carrying the `collide=` label moves. A `DijkstraMap` you hold is a snapshot and doesn't change when the grid does (#425). | Call `get_dijkstra_map()` again each turn instead of holding a map; it's cheap while nothing changed. |
| **`GridData.clear_dijkstra_maps()` is removed.** The cache now manages itself: the first lookup after an edit drops every stale map, and cached maps are capped at `GridData.dijkstra_cache_budget` bytes (default 256 MiB, 4 bytes per cell per map; least recently used evicted first). `dijkstra_cache_bytes` reports current use (#425). | Delete the calls. Raise the budget on very large grids if several maps should stay cached. |
| **`VisibilityMask` compares by value and is hashable.** `==` compares `origin`, `fov_radius`, `grid_size`, `cells`, and `light_walls`/`algorithm` when FOV ran; it ignores `tick`, so the same view on two frames is equal (#405). | Use `is` to tell two records apart, and `a.cells == b.cells` to compare only what was visible. |
| **Dijkstra maps are windowed** (#445). `get_dijkstra_map(..., radius=None, heuristic=Heuristic.OCTILE)` computes a field over the roots' bounding box grown by `radius` (default: the whole grid, up to 511, so at most 1023×1023 cells), clipped to the grid. Distances up to the radius are exact, as is the whole field when `dm.complete`. Beyond that, and for positions **off the grid** (which used to raise `IndexError`), `distance()` returns the heuristic's estimate; `dm.is_exact(pos)` tells which. `path_from()` beyond the field returns `None`. `step_from()` / SEEK / FLEE take greedy steps there. `to_heightmap()` is window-sized; place it with `copy_from(pos=dm.window[:2])`. | Grids up to 1023 on a side behave as before (the field is the whole grid and complete), except that off-grid positions now return `None` instead of raising. Pass `heuristic=None` to make queries beyond the field raise `IndexError`. |
| **An object is in one collection, once.** Every way of adding an entity or drawable *moves* it: out of its old grid / parent / viewport, or out of its old slot in the same collection. `entities.append(e)` with `e` already in the grid moves it to the end (was a no-op); `insert`, `extend`, `[i] =`, slices and `Entity.__init__(grid=)` used to leave it in both grids (#447, #438). A value list that names one object twice (`extend([e, e])`, `[0:1] = [e, e]`, `+= [e, e]`) raises `ValueError`. | Code that relied on an entity being in two grids, or listed twice, must hold two entities. |
| **`-c` and `-m` imply `--headless`** (and so `--audio-off`), as running the binary as `python` already did: they exit without running a frame, so they no longer open a window or an audio device (#451). | Pass `-i` to keep the windowed engine after the command. |
| **The engine no longer needs a display to start** (#451). GL resources are created on first use, so pure-Python work (`-c`, `-m`, scripts that build Frames and Captions, `step()`) runs with no X server. Creating one with no display raises `RuntimeError` instead of aborting the process: `Texture()`, `Grid()`, a Sprite/Entity/GridData with no texture (they load `mcrfpy.default_texture`), screenshots and scene transitions. A headless frame loop that has to render exits 1 saying so. `mcrfpy.default_texture` is loaded on first use and is now assignable, which changes what Sprite/Entity/Grid use by default (assigning it used to have no effect). | Render headlessly under a virtual display: `xvfb-run -a mcrogueface ...`. |
| `automation.click()` / `mouseDown()` / `mouseUp()` / `dragTo()` raise `ValueError` for an unknown `button=`, which used to click LEFT. `'x1'` and `'x2'` are accepted (#428). | — |

## New

- **Headless simulation control**:
  - `mcrfpy.advance(ms)` advances the simulation by a given amount of time.
  - `get_metrics()['simulation_time_ms']` exposes the simulation clock (#396).
  - Python `Scene.update()` now runs under `step()` too (#350).
- **Reproducible randomness**: `mcrfpy.set_random_seed(n)` / `get_random_seed()` seed
  the engine's internal random streams (entity behaviours, `Sound.play_varied`).
  `get_random_seed()` always returns the seed that was used (#394).
- **Observing a grid at one frame**: `GridData.observe(origin, fov_radius, ...)` returns
  the walkable/transparent cells and entities as seen through a field of view, stamped
  with the frame number. It also returns an immutable `mcrfpy.VisibilityMask`
  (experimental). `observe()` doesn't disturb the grid's own FOV state (#402, #404).
- **Zero-copy numpy views**:
  - `with layer.edit() as view:` on `ColorLayer` (`(h,w,4)` uint8) and `TileLayer`
    (`(h,w)` int32) (#335).
  - `DiscreteMap` supports the buffer protocol (#334).
- **GridView input works again**:
  - Cell callbacks (`on_cell_click`, `on_cell_enter`, `on_cell_exit`) and
    `hovered_cell` work.
  - Overlay children are clickable.
  - Several views over one map track hover independently (#355, #357, #358, #360,
    #362, #363, #365, #366).
  - `find()` / `find_all()` descend into grids.
- `children.clear()` and `entities.clear()` empty a collection in one call, with the
  same teardown as `remove()` (#418).
- **Windowed Dijkstra maps** (#445): a field's cost no longer grows with the grid. On an
  8192×8192 grid a default map builds in about 45 ms and holds 4 MB (the full-grid
  map took about 6 s and 268 MB). New `DijkstraMap.radius`, `.window`, `.complete`,
  `.heuristic` and `.is_exact(pos)`. `mcrfpy.Heuristic.OCTILE` is octile distance
  for the map's own `diagonal_cost`; `find_path(heuristic=Heuristic.OCTILE)` accepts
  it too.
- New read-only module attributes, now visible to `dir()`: `animations`, `scenes`,
  `timers`, `save_dir`, `current_scene`, and the `default_transition*` settings (#356).
- `automation.loseFocus()` and `automation.mouseLeave()` for testing hover and focus.
- `mcrfpy.lock()` is now covered by stress, soak and re-entrancy tests. Its cost is
  documented in `docs/frame-lock.md`: each millisecond a lock holder spends inside the
  lock adds about 1 ms of frame time (#395).

## Fixes

**Crashes and hangs**
- Every interpreter mode (`-c`, `-m`, a script) aborted with no X display, even with
  `--headless` (#451).
- `FrameLock::acquire()` deadlocked the whole interpreter when two background threads
  used `mcrfpy.lock()` (#412).
- In headless mode, `mcrfpy.lock()` from a background thread blocked forever (#398).
- A headless `--exec` script that never exited could hang the process (#350).
- Adding a drawable to itself or to one of its descendants (`b.children.append(a)`
  where `b` is inside `a`) segfaulted. Every path that sets a parent (`append`,
  `insert`, `extend`, `__setitem__`, slices, `parent=`, `Frame(children=)`) now raises
  `ValueError` before changing anything (#442).

**Object identity and lifetime** (#430, #436)
- A subclassed Entity keeps its type and attributes through remove + re-append,
  `die()` + append, and `grid = None` / `grid = g`; `.step` callbacks and `on_step`
  keep firing after a re-append (#429).
- Memory leaks fixed: an Entity never added to a grid (#424); a grid containing
  entities (#437); every grid touched by `grid.at()` / `grid[x, y]` (GridPoint never
  released it); every Texture, Font and SoundBuffer wrapper; `get_metrics()`,
  `SoundBuffer.sfxr_params` and the `automation` click/drag helpers (#413); Vector
  setters such as `Line.start`, `Circle.center`, `entity.cell_pos`,
  `GridView.center` (#414); one timer reference per timer fire; every `Sound` and
  `Music` (#440).
- `mcrfpy.Sound(...).play()` with no reference held plays to the end, and the sound is
  freed once it finishes. It used to work only because every Sound leaked (#440).
- The audio device is now closed on every exit, including `sys.exit()` in an `--exec`
  script. This removes the `AL lib: (EE) alc_cleanup: 1 device not closed` line that
  every run printed, and the occasional OpenAL abort at shutdown (#400).
- `mcrfpy.window is mcrfpy.Window.get()` (they were two objects).
- A handler that refers to its own object (`btn.on_click = lambda *a: btn...`, set up
  inside a function) no longer crashes the engine after a garbage collection. The
  collector could wipe the handler's closure, or remove the handler, while a scene or
  parent still used it; this happened in 0.2.8 too. Callbacks on Frame, Caption, Sprite,
  Line, Circle, Arc, Grid (including cell callbacks), Viewport3D and Scene were all
  affected (#441).
- Reference cycles that run through engine-owned objects are now collected: a subclassed
  child or entity with an attribute pointing back at its parent, grid or scene; an entity
  whose `step` refers to itself; an unregistered scene whose `on_key` refers to itself;
  a dialog whose button's hover handler refers to the button while its click handler
  refers to the dialog. Each one leaked its whole tree (#441, #443).
- An object in a collection keeps one Python object for as long as it stays there, so
  `grid.entities[0] is grid.entities[0]` and a `weakref` to a contained `Caption` hold
  even if you kept no reference of your own. This used to be true only for subclasses.
  Iterating a collection no longer allocates a new Python object per item (#443).
- `.parent`, `find()` and indexing return the *same* Python object every time, including
  Python subclasses with their own attributes. Previously a subclass instance could come
  back as a plain `Frame` with its attributes gone (#369, #373).
- `insert()`, `extend()`, `__setitem__` and slice operations on collections now keep
  `.parent` correct; only `append()` used to (#377).
- An entity added to a grid with `insert()`, `extend()`, `[i] =` or a slice, or by
  re-running `Entity.__init__(grid=)`, stayed in its old grid's list and spatial hash
  too, and that grid kept stepping it; within one grid those paths duplicated it.
  `Entity3D` had the same bug across viewports, which could cost a subclass its
  identity (#447, #438).
- `children[i] = x` and `entities[i] = e`, with the new item already earlier in the
  same collection, replaced the wrong element (#447).
- `Frame(children=[...])` moves each child out of its old parent (it used to end up
  in both), and accepts every drawable type (Line, Circle and Arc were rejected).
  `children.extend()` adds nothing if any item is invalid (#442).

**Wrong values**
- Scrolling over a grid cell reported `MouseButton.X1` / `X2` to `on_cell_click`; it
  now reports `SCROLL_UP` / `SCROLL_DOWN`. One converter now serves every input
  dispatcher. The X1/X2 mouse buttons reach `on_click` and `on_cell_click` (they
  were never delivered) (#428).
- A cached Dijkstra map kept its old distances after the map changed, so a SEEKing
  or FLEEing entity could walk into a new wall (#425).
- `DijkstraMap.invert()` read freed memory if the map outlived its grid, and ignored
  the `collide=` label it was built with. It now copies the distance field instead
  of recomputing it (about 25x faster). A finished map keeps only that field, about
  a third of the memory it used to take (#425).

**Silent no-ops**
- `Grid.center_camera()` and `Grid.size = ...` used to do nothing (#370).
- `Frame(cache_subtree=True)` froze the content of its children; content changes now
  show up (#368).
- The turn manager now redraws a grid view when entities move (#351).
- Entities added with `entities.append()` / `insert()` / `extend()` never appeared,
  and entities removed with `remove()` / `pop()` / `del` stayed on screen, until
  something else redrew the grid (#446).
- Grid layer edits (`set`, `fill`, `edit()`, `visible`, `z_index`, adding and removing
  layers) never appeared inside a `Frame(cache_subtree=True)` (#427).
  `fill_rect()` never repainted at all, and a new `z_index` never changed the draw
  order.
- Hover now ends when the cursor leaves the window or the window loses focus (#367).

**Other**
- A game's own `scripts/` directory is `sys.path[0]` (as is a script's directory for
  `mcrogueface dir/script.py`). It was always the engine's `build/scripts`, so a game
  outside the engine tree couldn't import its own modules, and a module named like an
  engine demo script imported the engine's copy (#452).
- Tracebacks, `linecache` and profilers name a script's file; they said `File "<string>"`
  (#422).
- Shader uniform binding confused a `GridView` with a `GridData` (#371).
- `UICollection` repr names Grids correctly.
- `Grid` layer setters now invalidate the render cache (#376).
- Web build: `IDBFS` is exported, so the `/save` mount works under Emscripten 5 (#385).
  The shipped web game is the clean build, not the REPL hybrid (#384).

## Performance

Measured with the new Crucible benchmark, master vs. the 0.2.8 package, headless: about
**33% faster overall** (geometric mean 0.673) and peak memory 103 MB vs. 119 MB.

| Benchmark | Change |
|---|---|
| grid allocation | −59% |
| layer fill | −56% |
| entity churn | −43% |
| grid fill | −25% |

Where it comes from:
- `GridData` stores its walkable/transparent cells in dense arrays, and the chunk manager
  is gone (#332).
- `grid.entities` is backed by a vector, so indexing is O(1) (#329).
- An idle grid view no longer re-renders every frame (#351).
- Hot-path fixes found with the profiler:
  - property getters no longer re-import `mcrfpy` on every read (#331);
  - scalar animations skip variant machinery (−18%, #342);
  - key and input-state enum values are cached (−31% wall clock, #344);
  - scenes that aren't subclassed skip the `update` lookup (#343);
  - `GridView` caches its internal grid object (−97% on that path, #348).

## Build, packaging and tooling

- **`make deps`** builds SFML, libtcod and CPython from a fresh clone.
  `tools/fetch_dev_headers.sh` covers machines without root.
- Platform targets:
  - `make python-windows` and `make python-wasm` stage the interpreter for each platform;
  - pydebug / free-threaded / TSan CPython variants are available for
    `make debug` / `asan` / `tsan`.
- Packaging:
  - The binary's library search path is relative to the executable (`$ORIGIN`), so
    packages no longer depend on the build machine's paths.
  - Packaged stdlib `.pyc` files are compiled by the embedded 3.15, not the host Python.
  - `make package-linux-full` is a tested configuration for running `socket` / `ssl` /
    `asyncio` / `selectors` on a background thread.
- **Profiling**: `make profile`, `make callgrind`, the `perf` + Python-trampoline recipe,
  `tools/fp_walk_gdb.py`. The Crucible (headless, deterministic) and the Gauntlet
  (on-screen stress test) are the benchmarks.
- **Docs are tests**:
  - The site's 282 code samples run in the test suite and render deterministic preview
    images.
  - `make release-docs` regenerates the API reference, stubs, man page and
    `api/manifest.json`.
  - `tools/api_delta.py` diffs the API between two git refs.
- CI builds from a clean checkout and fails if a test run modifies tracked files (#401).
- Test suite: 639/639 (up from ~300 at 0.2.8); 82 tests that had been silently not
  running were fixed, and `tests/demo/` is gated in CI (#372).

## Known issues

- **#416, #417**: changing engine objects from a background thread *without*
  `mcrfpy.lock()` can crash. Two threads holding the lock at once are only kept safe by
  the GIL, so the free-threaded (no-GIL) build is not supported.
- **#410**: a lock holder that re-acquires immediately can starve the main loop.
- **#448**: the clock and the window are still coupled. Windowed `step()`/`advance()` are
  silent no-ops, and headless `--run-forever` runs frames on a frozen simulation clock.
- **#420**: `mcrf-init.sh` scaffolds projects for Python 3.14.
- **#399**: the light/full stdlib presets ship the same stdlib.
