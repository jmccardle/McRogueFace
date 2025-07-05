# McRogueFace
*Blame my wife for the name*

A Python-powered 2D game engine for creating roguelike games, built with C++ and SFML.

**Pre-Alpha Release Demo**: my 7DRL 2025 entry *"Crypt of Sokoban"* - a prototype with buttons, boulders, enemies, and items.

## Tenets

- **Python & C++ Hand-in-Hand**: Create your game without ever recompiling. Your Python commands create C++ objects, and animations can occur without calling Python at all.
- **Simple Yet Flexible UI System**: Sprites, Grids, Frames, and Captions with full animation support
- **Entity-Component Architecture**: Implement your game objects with Python integration
- **Built-in Roguelike Support**: Dungeon generation, pathfinding, and field-of-view via libtcod (demos still under construction)
- **Automation API**: PyAutoGUI-inspired event generation framework. All McRogueFace interactions can be performed headlessly via script: for software testing or AI integration
- **Interactive Development**: Python REPL integration for live game debugging. Use `mcrogueface` like a Python interpreter

## Quick Start

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

For comprehensive documentation, tutorials, and API reference, visit:
**[https://mcrogueface.github.io](https://mcrogueface.github.io)**

## Requirements

- C++17 compiler (GCC 7+ or Clang 5+)
- CMake 3.14+
- Python 3.12+
- SFML 2.5+
- Linux or Windows (macOS untested)

## Project Structure

```
McRogueFace/
├── src/           # C++ engine source
├── scripts/       # Python game scripts
├── assets/        # Sprites, fonts, audio
├── build/         # Build output directory
└── tests/         # Automated test suite
```

## Contributing

PRs will be considered! Please include explicit mention that your contribution is your own work and released under the MIT license in the pull request.

The project has a private roadmap and issue list. Reach out via email or social media if you have bugs or feature requests.

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Acknowledgments

- Developed for 7-Day Roguelike 2023, 2024, 2025 - here's to many more
- Built with [SFML](https://www.sfml-dev.org/), [libtcod](https://github.com/libtcod/libtcod), and Python
- Inspired by David Churchill's COMP4300 game engine lectures
