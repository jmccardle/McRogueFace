#!/usr/bin/env bash
#
# Build the Windows (MinGW-w64 cross) dependencies from the submodules and stage them
# in __lib_windows/, where CMake expects them for `make windows`.
#
# Usage:
#   tools/build_deps_windows.sh          # CPython + SFML + libtcod -> __lib_windows/
#   tools/build_deps_windows.sh --clean  # rebuild everything from scratch
#
# Output layout (CMakeLists.txt, MCRF_CROSS_WINDOWS):
#   __lib_windows/python3XX.dll, *.pyd, ...   python.org's embeddable CPython, checksum
#                                             pinned, from tools/fetch_windows_python.sh
#   __lib_windows/sfml/{include,lib,bin}      SFML 2.6 shared, built from modules/SFML
#                                             (its static codec libs and openal32.dll are
#                                             the upstream extlibs/ the submodule carries)
#   __lib_windows/libtcod/{include,lib,bin}   libtcod.dll, self-contained: utf8proc, zlib,
#                                             lodepng and stb are compiled in, no SDL
#
# Each component is skipped when already staged (use --clean to force). Requires the
# MinGW-w64 posix toolchain (g++-mingw-w64-x86-64-posix), cmake, git, curl, unzip.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="$ROOT/__lib_windows"
TOOLCHAIN="$ROOT/cmake/toolchains/mingw-w64-x86_64.cmake"
JOBS="$(nproc 2>/dev/null || echo 4)"

CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --clean) CLEAN=1 ;;
        --help|-h) sed -n '2,19p' "$0"; exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

log() { echo "=== $* ==="; }

for tool in cmake git curl unzip sha256sum x86_64-w64-mingw32-g++-posix x86_64-w64-mingw32-gcc-posix \
            x86_64-w64-mingw32-objdump x86_64-w64-mingw32-dlltool x86_64-w64-mingw32-windres; do
    command -v "$tool" >/dev/null || { echo "ERROR: $tool not found" >&2; exit 1; }
done

cd "$ROOT"

# --- Submodules and deps/ links ---------------------------------------------
# CMake reads the Windows pyconfig.h through deps/cpython; build_deps.sh makes the same link.
log "Submodules"
git submodule update --init --depth 1 modules/SFML modules/libtcod-headless modules/cpython
git submodule update --init --depth 1 --recursive modules/libtcod-headless
mkdir -p deps
ln -sfn ../modules/cpython deps/cpython

# --- CPython ----------------------------------------------------------------
PYVER="$(sed -n 's/^#define PY_VERSION[[:space:]]*"\([0-9]*\)\.\([0-9]*\).*/\1\2/p' modules/cpython/Include/patchlevel.h)"
[ -n "$PYVER" ] || { echo "ERROR: cannot read PY_VERSION from modules/cpython" >&2; exit 1; }
if [ "$CLEAN" -eq 1 ] || [ ! -e "$DEST/libpython$PYVER.a" ] || [ ! -e "$DEST/python$PYVER.dll" ]; then
    log "CPython for Windows"
    "$SCRIPT_DIR/fetch_windows_python.sh"
else
    log "CPython already staged (skip)"
fi

# --- SFML -------------------------------------------------------------------
if [ "$CLEAN" -eq 1 ] || [ ! -e "$DEST/sfml/bin/sfml-graphics-2.dll" ]; then
    log "SFML"
    B="$ROOT/modules/SFML/build-windows"
    rm -rf "$B" "$DEST/sfml"
    mkdir -p "$B"
    # The engine's toolchain restricts find_* to the MinGW sysroot, so SFML's bundled
    # OpenAL/FLAC/Vorbis/FreeType (extlibs/) would not be found: add them as a root.
    # FindOpenAL looks for "OpenAL32", the bundled file is libopenal32.a, and the case
    # matters on Linux: that one is named explicitly below.
    cat > "$B/toolchain.cmake" <<TOOLCHAIN_EOF
