# McRogueFace Emscripten & Renderer Abstraction Research

**Date**: 2026-01-30
**Branch**: `emscripten-mcrogueface`
**Related Issues**: #157 (True Headless), #158 (Emscripten/WASM)

## Executive Summary

This document analyzes the technical requirements for:
1. **SFML 2.6 → 3.0 migration** (modernization)
2. **Emscripten/WebAssembly compilation** (browser deployment)

Both goals share a common prerequisite: **renderer abstraction**. The codebase already has a partial abstraction via `sf::RenderTarget*` pointer, but SFML types are pervasive (1276 occurrences across 78 files).

**Key Insight**: This is a **build-time configuration**, not runtime switching. The standard McRogueFace binary remains a dynamic environment; Emscripten builds bundle assets and scripts at compile time.

---

## Current Architecture Analysis

### Existing Abstraction Strengths

1. **RenderTarget Pointer Pattern** (`GameEngine.h:156`)
   ```cpp
   sf::RenderTarget* render_target;
   // Points to either window.get() or headless_renderer->getRenderTarget()
   ```
   This already decouples rendering logic from the specific backend.

2. **HeadlessRenderer** (`src/HeadlessRenderer.h`)
   - Uses `sf::RenderTexture` internally
   - Provides unified interface: `getRenderTarget()`, `display()`, `saveScreenshot()`
   - Demonstrates the pattern for additional backends

3. **UIDrawable Hierarchy**
   - Virtual `render(sf::Vector2f, sf::RenderTarget&)` method
   - 7 drawable types: Frame, Caption, Sprite, Entity, Grid, Line, Circle, Arc
   - Each manages its own SFML primitives internally

4. **Asset Wrappers**
   - `PyTexture`, `PyFont`, `PyShader` wrap SFML types
   - Python reference counting integrated
   - Single point of change for asset loading APIs

### Current SFML Coupling Points

| Area | Count | Difficulty | Notes |
|------|-------|------------|-------|
| `sf::Vector2f` | ~200+ | Medium | Used everywhere for positions, sizes |
| `sf::Color` | ~100+ | Easy | Simple 4-byte struct replacement |
| `sf::FloatRect` | ~50+ | Medium | Bounds, intersection testing |
| `sf::RenderTexture` | ~20 | Hard | Shader effects, caching |
| `sf::Sprite/Text` | ~30 | Hard | Core rendering primitives |
| `sf::Event` | ~15 | Medium | Input system coupling |
| `sf::Keyboard/Mouse` | ~50+ | Easy | Enum mappings |

Total: **1276 occurrences across 78 files**

---

## SFML 3.0 Migration Analysis

### Breaking Changes Requiring Code Updates

#### 1. Vector Parameters (High Impact)
```cpp
// SFML 2.6
setPosition(10, 20);
sf::VideoMode(1024, 768, 32);
sf::FloatRect(x, y, w, h);

// SFML 3.0
setPosition({10, 20});
sf::VideoMode({1024, 768}, 32);
sf::FloatRect({x, y}, {w, h});
```

**Strategy**: Regex-based search/replace with manual verification.

#### 2. Rect Member Changes (Medium Impact)
```cpp
// SFML 2.6
rect.left, rect.top, rect.width, rect.height
rect.getPosition(), rect.getSize()

// SFML 3.0
rect.position.x, rect.position.y, rect.size.x, rect.size.y
rect.position, rect.size  // direct access
rect.findIntersection() -> std::optional<Rect<T>>
```

#### 3. Resource Constructors (Low Impact)
```cpp
// SFML 2.6
sf::Sound sound;  // default constructible
sound.setBuffer(buffer);

// SFML 3.0
sf::Sound sound(buffer);  // requires buffer at construction
```

#### 4. Keyboard/Mouse Enum Scoping (Medium Impact)
```cpp
// SFML 2.6
sf::Keyboard::A
sf::Mouse::Left

// SFML 3.0
sf::Keyboard::Key::A
sf::Mouse::Button::Left
```

#### 5. Event Handling (Medium Impact)
```cpp
// SFML 2.6
sf::Event event;
while (window.pollEvent(event)) {
    if (event.type == sf::Event::Closed) ...
}

// SFML 3.0
while (auto event = window.pollEvent()) {
    if (event->is<sf::Event::Closed>()) ...
}
```

