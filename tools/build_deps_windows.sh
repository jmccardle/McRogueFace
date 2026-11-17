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
#   __lib_windows/libtcod/{include,lib,bin}   libtcod.dll, self-contained: utf8proc, lodepng
#                                             and stb are compiled in, no SDL (zlib is libz.dll)
#   build-windows-deps/{sfml,libtcod}/        the build trees (gitignored; submodules stay clean)
#
# A component is rebuilt when what it was built from changed: SFML and libtcod record the
# submodule commit and a hash of this script and the toolchain file in __lib_windows/.stamps/;
# CPython is compared with modules/cpython's patchlevel.h through the staged
# build-details.json. A mismatch rebuilds. Every run, built or not, then validates what is
# staged and fails on a problem. --clean forces a rebuild.
#
# Requires the MinGW-w64 posix toolchain (g++-mingw-w64-x86-64-posix), cmake, git, curl,
# unzip, python3.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="$ROOT/__lib_windows"
BUILD="$ROOT/build-windows-deps"
STAMPS="$DEST/.stamps"
TOOLCHAIN="$ROOT/cmake/toolchains/mingw-w64-x86_64.cmake"
JOBS="$(nproc 2>/dev/null || echo 4)"

CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --clean) CLEAN=1 ;;
        --help|-h) sed -n '2,25p' "$0"; exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

log() { echo "=== $* ==="; }
die() { echo "ERROR: $*" >&2; exit 1; }

for tool in cmake git curl unzip sha256sum python3 x86_64-w64-mingw32-g++-posix \
            x86_64-w64-mingw32-gcc-posix x86_64-w64-mingw32-objdump \
            x86_64-w64-mingw32-dlltool x86_64-w64-mingw32-windres; do
    command -v "$tool" >/dev/null || die "$tool not found"
done

cd "$ROOT"

# --- Submodules and deps/ links ---------------------------------------------
# Only what the Windows build uses: libtcod's nested vcpkg and docs theme are never built.
log "Submodules"
git submodule update --init --depth 1 modules/SFML modules/libtcod-headless modules/cpython
(cd modules/libtcod-headless && git submodule update --init --depth 1 src/vendor/utf8proc src/vendor/zlib)
# CMake reads the Windows pyconfig.h through deps/cpython; build_deps.sh makes the same link.
mkdir -p deps "$STAMPS"
ln -sfn ../modules/cpython deps/cpython

submodule_head() { (cd "$1" && git rev-parse HEAD); }
# A recipe change (this script, the toolchain) invalidates SFML and libtcod like a new commit.
RECIPE="$(cat "$0" "$TOOLCHAIN" | sha256sum | cut -c1-16)"
# stamp_matches NAME VALUE: the stamp recorded when NAME was last built equals VALUE.
stamp_matches() { [ -f "$STAMPS/$1" ] && [ "$(cat "$STAMPS/$1")" = "$2" ]; }

# --- CPython ----------------------------------------------------------------
# The embeddable archive ships build-details.json, so the staged version is read from what
# was staged, not from a record of what we meant to stage.
PY_WANT="$(sed -n 's/^#define PY_VERSION[[:space:]]*"\([0-9]*\.[0-9]*\.[0-9]*\).*/\1/p' modules/cpython/Include/patchlevel.h)"
[ -n "$PY_WANT" ] || die "cannot read PY_VERSION from modules/cpython"
PYVER="${PY_WANT%.*}"; PYVER="${PYVER/./}"
py_staged_version() {
    [ -f "$DEST/build-details.json" ] || return 0
    python3 -I -c 'import json, sys
v = json.load(open(sys.argv[1]))["language"]["version_info"]
print("%d.%d.%d" % (v["major"], v["minor"], v["micro"]))' "$DEST/build-details.json"
}
if [ "$CLEAN" -eq 1 ] || [ "$(py_staged_version)" != "$PY_WANT" ] \
        || [ ! -e "$DEST/libpython$PYVER.a" ] || [ ! -e "$DEST/python$PYVER.dll" ]; then
    log "CPython $PY_WANT for Windows (staged: '$(py_staged_version)')"
    "$SCRIPT_DIR/fetch_windows_python.sh"
else
    log "CPython $PY_WANT already staged"
fi

# --- SFML -------------------------------------------------------------------
SFML_STAMP="$(submodule_head modules/SFML) $RECIPE"
if [ "$CLEAN" -eq 1 ] || ! stamp_matches sfml "$SFML_STAMP"; then
    log "SFML"
    B="$BUILD/sfml"
    rm -rf "$B" "$DEST/sfml" "$STAMPS/sfml"
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
    echo "$SFML_STAMP" > "$STAMPS/sfml"
