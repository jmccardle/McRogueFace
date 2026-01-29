# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Gitea-First Workflow

**IMPORTANT**: This project uses Gitea for issue tracking, documentation, and project management. Always consult and update Gitea resources before and during development work.

**Gitea Instance**: https://gamedev.ffwf.net/gitea/john/McRogueFace

### Core Principles

1. **Gitea is the Single Source of Truth**
   - Issue tracker contains current tasks, bugs, and feature requests
   - Wiki contains living documentation and architecture decisions
   - Use Gitea MCP tools to query and update issues programmatically

2. **Always Check Gitea First**
   - Before starting work: Check open issues for related tasks or blockers
   - Before implementing: Read relevant wiki pages per the [Development Workflow](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Development-Workflow) consultation table
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
   - Follow the [Development Workflow](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Development-Workflow) for wiki update procedures

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

Claude Code has access to Gitea MCP tools for:
- `list_repo_issues` - Query current issues with filtering
- `get_issue` - Get detailed issue information
- `create_issue` - Create new issues programmatically
- `create_issue_comment` - Add comments to issues
- `edit_issue` - Update issue status, title, body
- `add_issue_labels` - Tag issues appropriately
- `add_issue_dependency` / `add_issue_blocking` - Link related issues
- Plus wiki, milestone, and label management tools

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

2. **Priority Labels** (development timeline):
   - `priority:tier1-active` - Current development focus - critical path to v1.0
   - `priority:tier2-foundation` - Important foundation work - not blocking v1.0
   - `priority:tier3-future` - Future features - deferred until after v1.0

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

**⚠️ CRITICAL BUG**: The Gitea MCP tool (v0.07) has a label application bug documented in `GITEA_MCP_LABEL_BUG_REPORT.md`:
- `add_issue_labels` and `replace_issue_labels` behave inconsistently
- Single ID arrays produce different results than multi-ID arrays for the SAME IDs
- Label IDs do not map reliably to actual labels

**Workaround Options:**
1. **Best**: Apply labels manually via web interface: `https://gamedev.ffwf.net/gitea/john/McRogueFace/issues/<number>`
2. **Automated**: Apply labels ONE AT A TIME using single-element arrays (slower but more reliable)
3. **Use single-ID mapping** (documented below)

**Label ID Reference** (for documentation purposes - see issue #131 for details):
```
1=Major Feature, 2=Alpha Release, 3=Bugfix, 4=Demo Target, 5=Documentation,
6=Minor Feature, 7=tier1-active, 8=tier2-foundation, 9=tier3-future,
10=Refactoring, 11=animation, 12=docs, 13=grid, 14=input, 15=performance,
16=python-binding, 17=rendering, 18=ui-hierarchy, 19=Tiny Feature,
20=blocked, 21=needs-benchmark, 22=needs-documentation
```

## Build System

McRogueFace uses a unified Makefile for both Linux native builds and Windows cross-compilation.

**IMPORTANT**: All `make` commands must be run from the **project root directory** (`/home/john/Development/McRogueFace/`), not from `build/` or any subdirectory.

### Quick Reference

```bash
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
- Libraries in `__lib/` directory (libpython3.14, libtcod, etc.)

**Windows cross-compilation:**
- MinGW-w64 (`x86_64-w64-mingw32-g++-posix`)
- Libraries in `__lib_windows/` directory
- Toolchain file: `cmake/toolchains/mingw-w64-x86_64.cmake`

### Library Dependencies

The build expects pre-built libraries in:
- `__lib/` - Linux shared libraries (libpython3.14.so, libsfml-*.so, libtcod.so)
- `__lib/Python/Lib/` - Python standard library source
- `__lib/Python/lib.linux-x86_64-3.14/` - Python extension modules (.so)
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
- `tools/package.sh` - Main packaging orchestrator
- `tools/package_stdlib.py` - Creates filtered stdlib archives
- `tools/stdlib_modules.yaml` - Module categorization config

### Troubleshooting

**"No rule to make target 'linux'"**: You're in the wrong directory. Run `make` from project root.

**Library linking errors**: Ensure `__lib/` contains all required .so files. Check `CMakeLists.txt` for `link_directories(${CMAKE_SOURCE_DIR}/__lib)`.

**Windows build fails**: Verify MinGW-w64 is installed with posix thread model: `x86_64-w64-mingw32-g++-posix --version`

### Legacy Build Scripts

The following are deprecated but kept for reference:
- `build.sh` - Original Linux build script (use `make` instead)
- `GNUmakefile.legacy` - Old wrapper makefile (renamed to avoid conflicts)

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
- Python 3.14 shared libraries in `./lib/`

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
# Run the full test suite (from tests/ directory)
cd tests && python3 run_tests.py

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

#### RET_PY_INSTANCE Macro (UIDrawable.h)
This macro handles converting C++ UI objects to their Python equivalents:
```cpp
RET_PY_INSTANCE(target);
// Expands to a switch on target->derived_type() that:
// 1. Allocates the correct Python object type (Frame, Caption, Sprite, Grid)
// 2. Sets the shared_ptr data member
// 3. Returns the PyObject*
```

#### Collection Patterns
- `UICollection` wraps `std::vector<std::shared_ptr<UIDrawable>>`
- `UIEntityCollection` wraps `std::list<std::shared_ptr<UIEntity>>`
- Different containers require different iteration code (vector vs list)

#### Python Object Creation Patterns
```cpp
// Pattern 1: Using tp_alloc (most common)
auto o = (PyUIFrameObject*)type->tp_alloc(type, 0);
o->data = std::make_shared<UIFrame>();

// Pattern 2: Getting type from module
auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
auto o = (PyUIEntityObject*)type->tp_alloc(type, 0);

// Pattern 3: Direct shared_ptr assignment
iterObj->data = self->data;  // Shares the C++ object
```

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

- The project uses SFML for graphics/audio and libtcod for roguelike utilities
- Python scripts are loaded at runtime from the `scripts/` directory
- Asset loading expects specific paths relative to the executable
- The game was created for 7DRL 2025 as "Crypt of Sokoban"
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

# Animation: (property, target_value, duration, easing)
# direct use of Animation object: deprecated
#anim = mcrfpy.Animation("x", 500.0, 2.0, "easeInOut")
#anim.start(frame)

# preferred: create animations directly against the targeted object; use Enum of easing functions
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