#### 6. CMake Target Changes
```cmake
# SFML 2.6
find_package(SFML 2 REQUIRED COMPONENTS graphics audio)
target_link_libraries(app sfml-graphics sfml-audio)

# SFML 3.0
find_package(SFML 3 REQUIRED COMPONENTS Graphics Audio)
target_link_libraries(app SFML::Graphics SFML::Audio)
```

### Migration Effort Estimate

| Phase | Files | Changes | Effort |
|-------|-------|---------|--------|
| CMakeLists.txt | 1 | Target names | 1 hour |
| Vector parameters | 30+ | ~200 calls | 4-8 hours |
| Rect refactoring | 20+ | ~50 usages | 2-4 hours |
| Event handling | 5 | ~15 sites | 2 hours |
| Keyboard/Mouse | 10 | ~50 enums | 2 hours |
| Resource constructors | 10 | ~30 sites | 2 hours |
| **Total** | - | - | **~15-25 hours** |

---

## Emscripten/VRSFML Analysis

### Why VRSFML Over Waiting for SFML 4.x?

1. **Available Now**: VRSFML is working today with browser demos
2. **Modern OpenGL**: Removes legacy calls, targets OpenGL ES 3.0+ (WebGL 2)
3. **SFML_GAME_LOOP Macro**: Handles blocking vs callback loop abstraction
4. **Performance**: 500k sprites @ 60FPS vs 3 FPS upstream (batching)
5. **SFML 4.x Timeline**: Unknown, potentially years away

### VRSFML API Differences from SFML

| Feature | SFML 2.6/3.0 | VRSFML |
|---------|--------------|--------|
| Default constructors | Allowed | Not allowed for resources |
| Texture ownership | Pointer in Sprite | Passed at draw time |
| Context management | Hidden global | Explicit `GraphicsContext` |
| Drawable base class | Polymorphic | Removed |
| Loading methods | `loadFromFile()` returns bool | Returns `std::optional` |
| Main loop | `while(running)` | `SFML_GAME_LOOP { }` |

### Main Loop Refactoring

Current blocking loop:
```cpp
void GameEngine::run() {
    while (running) {
        processEvents();
        update();
        render();
        display();
    }
}
```

Emscripten-compatible pattern:
```cpp
// Option A: VRSFML macro
SFML_GAME_LOOP {
    processEvents();
    update();
    render();
    display();
}

// Option B: Manual Emscripten integration
#ifdef __EMSCRIPTEN__
void mainLoopCallback() {
    if (!game.running) {
        emscripten_cancel_main_loop();
        return;
    }
    game.doFrame();
}
emscripten_set_main_loop(mainLoopCallback, 0, 1);
#else
while (running) { doFrame(); }
#endif
```

**Recommendation**: Use preprocessor-based approach with `doFrame()` extraction for cleaner separation.

---

## Build-Time Configuration Strategy

### Normal Build (Desktop)
- Dynamic loading of assets from `assets/` directory
- Python scripts loaded from `scripts/` directory at runtime
- Full McRogueFace environment with dynamic game loading

### Emscripten Build (Web)
- Assets bundled via `--preload-file assets`
- Scripts bundled via `--preload-file scripts`
- Virtual filesystem (MEMFS/IDBFS)
- Optional: Script linting with Pyodide before bundling
- Single-purpose deployment (one game per build)

### CMake Configuration
```cmake
option(MCRF_BUILD_EMSCRIPTEN "Build for Emscripten/WebAssembly" OFF)

if(MCRF_BUILD_EMSCRIPTEN)
    set(CMAKE_TOOLCHAIN_FILE ${CMAKE_SOURCE_DIR}/cmake/toolchains/emscripten.cmake)
    add_definitions(-DMCRF_EMSCRIPTEN)

    # Bundle assets
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} \
        --preload-file ${CMAKE_SOURCE_DIR}/assets@/assets \
        --preload-file ${CMAKE_SOURCE_DIR}/scripts@/scripts")
endif()
```

---

## Phased Implementation Plan

