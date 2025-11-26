# Building McRogueFace from Source

This document describes how to build McRogueFace from a fresh clone.

## Build Options

There are two ways to build McRogueFace:

1. **Quick Build** (recommended): Use pre-built dependency libraries from a `build_deps` archive
2. **Full Build**: Compile all dependencies from submodules

## Prerequisites

### System Dependencies

Install these packages before building:

```bash
# Debian/Ubuntu
sudo apt install \
    build-essential \
    cmake \
    git \
    zlib1g-dev \
    libx11-dev \
    libxrandr-dev \
    libxcursor-dev \
    libfreetype-dev \
    libudev-dev \
    libvorbis-dev \
    libflac-dev \
    libgl-dev \
    libopenal-dev
```

**Note:** SDL is NOT required - McRogueFace uses libtcod-headless which has no SDL dependency.

---

## Option 1: Quick Build (Using Pre-built Dependencies)

If you have a `build_deps.tar.gz` or `build_deps.zip` archive:

```bash
# Clone McRogueFace (no submodules needed)
git clone <repository-url> McRogueFace
cd McRogueFace

# Extract pre-built dependencies
tar -xzf /path/to/build_deps.tar.gz
# Or for zip: unzip /path/to/build_deps.zip

# Build McRogueFace
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

# Run
./mcrogueface
```

The `build_deps` archive contains:
- `__lib/` - Pre-built shared libraries (Python, SFML, libtcod-headless)
- `deps/` - Header symlinks for compilation

**Total build time: ~30 seconds**

---

## Option 2: Full Build (Compiling All Dependencies)

### 1. Clone with Submodules

```bash
git clone --recursive <repository-url> McRogueFace
cd McRogueFace
```

If submodules weren't cloned:
```bash
git submodule update --init --recursive
```

**Note:** imgui/imgui-sfml submodules may fail - this is fine, they're not used.

### 2. Create Dependency Symlinks

```bash
cd deps
ln -sf ../modules/cpython cpython
ln -sf ../modules/libtcod-headless/src/libtcod libtcod
ln -sf ../modules/cpython/Include Python
ln -sf ../modules/SFML/include/SFML SFML
cd ..
```

### 3. Build libtcod-headless

libtcod-headless is our SDL-free fork with vendored dependencies:

```bash
cd modules/libtcod-headless
mkdir build && cd build

cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON

make -j$(nproc)
cd ../../..
```

That's it! No special flags needed - libtcod-headless defaults to:
- `LIBTCOD_SDL3=disable` (no SDL dependency)
- Vendored lodepng, utf8proc, stb

### 4. Build Python 3.12

```bash
cd modules/cpython
./configure --enable-shared
make -j$(nproc)
cd ../..
```

### 5. Build SFML 2.6

```bash
cd modules/SFML
mkdir build && cd build

cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON

make -j$(nproc)
cd ../../..
```

### 6. Copy Libraries

```bash
mkdir -p __lib

# Python
cp modules/cpython/libpython3.12.so* __lib/

# SFML
cp modules/SFML/build/lib/libsfml-*.so* __lib/

# libtcod-headless
cp modules/libtcod-headless/build/bin/libtcod.so* __lib/

# Python standard library
cp -r modules/cpython/Lib __lib/Python
```

### 7. Build McRogueFace

```bash
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

### 8. Run

```bash
./mcrogueface
```

---

## Submodule Versions

| Submodule | Version | Notes |
|-----------|---------|-------|
| SFML | 2.6.1 | Graphics, audio, windowing |
| cpython | 3.12.2 | Embedded Python interpreter |
| libtcod-headless | 2.2.1 | SDL-free fork for FOV, pathfinding |

---

## Creating a build_deps Archive

To create a `build_deps` archive for distribution:

```bash
cd McRogueFace

# Create archive directory
mkdir -p build_deps_staging

# Copy libraries
cp -r __lib build_deps_staging/

# Copy/create deps symlinks as actual directories with only needed headers
mkdir -p build_deps_staging/deps
cp -rL deps/libtcod build_deps_staging/deps/  # Follow symlink
cp -rL deps/Python build_deps_staging/deps/
cp -rL deps/SFML build_deps_staging/deps/
cp -r deps/platform build_deps_staging/deps/

# Create archives
cd build_deps_staging
tar -czf ../build_deps.tar.gz __lib deps
zip -r ../build_deps.zip __lib deps
cd ..

# Cleanup
rm -rf build_deps_staging
```

The resulting archive can be distributed alongside releases for users who want to build McRogueFace without compiling dependencies.

**Archive contents:**
```
build_deps.tar.gz
├── __lib/
│   ├── libpython3.12.so*
│   ├── libsfml-*.so*
│   ├── libtcod.so*
│   └── Python/           # Python standard library
└── deps/
    ├── libtcod/          # libtcod headers
    ├── Python/           # Python headers
    ├── SFML/             # SFML headers
    └── platform/         # Platform-specific configs
```

---

## Verify the Build

```bash
cd build

# Check version
./mcrogueface --version

# Test headless mode
./mcrogueface --headless -c "import mcrfpy; print('Success')"

# Verify no SDL dependencies
ldd mcrogueface | grep -i sdl  # Should output nothing
```

---

## Troubleshooting

### OpenAL not found
```bash
sudo apt install libopenal-dev
```

### FreeType not found
```bash
sudo apt install libfreetype-dev
```

### X11/Xrandr not found
```bash
sudo apt install libx11-dev libxrandr-dev
```

### Python standard library missing
Ensure `__lib/Python` contains the standard library:
```bash
ls __lib/Python/os.py  # Should exist
```

### libtcod symbols not found
Ensure libtcod.so is in `__lib/` with correct version:
```bash
ls -la __lib/libtcod.so*
# Should show libtcod.so -> libtcod.so.2 -> libtcod.so.2.2.1
```

---

## Build Times (approximate)

On a typical 4-core system:

| Component | Time |
|-----------|------|
| libtcod-headless | ~30 seconds |
| Python 3.12 | ~3-5 minutes |
| SFML 2.6 | ~1 minute |
| McRogueFace | ~30 seconds |
| **Full build total** | **~5-7 minutes** |
| **Quick build (pre-built deps)** | **~30 seconds** |

---

## Runtime Dependencies

The built executable requires these system libraries:
- `libz.so.1` (zlib)
- `libopenal.so.1` (OpenAL)
- `libX11.so.6`, `libXrandr.so.2` (X11)
- `libfreetype.so.6` (FreeType)
- `libGL.so.1` (OpenGL)

All other dependencies (Python, SFML, libtcod) are bundled in `lib/`.
