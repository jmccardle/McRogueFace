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
   - When discovering undocumented behavior: Create task to document it
   - When documentation misleads you: Create task to correct or expand it
   - When implementing a feature: Update the Gitea wiki if appropriate

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

## Build Commands

```bash
# Build the project (compiles to ./build directory)
make

# Or use the build script directly
./build.sh

# Run the game
make run

# Clean build artifacts
make clean

# The executable and all assets are in ./build/
cd build
./mcrogueface
```

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
- Scene Management: `createScene()`, `setScene()`, `sceneUI()`
- Entity Creation: `Entity()` with position and sprite properties
- Grid Management: `Grid()` for tilemap rendering
- Input Handling: `keypressScene()` for keyboard events
- Audio: `createSoundBuffer()`, `playSound()`, `setVolume()`
- Timers: `setTimer()`, `delTimer()` for event scheduling

## Development Workflow

### Running the Game
After building, the executable expects:
- `assets/` directory with sprites, fonts, and audio
- `scripts/` directory with Python game files
- Python 3.12 shared libraries in `./lib/`

### Modifying Game Logic
- Game scripts are in `src/scripts/`
- Main game entry is `game.py`
- Entity behavior in `cos_entities.py`
- Level generation in `cos_level.py`

### Adding New Features
1. C++ API additions go in `src/McRFPy_API.cpp`
2. Expose to Python using the existing binding pattern
3. Update Python scripts to use new functionality

## Testing Game Changes

Currently no automated test suite. Manual testing workflow:
1. Build with `make`
2. Run `make run` or `cd build && ./mcrogueface`
3. Test specific features through gameplay
4. Check console output for Python errors

### Quick Testing Commands
```bash
# Test basic functionality
make test

# Run in Python interactive mode
make python

# Test headless mode
cd build
./mcrogueface --headless -c "import mcrfpy; print('Headless test')"
```

## Common Development Tasks

### Compiling McRogueFace
```bash
# Standard build (to ./build directory)
make

# Full rebuild
make clean && make

# Manual CMake build
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

# The library path issue: if linking fails, check that libraries are in __lib/
# CMakeLists.txt expects: link_directories(${CMAKE_SOURCE_DIR}/__lib)
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
echo 'import mcrfpy; print("Test"); mcrfpy.createScene("test")' > scripts/game.py
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
- **Always write tests first**: Create automation tests in `./tests/` for all bugs and new features
- **Practice TDD**: Write tests that fail to demonstrate the issue, then pass after the fix is applied
- **Close the loop**: Reproduce issue → change code → recompile → verify behavior change

### Two Types of Tests

#### 1. Direct Execution Tests (No Game Loop)
For tests that only need class initialization or direct code execution:
```python
# These tests can treat McRogueFace like a Python interpreter
import mcrfpy

# Test code here
result = mcrfpy.some_function()
assert result == expected_value
print("PASS" if condition else "FAIL")
```

#### 2. Game Loop Tests (Timer-Based)
For tests requiring rendering, game state, or elapsed time:
```python
import mcrfpy
from mcrfpy import automation
import sys

def run_test(runtime):
    """Timer callback - runs after game loop starts"""
    # Now rendering is active, screenshots will work
    automation.screenshot("test_result.png")
    
    # Run your tests here
    automation.click(100, 100)
    
    # Always exit at the end
    print("PASS" if success else "FAIL")
    sys.exit(0)

# Set up the test scene
mcrfpy.createScene("test")
# ... add UI elements ...

# Schedule test to run after game loop starts
mcrfpy.setTimer("test", run_test, 100)  # 0.1 seconds
```

### Key Testing Principles
- **Timer callbacks are essential**: Screenshots and UI interactions only work after the render loop starts
- **Use automation API**: Always create and examine screenshots when visual feedback is required
- **Exit properly**: Call `sys.exit()` at the end of timer-based tests to prevent hanging
- **Headless mode**: Use `--exec` flag for automated testing: `./mcrogueface --headless --exec tests/my_test.py`

### Example Test Pattern
```bash
# Run a test that requires game loop
./build/mcrogueface --headless --exec tests/issue_78_middle_click_test.py

# The test will:
# 1. Set up the scene during script execution
# 2. Register a timer callback
# 3. Game loop starts
# 4. Timer fires after 100ms
# 5. Test runs with full rendering available
# 6. Test takes screenshots and validates behavior
# 7. Test calls sys.exit() to terminate
```

## Development Best Practices

### Testing and Deployment
- **Keep tests in ./tests, not ./build/tests** - ./build gets shipped, and tests shouldn't be included

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

2. **Generate documentation** (automatic from compiled module):
   ```bash
   ./build/mcrogueface --headless --exec tools/generate_dynamic_docs.py
   ```
   This creates:
   - `docs/api_reference_dynamic.html`
   - `docs/API_REFERENCE_DYNAMIC.md`

3. **Generate stub files** (optional, for IDE support):
   ```bash
   ./build/mcrogueface --headless --exec tools/generate_stubs.py
   ```
   Creates `.pyi` stub files for type checking and autocompletion

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