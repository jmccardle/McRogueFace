# McRogueFace
*Blame my wife for the name*

A Python-powered 2D game engine for creating roguelike games, built with C++ and SFML.

* Core roguelike logic from libtcod: field of view, pathfinding
* Animate sprites with multiple frames. Smooth transitions for positions, sizes, zoom, and camera
* Simple GUI element system allows keyboard and mouse input, composition
* No compilation or installation necessary. The runtime is a full Python environment; "Zip And Ship"

📖 **[Full Documentation & Tutorials](https://mcrogueface.github.io/)** - Quickstart guide, API reference, and cookbook

## Quick Start

**Download** the [latest release](https://github.com/jmccardle/McRogueFace/releases/latest):
- **Windows**: `McRogueFace-*-Win.zip`
- **Linux**: `McRogueFace-*-Linux.tar.bz2`

Extract and run `mcrogueface` (or `mcrogueface.exe` on Windows) to see the demo game.

### Your First Game

Create `scripts/game.py` (or edit the existing one):

```python
import mcrfpy

# Create and activate a scene
scene = mcrfpy.Scene("game")
scene.activate()

# Load a sprite sheet
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Create a tile grid
grid = mcrfpy.Grid(grid_size=(20, 15), texture=texture, pos=(50, 50), size=(640, 480))
grid.zoom = 2.0
scene.children.append(grid)

# Add a player entity
player = mcrfpy.Entity(pos=(10, 7), texture=texture, sprite_index=84)
grid.entities.append(player)

# Handle keyboard input
def on_key(key, state):
    if state != "start":
        return
    x, y = int(player.x), int(player.y)
    if key == "W": y -= 1
    elif key == "S": y += 1
    elif key == "A": x -= 1
    elif key == "D": x += 1
    player.x, player.y = x, y

scene.on_key = on_key
```

Run `mcrogueface` and you have a movable character!

### Visual Framework

- **Sprite**: Single image or sprite from a shared sheet
- **Caption**: Text rendering with fonts
- **Frame**: Container rectangle for composing UIs
- **Grid**: 2D tile array with zoom and camera control
- **Entity**: Grid-based game object with sprite and pathfinding
- **Animation**: Interpolate any property over time with easing

## Building from Source

For most users, pre-built releases are available. If you need to build from source:

### Quick Build (with pre-built dependencies)

Download `build_deps.tar.gz` from the releases page, then:

```bash
git clone <repository-url> McRogueFace
cd McRogueFace
tar -xzf /path/to/build_deps.tar.gz
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

### Full Build (compiling all dependencies)

```bash
git clone --recursive <repository-url> McRogueFace
cd McRogueFace
# See BUILD_FROM_SOURCE.md for complete instructions
```

**[BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md)** - Complete build guide including:
- System dependency installation
- Compiling SFML, Python, and libtcod-headless from source
- Creating `build_deps` archives for distribution
- Troubleshooting common build issues

### System Requirements

- **Linux**: Debian/Ubuntu tested; other distros should work
- **Windows**: Supported (see build guide for details)
- **macOS**: Untested

## Example: Main Menu with Buttons

```python
import mcrfpy

# Create a scene
scene = mcrfpy.Scene("menu")

# Add a background frame
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                  fill_color=mcrfpy.Color(20, 20, 40))
scene.children.append(bg)

# Add a title
title = mcrfpy.Caption(pos=(312, 100), text="My Roguelike",
                       fill_color=mcrfpy.Color(255, 255, 100))
title.font_size = 48
scene.children.append(title)

# Create a button
button = mcrfpy.Frame(pos=(362, 300), size=(300, 80),
                      fill_color=mcrfpy.Color(50, 150, 50))
button_text = mcrfpy.Caption(pos=(90, 25), text="Start Game")
button.children.append(button_text)

def on_click(x, y, btn):
    print("Game starting!")

button.on_click = on_click
scene.children.append(button)

scene.activate()
```

## Documentation

### 📚 Developer Documentation

For comprehensive documentation about systems, architecture, and development workflows:

**[Project Wiki](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki)**

Key wiki pages:

- **[Home](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Home)** - Documentation hub with multiple entry points
- **[Grid System](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Grid-System)** - Three-layer grid architecture
- **[Python Binding System](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Python-Binding-System)** - C++/Python integration
- **[Performance and Profiling](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Performance-and-Profiling)** - Optimization tools
- **[Adding Python Bindings](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Adding-Python-Bindings)** - Step-by-step binding guide
- **[Issue Roadmap](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Issue-Roadmap)** - All open issues organized by system

### 📖 Development Guides

In the repository root:

- **[CLAUDE.md](CLAUDE.md)** - Build instructions, testing guidelines, common tasks
- **[ROADMAP.md](ROADMAP.md)** - Strategic vision and development phases
- **[roguelike_tutorial/](roguelike_tutorial/)** - Complete roguelike tutorial implementations

## Build Requirements

- C++17 compiler (GCC 7+ or Clang 5+)
- CMake 3.14+
- Python 3.14 (embedded)
- SFML 2.6
- Linux or Windows (macOS untested)

See [BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md) for detailed compilation instructions.

## Project Structure

```
McRogueFace/
├── assets/        # Sprites, fonts, audio
├── build/         # Build output: this is what you distribute
│   ├── assets/    # (copied from assets/)
│   ├── scripts/   # (copied from src/scripts/)
│   └── lib/       # Python stdlib and extension modules
├── docs/          # Generated HTML, markdown API docs
├── src/           # C++ engine source
│   └── scripts/   # Python game scripts
├── stubs/         # .pyi type stubs for IDE integration
├── tests/         # Automated test suite
└── tools/         # Documentation generation scripts
```

If you are building McRogueFace to implement game logic or scene configuration in C++, you'll have to compile the project.

If you are writing a game in Python using McRogueFace, you only need to rename and zip/distribute the `build` directory.

## Philosophy

- **C++ every frame, Python every tick**: All rendering data is handled in C++. Structure your UI and program animations in Python, and they are rendered without Python. All game logic can be written in Python.
- **No Compiling Required; Zip And Ship**: Implement your game objects with Python, zip up McRogueFace with your "game.py" to ship
- **Built-in Roguelike Support**: Dungeon generation, pathfinding, and field-of-view via libtcod 
- **Hands-Off Testing**: PyAutoGUI-inspired event generation framework. All McRogueFace interactions can be performed headlessly via script: for software testing or AI integration
- **Interactive Development**: Python REPL integration for live game debugging. Use `mcrogueface` like a Python interpreter

## Contributing

PRs will be considered! Please include explicit mention that your contribution is your own work and released under the MIT license in the pull request.

### Issue Tracking

The project uses [Gitea Issues](https://gamedev.ffwf.net/gitea/john/McRogueFace/issues) for task tracking and bug reports. Issues are organized with labels:

- **System labels** (grid, animation, python-binding, etc.) - identify which codebase area
- **Priority labels** (tier1-active, tier2-foundation, tier3-future) - development timeline
- **Type labels** (Major Feature, Minor Feature, Bugfix, etc.) - effort and scope

See the [Issue Roadmap](https://gamedev.ffwf.net/gitea/john/McRogueFace/wiki/Issue-Roadmap) on the wiki for organized view of all open tasks.

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Acknowledgments

- Developed for 7-Day Roguelike 2023, 2024, 2025, 2026 - here's to many more
- Built with [SFML](https://www.sfml-dev.org/), [libtcod](https://github.com/libtcod/libtcod), and Python
- Inspired by David Churchill's COMP4300 game engine lectures
