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

For CPython's optional modules, also install `libzstd-dev uuid-dev` (for
`compression.zstd` / `_uuid`). `_decimal` uses CPython's bundled libmpdec, so
`libmpdec-dev` is not needed.

#### Without root access

The `-dev` packages are only headers plus `.so` symlinks; the runtime libraries
are usually already installed. They can be unpacked into a local prefix instead:

```bash
mkdir -p build-sysroot/debs && cd build-sysroot/debs
apt-get download libx11-dev libxrandr-dev libxcursor-dev libxrender-dev libxext-dev \
    libxfixes-dev libxi-dev x11proto-dev libxcb1-dev libxau-dev libxdmcp-dev libudev-dev \
    libgl-dev libglx-dev libopengl-dev libegl-dev libfreetype-dev libpng-dev libbrotli-dev \
    libopenal-dev libflac-dev libogg-dev libvorbis-dev libzstd-dev uuid-dev
for f in *.deb; do dpkg -x "$f" ..; done
# Re-point the dev symlinks at the installed runtime libraries
cd ../usr/lib/x86_64-linux-gnu
for l in *.so; do t=$(readlink "$l"); [ -e "$t" ] || ln -sf "/usr/lib/x86_64-linux-gnu/$t" "$l"; done
rm -f *.a
```

Then pass `MCRF_SYSROOT=$PWD/build-sysroot` to `tools/build_python.sh`, and
`-DCMAKE_PREFIX_PATH=$S -DCMAKE_INCLUDE_PATH=$S/include -DCMAKE_LIBRARY_PATH=$S/lib/x86_64-linux-gnu -DCMAKE_CXX_FLAGS="-isystem $S/include" -DCMAKE_C_FLAGS="-isystem $S/include"`
(with `S=$PWD/build-sysroot/usr`) to the SFML and McRogueFace CMake configures.

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

**Note:** imgui and imgui-sfml *are* used by the default (SFML) build for the
debug console. If a pinned submodule commit cannot be fetched, check out the
nearest published equivalent (imgui-sfml `v2.6.1` pairs with imgui 1.89.x).

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

libtcod-headless is our SDL-free fork. The submodule pins the `mcrf-pinned`
branch (libtcod 2.2.2 plus McRogueFace's pathfinding/heightmap extensions and
FOV memory-safety fixes):

```bash
cd modules/libtcod-headless
git submodule update --init --depth 1 src/vendor/utf8proc

mkdir build && cd build
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON \
    -DLIBTCOD_SDL3=OFF \
    -DLIBTCOD_UTF8PROC=vendored \
    -DLIBTCOD_LODEPNG=vendored \
    -DLIBTCOD_STB=vendored \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON

make -j$(nproc)
cd ../../..
```

- `LIBTCOD_SDL3=OFF` keeps CMake from fetching SDL3.
- The `vendored` settings compile utf8proc/lodepng/stb into `libtcod.so`. With
  the defaults, utf8proc becomes a separate `libutf8proc.so.3` reachable only
  through a RUNPATH into this build tree, so packaged builds break on other
  machines. Check with `readelf -d build/libtcod.so.2.2.2 | grep -E 'NEEDED|RUNPATH'`
  (expect only libz/libstdc++/libm/libgcc_s/libc, and no RUNPATH).

### 4. Build Python 3.15

```bash
tools/build_python.sh                  # -> __lib/    (libpython3.15, stdlib, pyconfig.h)
tools/build_python.sh --free-threaded  # -> __lib_ft/ (optional, libpython3.15t)
```

This configures out-of-tree in `build-cpython315[t]/` with `--enable-shared
--without-system-libmpdec`, then strips and stages the shared library, the
extension modules (`__lib/Python/lib.linux-x86_64-3.15/`), the stdlib
(`__lib/Python/Lib/`) and the build's `pyconfig.h` (`__lib/include/`).

**3.15 note:** `configure` no longer falls back to the bundled libmpdec on its
own. Without libmpdec-dev *or* `--without-system-libmpdec`, `_decimal` is
silently skipped and `decimal` drops to the slow pure-Python implementation.

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

# Python: already staged by tools/build_python.sh

# SFML
cp modules/SFML/build/lib/libsfml-*.so* __lib/

# libtcod-headless
cp -a modules/libtcod-headless/build/libtcod.so* __lib/
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
| cpython | 3.15.0 | Embedded Python interpreter (`MCRF_PYTHON_VERSION` in CMakeLists.txt) |
| libtcod-headless | 2.2.2 (`mcrf-pinned`) | SDL-free fork for FOV, pathfinding |

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
│   ├── libpython3.15.so*
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

# Test headless mode. The SFML build still opens an X display even with
# --headless, so on a server without one use Xvfb:
xvfb-run -a ./mcrogueface --headless -c "import mcrfpy; print('Success')"

# Full test suite
cd ../tests && xvfb-run -a python3 run_tests.py

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
# Should show libtcod.so -> libtcod.so.2 -> libtcod.so.2.2.2
```

---

## Build Times (approximate)

On a typical 4-core system:

| Component | Time |
|-----------|------|
| libtcod-headless | ~30 seconds |
| Python 3.15 | ~3-5 minutes |
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