else
    log "SFML already staged"
fi
for f in sfml-system-2 sfml-window-2 sfml-graphics-2 sfml-audio-2 openal32; do
    [ -e "$DEST/sfml/bin/$f.dll" ] || die "$DEST/sfml/bin/$f.dll missing"
done
[ -e "$DEST/sfml/lib/libfreetype.a" ] || die "SFML did not stage libfreetype.a"
[ -e "$DEST/sfml/include/SFML/Graphics.hpp" ] || die "SFML headers not staged"

# --- libtcod-headless -------------------------------------------------------
TCOD_STAMP="$(submodule_head modules/libtcod-headless) $RECIPE"
if [ "$CLEAN" -eq 1 ] || ! stamp_matches libtcod "$TCOD_STAMP"; then
    log "libtcod-headless"
    B="$BUILD/libtcod"
    rm -rf "$B" "$DEST/libtcod" "$STAMPS/libtcod"
    # utf8proc, lodepng and stb are compiled into libtcod.dll (as for the Linux library);
    # zlib is built shared from the nested submodule at src/vendor/zlib, the commit
    # libtcod's FetchContent pins. libtcod asks find_package(ZLIB) before fetching, so the
    # lookup is switched off (FETCHCONTENT_TRY_FIND_PACKAGE_MODE=NEVER): a zlib installed
    # on the build host would be picked up and fail to link or load later.
    # SDL3=OFF: the engine does not use libtcod's SDL context.
    # UTF8PROC_STATIC: the vendored utf8proc is compiled in, but its header marks it
    # dllimport unless told so (a hard error under MinGW).
    cmake -S modules/libtcod-headless -B "$B" -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN" \
        -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON -DLIBTCOD_SDL3=OFF \
        -DLIBTCOD_UTF8PROC=vendored -DLIBTCOD_LODEPNG=vendored -DLIBTCOD_STB=vendored \
        -DFETCHCONTENT_SOURCE_DIR_ZLIB="$ROOT/modules/libtcod-headless/src/vendor/zlib" \
        -DFETCHCONTENT_TRY_FIND_PACKAGE_MODE=NEVER \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_C_FLAGS=-DUTF8PROC_STATIC \
        -DCMAKE_INSTALL_PREFIX="$DEST/libtcod" > /dev/null
    cmake --build "$B" -j"$JOBS" > "$B/build.log" 2>&1 || { tail -40 "$B/build.log"; exit 1; }
    cmake --install "$B" > /dev/null
    [ -e "$DEST/libtcod/bin/libtcod.dll" ] || die "libtcod.dll was not installed"
    # zlib installs its DLL twice (libz.dll and a byte-identical zlib1.dll); nothing imports
    # zlib1.dll, and CMake copies libtcod/bin/ beside the exe, so it would only ship.
    cmp -s "$DEST/libtcod/bin/libz.dll" "$DEST/libtcod/bin/zlib1.dll" \
        || die "zlib1.dll is not a copy of libz.dll any more; revisit this script"
    rm "$DEST/libtcod/bin/zlib1.dll"
    echo "$TCOD_STAMP" > "$STAMPS/libtcod"
else
    log "libtcod already staged"
fi
[ -e "$DEST/libtcod/bin/libtcod.dll" ] || die "$DEST/libtcod/bin/libtcod.dll missing"
[ -e "$DEST/libtcod/bin/libz.dll" ] || die "$DEST/libtcod/bin/libz.dll missing"
[ -e "$DEST/libtcod/lib/liblibtcod.dll.a" ] || die "libtcod import library missing"
[ ! -e "$DEST/libtcod/bin/zlib1.dll" ] || die "stale zlib1.dll in libtcod/bin"
# The DLLs libtcod.dll imports must be Windows system DLLs, the pthread runtime the engine
# build copies, and the libz.dll staged beside it (SDL3 or utf8proc here is a regression),
# and the parse must have found the ones it cannot do without.
imports="$(x86_64-w64-mingw32-objdump -p "$DEST/libtcod/bin/libtcod.dll" | sed -n 's/.*DLL Name: //p' | sort -u | tr 'A-Z' 'a-z')"
echo "libtcod.dll imports: $(echo $imports)"
for need in kernel32.dll libz.dll; do
    echo "$imports" | grep -qx "$need" || die "libtcod.dll does not import $need (imports parsed: '$(echo $imports)')"
done
unexpected="$(echo "$imports" | awk '!/^(kernel32|msvcrt|libwinpthread-1|libz)\.dll$/')"
[ -z "$unexpected" ] || die "libtcod.dll imports unexpected DLLs: $unexpected"

log "Windows dependencies staged and validated in $DEST"
