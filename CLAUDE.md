# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Gitea-First Workflow

**IMPORTANT**: This project uses Gitea for issue tracking, documentation, and project management. Always consult and update Gitea resources before and during development work.

**Forgejo Instance**: https://dev.ffwf.net/forgejo/john/McRogueFace

### Core Principles

1. **Gitea is the Single Source of Truth**
   - Issue tracker contains current tasks, bugs, and feature requests
   - Wiki contains living documentation and architecture decisions
   - Use Gitea MCP tools to query and update issues programmatically

2. **Always Check Gitea First**
   - Before starting work: Check open issues for related tasks or blockers
   - Before implementing: Read relevant wiki pages per the [Development Workflow](https://dev.ffwf.net/forgejo/john/McRogueFace/wiki/Development-Workflow) consultation table
   - When using `/roadmap` command: Query Gitea for up-to-date issue status
   - When researching a feature: Search Gitea wiki and issues before grepping codebase
   - When encountering a bug: Check if an issue already exists

3. **Create Granular Issues**
   - Break large features into separate, focused issues
   - Each issue should address one specific problem or enhancement
   - Tag issues appropriately: `[Bugfix]`, `[Major Feature]`, `[Minor Feature]`, etc.
   - Link related issues using dependencies or blocking relationships

4. **Document as You Go**
   - When work on one issue interacts with another system: Add notes to related issues
   - When discovering undocumented behavior: Note it for wiki update
   - When documentation misleads you: Note it for wiki correction
   - After committing code changes: Update relevant wiki pages (with user permission)
   - Follow the [Development Workflow](https://dev.ffwf.net/forgejo/john/McRogueFace/wiki/Development-Workflow) for wiki update procedures

5. **Cross-Reference Everything**
   - Commit messages should reference issue numbers (e.g., "Fixes #104", "Addresses #125")
   - Issue comments should link to commits when work is done
   - Wiki pages should reference relevant issues for implementation details
   - Issues should link to each other when dependencies exist

### Workflow Pattern

```
┌─────────────────────────────────────────────────────┐
│ 1. Check Gitea Issues & Wiki                       │
│    - Is there an existing issue for this?          │
│    - What's the current status?                    │
│    - Are there related issues or blockers?         │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 2. Create Issues (if needed)                       │
│    - Break work into granular tasks                │
│    - Tag appropriately                             │
│    - Link dependencies                             │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 3. Do the Work                                      │
│    - Implement/fix/document                        │
│    - Write tests first (TDD)                       │
│    - Add inline documentation                      │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 4. Update Gitea                                     │
│    - Add notes to affected issues                  │
│    - Create follow-up issues for discovered work   │
│    - Update wiki if architecture/APIs changed      │
│    - Add documentation correction tasks            │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 5. Commit & Reference                              │
│    - Commit messages reference issue numbers       │
│    - Close issues or update status                 │
│    - Add commit links to issue comments            │
└─────────────────────────────────────────────────────┘
```

### Benefits of Gitea-First Approach

- **Reduced Context Switching**: Check brief issue descriptions instead of re-reading entire codebase
- **Better Planning**: Issues provide roadmap; avoid duplicate or contradictory work
- **Living Documentation**: Wiki and issues stay current as work progresses
- **Historical Context**: Issue comments capture why decisions were made
- **Efficiency**: MCP tools allow programmatic access to project state

### MCP Tools Available

Claude Code has access to the `forgejo` MCP server (John's own project, `/home/john/Development/forgejo-mcp`). It exposes seven resource-oriented tools plus a built-in manual:
- `list_gitea` - List issues, labels (with IDs), milestones, comments, releases, wiki pages, PRs, etc.
- `get_gitea` - Get a single issue, PR, wiki page, or repository
- `create_gitea` - Create issues (supports `labels=[ids]` at creation), comments, labels, milestones, releases, wiki pages, PRs
- `edit_gitea` - Edit issues (including `state="closed"`), comments, labels, milestones, releases, wiki pages
- `delete_gitea` - Delete comments, labels, milestones, releases, wiki pages
- `link_gitea` / `unlink_gitea` - Add/remove issue labels (`type="issue_label"`), dependencies, and blocking relationships
- `gitea_manual` - Look up full documentation for any action/resource combination

Use these tools liberally to keep the project organized!

### Gitea Label System

**IMPORTANT**: Always apply appropriate labels when creating new issues!

The project uses a structured label system to organize issues:

**Label Categories:**

1. **System Labels** (identify affected codebase area):
   - `system:rendering` - Rendering pipeline and visuals
   - `system:ui-hierarchy` - UI component hierarchy and composition
   - `system:grid` - Grid system and spatial containers
   - `system:animation` - Animation and property interpolation
   - `system:python-binding` - Python/C++ binding layer
   - `system:input` - Input handling and events
   - `system:performance` - Performance optimization and profiling
   - `system:documentation` - Documentation infrastructure
   - `system:procgen` - Procedural Generation (Noise, BSP, Heightmap)

2. **Priority Labels** (development timeline):
   - `priority:tier1-active` - Current development focus - critical path to v1.0
   - `priority:tier2-foundation` - Important foundation work - not blocking v1.0
   - `priority:tier3-future` - Future features - deferred until after v1.0
   - `priority:tier4-deferred` - Deferred indefinitely

3. **Type/Scope Labels** (effort and complexity):
   - `Major Feature` - Significant time and effort required
   - `Minor Feature` - Some effort required to create or overhaul functionality
   - `Tiny Feature` - Quick and easy - a few lines or little interconnection
   - `Bugfix` - Fixes incorrect behavior
   - `Refactoring & Cleanup` - No new functionality, just improving codebase
   - `Documentation` - Documentation work
   - `Demo Target` - Functionality to demonstrate

4. **Workflow Labels** (current blockers/needs):
   - `workflow:blocked` - Blocked by other work - waiting on dependencies
   - `workflow:needs-documentation` - Needs documentation before or after implementation
   - `workflow:needs-benchmark` - Needs performance testing and benchmarks
   - `Alpha Release Requirement` - Blocker to 0.1 Alpha release

**When creating issues:**
- Apply at least one `system:*` label (what part of codebase)
- Apply one `priority:tier*` label (when to address it)
- Apply one type label (`Major Feature`, `Minor Feature`, `Tiny Feature`, or `Bugfix`)
- Apply `workflow:*` labels if applicable (blocked, needs docs, needs benchmarks)

**Example label combinations:**
- New rendering feature: `system:rendering`, `priority:tier2-foundation`, `Major Feature`
- Python API improvement: `system:python-binding`, `priority:tier1-active`, `Minor Feature`
- Performance work: `system:performance`, `priority:tier1-active`, `Major Feature`, `workflow:needs-benchmark`

**Applying labels via MCP** (validated 2026-07-02): label operations work correctly with multi-ID arrays.
- At creation: `create_gitea(resource="issue", labels=[3, 14], ...)`
- On existing issues: `link_gitea(type="issue_label", index=N, labels=[ids])` (additive) / `unlink_gitea(type="issue_label", index=N, label_id=id)`
- To look up IDs at runtime: `list_gitea(resource="label")` includes each label's numeric ID

(An older Gitea MCP server, v0.07, had an ID-mapping bug — report archived in `.archive/GITEA_MCP_LABEL_BUG_REPORT.md`. The one-label-at-a-time workaround is no longer needed.)

**Label ID Reference** (re-validated against `list_gitea` 2026-07-02):
```
1=Major Feature, 2=Minor Feature, 3=Tiny Feature, 4=Demo Target, 5=Documentation,
6=Alpha Release Requirement, 7=Refactoring & Cleanup, 8=Bugfix,
9=system:grid, 10=system:animation, 11=system:ui-hierarchy, 12=system:python-binding,
13=system:performance, 14=system:documentation, 15=system:rendering, 16=system:input,
17=priority:tier1-active, 18=priority:tier2-foundation, 19=priority:tier3-future,
20=workflow:needs-documentation, 21=workflow:needs-benchmark, 22=workflow:blocked,
140=priority:tier4-deferred, 141=system:procgen
```

## Build System

McRogueFace uses a unified Makefile for both Linux native builds and Windows cross-compilation.

**IMPORTANT**: All `make` commands must be run from the **project root directory** (`/home/john/Development/McRogueFace/`), not from `build/` or any subdirectory.

### Quick Reference

```bash
# Fresh clone: build SFML, libtcod, CPython into __lib/ first (see BUILD_FROM_SOURCE.md)
make deps               # no root? tools/fetch_dev_headers.sh + export MCRF_SYSROOT=...

# Linux builds
make                    # Build for Linux (default target)
make linux              # Same as above
make run                # Build and run
make clean              # Remove Linux build artifacts

# Windows cross-compilation (requires MinGW-w64)
make windows            # Release build for Windows
make windows-debug      # Debug build with console output
make clean-windows      # Remove Windows build artifacts

# Distribution packages
make package-linux-light    # Linux with minimal stdlib (~25 MB)
make package-linux-full     # Linux with full stdlib (~26 MB)
make package-windows-light  # Windows with minimal stdlib
make package-windows-full   # Windows with full stdlib
make package-all            # All platform/preset combinations

# Cleanup
make clean-all          # Remove all builds and packages
make clean-dist         # Remove only distribution packages
```

### Build Outputs

| Command | Output Directory | Executable |
|---------|------------------|------------|
| `make` / `make linux` | `build/` | `build/mcrogueface` |
| `make windows` | `build-windows/` | `build-windows/mcrogueface.exe` |
| `make windows-debug` | `build-windows-debug/` | `build-windows-debug/mcrogueface.exe` |
| `make package-*` | `dist/` | `.tar.gz` or `.zip` archives |

### Prerequisites

**Linux build:**
- CMake 3.14+
- GCC/G++ with C++17 support
- SFML 2.6 development libraries
- Libraries in `__lib/` directory (libpython3.15, libtcod, SFML) -- produced by `make deps`

**Windows cross-compilation:**
- MinGW-w64 (`x86_64-w64-mingw32-g++-posix`)
- Libraries in `__lib_windows/` directory
- Toolchain file: `cmake/toolchains/mingw-w64-x86_64.cmake`

### Library Dependencies

The build expects pre-built libraries in:
- `__lib/` - Linux shared libraries (libpython3.15.so, libsfml-*.so, libtcod.so)
- `__lib/Python/Lib/` - Python standard library source
- `__lib/Python/lib.linux-x86_64-3.15/` - Python extension modules (.so)
- `__lib_windows/` - Windows DLLs and libraries

### Manual CMake Build

If you need more control over the build:

```bash
# Linux
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

# Windows cross-compile
mkdir build-windows && cd build-windows
cmake .. -DCMAKE_TOOLCHAIN_FILE=../cmake/toolchains/mingw-w64-x86_64.cmake \
         -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

# Windows debug with console
cmake .. -DCMAKE_TOOLCHAIN_FILE=../cmake/toolchains/mingw-w64-x86_64.cmake \
         -DCMAKE_BUILD_TYPE=Debug \
         -DMCRF_WINDOWS_CONSOLE=ON
```

### Distribution Packaging

The packaging system creates self-contained archives with:
- Executable
- Required shared libraries
- Assets (sprites, fonts, audio)
- Python scripts
- Filtered Python stdlib (light or full variant)

**Light variant** (~25 MB): Core + gamedev + utility modules only
**Full variant** (~26 MB): Includes networking, async, debugging modules

Packaging tools:
- `src/pylib/mcrf_project/runtime.py` - **the** definition of what a package contains
  (the runtime: binary, libraries, filtered stdlib). Read from a built engine directory;
  every version-dependent name is discovered, never written down. Ships with the engine
  (copied to `lib/Python/Lib/` by the `mcrf_pylib` CMake target).
- `tools/package.sh` - thin wrapper: `build/mcrogueface -m mcrf_project package-engine`
  with the git version. Games use the same code: `mcrogueface -m mcrf_project dist` (#420).
  Never re-list runtime files anywhere else; that duplication is how #420 happened.
- `runtime.web_archive()` - **the** definition of a web package (#474): a flat zip,
  `index.html` (the build's `mcrogueface.html`) + `mcrogueface.{js,wasm,data}`, from a
  game-shell web build only. `make package-web` (engine release, `McRogueFace-<v>-WASM.zip`)
  and `mcrf_project dist --platform web` (games) both use it. Flat with `index.html` at
  the root is what itch.io, static hosts and folder URLs serve.
- `tools/version.sh` - prints `MCRFPY_VERSION` from `src/McRogueFaceVersion.h`, the only
  source of truth for the version, `-dev` included (#475). Nothing reads git tags for it.
- `tools/package_stdlib.py`, `tools/stdlib_modules.yaml` - unused (see #399)

**Caveat (#399): the light/full split is currently aspirational, not mechanical.**
Both presets ship the same stdlib; the preset only names the package. Do not assume
editing `stdlib_modules.yaml` changes what ships.

#### Networking / async guarantee

The **`make package-linux-full`** configuration is the named, gated one for embedders
who run a network client (message bus, telemetry feed) on a background thread inside
the engine process. In that artifact, `socket`, `ssl`, `asyncio` and `selectors` all
import and work from the package's own `lib/Python/Lib` — Python sources and the
`_socket` / `_ssl` / `_asyncio` / `select` C extensions alike.

This is gated, not assumed:

| Test | Proves |
|------|--------|
| `tests/packaging/network_stdlib_packaged_test.py` | Builds the real tarball, extracts it outside the source tree, and imports+uses all four **from the packaged binary**. Each module is mutation-checked: removing it must break the probe, so the test cannot silently lose its teeth. |
| `tests/integration/background_thread_network_test.py` | A background thread does real socket / selectors / TLS / asyncio work **off the main thread** while the main thread keeps completing frames, then hands its result back under `mcrfpy.lock()`. |

Both run in the default suite. The alternate-build suites (`make debug-test`,
`asan-test`, `tsan-test`, `valgrind-test`) pass `--exclude=packaging`, because
`tools/package.sh` packages the Release `build/` regardless of which build the suite
is driving — that exclusion is at the invocation site, not inside the test.

`nats-py` and friends are **not** engine dependencies and must never be vendored. The
engine's obligation stops at "the interpreter we ship can do sockets and asyncio from
a background thread"; installing a client library is the embedder's job.

#### Mutating the world from a background thread

Use `mcrfpy.lock()`, and treat it as a **mutation-only** critical section:

```python
data = bus.poll()                 # I/O OUTSIDE the lock
with mcrfpy.lock():
    entity.cell_pos = data.pos    # assignment only
```

The main thread parks until every lock holder returns, so I/O, `await`, or any blocking
wait inside the block is indistinguishable from engine stutter. The window opens once
per frame in both frame paths — `doFrame()` (windowed) and `runSimFrame()` (headless
`step()`/`advance()`). `acquire()` has no timeout, so a frame path that fails to open
the window blocks holders forever; that was #398, gated by
`tests/regression/issue_398_headless_frame_lock_test.py` (pre-fix: 12.2M `step()`
calls and the lock never opens; post-fix: 1).

### Troubleshooting

**"No rule to make target 'linux'"**: You're in the wrong directory. Run `make` from project root.

**Library linking errors**: Ensure `__lib/` contains all required .so files. Check `CMakeLists.txt` for `link_directories(${CMAKE_SOURCE_DIR}/__lib)`.

**Windows build fails**: Verify MinGW-w64 is installed with posix thread model: `x86_64-w64-mingw32-g++-posix --version`

### Legacy Build Scripts

The following are deprecated but kept for reference:
- `build.sh` - Original Linux build script (use `make` instead)
- `GNUmakefile.legacy` - Old wrapper makefile (renamed to avoid conflicts)

## Emscripten / WebAssembly Builds

McRogueFace supports WebGL deployment via Emscripten with an SDL2+OpenGL ES 2 backend.

### Quick Start

```bash
source ~/emsdk/emsdk_env.sh  # Activate Emscripten SDK
make wasm                     # Full game web build
make playground               # REPL-focused web build
make serve                    # Serve at http://localhost:8080
```

### Build Variants

| Target | Output Directory | Purpose |
|--------|------------------|---------|
| `make wasm` | `build-emscripten/` | Full game with all scripts/assets |
| `make playground` | `build-playground/` | Minimal REPL build for interactive testing |
| `make wasm-debug` | `build-wasm-debug/` | Debug build with DWARF symbols and source maps |
| `make playground-debug` | `build-playground-debug/` | Debug playground with DWARF and source maps |

### Rendering Backend Selection

The build system supports three backends via CMake defines:

```bash
cmake ..                      # SFML (default desktop)
cmake -DMCRF_SDL2=ON ..       # SDL2 + OpenGL ES 2 (Emscripten)
cmake -DMCRF_HEADLESS=ON ..   # No graphics (CI/testing)
```

Emscripten builds automatically select SDL2 mode. Backend selection happens in `Common.h`:

```cpp
#ifdef MCRF_HEADLESS
    #include "platform/HeadlessTypes.h"
#elif defined(MCRF_SDL2)
    #include "platform/SDL2Types.h"
#else
    #include <SFML/Graphics.hpp>
#endif
```

### SDL2 Backend Architecture

Game code remains unchanged because `SDL2Types.h` provides SFML-compatible type stubs:
- `sf::Vector2f`, `sf::Color`, `sf::RectangleShape`, etc. all work identically
- Rendering uses OpenGL ES 2 shaders internally
- Text rendering uses FreeType 2 (with outline support)

### Web Build Constraints

When developing features that must work in WebGL:

**Full audited parity matrix: [docs/web-parity-matrix.md](docs/web-parity-matrix.md)** — the living, per-row desktop↔web matrix with an honest **test-coverage** column (cites the real test or says `unverified`/`manual only`/`planned: #388`). Consult it before assuming a feature works on web. The trimmed summary below is only a quick reference:

| Feature | Desktop (SFML) | Web (SDL2) | Test coverage |
|---------|----------------|------------|---------------|
| Audio | ✅ Full | ✅ Full | manual only |
| Input (Key/MouseButton/mods) | ✅ Full | ✅ Full | ✅ `tests/unit/input_parity_test.py` (#389) |
| Web boot / Python / UI / errors | n/a | ✅ Works | ✅ `tests/wasm/run_wasm_tests.py` (#239) |
| Dynamic assets | ✅ Filesystem | ⚠️ Preloaded | unverified (build-time invariant) |
| ImGui console | ✅ Full | ❌ Disabled | n/a (absent by design) |
| Threading | ✅ Full | ⚠️ Single-threaded | unverified |
| Shaders (custom) | ✅ Full | ⚠️ Wired (#390), pixel-unverified | planned: #388 (see #347 §1a) |
| Text UTF-8 | ✅ Full | ✅ Full | ✅ `issue_477_utf8_text_test.py` + `run_wasm_tests.py::utf8_text` (#477) |
| Text kerning | ✅ Full | ❌ Diverges | planned: #388 (see #347 §3d) |
| RenderTexture / pixel scaling | ✅ Full | ⚠️ Verify | planned: #388 |
| Multi-window / free-threading / numpy | ⚠️ Planned | ❌ Desktop-only | n/a (#62 / #336 / #337) |

### Development Workflow

For iterative Emscripten development:

```bash
source ~/emsdk/emsdk_env.sh
# Initial configure (once)
emmake cmake -B build-emscripten -DMCRF_SDL2=ON

# Rebuild after code changes (fast)
emmake make -C build-emscripten -j$(nproc)

# Test in browser
make serve
```

### Adding Cross-Platform Features

When adding rendering features:

1. **Check backend at compile time** if needed:
   ```cpp
   #ifdef MCRF_SDL2
       // SDL2-specific implementation
   #else
       // SFML implementation
   #endif
   ```

2. **Prefer SFML API abstractions** - SDL2Types.h mirrors the SFML interface

3. **For new SDL2 features**: Add to `SDL2Renderer.cpp` with GLSL ES 2.0 shaders

4. **Test headless mode** for CI compatibility:
   ```bash
   ./mcrogueface --headless --exec ../tests/unit/my_test.py
   ```

### Asset Paths

Emscripten uses a virtual filesystem with preloaded assets:
- Use absolute paths: `/assets/sprite.png`, `/scripts/game.py`
- Assets defined in CMakeLists.txt `--preload-file` flags
- No runtime file loading from disk

### Playground Mode

The playground build (`-DMCRF_PLAYGROUND=ON`) provides:
- Python REPL widget in browser
- Scene reset capability via `reset_python_environment()`
- Minimal `src/scripts_playground/game.py` with idempotent initialization
- JavaScript interop via `Module.ccall()` to C functions

### Key Files

- `src/platform/SDL2Types.h` - SFML-compatible type stubs
- `src/platform/SDL2Renderer.cpp` - OpenGL ES 2 rendering implementation
- `src/platform/HeadlessTypes.h` - No-op types for headless mode
- `src/EmscriptenStubs.cpp` - JavaScript interop functions
- `emscripten_pre.js` - Browser quirk fixes
- `shell.html` - HTML template with REPL widget

## Project Architecture

McRogueFace is a C++ game engine with Python scripting support, designed for creating roguelike games. The architecture consists of:

### Core Engine (C++)
- **Entry Point**: `src/main.cpp` initializes the game engine
- **Scene System**: `Scene.h/cpp` manages game states
- **Entity System**: `UIEntity.h/cpp` provides game objects
- **Python Integration**: `McRFPy_API.h/cpp` exposes engine functionality to Python
- **UI Components**: `UIFrame`, `UICaption`, `UISprite`, `UIGrid` for rendering

### Game Logic (Python)
- **Main Script**: `src/scripts/game.py` contains game initialization and scene setup
- **Entity System**: `src/scripts/cos_entities.py` implements game entities (Player, Enemy, Boulder, etc.)
- **Level Generation**: `src/scripts/cos_level.py` uses BSP for procedural dungeon generation
- **Tile System**: `src/scripts/cos_tiles.py` implements Wave Function Collapse for tile placement

### Key Python API (`mcrfpy` module)
The C++ engine exposes these primary functions to Python:
- Scene Management: `Scene("name")` object with `scene.on_key` for keyboard events
- Entity Creation: `Entity()` with position and sprite properties
- Grid Management: `Grid()` for tilemap rendering with cell callbacks
- Input Handling: `scene.on_key = handler` receives `(Key, InputState)` enums
- Audio: `createSoundBuffer()`, `playSound()`, `setVolume()`
- Timers: `Timer("name", callback, interval)` object for event scheduling

## Development Workflow

### Running the Game
After building, the executable expects:
- `assets/` directory with sprites, fonts, and audio
- `scripts/` directory with Python game files
- Python 3.15 shared libraries in `./lib/`

### Modifying Game Logic
- Game scripts are in `src/scripts/`
- Main game entry is `game.py`
- Entity behavior in `cos_entities.py`
- Level generation in `cos_level.py`

### Adding New Features
1. C++ API additions go in `src/McRFPy_API.cpp`
2. Expose to Python using the existing binding pattern
3. Update Python scripts to use new functionality

## Testing

### Test Suite Structure

The `tests/` directory contains the comprehensive test suite:

```
tests/
├── run_tests.py          # Test runner - executes all tests with timeout
├── unit/                 # Unit tests for individual components (105+ tests)
├── integration/          # Integration tests for system interactions
├── regression/           # Bug regression tests (issue_XX_*.py)
├── benchmarks/           # Performance benchmarks
├── demo/                 # Feature demonstration system
│   ├── demo_main.py      # Interactive demo runner
│   ├── screens/          # Per-feature demo screens
│   └── screenshots/      # Generated demo screenshots
└── notes/                # Analysis files and documentation
```

### Running Tests

```bash
# Run the full test suite (from tests/ directory). Rendering in the SFML build needs a
# display even with --headless (GL resources are created on first use, and raise
# RuntimeError with no display, #451); ALSOFT_DRIVERS=null stands in for a missing audio device.
cd tests && ALSOFT_DRIVERS=null xvfb-run -a python3 run_tests.py

# Run a specific test
cd build && ./mcrogueface --headless --exec ../tests/unit/some_test.py

# Run the demo system interactively
cd build && ./mcrogueface ../tests/demo/demo_main.py

# Generate demo screenshots (headless)
cd build && ./mcrogueface --headless --exec ../tests/demo/demo_main.py
```

### Reading Tests as Examples

**IMPORTANT**: Before implementing a feature or fixing a bug, check existing tests for API usage examples:

- `tests/unit/` - Shows correct usage of individual mcrfpy classes and functions
- `tests/demo/screens/` - Complete working examples of UI components
- `tests/regression/` - Documents edge cases and bug scenarios

Example: To understand Animation API:
```bash
grep -r "Animation" tests/unit/
cat tests/demo/screens/animation_demo.py
```

### Writing Tests

**Always write tests when adding features or fixing bugs:**

1. **For new features**: Create `tests/unit/feature_name_test.py`
2. **For bug fixes**: Create `tests/regression/issue_XX_description_test.py`
3. **For demos**: Add to `tests/demo/screens/` if it showcases a feature

### Quick Testing Commands
```bash
# Test headless mode with inline Python
cd build
./mcrogueface --headless -c "import mcrfpy; print('Headless test')"

# Run specific test with output
./mcrogueface --headless --exec ../tests/unit/my_test.py 2>&1
```

## Common Development Tasks

### Compiling McRogueFace

See the [Build System](#build-system) section above for comprehensive build instructions.

```bash
# Quick reference (run from project root!)
make                # Linux build
make windows        # Windows cross-compile
make clean && make  # Full rebuild
```

### Profiling the Engine (native C++)

For diagnosing/validating C++ hot-path work, use the dedicated profiling build. The
default Release build keeps frame pointers (#421, PEP 831: `MCRF_FRAME_POINTERS=ON`, about
1% cost), so `perf --call-graph fp` unwinds it end to end, but it has no DWARF, so it
can't be line-annotated. Python frames get names via `sys.activate_stack_trampoline("perf")`.
See [docs/profiling.md](docs/profiling.md) for the full workflow. Quick version:

```bash
make profile                                    # build-profile/ : RelWithDebInfo + frame pointers
make callgrind SCRIPT=tests/benchmarks/foo.py   # deterministic instruction counts, no perms needed
callgrind_annotate build-profile/callgrind.out | head -60
```

Callgrind is deterministic (exact `Ir` counts + source line attribution) — ideal for
A/B-validating optimizations like #331/#342. `perf record --call-graph fp` gives
wall-clock sampling but needs `sudo sysctl kernel.perf_event_paranoid=1` first.

### Running and Capturing Output
```bash
# Run with timeout and capture output
cd build
timeout 5 ./mcrogueface 2>&1 | tee output.log

# Run in background and kill after delay
./mcrogueface > output.txt 2>&1 & PID=$!; sleep 3; kill $PID 2>/dev/null

# Just capture first N lines (useful for crashes)
./mcrogueface 2>&1 | head -50
```

### Debugging with GDB
```bash
# Interactive debugging
gdb ./mcrogueface
(gdb) run
(gdb) bt  # backtrace after crash

# Batch mode debugging (non-interactive)
gdb -batch -ex run -ex where -ex quit ./mcrogueface 2>&1

# Get just the backtrace after a crash
gdb -batch -ex "run" -ex "bt" ./mcrogueface 2>&1 | head -50

# Debug with specific commands
echo -e "run\nbt 5\nquit\ny" | gdb ./mcrogueface 2>&1
```

### Testing Different Python Scripts
```bash
# The game automatically runs build/scripts/game.py on startup
# To test different behavior:

# Option 1: Replace game.py temporarily
cd build
cp scripts/my_test_script.py scripts/game.py
./mcrogueface

# Option 2: Backup original and test
mv scripts/game.py scripts/game.py.bak
cp my_test.py scripts/game.py
./mcrogueface
mv scripts/game.py.bak scripts/game.py

# Option 3: For quick tests, create minimal game.py
echo 'import mcrfpy; print("Test"); scene = mcrfpy.Scene("test"); scene.activate()' > scripts/game.py
```

### Understanding Key Macros and Patterns

#### Binding recipes live in `src/PyWrap.h` (#369, #430, #436)

**Never hand-roll a CPython recipe that `PyWrap.h` already provides.** A fresh wrapper for
an object that already has one breaks identity (`x.parent is x.parent` -> False) and
downgrades a Python subclass to its base type; the other recipes below each produced leaks.

```cpp
// Returning a C++ object to Python: the live wrapper if one exists, else a new
// registered one. New reference; None for nullptr.
mcrf::to_python(drawable_or_entity_or_griddata_shared_ptr);
Foo::pyobject_for(shared_ptr)          // every other identity type has one, built on
                                       // mcrf::cached_wrapper<Obj>(serial, type, fill)
// tp_init of an identity type: make the user's object THE wrapper.
if (mcrf::register_wrapper(self->data->serial_number, (PyObject*)self) < 0) return -1;
mcrf::live_wrapper(serial) / mcrf::unregister_wrapper(serial)   // never PythonObjectCache::
// Vector arguments: never PyVector::from_arg() (new reference) in a setter.
sf::Vector2f v; if (!mcrf::to_vector2f(value, v, "pos")) return -1;
// Color values (#450): every write to a Color -- setter, ctor kwarg, item, method arg,
// animate target -- goes through PyColor::to_color, which is exactly Color(value): a Color
// or an (r, g, b[, a]) int tuple in 0-255, else the same exception. Never clamp, wrap or
// default inside it; an optional arg checks for None itself. (fromPy/from_arg are gone.)
sf::Color c; if (!PyColor::to_color(value, c)) return -1;
// Text (#477): every std::string of text is UTF-8, regardless of locale (as in Python
// 3.15). Text crosses into SFML only through src/Utf8.h -- never a bare std::string,
// which SFML widens byte-per-code-point -- and the SDL2 glyph loops walk code points.
text.setString(mcrf::from_utf8(s));  std::string s = mcrf::to_utf8(text.getString());
// New references handed to non-stealing calls:
mcrf::dict_steal(d, "fps", PyLong_FromLong(fps));      // steals; fails cleanly on nullptr
_click(self, mcrf::PyRef(PyTuple_New(0)).get(), kw);  // PyRef owns it for the expression
```

To make a new type cacheable: give it weakref support (`weakreflist` +
`tp_weaklistoffset`, cleared in `tp_dealloc`), a `uint64_t` serial on the C++ object (or,
for a view such as a collection, on its owner: `UIDrawable::children_serial`,
`GridData::entities_serial`), `unregister_wrapper()` where that owner dies, and one
`pyobject_for()` on `cached_wrapper`. `tp_alloc`'d structs are zero-filled, not
constructed: placement-new C++ members in the fill lambda and destroy them in `tp_dealloc`.

**Identity pin (#436, #443).** An object's live Python wrapper (plain or subclass) is kept
alive exactly while a C++ container owns the object, via an `mcrf::PyIdentityPin` synced in ONE
choke point per kind: `UIDrawable::updatePyIdentityPin()` (from `setParent()/setParentScene()`),
`UIEntity::syncIdentityPin()` (from `setGrid()`), `Entity3D::syncIdentityPin()` (from
`setViewport()`). The converters call the same function, so a wrapper made later for a contained
object is pinned too. An object attached from C++ has no wrapper, and is not pinned, until
Python first touches it.
Never read the pin as "the wrapper" (it has no getter); use `to_python()`. An entity's grid
back-reference is a `weak_ptr` (`getGrid()`), so dropping a grid frees it and its entities.

**Membership (#442, #447, #438).** A drawable has one parent, an entity one grid, an
`Entity3D` one viewport, each at most once. Every add *moves*: out of the old collection, or
out of the old slot in the same one. One choke point per kind: drawables detach with
`UIDrawable::removeFromParent()` and are cycle-checked first with `UIDrawable::canAdopt()`
(`can_link()` inside `UICollection`), before anything is mutated; entities go through
`UIEntity::moveToGrid(grid, index)` (built on `removeFromGrid()`), and Entity3D through
`moveToViewport()` (built on `removeFromViewport()`). Never push onto a children/`entities`
vector by hand. `[i] = x` replaces the element at `i` before `x` leaves its old slot; slice
assignment builds the result list and commits it once; a value list naming one object twice
raises `ValueError`. Membership changes repaint: `UIEntity::setGrid()` marks the old and new
grid dirty (#446).

**Render invalidation (#427, #446).** `GridData::markDirty()` / `markCompositeDirty()` are the
only writers of `content_generation`: they also mark every registered view, which walks up to
any `cache_subtree` ancestor. Layer edits reach them through `GridLayer::notifyGrid()`, layer
add/remove through `GridData::attachLayer()` / `removeLayer()`, and `GridLayer::setZIndex()`
also sets `layers_need_sort`. Bumping the counter directly repaints the view but not a caching
parent.

**GC ownership (#441).** A wrapper's `tp_traverse` may report the Python objects held inside
its C++ object (callbacks, children's pins, a cached wrapper) only when it owns that object
exclusively: `mcrf::owns_exclusively(use_count, keepers)`, where keepers are other owners that
hold the wrapper (its pin's container, a view caching its GridData wrapper). `tp_clear` applies
the same test. Reporting a co-owned object's callback let the GC wipe a closure a scene still
calls (segfault); clearing it dropped live handlers; reporting nothing leaked every cycle
through a pin. Drawables use `UIDrawable::traverseWrapper/clearWrapper` and extend
`traverseOwned()/clearOwned()`; owners of children/entities descend via `traverseChildren`.
Pinning plain wrappers too (#443) is what makes this complete: otherwise a contained object
with a live wrapper has two owners, and neither may report its callbacks.

**Audio ownership (#440, #406, #400).** `src/Audio.h` owns playback. A playing `Sound` or
`Music` is retained by `mcrf::audio` until it stops (swept once per frame), which is what
makes `Sound(...).play()` work without a held reference. Device resources (`sf::Sound`,
`sf::Music`, `sf::SoundBuffer`, each of which opens the OpenAL device when constructed)
exist only while `mcrf::audio::enabled()`. They live behind a `unique_ptr` in an
`mcrf::audio::Source`, so that `shutdown()` (run via `Py_AtExit`) can close the device
before `exit()`. Never add an `sf::` audio member anywhere else: an unused one on
`GameEngine` kept a device open in every run, and it is what caused #400.

`tools/lint_bindings.py` (tree-sitter, `make lint-bindings`) enforces all of this:
identity-type construction outside a converter (via `tp_alloc`, `Foo::pynew`, or
`PyObject_New`), direct `PythonObjectCache::` use, a new reference passed inline to a
non-stealing call, an unreleased `from_arg()`, the pin touched outside its owner, a
`tp_traverse`/`tp_clear` reaching into the C++ object without `owns_exclusively`, a parent
link without `canAdopt` (`adopt-unchecked`), an entity-list insert without
`removeFromGrid`/`removeFromViewport` (`entity-unlinked`), and backend text
(`setString`/`getString`/`setTitle`/window `create`) not passed through `mcrf::from_utf8`/`to_utf8`
(`text-unencoded`, #477). Every
constructed type must be classified identity/value in its `TYPE_CLASS` table. The baseline
(`tools/lint_bindings_baseline.txt`) is empty and may only shrink; the pre-commit hook and
CI fail on any finding. `tools/refactor_check.py FILE --site KEY` is the fast per-file
check (syntax-only compile + lint) used for migrations.

#### Collection Patterns
- `UICollection` wraps `std::vector<std::shared_ptr<UIDrawable>>`
- `UIEntityCollection` wraps `std::vector<std::shared_ptr<UIEntity>>` (#329: was a
  `std::list`; indexing is O(1) now, so don't reintroduce `std::advance`)

### Working Directory Structure
```
build/
├── mcrogueface          # The executable
├── scripts/            
│   └── game.py         # Auto-loaded Python script
├── assets/             # Copied from source during build
└── lib/                # Python libraries (copied from __lib/)
```

### Quick Iteration Tips
- Keep a test script ready for quick experiments
- Use `timeout` to auto-kill hanging processes
- The game expects a window manager; use Xvfb for headless testing
- Python errors go to stderr, game output to stdout
- Segfaults usually mean Python type initialization issues

## Important Notes

- The project uses SFML for graphics/audio (or SDL2 when building for wasm) and libtcod for roguelike utilities
- Python scripts are loaded at runtime from the `scripts/` directory
- Asset loading expects specific paths relative to the executable
- The game was created for 7DRL 2023
- Iterator implementations require careful handling of C++/Python boundaries

## Testing Guidelines

### Test-Driven Development
- **Always write tests first**: Create tests in `./tests/` for all bugs and new features
- **Practice TDD**: Write tests that fail to demonstrate the issue, then pass after the fix
- **Read existing tests**: Check `tests/unit/` and `tests/demo/screens/` for API examples before writing code
- **Close the loop**: Reproduce issue → change code → recompile → run test → verify

### Two Types of Tests

#### 1. Direct Execution Tests (No Game Loop)
For tests that only need class initialization or direct code execution:
```python
# tests/unit/my_feature_test.py
import mcrfpy
import sys

# Test code - runs immediately
frame = mcrfpy.Frame(pos=(0,0), size=(100,100))
assert frame.x == 0
assert frame.w == 100

print("PASS")
sys.exit(0)
```

#### 2. Game Loop Tests (Timer-Based)
For tests requiring rendering, screenshots, or elapsed time:
```python
# tests/unit/my_visual_test.py
import mcrfpy
from mcrfpy import automation
import sys

def run_test(runtime):
    """Timer callback - runs after game loop starts"""
    automation.screenshot("test_result.png")
    # Validate results...
    print("PASS")
    sys.exit(0)

test_scene = mcrfpy.Scene("test")
ui = test_scene.children
ui.append(mcrfpy.Frame(pos=(50,50), size=(100,100)))
mcrfpy.current_scene = test_scene
timer = mcrfpy.Timer("test", run_test, 100)
```

### Key Testing Principles
- **Timer callbacks are essential**: Screenshots only work after the render loop starts
- **Use automation API**: `automation.screenshot()`, `automation.click()` for visual testing
- **Exit properly**: Always call `sys.exit(0)` for PASS or `sys.exit(1)` for FAIL
- **Headless mode**: Use `--headless --exec` for CI/automated testing
- **Check examples first**: Read `tests/demo/screens/*.py` for correct API usage

### API Quick Reference (from tests)
```python
# Scene: create and activate a scene, or create another scene
mcrfpy.current_scene = mcrfpy.Scene("test")
demo_scene = mcrfpy.Scene("demo")

# Animation: construct via the object's .animate() method (mcrfpy.Animation no longer exported).
frame.animate("x", 500.0, 2.0, mcrfpy.Easing.EASE_IN_OUT)

# Animation callbacks (#229) receive (target, property, final_value):
def on_anim_complete(target, prop, value):
    print(f"{type(target).__name__}.{prop} reached {value}")
frame.animate("x", 500.0, 2.0, mcrfpy.Easing.EASE_IN_OUT, callback=on_anim_complete)

# Caption: use keyword arguments to avoid positional conflicts
cap = mcrfpy.Caption(text="Hello", pos=(100, 100))

# Grid center: uses pixel coordinates, not cell coordinates
grid = mcrfpy.Grid(grid_size=(15, 10), pos=(50, 50), size=(400, 300))
grid.center = (120, 80)  # pixels: (cells * cell_size / 2)
# grid center defaults to the position that puts (0, 0) in the top left corner of the grid's visible area.
# set grid.center to focus on that position. To position the camera in tile coordinates, use grid.center_camera():
grid.center_camera((14.5, 8.5)) # offset of 0.5 tiles to point at the middle of the tile

# Grid texture / cell size (#453, #454): a grid made without texture= has none and 1x1 cells
# until a view first DRAWS it (screenshot or windowed frame; step() never draws), which then
# assigns mcrfpy.default_texture with a mcrfpy.TextureWarning. Tests doing 16px pixel math or
# clicks before drawing must pass texture=mcrfpy.default_texture (or set grid.cell_size).
# Layers/entities without their own texture have .texture None and draw with grid.texture.

# Grid.step (turn manager): advances all entities by n turns in turn_order order.
grid.step(n=1, turn_order=None)  # turn_order=None = use each entity's .turn_order (ascending)

# Entity behaviors (set_behavior + Behavior enum):
enemy.set_behavior(mcrfpy.Behavior.SEEK, pathfinder=dijkstra_map)
enemy.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(5, 5), (10, 10)], turns=3)
enemy.labels = {"hostile", "medium"}  # frozenset of str, for collision/targeting
enemy.turn_order = 2                  # higher = later in turn; 0 = skip
enemy.cell_pos                        # logical cell (Vector), distinct from draw_pos

# Trigger callback (fires on DONE, BLOCKED, ARRIVED, etc.):
def on_trigger(trigger, data):
    if trigger == mcrfpy.Trigger.DONE: ...
enemy.step = on_trigger

# Keyboard handler (#184): receives Key and InputState enums
def on_key(key, action):
    if key == mcrfpy.Key.Num1 and action == mcrfpy.InputState.PRESSED:
        demo_scene.activate()
scene.on_key = on_key

# Mouse callbacks (#230):
# on_click receives (pos: Vector, button: MouseButton, action: InputState)
def on_click(pos, button, action):
    if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
        print(f"Clicked at {pos.x}, {pos.y}")
frame.on_click = on_click

# Hover callbacks (#230) receive only position:
def on_enter(pos):
    print(f"Entered at {pos.x}, {pos.y}")
frame.on_enter = on_enter  # Also: on_exit, on_move

# Grid cell callbacks (#230):
# on_cell_click receives (cell_pos: Vector, button: MouseButton, action: InputState)
# on_cell_enter/on_cell_exit receive only (cell_pos: Vector)
```

## Development Best Practices

### Testing and Deployment
- **Keep tests in ./tests, not ./build/tests** - ./build gets shipped, tests shouldn't be included
- **Run full suite before commits**: `cd tests && python3 run_tests.py`

## Documentation Guidelines

### Documentation Macro System

**As of 2025-10-30, McRogueFace uses a macro-based documentation system** (`src/McRFPy_Doc.h`) that ensures consistent, complete docstrings across all Python bindings.

#### Include the Header

```cpp
#include "McRFPy_Doc.h"
```

#### Documenting Methods

For methods in PyMethodDef arrays, use `MCRF_METHOD`:

```cpp
{"method_name", (PyCFunction)Class::method, METH_VARARGS,
 MCRF_METHOD(ClassName, method_name,
     MCRF_SIG("(arg1: type, arg2: type)", "return_type"),
     MCRF_DESC("Brief description of what the method does."),
     MCRF_ARGS_START
     MCRF_ARG("arg1", "Description of first argument")
     MCRF_ARG("arg2", "Description of second argument")
     MCRF_RETURNS("Description of return value")
     MCRF_RAISES("ValueError", "Condition that raises this exception")
     MCRF_NOTE("Important notes or caveats")
     MCRF_LINK("docs/guide.md", "Related Documentation")
 )},
```

#### Documenting Properties

For properties in PyGetSetDef arrays, use `MCRF_PROPERTY`:

```cpp
{"property_name", (getter)getter_func, (setter)setter_func,
 MCRF_PROPERTY(property_name,
     "Brief description of the property. "
     "Additional details about valid values, side effects, etc."
 ), NULL},
```

#### Available Macros

- `MCRF_SIG(params, ret)` - Method signature
- `MCRF_DESC(text)` - Description paragraph
- `MCRF_ARGS_START` - Begin arguments section
- `MCRF_ARG(name, desc)` - Individual argument
- `MCRF_RETURNS(text)` - Return value description
- `MCRF_RAISES(exception, condition)` - Exception documentation
- `MCRF_NOTE(text)` - Important notes
- `MCRF_LINK(path, text)` - Reference to external documentation

#### Documentation Prose Guidelines

**Keep C++ docstrings concise** (1-2 sentences per section). For complex topics, use `MCRF_LINK` to reference external guides:

```cpp
MCRF_LINK("docs/animation-guide.md", "Animation System Tutorial")
```

**External documentation** (in `docs/`) can be verbose with examples, tutorials, and design rationale.

### Regenerating Documentation

After modifying C++ inline documentation with MCRF_* macros:

1. **Rebuild the project**: `make -j$(nproc)`

2. **Generate all documentation** (recommended - single command):
   ```bash
   ./tools/generate_all_docs.sh
   ```
   This creates:
   - `docs/api_reference_dynamic.html` - HTML API reference
   - `docs/API_REFERENCE_DYNAMIC.md` - Markdown API reference
   - `docs/mcrfpy.3` - Unix man page (section 3)
   - `stubs/mcrfpy.pyi` - Type stubs for IDE support

3. **Or generate individually**:
   ```bash
   # API docs (HTML + Markdown)
   ./build/mcrogueface --headless --exec tools/generate_dynamic_docs.py

   # Type stubs (manually-maintained with @overload support)
   ./build/mcrogueface --headless --exec tools/generate_stubs_v2.py

   # Man page (requires pandoc)
   ./tools/generate_man_page.sh
   ```

**System Requirements:**
- `pandoc` must be installed for man page generation: `sudo apt-get install pandoc`

### Important Notes

- **Single source of truth**: Documentation lives in C++ source files via MCRF_* macros
- **McRogueFace as Python interpreter**: Documentation scripts MUST be run using McRogueFace itself, not system Python
- **Use --headless --exec**: For non-interactive documentation generation
- **Link transformation**: `MCRF_LINK` references are transformed to appropriate format (HTML, Markdown, etc.)
- **No manual dictionaries**: The old hardcoded documentation system has been removed

### Documentation Pipeline Architecture

1. **C++ Source** → MCRF_* macros in PyMethodDef/PyGetSetDef arrays
2. **Compilation** → Macros expand to complete docstrings embedded in module
3. **Introspection** → Scripts use `dir()`, `getattr()`, `__doc__` to extract
4. **Generation** → HTML/Markdown/Stub files created with transformed links
5. **No drift**: Impossible for docs and code to disagree - they're the same file!

The macro system ensures complete, consistent documentation across all Python bindings.

### Adding Documentation for New Python Types

When adding a new Python class/type to the engine, follow these steps to ensure it's properly documented:

#### 1. Class Docstring (tp_doc)

In the `PyTypeObject` definition (usually in the header file), set `tp_doc` with a comprehensive docstring:

```cpp
// In PyMyClass.h
.tp_doc = PyDoc_STR(
    "MyClass(arg1: type, arg2: type)\n\n"
    "Brief description of what this class does.\n\n"
    "Args:\n"
    "    arg1: Description of first argument.\n"
    "    arg2: Description of second argument.\n\n"
    "Properties:\n"
    "    prop1 (type, read-only): Description of property.\n"
    "    prop2 (type): Description of writable property.\n\n"
    "Example:\n"
    "    obj = mcrfpy.MyClass('example', 42)\n"
    "    print(obj.prop1)\n"
),
```

#### 2. Method Documentation (PyMethodDef)

For each method in the `methods[]` array, use the MCRF_* macros:

```cpp
// In PyMyClass.cpp
PyMethodDef PyMyClass::methods[] = {
    {"do_something", (PyCFunction)do_something, METH_VARARGS,
     MCRF_METHOD(MyClass, do_something,
         MCRF_SIG("(value: int)", "bool"),
         MCRF_DESC("Does something with the value."),
         MCRF_ARGS_START
         MCRF_ARG("value", "The value to process")
         MCRF_RETURNS("True if successful, False otherwise")
     )},
    {NULL}  // Sentinel
};
```

#### 3. Property Documentation (PyGetSetDef)

For each property in the `getsetters[]` array, include a docstring:

```cpp
// In PyMyClass.cpp
PyGetSetDef PyMyClass::getsetters[] = {
    {"property_name", (getter)get_property, (setter)set_property,
     "Property description. Include (type, read-only) if not writable.",
     NULL},
    {NULL}  // Sentinel
};
```

**Important for read-only properties:** Include "read-only" in the docstring so the doc generator detects it:
```cpp
{"name", (getter)get_name, NULL,  // NULL setter = read-only
 "Object name (str, read-only). Unique identifier.",
 NULL},
```

#### 4. Register Type in Module

Ensure the type is properly registered in `McRFPy_API.cpp` and its methods/getsetters are assigned:

```cpp
// Set methods and getsetters before PyType_Ready
mcrfpydef::PyMyClassType.tp_methods = PyMyClass::methods;
mcrfpydef::PyMyClassType.tp_getset = PyMyClass::getsetters;

// Then call PyType_Ready and add to module
```

#### 5. Regenerate Documentation

After adding the new type, regenerate all docs:

```bash
make -j4  # Rebuild with new documentation
cd build
./mcrogueface --headless --exec ../tools/generate_dynamic_docs.py
cp docs/API_REFERENCE_DYNAMIC.md ../docs/
cp docs/api_reference_dynamic.html ../docs/
```

#### 6. Update Type Stubs (Optional)

For IDE support, update `stubs/mcrfpy.pyi` with the new class:

```python
class MyClass:
    """Brief description."""
    def __init__(self, arg1: str, arg2: int) -> None: ...
    @property
    def prop1(self) -> str: ...
    def do_something(self, value: int) -> bool: ...
```

### Documentation Extraction Details

The doc generator (`tools/generate_dynamic_docs.py`) uses Python introspection:

- **Classes**: Detected via `inspect.isclass()`, docstring from `cls.__doc__`
- **Methods**: Detected via `callable()` check on class attributes
- **Properties**: Detected via `types.GetSetDescriptorType` (C++ extension) or `property` (Python)
- **Read-only detection**: Checks if "read-only" appears in property docstring

If documentation isn't appearing, verify:
1. The type is exported to the `mcrfpy` module
2. Methods/getsetters arrays are properly assigned before `PyType_Ready()`
3. Docstrings don't contain null bytes or invalid UTF-8

---

- Close issues automatically in gitea by adding to the commit message "closes #X", where X is the issue number. This associates the issue closure with the specific commit, so granular commits are preferred. You should only use the MCP tool to close issues directly when discovering that the issue is already complete; when committing changes, always such "closes" (or the opposite, "reopens") references to related issues. If on a feature branch, the issue will be referenced by the commit, and when merged to master, the issue will be actually closed (or reopened).