include("$TOOLCHAIN")
list(APPEND CMAKE_FIND_ROOT_PATH "$ROOT/modules/SFML/extlibs")
list(APPEND CMAKE_LIBRARY_PATH "$ROOT/modules/SFML/extlibs/libs-mingw/x64")
TOOLCHAIN_EOF
    cmake -S modules/SFML -B "$B" -DCMAKE_TOOLCHAIN_FILE="$B/toolchain.cmake" \
        -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON -DSFML_BUILD_NETWORK=OFF \
        -DOPENAL_LIBRARY="$ROOT/modules/SFML/extlibs/libs-mingw/x64/libopenal32.a" \
        -DSFML_BUILD_EXAMPLES=OFF -DSFML_BUILD_DOC=OFF \
        -DCMAKE_INSTALL_PREFIX="$DEST/sfml" > /dev/null
    cmake --build "$B" -j"$JOBS" > "$B/build.log" 2>&1 || { tail -40 "$B/build.log"; exit 1; }
    cmake --install "$B" > /dev/null
    for f in sfml-system-2 sfml-window-2 sfml-graphics-2 sfml-audio-2 openal32; do
        [ -e "$DEST/sfml/bin/$f.dll" ] || { echo "ERROR: $DEST/sfml/bin/$f.dll missing" >&2; exit 1; }
    done
    [ -e "$DEST/sfml/lib/libfreetype.a" ] || { echo "ERROR: SFML did not stage libfreetype.a" >&2; exit 1; }
else
    log "SFML already staged (skip)"
fi

# --- libtcod-headless -------------------------------------------------------
if [ "$CLEAN" -eq 1 ] || [ ! -e "$DEST/libtcod/bin/libtcod.dll" ]; then
    log "libtcod-headless"
    B="$ROOT/modules/libtcod-headless/build-windows"
    rm -rf "$B" "$DEST/libtcod"
    # utf8proc, lodepng and stb are compiled into libtcod.dll (as for the Linux library);
    # zlib is built shared from the nested submodule at src/vendor/zlib (the commit
    # libtcod's FetchContent pins; a source dir means no download and no host zlib lookup).
    # SDL3=OFF: the engine does not use libtcod's SDL context.
    # UTF8PROC_STATIC: the vendored utf8proc is compiled in, but its header marks it
    # dllimport unless told so (a hard error under MinGW).
    cmake -S modules/libtcod-headless -B "$B" -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN" \
        -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON -DLIBTCOD_SDL3=OFF \
        -DLIBTCOD_UTF8PROC=vendored -DLIBTCOD_LODEPNG=vendored -DLIBTCOD_STB=vendored \
        -DFETCHCONTENT_SOURCE_DIR_ZLIB="$ROOT/modules/libtcod-headless/src/vendor/zlib" \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_C_FLAGS=-DUTF8PROC_STATIC \
        -DCMAKE_INSTALL_PREFIX="$DEST/libtcod" > /dev/null
    cmake --build "$B" -j"$JOBS" > "$B/build.log" 2>&1 || { tail -40 "$B/build.log"; exit 1; }
    cmake --install "$B" > /dev/null
    [ -e "$DEST/libtcod/bin/libtcod.dll" ] || { echo "ERROR: libtcod.dll was not installed" >&2; exit 1; }
    # zlib installs its DLL twice (libz.dll and a byte-identical zlib1.dll); nothing imports
    # zlib1.dll, and CMake copies libtcod/bin/ beside the exe, so it would only ship.
    cmp -s "$DEST/libtcod/bin/libz.dll" "$DEST/libtcod/bin/zlib1.dll" \
        || { echo "ERROR: zlib1.dll is not a copy of libz.dll any more; revisit this script" >&2; exit 1; }
    rm "$DEST/libtcod/bin/zlib1.dll"
    # The DLLs libtcod.dll may import: Windows system DLLs, the pthread runtime the engine
    # build copies, and the libz.dll staged beside it. SDL3 or utf8proc here is a regression.
    imports="$(x86_64-w64-mingw32-objdump -p "$DEST/libtcod/bin/libtcod.dll" | sed -n 's/.*DLL Name: //p' | sort -u)"
    echo "libtcod.dll imports: $(echo $imports)"
    unexpected="$(echo "$imports" | awk 'tolower($0) !~ /^(kernel32|msvcrt|libwinpthread-1|libz)\.dll$/')"
    [ -z "$unexpected" ] || { echo "ERROR: libtcod.dll imports unexpected DLLs: $unexpected" >&2; exit 1; }
else
    log "libtcod already staged (skip)"
fi

log "Windows dependencies staged in $DEST"