### Phase 0: Preparation (This PR)
- [ ] Create `docs/EMSCRIPTEN_RESEARCH.md` (this document)
- [ ] Update Gitea issues #157, #158 with findings
- [ ] Identify specific files requiring changes
- [ ] Create test matrix for rendering features

### Phase 1: Type Abstraction Layer
**Goal**: Isolate SFML types behind McRogueFace wrappers

```cpp
// src/types/McrfTypes.h
namespace mcrf {
    using Vector2f = sf::Vector2f;  // Alias initially, replace later
    using Color = sf::Color;
    using FloatRect = sf::FloatRect;
}
```

Changes:
- [ ] Create `src/types/` directory with wrapper types
- [ ] Gradually replace `sf::` with `mcrf::` namespace
- [ ] Update Common.h to provide both namespaces during transition

### Phase 2: Main Loop Extraction
**Goal**: Make game loop callback-compatible

- [ ] Extract `GameEngine::doFrame()` from `run()`
- [ ] Add `#ifdef __EMSCRIPTEN__` conditional in `run()`
- [ ] Test that desktop behavior is unchanged

### Phase 3: Render Backend Interface
**Goal**: Abstract RenderTarget operations

```cpp
class RenderBackend {
public:
    virtual ~RenderBackend() = default;
    virtual void clear(const Color& color) = 0;
    virtual void draw(const Sprite& sprite) = 0;
    virtual void draw(const Text& text) = 0;
    virtual void display() = 0;
    virtual bool isOpen() const = 0;
    virtual Vector2u getSize() const = 0;
};

class SFMLBackend : public RenderBackend { ... };
class VRSFMLBackend : public RenderBackend { ... };  // Future
```

### Phase 4: SFML 3.0 Migration
**Goal**: Update to SFML 3.0 API

- [ ] Update CMakeLists.txt targets
- [ ] Fix vector parameter calls
- [ ] Fix rect member access
- [ ] Fix event handling
- [ ] Fix keyboard/mouse enums
- [ ] Test thoroughly

### Phase 5: VRSFML Integration (Experimental)
**Goal**: Add VRSFML as alternative backend

- [ ] Add VRSFML as submodule/dependency
- [ ] Implement VRSFMLBackend
- [ ] Add Emscripten CMake configuration
- [ ] Test in browser

### Phase 6: Python-in-WASM
**Goal**: Get Python scripting working in browser

**High Risk** - This is the major unknown:
- [ ] Build CPython for Emscripten
- [ ] Test `McRFPy_API` binding compatibility
- [ ] Evaluate Pyodide vs raw CPython
- [ ] Handle filesystem virtualization
- [ ] Test threading limitations

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| SFML 3.0 breaks unexpected code | Medium | Medium | Comprehensive test suite |
| VRSFML API too different | Low | High | Can fork/patch VRSFML |
| Python-in-WASM fails | Medium | Critical | Evaluate Pyodide early |
| Performance regression | Low | Medium | Benchmark before/after |
| Binary size too large | Medium | Medium | Lazy loading, stdlib trimming |

---

## References

