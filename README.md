# McRogueFace
*Blame my wife for the name*

A Python-powered 2D game engine for creating roguelike games, built with C++ and SFML.

* Core roguelike logic from libtcod: field of view, pathfinding
* Animate sprites with multiple frames. Smooth transitions for positions, sizes, zoom, and camera
* Simple GUI element system allows keyboard and mouse input, composition
* No compilation or installation necessary. The runtime is a full Python environment; "Zip And Ship"

![ Image ]()

**Pre-Alpha Release Demo**: my 7DRL 2025 entry *"Crypt of Sokoban"* - a prototype with buttons, boulders, enemies, and items.

## Quick Start

**Download**: 

- The entire McRogueFace visual framework:
  - **Sprite**: an image file or one sprite from a shared sprite sheet
  - **Caption**: load a font, display text
  - **Frame**: A rectangle; put other things on it to move or manage GUIs as modules
  - **Grid**: A 2D array of tiles with zoom + position control
  - **Entity**: Lives on a Grid, displays a sprite, and can have a perspective or move along a path
  - **Animation**: Change any property on any of the above over time

```bash
# Clone and build
git clone <wherever you found this repo>
cd McRogueFace
make

# Run the example game
cd build
./mcrogueface
```

## Example: Creating a Simple Scene

```python
import mcrfpy

# Create a new scene
mcrfpy.createScene("intro")

# Add a text caption
caption = mcrfpy.Caption((50, 50), "Welcome to McRogueFace!")
caption.size = 48 
caption.fill_color = (255, 255, 255)

# Add to scene
mcrfpy.sceneUI("intro").append(caption)

# Switch to the scene
mcrfpy.setScene("intro")
```

## Documentation

### 📚 Full Documentation Site

For comprehensive documentation, tutorials, and API reference, visit:
**[https://mcrogueface.github.io](https://mcrogueface.github.io)**

The documentation site includes:

- **[Quickstart Guide](https://mcrogueface.github.io/quickstart/)** - Get running in 5 minutes
- **[McRogueFace Does The Entire Roguelike Tutorial](https://mcrogueface.github.io/tutorials/)** - Step-by-step game building
- **[Complete API Reference](https://mcrogueface.github.io/api/)** - Every function documented
- **[Cookbook](https://mcrogueface.github.io/cookbook/)** - Ready-to-use code recipes
- **[C++ Extension Guide](https://mcrogueface.github.io/extending-cpp/)** - For C++ developers: Add engine features

## Build Requirements

- C++17 compiler (GCC 7+ or Clang 5+)
- CMake 3.14+
- Python 3.12+
- SFML 2.6
- Linux or Windows (macOS untested)

## Project Structure

```
McRogueFace/
├── assets/        # Sprites, fonts, audio
├── build/         # Build output directory: zip + ship
│   ├─ (*)assets/  # (copied location of assets) 
│   ├─ (*)scripts/ # (copied location of src/scripts)
│   └─ lib/        # SFML, TCOD libraries,  Python + standard library / modules
├── deps/          # Python, SFML, and libtcod imports can be tossed in here to build
│   └─ platform/   # windows, linux subdirectories for OS-specific cpython config
├── docs/          # generated HTML, markdown docs
│   └─ stubs/      # .pyi files for editor integration
├── modules/       # git submodules, to build all of McRogueFace's dependencies from source
├── src/           # C++ engine source
│   └─ scripts/    # Python game scripts (copied during build)
└── tests/         # Automated test suite
└── tools/         # For the McRogueFace ecosystem: docs generation
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

The project has a private roadmap and issue list. Reach out via email or social media if you have bugs or feature requests.

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Acknowledgments

- Developed for 7-Day Roguelike 2023, 2024, 2025 - here's to many more
- Built with [SFML](https://www.sfml-dev.org/), [libtcod](https://github.com/libtcod/libtcod), and Python
- Inspired by David Churchill's COMP4300 game engine lectures
