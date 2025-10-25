# McRogueFace - Development Roadmap

## Project Status

**Current State**: Active development - C++ game engine with Python scripting
**Latest Release**: Alpha 0.1
**Issue Tracking**: See [Gitea Issues](https://gamedev.ffwf.net/gitea/john/McRogueFace/issues) for current tasks and bugs

---

## 🎯 Strategic Vision

### Engine Philosophy

- **C++ First**: Performance-critical code stays in C++
- **Python Close Behind**: Rich scripting without frame-rate impact
- **Game-Ready**: Each improvement should benefit actual game development

### Architecture Goals

1. **Clean Inheritance**: Drawable → UI components, proper type preservation
2. **Collection Consistency**: Uniform iteration, indexing, and search patterns
3. **Resource Management**: RAII everywhere, proper lifecycle handling
4. **Multi-Platform**: Windows/Linux feature parity maintained

---

## 🏗️ Architecture Decisions

### Three-Layer Grid Architecture
Following successful roguelike patterns (Caves of Qud, Cogmind, DCSS):

1. **Visual Layer** (UIGridPoint) - Sprites, colors, animations
2. **World State Layer** (TCODMap) - Walkability, transparency, physics
3. **Entity Perspective Layer** (UIGridPointState) - Per-entity FOV, knowledge

### Performance Architecture
Critical for large maps (1000x1000):

- **Spatial Hashing** for entity queries (not quadtrees!)
- **Batch Operations** with context managers (10-100x speedup)
- **Memory Pooling** for entities and components
- **Dirty Flag System** to avoid unnecessary updates
- **Zero-Copy NumPy Integration** via buffer protocol

### Key Insight from Research
"Minimizing Python/C++ boundary crossings matters more than individual function complexity"
- Batch everything possible
- Use context managers for logical operations
- Expose arrays, not individual cells
- Profile and optimize hot paths only

---

## 🚀 Development Phases

For detailed task tracking and current priorities, see the [Gitea issue tracker](https://gamedev.ffwf.net/gitea/john/McRogueFace/issues).

### Phase 1: Foundation Stabilization ✅
**Status**: Complete
**Key Issues**: #7 (Safe Constructors), #71 (Base Class), #87 (Visibility), #88 (Opacity)

### Phase 2: Constructor & API Polish ✅
**Status**: Complete
**Key Features**: Pythonic API, tuple support, standardized defaults

### Phase 3: Entity Lifecycle Management ✅
**Status**: Complete
**Key Issues**: #30 (Entity.die()), #93 (Vector methods), #94 (Color helpers), #103 (Timer objects)

### Phase 4: Visibility & Performance ✅
**Status**: Complete
**Key Features**: AABB culling, name system, profiling tools

### Phase 5: Window/Scene Architecture ✅
**Status**: Complete
**Key Issues**: #34 (Window object), #61 (Scene object), #1 (Resize events), #105 (Scene transitions)

### Phase 6: Rendering Revolution ✅
**Status**: Complete
**Key Issues**: #50 (Grid backgrounds), #6 (RenderTexture), #8 (Viewport rendering)

### Phase 7: Documentation & Distribution
**Status**: In Progress
**Key Issues**: #85 (Docstrings), #86 (Parameter docs), #108 (Type stubs), #97 (API docs)

See [current open issues](https://gamedev.ffwf.net/gitea/john/McRogueFace/issues?state=open) for active work.

---

## 🔮 Future Vision: Pure Python Extension Architecture

### Concept: McRogueFace as a Traditional Python Package
**Status**: Long-term vision
**Complexity**: Major architectural overhaul

Instead of being a C++ application that embeds Python, McRogueFace could be redesigned as a pure Python extension module that can be installed via `pip install mcrogueface`.

### Technical Approach

1. **Separate Core Engine from Python Embedding**
   - Extract SFML rendering, audio, and input into C++ extension modules
   - Remove embedded CPython interpreter
   - Use Python's C API to expose functionality

2. **Module Structure**
   ```
   mcrfpy/
   ├── __init__.py          # Pure Python coordinator
   ├── _core.so             # C++ rendering/game loop extension
   ├── _sfml.so             # SFML bindings
   ├── _audio.so            # Audio system bindings
   └── engine.py            # Python game engine logic
   ```

3. **Inverted Control Flow**
   - Python drives the main loop instead of C++
   - C++ extensions handle performance-critical operations
   - Python manages game logic, scenes, and entity systems

### Benefits

- **Standard Python Packaging**: `pip install mcrogueface`
- **Virtual Environment Support**: Works with venv, conda, poetry
- **Better IDE Integration**: Standard Python development workflow
- **Easier Testing**: Use pytest, standard Python testing tools
- **Cross-Python Compatibility**: Support multiple Python versions
- **Modular Architecture**: Users can import only what they need

### Challenges

- **Major Refactoring**: Complete restructure of codebase
- **Performance Considerations**: Python-driven main loop overhead
- **Build Complexity**: Multiple extension modules to compile
- **Platform Support**: Need wheels for many platform/Python combinations
- **API Stability**: Would need careful design to maintain compatibility

### Example Usage (Future Vision)

```python
import mcrfpy
from mcrfpy import Scene, Frame, Sprite, Grid

# Create game directly in Python
game = mcrfpy.Game(width=1024, height=768)

# Define scenes using Python classes
class MainMenu(Scene):
    def on_enter(self):
        self.ui.append(Frame(100, 100, 200, 50))
        self.ui.append(Sprite("logo.png", x=400, y=100))

    def on_keypress(self, key, pressed):
        if key == "ENTER" and pressed:
            self.game.set_scene("game")

# Run the game
game.add_scene("menu", MainMenu())
game.run()
```

This architecture would make McRogueFace a first-class Python citizen, following standard Python packaging conventions while maintaining high performance through C++ extensions.

---

## 📋 Major Feature Areas

For current status and detailed tasks, see the corresponding Gitea issue labels:

### Core Systems
- **UI/Rendering System**: Issues tagged `[Major Feature]` related to rendering
- **Grid/Entity System**: Pathfinding, FOV, entity management
- **Animation System**: Property animation, easing functions, callbacks
- **Scene/Window Management**: Scene lifecycle, transitions, viewport

### Performance Optimization
- **#115**: SpatialHash for 10,000+ entities
- **#116**: Dirty flag system
- **#113**: Batch operations for NumPy-style access
- **#117**: Memory pool for entities

### Advanced Features
- **#118**: Scene as Drawable (scenes can be drawn/animated)
- **#122**: Parent-Child UI System
- **#123**: Grid Subgrid System (256x256 chunks)
- **#124**: Grid Point Animation
- **#106**: Shader support
- **#107**: Particle system

### Documentation
- **#92**: Inline C++ documentation system
- **#91**: Python type stub files (.pyi)
- **#97**: Automated API documentation extraction
- **#126**: Generate perfectly consistent Python interface

---

## 📚 Resources

- **Issue Tracker**: [Gitea Issues](https://gamedev.ffwf.net/gitea/john/McRogueFace/issues)
- **Source Code**: [Gitea Repository](https://gamedev.ffwf.net/gitea/john/McRogueFace)
- **Documentation**: See `CLAUDE.md` for build instructions and development guide
- **Tutorial**: See `roguelike_tutorial/` for implementation examples

---

*For current priorities, task tracking, and bug reports, please use the [Gitea issue tracker](https://gamedev.ffwf.net/gitea/john/McRogueFace/issues).*
