# McRogueFace - Development Roadmap

**Version**: 0.2.8-7DRL-2026 | **Era**: McRogueFace (2D roguelikes) -- on the road to 1.0

For detailed architecture, philosophy, and decision framework, see the [Strategic Direction](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Strategic-Direction) wiki page. For per-issue tracking, see the [Issue Roadmap](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Issue-Roadmap).

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

## Current Focus: API Freeze + Memory Safety Sweep

7DRL 2026 is behind us (Feb 28 -- Mar 8). The engine has two concurrent tracks to 1.0:

### Track 1: API Freeze
The process is underway. Closed in this pass: camelCase module functions (#304), deprecated `sprite_number` (#305), legacy string enum comparisons (#306), `Color.__eq__`/`__ne__` (#307), `Grid.position` alias (#308). The freeze decisions are now locked behind a public API-surface snapshot regression test (#314), so accidental signature drift fails CI.

Remaining freeze work:
1. Catalog every public Python class, method, and property -- audit against `stubs/mcrfpy.pyi` and generated docs (snapshot test now enforces the catalog)
2. Identify any last naming/signature/default changes before committing
3. Final breaking-change pass, bundled
4. Document the stable API as the contract
5. Experimental modules (3D/Voxel) stay out of the freeze with an `experimental` label

### Track 2: Fuzz-Driven Bug Sweep
The libFuzzer+ASan harness (#283) has nine work tranches merged: build plumbing (W1), native harness (W2/W3), then six targeted fuzzers under `tests/fuzz/`:
- `fuzz_grid_entity` -- EntityCollection lifetime (W4, fixed #258-#263, #273, #274)
- `fuzz_property_types` -- refcount / type confusion (W5, fixed #267, #268, #272)
- `fuzz_anim_timer_scene` -- animation/timer/scene lifecycles (W6)
- `fuzz_fov` -- compute_fov parameters (W8, fixed #310)
- `fuzz_maps_procgen` -- HeightMap/DiscreteMap interfaces (W7)
- `fuzz_pathfinding_behavior` -- Dijkstra + turn manager (W9, fixed #311)

Coverage extension (#312) added four more: `fuzz_audio_dsp` (SoundBuffer DSP), `fuzz_import_parsers` (Tiled/LDtk file parsers), `fuzz_texture_factory` (byte ingestion), `fuzz_shader_bindings` (uniform-binding lifetime), plus Tier C surface folded into the existing targets. That run found five new bugs: #321 (HIGH -- ColorLayer.draw_fov bad-free), #322 (WangSet.terrain_enum error-pending abort), #323/#324/#325 (float→int UB in pitch_shift/hsl_shift/Vector).

### Recently Shipped (April 2026)
- **#294** -- `entity.perspective_map` replaces flat `vector<UIGridPointState>` with a 3-state DiscreteMap (UNKNOWN/DISCOVERED/VISIBLE). Per-entity FOV memory is now serializable, swappable, and structurally enforces visible-as-subset-of-discovered.
- **#315** -- Pathfinding API extended with built-in heuristics (Euclidean/Manhattan/Chebyshev/Diagonal/Zero), multi-root Dijkstra, FLEE primitives (invert + descent), and an interactive demo. EntityBehavior SEEK/FLEE refactored to a `PathProvider` strategy.
- **Phase 5.2** -- six performance benchmark scripts under `tests/benchmarks/` covering grid.step(), FOV writeback cost, spatial hash vs. O(n), pathfinding with collision labels, multi-GridView render, and Dijkstra variants. Baselines under `tests/benchmarks/baseline/phase5_2/`.
- **Phase 5.3** -- documentation regenerated; `tools/generate_stubs_v2.py` rewritten as introspection-based so it can no longer drift from the C++ source.

### Recently Shipped (June 2026)
- **#321** (HIGH) -- Fixed the `ColorLayer.draw_fov` heap-buffer-overflow by bumping `libtcod-headless` to 79abc66, pulling in upstream FOV overflow fixes (root cause: off-by-one in `view_array_insert` overflowing `active_views` in `fov_permissive2.c`; the "bad-free in ~GridData" of the issue title is the downstream symptom). Verified by A/B replay of the #312 `fuzz_fov` crash corpus under clang-18 ASan -- pre-fix (8835239) inputs abort with the overflow inside `GridData::computeFOV`, post-fix (79abc66) all clean plus a 45s/21,952-run fuzz smoke. The gitignored shipped `__lib/libtcod.so` must be rebuilt from this commit for release binaries to carry the fix.
- **#322-#325** (fuzz-surfaced safety batch) -- the four remaining #312 fuzz bugs fixed and regression-tested. **#322**: `WangSet.terrain_enum` (and the parallel `AutoRuleSet.terrain_enum`) ignored Python C-API return codes, so an invalid-UTF-8 import name left an exception pending and the next `PyObject_Call` tripped a `_PyErr_Occurred` assertion/abort; every C-API return is now checked and the real exception propagated. **#323/#324/#325**: NaN/inf (or out-of-long-range) floats reached unchecked float->integer casts -- `pitch_shift` factor (`AudioEffects.cpp:27`, nan->unsigned long), `hsl_shift` shifts (`PyTexture.cpp:458`, nan->unsigned char), and `Vector.int` components (`PyVector.cpp:610`, inf->long), all undefined behavior; each now validates finiteness/range at the binding boundary and raises ValueError/OverflowError. Verified by A/B replay of the #312 crash corpus under clang-18 UBSan/ASan: all four inputs abort pre-fix at the exact cited lines and run clean post-fix, with four new regression tests (`tests/regression/issue_322..325_*`).
- **#312** -- Fuzz coverage extended to the remaining public API surface. Four new libFuzzer targets (`fuzz_audio_dsp`, `fuzz_import_parsers`, `fuzz_texture_factory`, `fuzz_shader_bindings`) cover the Tier A/B gaps (external file parsers, audio DSP math, raw-byte texture ingestion, shader uniform-binding lifetime); Tier C surface (Line/Circle/Arc, `Scene.children` collections, `find`/`find_all`/`bresenham`/`lock`, grid spatial queries, GridPoint dynamic attrs, `Grid.find_path`+AStarPath, ColorLayer perspective/`draw_fov`, layer `apply_*`) folded into the five existing targets. Each new target is signature-validated against the live API and seeded from real fixtures. The campaign immediately found **five new bugs** -- filed #321-#325 (no fixes this round; targets only). A pre-existing infra fix rode along: `tools/build_debug_libs.sh` flag-quoting bug that broke instrumented debug-lib rebuilds. The benchmark triplet is deliberately excluded from fuzzing (`end_benchmark()` writes a file per call).
- **#320** -- `Caption` constructor positional signature now matches its frozen docstring. The docstring advertised `Caption(pos, font, text, ...)` (parallel to `Sprite`/`Entity`, whose 2nd positional is the resource), but the implementation laid its two positional slots out as `(pos, text)` with `font` keyword-only, so `Caption((x,y), None, "text")` raised `TypeError`. Fixed `UICaption::init` to `(pos, font, text)` positional-or-keyword. Audited zero live callers of the old `(pos, text)` 2-positional form. Also added the matching read-only `Caption.font` getter (the class docstring listed `font` as an attribute but no getter existed; it now reflects the supplied or engine-default font). Also rewrote two stale unit tests (`test_animation_raii`, `test_animation_property_locking`) that called the removed `mcrfpy.Animation(...)` constructor to use `drawable.animate(...)` -- preserving the suite's only `conflict_mode` (#120) coverage and the weak-target RAII checks. Suite now 297/297.
- **#317 / #318 / #319** -- The three code-level bugs surfaced by the #314 docstring-accuracy verify pass, fixed together. #317: `automation.scroll()` dropped the x of its position argument (the scroll delta now has its own `injectMouseEvent` parameter, so the real x/y is forwarded). #318: `GridView.texture` always returned `None` (a TODO stub) -- it now returns a `Texture` wrapper (and since `mcrfpy.Grid`/`mcrfpy.GridView` are one type post-#252, both names benefit). #319: `Entity.visible_entities(radius=None)` raised `TypeError` (the `i` format code rejects `None`) -- radius is now parsed as an object so `None`/omitted/`-1` mean "grid default". Regression tests for each; api-surface snapshot re-baselined and docs/stubs regenerated.
- **#316** -- Sparse (windowed) perspective writeback in `UIEntity::updateVisibility`. The demote+promote passes are now clipped to an AABB sized to `fov_radius` (with a `prev_fov` window cache so a moving entity leaves no trailing "ghost vision"), replacing two full-`W*H` walks per entity. The Phase 5.2 benchmark's flat ~25-36 ms/entity writeback overhead on a 1000x1000 grid collapses to single-digit microseconds (384x-6577x on the cheap algorithms; lost in timing noise on the rest). Adversarial verify caught a regression the happy-path test missed -- externally-assigned maps (the documented `from_bytes` load/resume path) need a one-shot full demote (`perspective_full_demote_pending`) since `prev_fov` only bounds engine-promoted cells; fixed and locked with a 7-section regression test.
- **#313** -- `UIEntity::grid` migrated from `shared_ptr<UIGrid>` to `shared_ptr<GridData>` (post-#252 refactor cleanup), adding a new public `entity.texture` read/write property. Merged to master.
- **#314** -- API audit follow-through complete. (1) Snapshot lock: a public API-surface regression test (`tests/unit/api_surface_snapshot_test.py`) enshrines the frozen contract. (2) **F15**: all 289 raw docstring slots across the 20 frozen binding files converted to `MCRF_*` macros (frozen surface 100% compliant), driven by two one-agent-per-file workflows with build/doc gates and an adversarial signature-accuracy verify pass. Property types now resolve to real types (not `Any`) and read-only flags are correct. (3) A strict frozen-docstring gate (`tools/check_frozen_docstrings.sh`, wired into `generate_all_docs.sh`) locks it against regression. Breaking-change findings (F1/F4/F6/F11/F13) closed earlier; F7/F8/F10 deferred as non-1.0. Code-level bugs surfaced by the verify pass filed as #317/#318/#319.

### Active Follow-Ups
- The #312 fuzz-surfaced bug batch (#321-#325) is now fully fixed on-branch and verified under UBSan/ASan; see Recently Shipped. No open follow-ups from the fuzz run remain -- pending merge to master.

### Other Post-7DRL Priorities
- Progress on the r/roguelikedev tutorial series (#167)
- Better pip/virtualenv integration for adding packages to McRogueFace's embedded interpreter

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
The next major capability expansion. Sparse grid layers, a polygon/shape rendering class, and eventually physics integration. This would support games that aren't purely tile-based -- top-down action, strategy maps with irregular regions, or hybrid tile+vector visuals. See the [Strategic Direction](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Strategic-Direction) wiki for the full era model.

### McRogueFace Standard Library
A built-in collection of reusable GUI widgets and game UI patterns: menus, dialogs, inventory screens, stat bars, text input fields, scrollable lists. These would ship with the engine as importable Python modules, saving every game from reimplementing the same UI primitives. Think of it as `mcrfpy.widgets` -- batteries included.

### Pip/Virtualenv Integration
Rather than inverting the architecture to make McRogueFace a pip-installable package, the nearer-term goal is better integration in the other direction: making it easy to install and use third-party Python packages within McRogueFace's embedded interpreter. This could mean virtualenv awareness, a `mcrf install` command, or bundling pip itself.

---

## Open Issues by Area

26 open issues across the tracker. Key groupings:

- **Fuzz-surfaced bugs** (#321-#325) -- all fixed on-branch (FOV overflow, terrain_enum error-pending abort, three float->int UB casts), pending merge to master
- **7DRL 2026 carry-over** (#248) -- Crypt of Sokoban remaster, superseded by the 7DRL 2026 entry but still relevant as a demo
- **Tooling / infrastructure** (#282, #255) -- Modern Clang for TSan/fuzzing, performance profiling
- **Demos / tutorials** (#167, #154, #156, #55) -- r/roguelikedev series, LLM agent simulations
- **Grid enhancements** (#152, #67) -- Sparse layers, infinite worlds
- **Performance** (#117, #124, #145) -- Memory pools, grid point animation, texture reuse
- **Platform/distribution** (#70, #54, #62, #53) -- Packaging, Jupyter, multiple windows, input methods
- **WASM tooling** (#239) -- Automated browser testing
- **Rendering** (#107) -- Particle system
- **Deferred** (#220, #46, #45) -- Subinterpreter support / tests, accessibility modes

See the [Gitea issue tracker](https://gamedev.ffwf.net/gitea/john/McRogueFace/issues) for current status.

---

## Resources

- **Issue Tracker**: [Gitea Issues](https://gamedev.ffwf.net/gitea/john/McRogueFace/issues)
- **Wiki**: [Strategic Direction](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Strategic-Direction), [Issue Roadmap](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Issue-Roadmap), [Development Workflow](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Development-Workflow)
- **Build Guide**: See `CLAUDE.md` for build instructions
- **Tutorial**: `roguelike_tutorial/` for implementation examples
