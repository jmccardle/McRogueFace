# McRogueFace - Development Roadmap

**Version**: 0.2.6-prerelease | **Era**: McRogueFace (2D roguelikes)

For detailed architecture, philosophy, and decision framework, see the [Strategic Direction](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Strategic-Direction) wiki page. For per-issue tracking, see the [Issue Roadmap](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Issue-Roadmap).

---

## What Has Shipped

**Alpha 0.1** (2024) -- First complete release. Milestone: all datatypes behaving.

**0.2 series** (Jan-Feb 2026) -- Weekly updates to GitHub. Key additions:
- 3D/Voxel pipeline (experimental): Viewport3D, Camera3D, Entity3D, VoxelGrid with greedy meshing and serialization
- Procedural generation: HeightMap, BSP, NoiseSource, DiscreteMap
- Tiled and LDtk import with Wang tile / AutoRule resolution
- Emscripten/SDL2 backend for WebAssembly deployment
- Animation callbacks, mouse event system, grid cell callbacks
- Multi-layer grid system with chunk-based rendering and dirty-flag caching
- Documentation macro system with auto-generated API docs, man pages, and type stubs
- Windows cross-compilation, mobile-ish WASM support, SDL2_mixer audio

**Proving grounds**: Crypt of Sokoban (7DRL 2025) was the first complete game. 7DRL 2026 is the current target.

---

## Current Focus: 7DRL 2026

**Dates**: February 28 -- March 8, 2026

Engine preparation is complete. All 2D systems are production-ready. The jam will expose remaining rough edges in the workflow of building a complete game on McRogueFace.

Open prep items:
- **#248** -- Crypt of Sokoban Remaster (game content for the jam)

---

## Post-7DRL: The Road to 1.0

After 7DRL, the priority shifts from feature development to **API stability**. 1.0 means the Python API is frozen: documented, stable, and not going to break.

### API Freeze Process
1. Catalog every public Python class, method, and property
2. Identify anything that should change before committing (naming, signatures, defaults)
3. Make breaking changes in a single coordinated pass
4. Document the stable API as the contract
5. Experimental modules (3D/Voxel) get an explicit `experimental` label and are exempt from the freeze

### Post-Jam Priorities
- Fix pain points discovered during actual 7DRL game development
- Progress on the r/roguelikedev tutorial series (#167)
- API consistency audit and freeze
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

30 open issues across the tracker. Key groupings:

- **Multi-tile entities** (#233-#237) -- Oversized sprites, composite entities, origin offsets
- **Grid enhancements** (#152, #149, #67) -- Sparse layers, refactoring, infinite worlds
- **Performance** (#117, #124, #145) -- Memory pools, grid point animation, texture reuse
- **LLM agent testbed** (#154, #156, #55) -- Multi-agent simulation, turn-based orchestration
- **Platform/distribution** (#70, #54, #62, #53) -- Packaging, Jupyter, multiple windows, input methods
- **WASM tooling** (#238-#240) -- Debug infrastructure, automated browser testing, troubleshooting docs
- **Rendering** (#107, #218) -- Particle system, Color/Vector animation targets

See the [Gitea issue tracker](https://gamedev.ffwf.net/gitea/john/McRogueFace/issues) for current status.

---

## Resources

- **Issue Tracker**: [Gitea Issues](https://gamedev.ffwf.net/gitea/john/McRogueFace/issues)
- **Wiki**: [Strategic Direction](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Strategic-Direction), [Issue Roadmap](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Issue-Roadmap), [Development Workflow](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Development-Workflow)
- **Build Guide**: See `CLAUDE.md` for build instructions
- **Tutorial**: `roguelike_tutorial/` for implementation examples