### SFML 3.0
- [Migration Guide](https://www.sfml-dev.org/tutorials/3.0/getting-started/migrate/)
- [Changelog](https://www.sfml-dev.org/development/changelog/)
- [Release Notes](https://github.com/SFML/SFML/releases/tag/3.0.0)

### VRSFML/Emscripten
- [VRSFML Blog Post](https://vittorioromeo.com/index/blog/vrsfml.html)
- [VRSFML GitHub](https://github.com/vittorioromeo/VRSFML)
- [Browser Demos](https://vittorioromeo.github.io/VRSFML_HTML5_Examples/)

### Python WASM
- [PEP 776 - Python Emscripten Support](https://peps.python.org/pep-0776/)
- [CPython WASM Build Guide](https://github.com/python/cpython/blob/main/Tools/wasm/README.md)
- [Pyodide](https://github.com/pyodide/pyodide)

### Related Issues
- [SFML Emscripten Discussion #1494](https://github.com/SFML/SFML/issues/1494)
- [libtcod Emscripten #41](https://github.com/libtcod/libtcod/issues/41)

---

## Appendix A: File-by-File SFML Usage Inventory

### Critical Files (Must Abstract for Emscripten)

| File | SFML Types Used | Role | Abstraction Difficulty |
|------|-----------------|------|------------------------|
| `GameEngine.h/cpp` | RenderWindow, Clock, Font, Event | Main loop, window | **CRITICAL** |
| `HeadlessRenderer.h/cpp` | RenderTexture | Headless backend | **CRITICAL** |
| `UIDrawable.h/cpp` | Vector2f, RenderTarget, FloatRect | Base render interface | **HARD** |
| `UIFrame.h/cpp` | RectangleShape, Vector2f, Color | Container rendering | **HARD** |
| `UISprite.h/cpp` | Sprite, Texture, Vector2f | Texture display | **HARD** |
| `UICaption.h/cpp` | Text, Font, Vector2f, Color | Text rendering | **HARD** |
| `UIGrid.h/cpp` | RenderTexture, Sprite, Vector2f | Tile grid system | **HARD** |
| `UIEntity.h/cpp` | Sprite, Vector2f | Game entities | **HARD** |
| `UICircle.h/cpp` | CircleShape, Vector2f, Color | Circle shape | **MEDIUM** |
| `UILine.h/cpp` | VertexArray, Vector2f, Color | Line rendering | **MEDIUM** |
| `UIArc.h/cpp` | CircleShape segments, Vector2f | Arc shape | **MEDIUM** |
| `Scene.h/cpp` | Vector2f, RenderTarget | Scene management | **MEDIUM** |
| `SceneTransition.h/cpp` | RenderTexture, Sprite | Transitions | **MEDIUM** |

### Wrapper Files (Already Partially Abstracted)

| File | SFML Types Wrapped | Python API | Notes |
|------|-------------------|------------|-------|
| `PyVector.h/cpp` | sf::Vector2f | Vector | Ready for backend swap |
| `PyColor.h/cpp` | sf::Color | Color | Ready for backend swap |
| `PyTexture.h/cpp` | sf::Texture | Texture | Asset loading needs work |
| `PyFont.h/cpp` | sf::Font | Font | Asset loading needs work |
| `PyShader.h/cpp` | sf::Shader | Shader | Optional feature |

### Input System Files

| File | SFML Types Used | Notes |
|------|-----------------|-------|
| `ActionCode.h` | Keyboard::Key, Mouse::Button | Enum encoding only |
| `PyKey.h/cpp` | Keyboard::Key enum | 140+ key mappings |
| `PyMouseButton.h/cpp` | Mouse::Button enum | Simple enum |
| `PyKeyboard.h/cpp` | Keyboard::isKeyPressed | State queries |
| `PyMouse.h/cpp` | Mouse::getPosition | Position queries |
| `PyInputState.h/cpp` | None (pure enum) | No SFML dependency |

### Support Files (Low Priority)

| File | SFML Types Used | Notes |
|------|-----------------|-------|
| `Animation.h/cpp` | Vector2f, Color (as values) | Pure data animation |
| `GridLayers.h/cpp` | RenderTexture, Color | Layer caching |
| `IndexTexture.h/cpp` | Texture, IntRect | Legacy texture format |
| `Resources.h/cpp` | Font | Global font storage |
| `ProfilerOverlay.cpp` | Text, RectangleShape | Debug overlay |
| `McRFPy_Automation.h/cpp` | Various | Testing only |

---

## Appendix B: Recommended First Steps

### Immediate (Non-Breaking Changes)

1. **Extract `GameEngine::doFrame()`**
   - Move loop body to separate method
   - No API changes, just internal refactoring
   - Enables future Emscripten callback integration

2. **Create type aliases in Common.h**
   ```cpp
   namespace mcrf {
       using Vector2f = sf::Vector2f;
       using Vector2i = sf::Vector2i;
       using Color = sf::Color;
       using FloatRect = sf::FloatRect;
   }
   ```
   - Allows gradual migration from `sf::` to `mcrf::`
   - No functional changes

3. **Document current render path**
   - Add comments to key rendering functions
   - Identify all `target.draw()` call sites
   - Create rendering flow diagram

### Short-Term (Preparation for SFML 3.0)

1. **Audit vector parameter calls**
   - Find all `setPosition(x, y)` style calls
   - Prepare regex patterns for migration

2. **Audit rect member access**
   - Find all `.left`, `.top`, `.width`, `.height` uses
   - Prepare for `.position.x`, `.size.x` style

3. **Test suite expansion**
   - Add rendering validation tests
   - Screenshot comparison tests
   - Animation correctness tests

---

## Appendix C: libtcod Architecture Analysis

**Key Finding**: libtcod uses a much simpler abstraction pattern than initially proposed.

### libtcod's Context Vtable Pattern

libtcod doesn't wrap every SDL type. Instead, it abstracts at the **context level** using a C-style vtable:

```c
struct TCOD_Context {
    int type;
    void* contextdata_;  // Backend-specific data (opaque pointer)

    // Function pointers - the "vtable"
    void (*c_destructor_)(struct TCOD_Context* self);
    TCOD_Error (*c_present_)(struct TCOD_Context* self,
                             const TCOD_Console* console,
                             const TCOD_ViewportOptions* viewport);
    void (*c_pixel_to_tile_)(struct TCOD_Context* self, double* x, double* y);
    TCOD_Error (*c_save_screenshot_)(struct TCOD_Context* self, const char* filename);
    struct SDL_Window* (*c_get_sdl_window_)(struct TCOD_Context* self);
    TCOD_Error (*c_set_tileset_)(struct TCOD_Context* self, TCOD_Tileset* tileset);
    TCOD_Error (*c_screen_capture_)(struct TCOD_Context* self, ...);
    // ... more operations
};
```

### How Backends Implement It

Each renderer fills in the function pointers:

```c
// In renderer_sdl2.c
context->c_destructor_ = sdl2_destructor;
context->c_present_ = sdl2_present;
context->c_get_sdl_window_ = sdl2_get_window;
// ...

// In renderer_xterm.c
context->c_destructor_ = xterm_destructor;
context->c_present_ = xterm_present;
// ...
```

### Conditional Compilation with NO_SDL

libtcod uses simple preprocessor guards:

```c
// In CMakeLists.txt
if(LIBTCOD_SDL3)
    target_link_libraries(${PROJECT_NAME} PUBLIC SDL3::SDL3)
else()
    target_compile_definitions(${PROJECT_NAME} PUBLIC NO_SDL)
endif()

// In source files
#ifndef NO_SDL
#include <SDL3/SDL.h>
// ... SDL-dependent code ...
#endif
```

**47 files** use this pattern. When building headless, SDL code is simply excluded.

### Why This Pattern Works

1. **Core functionality is SDL-independent**: Console manipulation, pathfinding, FOV, noise, BSP, etc. don't need SDL
2. **Only rendering needs abstraction**: The `TCOD_Context` is the single point of abstraction
3. **Minimal API surface**: Just ~10 function pointers instead of wrapping every primitive
4. **Backend-specific data is opaque**: `contextdata_` holds renderer-specific state

### Implications for McRogueFace

**libtcod's approach suggests we should NOT try to abstract every `sf::` type.**

Instead, consider:

1. **Keep SFML types internally** - `sf::Vector2f`, `sf::Color`, `sf::FloatRect` are fine
2. **Abstract at the RenderContext level** - One vtable for window/rendering operations
3. **Use `#ifndef NO_SFML` guards** - Compile-time backend selection
4. **Create alternative backend for Emscripten** - WebGL + canvas implementation

### Proposed McRogueFace Context Pattern

```cpp
struct McRF_RenderContext {
    void* backend_data;  // SFML or WebGL specific data

    // Function pointers
    void (*destroy)(McRF_RenderContext* self);
    void (*clear)(McRF_RenderContext* self, uint32_t color);
    void (*present)(McRF_RenderContext* self);
    void (*draw_sprite)(McRF_RenderContext* self, const Sprite* sprite);
    void (*draw_text)(McRF_RenderContext* self, const Text* text);
    void (*draw_rect)(McRF_RenderContext* self, const Rect* rect);
    bool (*poll_event)(McRF_RenderContext* self, Event* event);
    void (*screenshot)(McRF_RenderContext* self, const char* path);
    // ...
};

// SFML backend
McRF_RenderContext* mcrf_sfml_context_new(int width, int height, const char* title);

// Emscripten backend (future)
McRF_RenderContext* mcrf_webgl_context_new(const char* canvas_id);
```

### Comparison: Original Plan vs libtcod-Inspired Plan

| Aspect | Original Plan | libtcod-Inspired Plan |
|--------|---------------|----------------------|
| Type abstraction | Replace all `sf::*` with `mcrf::*` | Keep `sf::*` internally |
| Abstraction point | Every primitive type | Single Context object |
| Files affected | 78+ files | ~10 core files |
| Compile-time switching | Complex namespace aliasing | Simple `#ifndef NO_SFML` |
| Backend complexity | Full reimplementation | Focused vtable |

**Recommendation**: Adopt libtcod's simpler pattern. Focus abstraction on the rendering context, not on data types.

---

## Appendix D: Headless Build Experiment Results

**Experiment Date**: 2026-01-30
**Branch**: `emscripten-mcrogueface`

### Objective

Attempt to compile McRogueFace without SFML dependencies to identify true coupling points.

### What We Created

1. **`src/platform/HeadlessTypes.h`** - Complete SFML type stubs (~600 lines):
   - Vector2f, Vector2i, Vector2u
   - Color with standard color constants
   - FloatRect, IntRect
   - Time, Clock (with chrono-based implementation)
   - Transform, Vertex, View
   - Shape hierarchy (RectangleShape, CircleShape, etc.)
   - Texture, Sprite, Font, Text stubs
   - RenderTarget, RenderTexture, RenderWindow stubs
   - Audio stubs (Sound, Music, SoundBuffer)
   - Input stubs (Keyboard, Mouse, Event)
   - Shader stub

2. **Modified `src/Common.h`** - Conditional include:
   ```cpp
   #ifdef MCRF_HEADLESS
       #include "platform/HeadlessTypes.h"
   #else
       #include <SFML/Graphics.hpp>
       #include <SFML/Audio.hpp>
   #endif
   ```

### Build Attempt Result

**SUCCESS** - Headless build compiles after consolidating includes and adding stubs.

### Work Completed

#### 1. Consolidated SFML Includes

**15 files** had direct SFML includes that bypassed Common.h. All were modified to use `#include "Common.h"` instead:

| File | Original Include | Fixed |
|------|------------------|-------|
| `main.cpp` | `<SFML/Graphics.hpp>` | ✓ |
| `Animation.h` | `<SFML/Graphics.hpp>` | ✓ |
| `GridChunk.h` | `<SFML/Graphics.hpp>` | ✓ |
| `GridLayers.h` | `<SFML/Graphics.hpp>` | ✓ |
| `HeadlessRenderer.h` | `<SFML/Graphics.hpp>` | ✓ |
| `SceneTransition.h` | `<SFML/Graphics.hpp>` | ✓ |
| `McRFPy_Automation.h` | `<SFML/Graphics.hpp>`, `<SFML/Window.hpp>` | ✓ |
| `PyWindow.cpp` | `<SFML/Graphics.hpp>` | ✓ |
| `ActionCode.h` | `<SFML/Window/Keyboard.hpp>` | ✓ |
| `PyKey.h` | `<SFML/Window/Keyboard.hpp>` | ✓ |
| `PyMouseButton.h` | `<SFML/Window/Mouse.hpp>` | ✓ |
| `PyBSP.h` | `<SFML/System/Vector2.hpp>` | ✓ |
| `UIGridPathfinding.h` | `<SFML/System/Vector2.hpp>` | ✓ |

#### 2. Wrapped ImGui-SFML with Guards

ImGui-SFML is disabled entirely in headless builds since debug tools can't be accessed through the API:

| File | Changes |
|------|---------|
| `GameEngine.h` | Guarded includes and member variables |
| `GameEngine.cpp` | Guarded all ImGui::SFML calls |
| `ImGuiConsole.h/cpp` | Entire file wrapped with `#ifndef MCRF_HEADLESS` |
| `ImGuiSceneExplorer.h/cpp` | Entire file wrapped with `#ifndef MCRF_HEADLESS` |
| `McRFPy_API.cpp` | Guarded ImGuiConsole include and setEnabled call |

#### 3. Extended HeadlessTypes.h

The stub file grew from ~700 lines to ~900 lines with additional types and methods:

**Types Added:**
- `sf::Image` - For screenshot functionality
- `sf::Glsl::Vec3`, `sf::Glsl::Vec4` - For shader uniforms
- `sf::BlendMode` - For rendering states
- `sf::CurrentTextureType` - For shader texture binding

**Methods Added:**
- `Font::Info` struct and `Font::getInfo()`
- `Texture::update()` overloads
- `Texture::copyToImage()`
- `Transform::getInverse()`
- `RenderStates` constructors from Transform, BlendMode, Shader*
- `Music::getDuration()`, `getPlayingOffset()`, `setPlayingOffset()`
- `SoundBuffer::getDuration()`
- `RenderWindow::setMouseCursorGrabbed()`
- `sf::err()` stream function
- Keyboard aliases: `BackSpace`, `BackSlash`, `SemiColon`, `Dash`

### Build Commands

```bash
# Normal SFML build (default)
make

# Headless build (no SFML/ImGui dependencies)
mkdir build-headless && cd build-headless
cmake .. -DMCRF_HEADLESS=ON -DCMAKE_BUILD_TYPE=Release
make
```

### Key Insight

The libtcod approach of `#ifndef NO_SDL` guards works when **all platform includes go through a single point**. The consolidation of 15+ bypass points into Common.h was the prerequisite that made this work.

### Actual Effort

| Task | Files | Time |
|------|-------|------|
| Replace direct SFML includes with Common.h | 15 | ~30 min |
| Wrap ImGui-SFML in guards | 5 | ~20 min |
| Extend HeadlessTypes.h with missing stubs | 1 | ~1 hour |
| Fix compilation errors iteratively | - | ~1 hour |

**Total**: ~3 hours for clean headless compilation

### Completed Milestones

1. ✅ **Test Python bindings** - mcrfpy module loads and works in headless mode
   - Vector, Color, Scene, Frame, Grid all functional
   - libtcod integrations (BSP, pathfinding) available
2. ✅ **Add CMake option** - `option(MCRF_HEADLESS "Build without graphics" OFF)`
   - Proper conditional compilation and linking
   - No SFML symbols in headless binary
3. ✅ **Link-time validation** - `ldd` confirms zero SFML/OpenGL dependencies
4. ✅ **Binary size reduction** - Headless is 1.6 MB vs 2.5 MB normal build (36% smaller)

### Python Test Results (Headless Mode)

```python
# All these work in headless build:
import mcrfpy
v = mcrfpy.Vector(10, 20)        # ✅
c = mcrfpy.Color(255, 128, 64)   # ✅
scene = mcrfpy.Scene('test')     # ✅
frame = mcrfpy.Frame(pos=(0,0))  # ✅
grid = mcrfpy.Grid(grid_size=(10,10))  # ✅
```

### Remaining Steps for Emscripten

1. ✅ **Main loop extraction** - `GameEngine::doFrame()` extracted with Emscripten callback support
   - `run()` now uses `#ifdef __EMSCRIPTEN__` to choose between callback and blocking loop
   - `emscripten_set_main_loop_arg()` integration ready
2. ✅ **Emscripten toolchain** - `emcmake cmake` works with headless mode
3. ✅ **Python-in-WASM** - Built CPython 3.14.2 for wasm32-emscripten target
   - Uses official `Tools/wasm/emscripten build` script from CPython repo
   - Produced libpython3.14.a (47MB static library)
   - Also builds: libmpdec, libffi, libexpat for WASM
4. ✅ **libtcod-in-WASM** - Built libtcod-headless for Emscripten
   - Uses `LIBTCOD_SDL3=OFF` to avoid SDL dependency
   - Includes lodepng and utf8proc dependencies
5. ✅ **First successful WASM build** - mcrogueface.wasm (8.9MB) + mcrogueface.js (126KB)
   - All 68 C++ source files compile with emcc
   - Links: Python, libtcod, HACL crypto, expat, mpdec, ffi, zlib, bzip2, sqlite3
6. 🔲 **Python stdlib bundling** - Need to package Python stdlib for WASM filesystem
7. 🔲 **VRSFML integration** - Replace stubs with actual WebGL rendering

### First Emscripten Build Attempt (2026-01-31)

**Command:**
```bash
source ~/emsdk/emsdk_env.sh
emcmake cmake .. -DMCRF_HEADLESS=ON -DCMAKE_BUILD_TYPE=Release
emmake make -j8
```

**Result:** Build failed on Python headers.

**Key Errors:**
```
deps/Python/pyport.h:429:2: error: "LONG_BIT definition appears wrong for platform"
```
```
warning: shift count >= width of type [-Wshift-count-overflow]
_Py_STATIC_FLAG_BITS << 48  // 48-bit shift on 32-bit WASM!
```

**Root Cause:**
1. Desktop Python 3.14 headers assume 64-bit Linux with glibc
2. Emscripten targets 32-bit WASM with musl-based libc
3. Python's immortal reference counting uses `<< 48` shifts that overflow on 32-bit
4. `LONG_BIT` check fails because WASM's `long` is 32 bits

**Analysis:**
The HeadlessTypes.h stubs and game engine code compile fine. The blocker is exclusively the Python C API integration.

### Python-in-WASM Options

| Option | Complexity | Description |
|--------|------------|-------------|
| **Pyodide** | Medium | Pre-built Python WASM with package ecosystem |
| **CPython WASM** | High | Build CPython ourselves with Emscripten |
| **No-Python mode** | Low | New CMake option to exclude Python entirely |

**Pyodide Approach (Recommended):**
- Pyodide provides Python 3.12 compiled for WASM
- Would need to replace `deps/Python` with Pyodide headers
- `McRFPy_API` binding layer needs adaptation
- Pyodide handles asyncio, file system virtualization
- Active project with good documentation

### CPython WASM Build (Successful!)

**Date**: 2026-01-31

Used the official CPython WASM build process:

```bash
# From deps/cpython directory
./Tools/wasm/emscripten build

# This produces:
# - cross-build/wasm32-emscripten/build/python/libpython3.14.a
# - cross-build/wasm32-emscripten/prefix/lib/libmpdec.a
# - cross-build/wasm32-emscripten/prefix/lib/libffi.a
# - cross-build/wasm32-emscripten/build/python/Modules/expat/libexpat.a
```

**CMake Integration:**
```cmake
if(EMSCRIPTEN)
    set(PYTHON_WASM_BUILD "${CMAKE_SOURCE_DIR}/deps/cpython/cross-build/wasm32-emscripten/build/python")
    set(PYTHON_WASM_PREFIX "${CMAKE_SOURCE_DIR}/deps/cpython/cross-build/wasm32-emscripten/prefix")

    # Force WASM-compatible pyconfig.h
    add_compile_options(-include ${PYTHON_WASM_BUILD}/pyconfig.h)

    # Link all Python dependencies
    set(LINK_LIBS
        ${PYTHON_WASM_BUILD}/libpython3.14.a
        ${PYTHON_WASM_BUILD}/Modules/_hacl/*.o  # HACL crypto not in libpython
        ${PYTHON_WASM_BUILD}/Modules/expat/libexpat.a
        ${PYTHON_WASM_PREFIX}/lib/libmpdec.a
        ${PYTHON_WASM_PREFIX}/lib/libffi.a
    )

    # Emscripten ports for common libraries
    target_link_options(mcrogueface PRIVATE
        -sUSE_ZLIB=1
        -sUSE_BZIP2=1
        -sUSE_SQLITE3=1
    )
endif()
```

**No-Python Mode (For Testing):**
- Add `MCRF_NO_PYTHON` CMake option
- Allows testing WASM build without Python complexity
- Game engine would be pure C++ (no scripting)
- Useful for validating rendering, input, timing first

### Main Loop Architecture

The game loop now supports both desktop (blocking) and browser (callback) modes:

```cpp
// GameEngine::run() - build-time conditional
#ifdef __EMSCRIPTEN__
    emscripten_set_main_loop_arg(emscriptenMainLoopCallback, this, 0, 1);
#else
    while (running) { doFrame(); }
#endif

// GameEngine::doFrame() - same code runs in both modes
void GameEngine::doFrame() {
    metrics.resetPerFrame();
    currentScene()->update();
    testTimers();
    // ... animations, input, rendering ...
    currentFrame++;
    frameTime = clock.restart().asSeconds();
}
```
