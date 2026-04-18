# McRogueFace - Development Roadmap

**Version**: 0.2.7-prerelease | **Era**: McRogueFace (2D roguelikes) -- on the road to 1.0

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
The process is underway. Closed in this pass: camelCase module functions (#304), deprecated `sprite_number` (#305), legacy string enum comparisons (#306), `Color.__eq__`/`__ne__` (#307), `Grid.position` alias (#308).

Remaining freeze work:
1. Catalog every public Python class, method, and property -- audit against `stubs/mcrfpy.pyi` and generated docs
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

The active tier1 queue is empty. The last three findings (#309 Caption float→uint, #310 FOV enum, #311 DijkstraMap OOB) all landed on master in mid-April. Coverage extension to remaining public API surface is tracked under #312.

### Recently Shipped (April 2026)
- **#294** -- `entity.perspective_map` replaces flat `vector<UIGridPointState>` with a 3-state DiscreteMap (UNKNOWN/DISCOVERED/VISIBLE). Per-entity FOV memory is now serializable, swappable, and structurally enforces visible-as-subset-of-discovered.
- **#315** -- Pathfinding API extended with built-in heuristics (Euclidean/Manhattan/Chebyshev/Diagonal/Zero), multi-root Dijkstra, FLEE primitives (invert + descent), and an interactive demo. EntityBehavior SEEK/FLEE refactored to a `PathProvider` strategy.
- **Phase 5.2** -- six performance benchmark scripts under `tests/benchmarks/` covering grid.step(), FOV writeback cost, spatial hash vs. O(n), pathfinding with collision labels, multi-GridView render, and Dijkstra variants. Baselines under `tests/benchmarks/baseline/phase5_2/`.
- **Phase 5.3** -- documentation regenerated; `tools/generate_stubs_v2.py` rewritten as introspection-based so it can no longer drift from the C++ source.

### Active Follow-Ups
- **#312** Extend fuzz coverage to remaining public API surface
- **#313** Migrate `UIEntity::grid` from `shared_ptr<UIGrid>` to `shared_ptr<GridData>` (post-#252 refactor cleanup)
- **#314** API audit follow-through: close gaps from `docs/api-audit-2026-04.md`
- **#316** Sparse perspective writeback in `UIEntity::updateVisibility` (Phase 5.2 finding: full-grid demote+promote dominates over TCOD FOV cost)

### Other Post-7DRL Priorities
- Progress on the r/roguelikedev tutorial series (#167)
- Complete the API freeze catalog pass (#314)
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

25 open issues across the tracker. Key groupings:

- **Recent follow-ups** (#312, #313, #314, #316) -- Fuzz coverage extension, UIEntity grid refactor, API audit follow-through, sparse perspective writeback
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
