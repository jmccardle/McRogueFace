# McRogueFace - Development Roadmap

**Version**: 0.3.3 released, master is 0.3.4-dev | **Era**: McRogueFace (2D roguelikes) -- on the road to 1.0

For detailed architecture, philosophy, and decision framework, see the [Strategic Direction](https://dev.ffwf.net/forgejo/john/McRogueFace/wiki/Strategic-Direction) wiki page. For per-issue tracking, see the [issue tracker](https://dev.ffwf.net/forgejo/john/McRogueFace/issues) and the [0.3.0 release board](https://dev.ffwf.net/forgejo/john/McRogueFace/projects/8) (release notes per version: `docs/release-notes-*.md`).

---

## What Has Shipped

**Alpha 0.1** (2024) -- First complete release. Milestone: all datatypes behaving.

**0.2 series** (Jan-Mar 2026) -- Weekly updates to GitHub. Key additions:
- 3D/Voxel pipeline (experimental): Viewport3D, Camera3D, Entity3D, VoxelGrid with greedy meshing and serialization
- Procedural generation: HeightMap, BSP, NoiseSource, DiscreteMap
- Tiled and LDtk import with Wang tile / AutoRule resolution
- Emscripten/SDL2 backend for WebAssembly deployment
- Animation callbacks, mouse event system, grid cell callbacks
- Multi-layer grid system with chunk-based rendering and dirty-flag caching
- Documentation macro system with auto-generated API docs, man pages, and type stubs
- Windows cross-compilation, mobile-ish WASM support, SDL2_mixer audio
- Behavior/Trigger turn manager: `grid.step()`, entity labels, `cell_pos`, Dijkstra-backed pathfinding (#295-#303)

**Proving grounds**: Crypt of Sokoban (7DRL 2025), then 7DRL 2026 -- both shipped on the same engine. The 2026 jam surfaced hotfix-worthy issues (SDL key scancodes, composite textures) that have since landed on master.

---

## Current State (2026-10-14)

**0.3.3 is released** (tag `0.3.3` = 88baca4; Linux, Windows and WASM packages in `dist/`), pushed to Forgejo and GitHub with tags 0.3.1-0.3.3. Master is `0.3.4-dev`. Releases are cut by `make release VERSION=x.y.z` (#475); the version header is the only source of truth, the tag comes last, and the script never pushes or publishes.

### The 0.3 series (October 2026)
- **0.3.0** (26cd8b6): CPython 3.15 embed, frame pointers (#421), exit teardown (#468), `mcrfpy.lock()` windows, one package per platform (#435). Notes: `docs/release-notes-0.3.0.md`.
- **0.3.1 / 0.3.2**: release pipeline (#475), sprites fill their cells (tile layers and entities scale to the cell), `Caption.advance` (#479), `lock()` serves each thread once per frame (#410), working shipped templates (#380).
- **0.3.3**: `Caption.advance` is a pure pen advance (the 0.3.2 `pos.x` bug), Caption font metrics (`ascent`, `descent`, `line_height`, `baseline`; #478/#494), `Font` metrics from Python.
- Known doc debt: pages listed in #491 still describe the old entity-position behaviour; the 0.3.2 docs describe the buggy `Caption.advance`.

### API freeze and fuzzing (carried over, still the 1.0 path)
The public surface is locked behind the API-surface snapshot test (#314) and `api/manifest.json` (`tools/api_delta.py REF1 REF2` diffs it by ref). Remaining freeze work: a last bundled breaking-change pass, then document the stable API as the contract; 3D/Voxel stays `experimental` and outside the freeze. The libFuzzer+ASan harness (#283, #312) covers grids, property types, anim/timer/scene lifecycles, FOV, procgen, pathfinding, audio DSP, import parsers, texture factory and shader bindings; its bugs (#258-#325) are fixed.

## Next Releases

Milestones are not set up in Forgejo; these groupings are from the labels and the work in flight. 0.4.0 is a **proposal** for John to confirm.

### 0.3.4 (in flight: five agents, branches unmerged)
| Group | Issues |
|---|---|
| Packaging and project tooling | #498 (package lacks `_sysconfigdata`, tier1 bug), #500 (`mcrf_project run` finds an installed engine), #499 (project dependencies -> `.venv`, bundled by `dist`) |
| Engine startup / `sys.path` | #502 (document the order; make #452's test hermetic; tier1 bug), #501 (expose engine flags and run configuration to scripts) |
| Input (requested by mcrf-term) | #497 (modifier keys from the event), #495 (text-entry event), #496 (configurable console hotkeys) |
| Grid | #493 (`default_fov` is dead, tier1 bug) |
| Color names | #489 / #458, branch `issue-458-color-names`: catch-up merge, one deduplicated list, lowercase/no-space names normalized at parse time. Held for John's review |

### 0.4.0 candidates (proposed)
Theme: a stable foundation for simulation and tooling, ahead of the 1.0 freeze.
- **Clock and determinism**: #448 clock ownership (one simulation clock, realtime or manual driver), #408 unrecorded RNG seeds, #403 `GridData` identity, #393 deterministic animated-snippet capture.
- **Textures and rendering**: #454 textures resolve when drawn (own -> GridView -> GridData -> default), #455 non-16 / non-square cells, #352 perspective grids take the render early-out, #347 SFML vs SDL2 renderer parity, #390 SDL2 Fail-Early hardening.
- **Web**: epic #387 (parity and divergence testing; the only open tier1 epic).
- **Grid and FOV design**: #434 `compute_fov()` vs entity perspective, #444 Dijkstra at 8192x8192.
- **Python environment**: #337 numpy strategy (builds on #499/#500 project tooling).
- **Threading**: #416 unlocked-mutation use-after-free (tier2 bug). #417 and #336 (free-threading) stay tier3.
- **Design proposals**: #349 hybrid scene serialization, #459 evolved-programs epic.

Later (tier3/4): #471, #415, #439, #338, #152, #124, #107, #67, #62, #54, #70, #55, #220.

### Follow-ups not yet filed
- An entity "move to cell and slide" helper.
- Multi-tile entities (`sprite_grid` / `tile_width`) are never drawn.
- Open #494 decisions: `Font(path)` raising IOError, the Windows build needing the `modules/SFML` submodule for FreeType headers, `bounds` being the ink box on desktop but the line box on web, and `Font.metrics` returning a plain tuple.
- Machine concern: `~/.local/bin/python3.15` is a symlink into a `/tmp` scratchpad (3.15.0rc3); mcrf-term's `.venv` depends on it.
- Gauntlet baseline (`tests/benchmarks/gauntlet/run_gauntlet.py`) should be recaptured on a quiet machine; resolution is ~2x too coarse (#472).

---

## Previously Shipped

### Merged from `sim/integration` (October 2026)
- **CPython 3.15 embed (`feat/python-315`, merged as `fb63add`)** -- `modules/cpython` pinned to **v3.15.0** final (`d220409`; was 3.15.0rc3 `8a8eb0b` -- the rc3->final diff touches only `_remote_debugging`, no build files). 3.15 builds with frame pointers by default (PEP 831); the engine now does too (#421). Interpreter version is derived from `Include/patchlevel.h`, not hardcoded. Per-platform staging: Linux `make deps` -> `__lib/`; Windows `make python-windows` (python.org embeddable zip, import lib built via `objdump` export table -> `dlltool`); WASM `make python-wasm` (CPython's `Platforms/emscripten`, bootstrapped through the native build python because it needs >=3.12; Node from emsdk via `--host-runner`). Follow-up fixes on the branch: **6f0dc3f** staging is pinned to the submodule version (a leftover 3.14 `__lib` made `make deps` skip the build, then fail linking `-lpython3.15`) and the build refuses a stray in-tree `Include/pyconfig.h` (it shadows the build's own and broke wasm32 with a `LONG_BIT` error); **3be5cb5** Windows packages never shipped the `.pyd` extension modules -- `socket`/`ssl`/`asyncio`/`ctypes`/`sqlite3` were unimportable, including in 0.2.8 (#419) -- now staged to `lib/Python/DLLs`; **b538691** WASM links export `__PyRuntime` + the Emscripten trampoline offset, and `wasm_stdlib/lib/python3.15` adds `_colorize`/`pathlib`/`email`/full `importlib` (fixes the #392 REPL traceback). Verified: Linux suite 638/638; Windows under Wine (asyncio TCP, OpenSSL 3.5.9, 30/30 sampled unit tests, packaged zip runs outside the tree); WASM boots and renders in headless Chromium with a real REPL traceback.
- **Frame pointers in Release (#421, closed)** -- `MCRF_FRAME_POINTERS` (default ON; no-op for wasm/MSVC) adds PEP 831's `-fno-omit-frame-pointer -mno-omit-leaf-frame-pointer` (**91308e8**). Cost: engine-only Callgrind Ir +1.4% (Crucible) to +12.1% (tight-getter worst case), whole-process Ir +0.2-0.4%, wall clock inside noise, `.text` +1.4 KB. Verified with real `perf record --call-graph fp`: every sample under `runSimFrame` unwinds to `main` with `py::` trampoline frames named in between; FP-off reaches `main` in 0 samples. libpython is now `--strip-debug` (keeps `.symtab`, ~+1 MB). **1921dcb**: `sys.version` read `v3.15.0-dirty` on a clean checkout because CPython's `git describe --dirty` runs from the out-of-tree build dir -- fixed with `GIT_WORK_TREE` + a fresh `getbuildinfo.o` in `build_python.sh`/`build_python_wasm.sh`. Tools: `tests/regression/issue_421_frame_pointer_test.py` (objdump prologue check), `tools/fp_walk_gdb.py` (no perf perms), `tests/benchmarks/fp_loop_workload.py`; workflow in `docs/profiling.md`. The perf capture found `entity.cell_pos` is 27% of a movement-heavy loop, and that it's the **#414** leak: `PyObject_to_sfVector2f/2i` never DECREF the `PyVector::from_arg` result (1 leaked Vector per set across cell_pos/draw_pos/sprite_offset/GridView.center/...). Root cause posted on #414, not yet fixed. Filed **#422** (`--exec` tracebacks say `<string>`).
- **Thread-safety probe (1a162fa)** -- unlocked background mutation crashes GIL builds via hover/click/step use-after-free (#416); `mcrfpy.lock()` is clean 150/150 but is a frame barrier, not a mutex, so two holders race once the GIL is off (#417, blocks #336). Architecture (harden vs. document-as-mandatory; lock semantics) is **undecided**.

### Recently Shipped (April 2026)
- **#294** -- `entity.perspective_map` replaces flat `vector<UIGridPointState>` with a 3-state DiscreteMap (UNKNOWN/DISCOVERED/VISIBLE). Per-entity FOV memory is now serializable, swappable, and structurally enforces visible-as-subset-of-discovered.
- **#315** -- Pathfinding API extended with built-in heuristics (Euclidean/Manhattan/Chebyshev/Diagonal/Zero), multi-root Dijkstra, FLEE primitives (invert + descent), and an interactive demo. EntityBehavior SEEK/FLEE refactored to a `PathProvider` strategy.
- **Phase 5.2** -- six performance benchmark scripts under `tests/benchmarks/` covering grid.step(), FOV writeback cost, spatial hash vs. O(n), pathfinding with collision labels, multi-GridView render, and Dijkstra variants. Baselines under `tests/benchmarks/baseline/phase5_2/`.
- **Phase 5.3** -- documentation regenerated; `tools/generate_stubs_v2.py` rewritten as introspection-based so it can no longer drift from the C++ source.

### Recently Shipped (July 2026)
- **Grid input revival + the GridData/GridView type split (#355, #357-#368, #370, #371)** -- merged to master as `36e74e0`; 15 issues closed. Grid input had been dead since the #252 GridView unification: cell callbacks never fired, grid children were unclickable, cell hover was stuck. The cause was structural -- `UIGrid` inherited *both* `UIDrawable` and `GridData`, so every map secretly carried a second camera and RenderTexture that nothing on screen corresponded to, and input, children, and dirty propagation all dead-ended in it. **Input fix (#355, #357, #358, #360, #362, #363, #365, #366)**: cell callbacks and hit-testing move to `UIGridView` -- input belongs to the *camera*, not the data, so two views over one map track hover independently; a `weak_ptr` view registry replaces the single `owning_view` (N views, one map); `find()`/`findAll()` descend into grids again; the ImGui scene explorer can expand them; hover-exit fires when the cursor leaves the window; `UICollection.repr` names Grids instead of `"UIDrawable"`. **Type split (#359, #361, #364, #370, #371)**: `UIGrid` is **deleted, not demoted**. `mcrfpy.GridData` is now public and standalone-constructible -- a map with no position, size, camera, or `render()`; only `UIGridView` is a `UIDrawable`. `mcrfpy.Grid` is an *alias bound to the same type object* as `GridView` (not a subclass -- `isinstance` works both ways, no MRO to explain). Overlay children belong to the view; entities belong to the map. Breaking change: `entity.grid` now returns a `GridData` (the setter still accepts a view). The split flushed out four latent bugs, each verified against unmodified master before being fixed: **#370** `Grid.center_camera()` and `Grid.size = ...` were silent **no-ops** (writing to the ghost camera nothing rendered); **#371** the shader uniform binder did type-confused pointer arithmetic, reading a `GridView` wrapper as a `_GridData` wrapper -- which "worked" only because both wrappers had identical layout and both C++ classes happened to put `UIDrawable` at offset 0; **#368** `markContentDirty()`'s walk up the parent chain was gated on a flag with exactly one `clearDirty()` call site in the whole engine, so the guard was permanently false and content invalidation propagated **nowhere** -- `Frame(cache_subtree=True)` silently froze its subtree's content (text never updated, colours never changed; only movement survived, being already on an unconditional path). The walk is now unconditional; entity movement, the hot path, is unaffected (164 ns/move). **#367**: hover state is cleared on focus loss. Suite 329/329. Riding along on the same branch: generated docs are **untracked** (regenerated by `tools/hooks/pre-commit`, installed via `make install-hooks`, and shipped inside release artifacts), with a compact `api/manifest.json` -- signatures + docstring hashes + carried-forward `since`/`modified` lifecycle metadata -- as the one committed exception, so API drift stays diffable by ref via `tools/api_delta.py REF1 REF2` without rebuilding at old commits.
- **Grid render/memory sprint (#351, #334, #338, #332, #335; safety #353/#354)** -- a batch review closed dead/unbottlenecked issues (#117 entity pool, #145 TexturePool -- no demonstrated allocation gate; reopen after profiling) and shipped six grid-layer changes. **#351**: `UIGridView::render()` had *no* dirty check post-#252 and cleared+redrew every frame -- added a `GridData::content_generation` counter (bumped at every data/layer/entity mutation choke point) so an idle, non-perspective, childless view re-blits its cached texture instead of re-rendering; fixed a latent bug where Python entity `set_position`/`set_spritenumber` updated the spatial hash but never invalidated render (masked by the unconditional redraw). A follow-on regression (**6b99a1b**): the C++ turn manager `py_step` mutates entity cells directly, bypassing the setters -- it now calls `GridData::markCompositeDirty()` once per step (must qualify `GridData::`; `using UIDrawable::markCompositeDirty` shadows the data-layer override). **#334**: `DiscreteMap` exposes its `uint8_t` plane via the Python buffer protocol (`tp_as_buffer`, 2D zero-copy numpy/memoryview views). **#332**: `GridData` migrated from per-cell `UIGridPoint` structs (24 B for 2 B payload) + the whole chunk manager to two dense `std::vector<uint8_t>` planes (walkable/transparent) -- deleted `GridChunk`/`ChunkManager`/`CHUNK_THRESHOLD`, stripped `UIGridPoint` to a Python-accessor namespace, net **-257 lines**; pathfinding's `isCellWalkable`/`cellWalkable` were the critical non-obvious callers. **#335**: `ColorLayer`/`TileLayer` get zero-copy numpy views through a new `with layer.edit() as view:` context manager (implements the #328 convention; `__exit__` marks the layer dirty) -- `(h,w,4)` uint8 and `(h,w)` int32. **#338** (issue left open): safe subset only -- `rotationTexture` is now lazily allocated (`unique_ptr`) on Grid/GridView; deferred the `render_sprite` relocation as not worth the churn. Validation was delivered via **The Crucible** (**#354**, `tests/benchmarks/crucible.py`) -- a headless, deterministic, wall-clock A/B harness that safely replaces the windowed Gauntlet (which OOM-hard-locked the desktop during grid ramp). **#353** hardened the Gauntlet with `predict_bytes`/`max_load` refusal + an `RLIMIT_AS` backstop + RSS watchdog. Crucible A/B, current master vs the 0.2.8 dist artifact (both headless): grid_alloc **-58.9%**, layer_fill **-56.1%**, entity_churn **-43.0%**, grid_fill **-25.4%**, fov_storm/step_swarm/path_queries single-digit; **geomean 0.673 = ~32.7% faster overall**, peak RSS ~103 vs ~119 MB -- the big wins track #332 SoA + #329 indexing. Suite 314/314. Remaining in the thread: **#333** (lazy TCOD map rebuild, unblocked by #332), **#352** (perspective-grid early-out), and the deferred #338 relocation.
- **Native profiling rig + hot-path perf batch (#345, #331, #342/#343/#344/#348)** -- a Callgrind/perf profiling workflow (`make profile` -> `build-profile/` RelWithDebInfo + frame pointers; `make callgrind SCRIPT=...`; `docs/profiling.md`) landed as **#345**, then drove five measured fixes. **#331**: hot property getters stop re-importing `mcrfpy` per call. **#348** (found *by* Callgrind, not by guessing): `UIGridView::get_grid` re-allocated a throwaway Grid wrapper + weakref every call at 0% cache hit -- now holds one persistent strong ref (`get_grid` inclusive **72.6M -> 2.1M Ir, -97%**). **#342**: scalar-float animation fast path bypasses two per-frame `std::variant` visits (`Animation::update` **-18%**, variant machinery **473M -> 99M Ir**) -- the profiler *disproved* the guessed strcmp-cascade and weak_ptr-lock hypotheses and found the real cost. **#344**: memoized Key/InputState enum members instead of rebuilding via `EnumMeta.__call__` per event (enum-ctor **19.18M -> 0.228M Ir, -99%**; wall-clock -31%). **#343**: skip the per-frame `GetAttrString("update")` for non-subclassed scenes (**4,559 -> 3 Ir/frame** on the real `doFrame` loop; measuring it required bypassing headless `step()`, which doesn't call `updatePythonScenes()` -- filed as **#350**). Harness total instructions **3,522.9M -> 3,211.5M (-8.8%)**; suite 307/307 with new regression tests `issue_34{2,4,8}_*`. Durable sprint doc with A/B numbers at `docs/sprint-perf-342-348.md`. Spun out **#349** (hybrid declarative scene serialization, Major Feature, tier2) from the finding that `automation.screenshot()` PNG encode is ~96% of a render-profile's instructions.
- **Tier1 memory-model batch resolved** -- all five pre-1.0 freeze decisions from the 2026-07-02 review are closed on master. **#326**: Color/Vector are value types forever (copies at every property boundary; write-through proxies rejected); **#328**: `with layer.edit() as view:` is the single bulk-edit convention for future buffer/numpy APIs (conservative invalidation on `__exit__`; unblocks #335); **#327**: threading contract documented -- `docs/threading-model.md` + normative `mcrfpy.lock()` docstring ("off-main-thread access outside the lock is undefined"); **#330**: subinterpreters explicitly excluded from 1.x compatibility; **#329**: `grid.entities` re-backed by `std::vector` -- indexing is O(1) (5000-entity indexed sweep: 49.7 ms -> 0.5 ms), iterator is index-based with the same mutation-guard semantics, suite 304/304. #326/#328/#330 are recorded in the new `docs/api-stability.md` compatibility policy, enforced by the api-surface snapshot test.
- **#340 The Gauntlet** -- interactive on-screen stress benchmark (`tests/benchmarks/gauntlet/`). Six trials (ENTITY SWARM, ANIMATION STORM, GRID TITAN, PATHFINDER RUSH, UI AVALANCHE, SIGHTLINE SIEGE) ramp load geometrically until p95 frame time breaks the 16.67 ms budget; live HUD with frame-time sparkline; menu + results screens diff against a committed JSON baseline with letter grades and a geometric-mean GAUNTLET SCORE. First real baseline captured windowed on 0.2.8 (e.g. 10,555 entities, 450 pathfinding queries/tick, 4,123 UI elements at budget). Caveat: desktop noise made callback-heavy trials vary run-to-run -- recapture on a quiet system for a canonical baseline. Found #341 (get_metrics draw_calls/render counters read 0).

### Recently Shipped (June 2026)
- **0.2.8 release** -- Version bumped to `0.2.8` (dropped the in-development `-7DRL-2026` suffix) and cut for distribution: `dist/McRogueFace-0.2.8-{Linux-full.tar.gz,Windows-full.zip,WASM.zip}`. Shipped libtcod (Linux `.so` / Windows `.dll` / Emscripten `.a`) rebuilt from submodule 79abc66 so release binaries carry the #321 FOV fix; the Linux build is `SDL3=OFF` with vendored utf8proc to stay self-contained (only libz + system libs), matching prior releases. Also fixed a pre-existing `tools/package.sh` bug that affected 0.2.7 too: the Linux package shipped the bare `libtcod.so` instead of its DT_NEEDED SONAME `libtcod.so.2` (+ compat symlink, mirroring the SFML packaging), so the runtime loader couldn't resolve it on a clean machine -- an absolute dev RUNPATH had masked this locally. No Gitea issue tracks this release (declined). Local commit `cf844f4`, pushed to origin/master; the `0.2.8` tag exists locally but has not been pushed yet.
- **#321** (HIGH) -- Fixed the `ColorLayer.draw_fov` heap-buffer-overflow by bumping `libtcod-headless` to 79abc66, pulling in upstream FOV overflow fixes (root cause: off-by-one in `view_array_insert` overflowing `active_views` in `fov_permissive2.c`; the "bad-free in ~GridData" of the issue title is the downstream symptom). Verified by A/B replay of the #312 `fuzz_fov` crash corpus under clang-18 ASan -- pre-fix (8835239) inputs abort with the overflow inside `GridData::computeFOV`, post-fix (79abc66) all clean plus a 45s/21,952-run fuzz smoke. (The gitignored shipped `__lib/libtcod.so` needed rebuilding from this commit for release binaries to carry the fix -- done for 0.2.8, see above.)
- **#322-#325** (fuzz-surfaced safety batch) -- the four remaining #312 fuzz bugs fixed and regression-tested. **#322**: `WangSet.terrain_enum` (and the parallel `AutoRuleSet.terrain_enum`) ignored Python C-API return codes, so an invalid-UTF-8 import name left an exception pending and the next `PyObject_Call` tripped a `_PyErr_Occurred` assertion/abort; every C-API return is now checked and the real exception propagated. **#323/#324/#325**: NaN/inf (or out-of-long-range) floats reached unchecked float->integer casts -- `pitch_shift` factor (`AudioEffects.cpp:27`, nan->unsigned long), `hsl_shift` shifts (`PyTexture.cpp:458`, nan->unsigned char), and `Vector.int` components (`PyVector.cpp:610`, inf->long), all undefined behavior; each now validates finiteness/range at the binding boundary and raises ValueError/OverflowError. Verified by A/B replay of the #312 crash corpus under clang-18 UBSan/ASan: all four inputs abort pre-fix at the exact cited lines and run clean post-fix, with four new regression tests (`tests/regression/issue_322..325_*`).
- **#312** -- Fuzz coverage extended to the remaining public API surface. Four new libFuzzer targets (`fuzz_audio_dsp`, `fuzz_import_parsers`, `fuzz_texture_factory`, `fuzz_shader_bindings`) cover the Tier A/B gaps (external file parsers, audio DSP math, raw-byte texture ingestion, shader uniform-binding lifetime); Tier C surface (Line/Circle/Arc, `Scene.children` collections, `find`/`find_all`/`bresenham`/`lock`, grid spatial queries, GridPoint dynamic attrs, `Grid.find_path`+AStarPath, ColorLayer perspective/`draw_fov`, layer `apply_*`) folded into the five existing targets. Each new target is signature-validated against the live API and seeded from real fixtures. The campaign immediately found **five new bugs** -- filed #321-#325 (no fixes this round; targets only). A pre-existing infra fix rode along: `tools/build_debug_libs.sh` flag-quoting bug that broke instrumented debug-lib rebuilds. The benchmark triplet is deliberately excluded from fuzzing (`end_benchmark()` writes a file per call).
- **#320** -- `Caption` constructor positional signature now matches its frozen docstring. The docstring advertised `Caption(pos, font, text, ...)` (parallel to `Sprite`/`Entity`, whose 2nd positional is the resource), but the implementation laid its two positional slots out as `(pos, text)` with `font` keyword-only, so `Caption((x,y), None, "text")` raised `TypeError`. Fixed `UICaption::init` to `(pos, font, text)` positional-or-keyword. Audited zero live callers of the old `(pos, text)` 2-positional form. Also added the matching read-only `Caption.font` getter (the class docstring listed `font` as an attribute but no getter existed; it now reflects the supplied or engine-default font). Also rewrote two stale unit tests (`test_animation_raii`, `test_animation_property_locking`) that called the removed `mcrfpy.Animation(...)` constructor to use `drawable.animate(...)` -- preserving the suite's only `conflict_mode` (#120) coverage and the weak-target RAII checks. Suite now 297/297.
- **#317 / #318 / #319** -- The three code-level bugs surfaced by the #314 docstring-accuracy verify pass, fixed together. #317: `automation.scroll()` dropped the x of its position argument (the scroll delta now has its own `injectMouseEvent` parameter, so the real x/y is forwarded). #318: `GridView.texture` always returned `None` (a TODO stub) -- it now returns a `Texture` wrapper (and since `mcrfpy.Grid`/`mcrfpy.GridView` are one type post-#252, both names benefit). #319: `Entity.visible_entities(radius=None)` raised `TypeError` (the `i` format code rejects `None`) -- radius is now parsed as an object so `None`/omitted/`-1` mean "grid default". Regression tests for each; api-surface snapshot re-baselined and docs/stubs regenerated.
- **#316** -- Sparse (windowed) perspective writeback in `UIEntity::updateVisibility`. The demote+promote passes are now clipped to an AABB sized to `fov_radius` (with a `prev_fov` window cache so a moving entity leaves no trailing "ghost vision"), replacing two full-`W*H` walks per entity. The Phase 5.2 benchmark's flat ~25-36 ms/entity writeback overhead on a 1000x1000 grid collapses to single-digit microseconds (384x-6577x on the cheap algorithms; lost in timing noise on the rest). Adversarial verify caught a regression the happy-path test missed -- externally-assigned maps (the documented `from_bytes` load/resume path) need a one-shot full demote (`perspective_full_demote_pending`) since `prev_fov` only bounds engine-promoted cells; fixed and locked with a 7-section regression test.
- **#313** -- `UIEntity::grid` migrated from `shared_ptr<UIGrid>` to `shared_ptr<GridData>` (post-#252 refactor cleanup), adding a new public `entity.texture` read/write property. Merged to master.
- **#314** -- API audit follow-through complete. (1) Snapshot lock: a public API-surface regression test (`tests/unit/api_surface_snapshot_test.py`) enshrines the frozen contract. (2) **F15**: all 289 raw docstring slots across the 20 frozen binding files converted to `MCRF_*` macros (frozen surface 100% compliant), driven by two one-agent-per-file workflows with build/doc gates and an adversarial signature-accuracy verify pass. Property types now resolve to real types (not `Any`) and read-only flags are correct. (3) A strict frozen-docstring gate (`tools/check_frozen_docstrings.sh`, wired into `generate_all_docs.sh`) locks it against regression. Breaking-change findings (F1/F4/F6/F11/F13) closed earlier; F7/F8/F10 deferred as non-1.0. Code-level bugs surfaced by the verify pass filed as #317/#318/#319.

---

## Engine Eras

One engine, accumulating capabilities. Nothing is thrown away.

| Era | Focus | Status |
|-----|-------|--------|
| **McRogueFace** | 2D tiles, roguelike systems, procgen | Active -- approaching 1.0 |
| **McVectorFace** | Sparse grids, vector graphics, physics | Planned |
| **McVoxelFace** | Voxel terrain, 3D gameplay | Proof-of-concept complete |

---

## 3D/Voxel Pipeline (Experimental)

The 3D pipeline is proof-of-concept scouting for the McVoxelFace era. It works and is tested but is explicitly **not** part of the 1.0 API freeze.

**What exists**: Viewport3D, Camera3D, Entity3D, MeshLayer, Model3D (glTF), Billboard, Shader3D, VoxelGrid with greedy meshing, face culling, RLE serialization, and navigation projection.

**Known gaps**: Some Entity3D collection methods, animation stubs, shader pipeline incomplete.

**Maturity track**: These modules will mature on their own timeline, driven by games that need 3D. They won't block 2D stability.

---

## Future Directions

These are ideas on the horizon -- not yet concrete enough for issues, but worth capturing.

### McRogueFace Lite
A spiritual port to MicroPython targeting the PicoCalc and other microcontrollers. Could provide a migration path to retro ROMs or compete in the Pico-8 space. The core idea: strip McRogueFace down to its essential tile/entity/scene model and run it on constrained hardware.

### McVectorFace Era
The next major capability expansion. Sparse grid layers, a polygon/shape rendering class, and eventually physics integration. This would support games that aren't purely tile-based -- top-down action, strategy maps with irregular regions, or hybrid tile+vector visuals. See the [Strategic Direction](https://dev.ffwf.net/forgejo/john/McRogueFace/wiki/Strategic-Direction) wiki for the full era model.

### McRogueFace Standard Library
A built-in collection of reusable GUI widgets and game UI patterns: menus, dialogs, inventory screens, stat bars, text input fields, scrollable lists. These would ship with the engine as importable Python modules, saving every game from reimplementing the same UI primitives. Think of it as `mcrfpy.widgets` -- batteries included.

### Pip/Virtualenv Integration
Rather than inverting the architecture to make McRogueFace a pip-installable package, the nearer-term goal is better integration in the other direction: making it easy to install and use third-party Python packages within McRogueFace's embedded interpreter. This could mean virtualenv awareness, a `mcrf install` command, or bundling pip itself.

---

## Open Issues by Area

50 open issues (2026-10-14). Key groupings:

- **Packaging / project tooling** (#498-#502, #70, #337) -- the package `_sysconfigdata`, project dependencies, finding an installed engine, `sys.path` order, run configuration visible to scripts
- **Input** (#495, #496, #497, #53) -- text-entry events, console hotkeys, event-sourced modifier keys
- **Threading / frame lock** (#416, #417, #336) -- unlocked-mutation UAF, holder-vs-holder races, free-threaded hardening
- **Simulation determinism** (#448, #408, #403) -- one clock, recorded RNG seeds, `GridData` identity
- **Grid / FOV / rendering** (#493, #454, #455, #434, #444, #471, #352, #152, #124, #67, #107, #347, #390, #393) -- default FOV, texture resolution, cell shapes, FOV design, big Dijkstra maps, chunk cache
- **Color** (#458, #489) -- color names, on a branch awaiting review
- **Docs / tooling** (#380, #381, #349, #472) -- template gating, snippet screenshots, scene serialization, Gauntlet resolution
- **Epics** (#387 web parity, #459 evolved programs)
- **Demos / tutorials** (#167, #248, #154, #156, #55, #54, #62) -- r/roguelikedev series, Crypt of Sokoban remaster, LLM agent simulations
- **Deferred** (#220, #124) -- subinterpreters, grid point animation

See the [Forgejo issue tracker](https://dev.ffwf.net/forgejo/john/McRogueFace/issues) for current status.

---

## Resources

- **Issue Tracker**: [Forgejo Issues](https://dev.ffwf.net/forgejo/john/McRogueFace/issues)
- **Wiki**: [Strategic Direction](https://dev.ffwf.net/forgejo/john/McRogueFace/wiki/Strategic-Direction), [Development Workflow](https://dev.ffwf.net/forgejo/john/McRogueFace/wiki/Development-Workflow)
- **Build Guide**: See `CLAUDE.md` for build instructions
- **Tutorial**: `roguelike_tutorial/` for implementation examples
