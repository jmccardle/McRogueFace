# McRogueFace 0.3.6 — release notes

> Changes since the `0.3.5` tag.

## Breaking changes and upgrade notes

| Change | What to do |
|---|---|
| **A position is a `Vector` or a pair of real numbers, everywhere** (#540, #543). A bare number (`Frame(size=5)` used to be `(5, 0)`), `None`, an object that only has `.x` / `.y`, and `bytes` / `bytearray` / `memoryview` / `range` / `str` are `TypeError`. `Vector(5)` and `Vector(None)` raise `TypeError`. `HeightMap.sparse_kernel_from` weight keys must be positions (the `.x` / `.y` fallback is gone). | Pass `(x, y)` or a `Vector`. Numbers may be int, float, `bool`, or any object with `__index__` / `__float__` (numpy scalars, `Fraction`, `Decimal`). |
| **`nan` / `inf` raise `ValueError` and out-of-range values `OverflowError`** in constructors, setters and animation targets (#540), as `move()` / `resize()` already did. `Frame(pos=(inf, 0))`, `frame.x = nan` and `frame.animate("x", inf, 1)` used to be accepted; `Frame(pos=(1e39, 0))` stored `inf`. Animation `duration` must be finite and not negative. | Fix the value. `Grid(center_x=nan)` still means "default camera". |
| **A cell position is floored, not truncated**, wherever a cell is addressed (`Grid.at`, `grid[x, y]`, layers, `Entity.cell_pos` / `grid_pos`, path steps, waypoints, `bresenham`, `draw_fov`, sizes and `pos=` of the map classes) (#540). `Vector(1.7, -0.2)` is cell `(1, -1)`; it was `(1, 0)`. An integer too large for a C int is `OverflowError` rather than wrapping (`2**32` was cell 0). | Floor or round positions yourself if you relied on truncation of negative values. |
| **Grid camera limits are enforced** (#558). `zoom <= 0` is `ValueError`, as is a `zoom`, `size`, `center` or cell size beyond the limits (minimum zoom `max(w + h, 1) / (INT_MAX / 4)`), from the constructor, a setter or `Drawable.resize`. A failed `Grid(...)` changes nothing. Animations cannot raise mid-flight: an animated value outside the limits shows the limit for those ticks (an overshooting easing rejoins its curve), and the first-draw texture assignment is capped the same way. | Keep zoom and sizes sane; animate within limits. |
| **A screenshot is the last complete frame** (#529). The first screenshot, before any frame has rendered, renders the scene. After that it returns the previous frame, so a mutation with no frame between it and the screenshot is not in the picture (a Timer-callback screenshot is the frame before the callback). Headless `step()` / `advance()` draw nothing; a headless screenshot re-renders only when a step has finished since the last render. A screenshot requested during a render raises `RuntimeError`. | Run a frame (`mcrfpy.step(0)` headless) between changing the scene and taking the shot. |
| **`step()` / `advance()` inside a callback raise `RuntimeError`** (#551), headless or windowed (windowed used to return `0.0`). From a timer callback it crashed. | Do not advance the clock from a callback; set a flag and step outside the frame. |
| **`sys.exit()` in a callback no longer finalizes Python mid-frame** (#557). The frame stops dispatching handlers, unwinds, then the process exits with the same code and message. Under `-i` the exit is printed and the game continues. If a background thread drives the clock, it ends only that thread. | Nothing for most scripts. Code after a binding that dispatches callbacks (`Scene.activate`, `Grid.step`, `automation.*`) does not run once an exit is pending. |
| **`mcrfpy.lock()`: every non-nested call waits for the next frame window** (#535), even if one is open. Once the engine is shutting down, `lock()` raises `RuntimeError("engine is shutting down")` (#556). The thread that drives the clock keeps its no-op lock. | Do I/O outside the lock; catch `RuntimeError` in worker threads. |
| **A `z_index` given before `append` is kept** (setter, constructor argument, animation) (#552). Before, `append` / `extend` overwrote it, so such a drawable drew in insertion order. Drawables with no chosen `z_index` get ten above the highest in the collection (0 for an empty one). Equal `z_index` keeps insertion order; `Grid.step` acts entities with equal `turn_order` in collection order. Appending an object again no longer brings it to the front once its `z_index` has been set. | Check scenes that set `z_index` before appending: they now draw as written. To raise an object, assign a higher `z_index`. |
| **`BSP.split_once` raises `ValueError`** for a position outside the node (`x < position < x + w`, both ends exclusive) and leaves the tree untouched (#540). Splitting a node that has children replaces them (it used to add two more). `BSP(pos, size)`, `split_recursive` and `dig_bezier` raise `ValueError` where libtcod's int arithmetic would overflow. | Pass an interior position. |
| **`ColorLayer` / `TileLayer(grid_size=...)` negative sizes raise `ValueError`**; `(0, 0)` still means "size from the grid" (#558). A float size or position is floored. | |
| **`DiscreteMap.__init__` raises `BufferError` while a `memoryview` of it exists**; `mask()` is now a view of the map (#560). `VoxelPoint` raises `RuntimeError` when its cell or viewport is gone. `Viewport3D(camera_pos=, camera_target=)` raises on an invalid value instead of ignoring it. | Release views before re-initialising. |
| **Pathfinding from an `Entity` starts at its logical cell** (`path_to`, endpoints), not its draw position (#540). | |
| **Drawable constructors clamp `opacity`** like the setter. An entity's `sprite_grid` is cleared to `None` when its tile size changes; an entity's `perspective_map` is dropped when it moves to a grid of another size (#558, #560). | Re-assign `sprite_grid` after changing the tile size. |
| **Real subclasses and name-alikes**: engine type checks use the type object (#559). A subclass of `Frame` is now accepted where a `Frame` is required; a class that is merely *named* `mcrfpy.Frame` is rejected (it used to crash). | |

## Frame lock and exit paths (#535, #556, #557)

- **The lock barrier is load-independent** (#535). A window serves only threads that were already waiting when it opened, each at most once. `mcrfpy.get_metrics()` gains `lock_waiting`, `lock_windows` and `lock_admissions` (live counts) so contention can be checked without a clock. The frame-lock tests assert counts and ordering, not milliseconds; they no longer fail on an overloaded machine.
- **Exit no longer hangs with a thread blocked in `lock()`** (#556), including `ThreadPoolExecutor` and `asyncio.to_thread` workers and a daemon thread that drives the clock. The waiters get the `RuntimeError` above. A Python version that changes the private `threading` hook this relies on fails at `import mcrfpy` with a message, not at exit. The web build is single-threaded and ships no `threading`, so it has no hook.
- **Exit from a callback** (#557): timer, animation, input, scene, hover and trigger callbacks, the ImGui console and warning hooks all defer the exit to the top of the loop. Previously the interpreter finalized under live frames and leaked `__main__` (LeakSanitizer under `make asan-test`).

## Positions, camera and layers

- **`fill_rect` accepts a tuple, list or `Vector` for `pos` and `size`** (#533) and names the bad argument in its error. Extreme rectangles no longer overflow (one wrote past the buffer).
- Errors raised by a position's own `__len__` / `__getitem__` / `__index__` propagate with their type instead of being replaced by a `TypeError` (#540). A list mutated by `__index__` while it is parsed no longer crashes (#543).
- `HeightMap.get_interpolated` / `get_normal` with `nan` raise `ValueError` (segfault before). `add_bsp` / `multiply_bsp` regions off the map no longer paint every cell. `HeightMap(size=)`, `pos=` and `size=` keywords of the map operations are range-checked (`pos=(2**32, 0)` was `(0, 0)`).
- Layers repaint only the chunks in view (the range was one chunk too far on both axes) and a dirty chunk is drawn as one vertex array instead of one draw per cell (#536, #539). Output is pixel-identical; `get_metrics()` gains `grid_chunks_repainted`. The web build draws textured vertex arrays, which also makes `mcrfpy.Arc` draw there (#542).
- `Entity.at()` bounds against the entity's own perspective map (#560).

## Memory-safety fixes with visible effects (#558, #559, #560)

- A binding no longer reads or validates engine state and *then* runs user code (`__index__`, `__float__`, `__bool__`, a warning hook, a finalizer) on its arguments: arguments are converted first. Six confirmed crashes (`ColorLayer.draw_fov`, `ColorLayer.set`, layer and `DiscreteMap` subscript assignment, `BSPNode.contains`, `Entity.set_behavior`) and the same pattern in about forty more bindings (layer and `GridData` `apply_*`, `HeightMap` / `DiscreteMap` region operations, `sparse_kernel`, `NoiseSource.sample`, collection slices and `pop`, `Shader.set_uniform`, `Sound` / `Music` loop and others).
- An exception from `__bool__` propagates from every boolean setter that ignored it (`Timer.active`, 3D bool setters).
- Replacing a collection member (`children[i] = x`, slice assignment) no longer leaks when a displaced child's `__del__` empties the collection.
- 3D: iterating `Viewport3D.entities` while adding and removing no longer reads freed memory and is O(1) per step; `VoxelGrid.offset` / `rotation` and `VoxelPoint.height` / `cost` report conversion errors; an entity's per-cell visibility memory resets when its viewport or grid size changes.
- `PropertyBinding`, `WangSet`, `AutoRuleSet` and `TileMapFile.apply_to_tile_layer` identify types by type object (see the table).

## Docs and tooling

- **Cookbook pages and the procgen demos are tested snippets** (#541). Every code fence of the 29 cookbook pages comes from a snippet in `tests/snippets/` (62 new; wrong ones repaired), and the site injects them (`inject_snippets.py`), so the pages cannot drift from the API. `# region:` markers pick part of a snippet; the stale January copies under `docs/cookbook/` and its committed PNGs are removed; `sprite_labeler.py` moved to `tools/`. `tools/release.sh` fails on drift. `tools/lint_snippet_batch.py` and `tests/snippets/CONTRIBUTING.md` set the rules; a snippet may exit inside a function body and opt in to `mcrfpy.automation` with `# snippet: allow-automation`.
- Headless-mode page: snippets 411 / 412 cover `step` / `advance` / `seed` and Timer behaviour.
- Docstrings say that integer positions are floored and non-finite values raise; `step()`, `lock()`, `zoom`, `center`, `animate` and the screenshot functions document the rules above. `tools/lint_bindings.py` gains rules for check-then-convert (#558) and type-by-name (#559).

## Packaging and CI

- **A Windows CI job** (#538): `make deps-windows` builds SFML 2.6, libtcod-headless and the pinned CPython from source with MinGW (the python.org embeddable download is verified against a pinned sha256, and a version with no pin is an error), cross-compiles, packages and runs `tools/smoke_package.py` under Wine. It builds and passes on GitHub Actions. Dependency builds are stamped and revalidated on every run.
- **Linux and web packages are built and smoke-tested in CI** from a clean checkout on ubuntu-24.04 (clean Debian 13 / Ubuntu 24.04 containers; headless Chromium for web), on GitHub Actions and the Forgejo runner (#534, #512). The CI suite runs under `xvfb-run -s "-noreset"` (#513).
- Fresh-clone builds: `rsync` is documented and checked, the staged stdlib is verified, the web configure fails on missing python-wasm outputs and `tools/build_deps_wasm.sh` builds the web build's inputs (#512).
- The profiler overlay names the bound `profiler_key` (and is omitted when it is `None`) instead of always saying F3; a literal U+FFFD from a web IME is delivered, while malformed UTF-8 is dropped (#511).
- Web: an `mcrfpy.Arc` pixel test runs in headless Chromium, with a row in `docs/web-parity-matrix.md` (#542).
- **`tests/run_tests.py -j N`** runs the suite in N workers, each on its own private Xvfb and in its own working directory. On an 8-core desktop the suite drops from about 5 minutes to under 2 at `-j6`. `--shard i/n` splits it across CI jobs; `-h` prints usage; unknown arguments are errors. `make *-test TEST_JOBS=N` passes it through. The Forgejo CI (`.gitea/workflows/ci.yaml`) runs on every branch push with `-j 8`. Release packaging stays on GitHub Actions; the Forgejo copy of `package.yaml` is manual-only.
- **`make release` never renders on the caller's display.** Every rendering step runs under its own Xvfb and the suite runs with `-j` (default `nproc - 2`). An inherited `DISPLAY` used to put every test window on the desktop, slow enough to time tests out.
- Debug and sanitizer engines skip the `mcrf_project deps` tests with the reason shown: `deps` refuses an interpreter with ABI flags by design.

## Performance: the Gauntlet

The Gauntlet (`make gauntlet`) ramps each trial's load in ~1.6× steps until a frame misses the 16.67 ms budget and records the highest load that held. It is a windowed stress test on a desktop, not a controlled benchmark: desktop noise moves a trial by one or two steps, so only changes of about 2× mean anything.

Three back-to-back runs of the 0.3.6 code, compared with the 0.2.8 baseline (median of three runs):

| Trial | Unit | 0.2.8 | 0.3.6 (median) | Ratio |
|---|---|---:|---:|---:|
| entity_swarm | entities | 4123 | 4123 | 1.00 |
| animation_storm | animations | 10555 | 10555 | 1.00 |
| grid_titan | grid side | 810 | 810 | 1.00 |
| pathfinder_rush | queries / tick | 450 | 281 | 0.62 |
| ui_avalanche | UI elements | 1611 | 4123 | 2.56 |
| sightline_siege | FOV entities | 537 | 336 | 0.63 |

- **Overall score 1.00** against the baseline (runs 2 and 3; run 1 missed the budget at the first step of two trials and scored 0.47).
- **UI-heavy scenes hold about 2.5× more elements.**
- **Pathfinding and FOV came in one step lower in every run.** That is within the noise the Gauntlet allows, but it was consistent.
- **The machine changed between the two measurements:** the baseline was recorded on Debian 12 (kernel 6.1, glibc 2.36) and 0.3.6 on Debian 13 (kernel 6.12, glibc 2.41, newer Mesa). Part of any difference may be the platform, not the engine.

## Known gaps

- `HeightMap.dig_hill` / `dig_bezier`: the sign of the height decides raise or lower, as in libtcod. A positive height does nothing to higher terrain, and the docstrings ("only lowers cells") say otherwise (#553).
- `HeightMap.sparse_kernel` with a kernel whose weights sum to zero returns `inf` / `nan` (#561).
- Windowed screenshots after the first read the GL back buffer after the swap; contents are undefined on page-flipping drivers (not run on real hardware) and include the profiler overlay and console (#554). A windowed screenshot from a background thread aborts (#545). Web-build screenshots capture nothing (#546).
- Snippet handler bodies (`on_key`, `on_click`) are registered but never run by the snippet harness (#544). Several test scripts pass without asserting anything (#555).
- Two slice-assignment commit loops and `concat` / slice reads in the collections still call user code before committing (#558 review, items 3 and 4).
- `#513` item 4 is deferred: a failed `--exec` script can exit 0 in windowed mode. On a fresh clone `mcrf_project init` needs the generated `stubs/mcrfpy.pyi` (CI generates the docs and stubs before the tests).
- The per-push Forgejo CI does not build the web target; only the release packaging on GitHub does (#534). A web-only regression in 0.3.6 was caught by the release's browser smoke test, not by CI.
- A `ColorLayer` over a non-opaque background applies alpha twice; translucent layer cells are not covered by the pixel tests (#542).
- Web key input is tested in headless Chromium only (`docs/web-key-test-sheet.md`); X11 Shift state in the web text path is not addressed (#511 item 1).
