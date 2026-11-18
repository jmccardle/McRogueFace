#!/usr/bin/env bash
#
# Build McRogueFace's native dependencies from the submodules and stage them
# where CMake expects them. This is what `make deps` runs.
#
# Usage:
#   tools/build_deps.sh                 # SFML + libtcod + CPython -> __lib/, libghostty-vt
#                                       # (static, via build_libghostty.sh) -> __lib_static/, deps/ links
#   tools/build_deps.sh --free-threaded # also the free-threaded CPython -> __lib_ft/
#   tools/build_deps.sh --clean         # rebuild everything from scratch
#
# Environment:
#   MCRF_SYSROOT  Prefix with extra -dev headers/libs (tools/fetch_dev_headers.sh),
#                 for machines without root access.
#
# Each component is skipped if it is already staged in __lib/ (use --clean to
# force a rebuild). Output layout:
#   __lib/libsfml-*.so*, __lib/libtcod.so*, __lib/libpython3.X.so*,
#   __lib/Python/{Lib,lib.linux-x86_64-3.X}/, __lib/include/pyconfig.h
#   __lib_static/ghostty-vt/{include,lib}  (libghostty-vt static archive: a link input, so it
#                                           stays out of __lib/, which is shipped whole)
#   deps/{cpython,Python,libtcod,SFML} -> modules/...

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LIB_DIR="$PROJECT_ROOT/__lib"
JOBS="$(nproc 2>/dev/null || echo 4)"

FT=0
CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --free-threaded) FT=1 ;;
        --clean) CLEAN=1 ;;
        --help|-h) sed -n '2,22p' "$0"; exit 0 ;;
        *) echo "Unknown argument: $arg"; exit 1 ;;
    esac
done

log() { echo "=== $* ==="; }

# build_python.sh stages the pure-Python stdlib with rsync, as its last step. Without it
# the interpreter is staged (so a re-run sees libpython and skips) but the stdlib is not.
if ! command -v rsync >/dev/null 2>&1; then
    echo "ERROR: rsync is required (it stages the Python stdlib). sudo apt install rsync"
    exit 1
fi

# The staged interpreter is only usable with its stdlib beside it. Check for the files
# an embedded CPython cannot start without, instead of trusting that the stager finished.
verify_stdlib() {
    local lib_dir="$1" f
    for f in os.py site.py encodings/__init__.py importlib/__init__.py; do
        if [ ! -f "$lib_dir/Python/Lib/$f" ]; then
            echo "ERROR: Python stdlib not staged: $lib_dir/Python/Lib/$f is missing."
            echo "       Fix the cause (is rsync installed?), then re-run: tools/build_deps.sh --clean"
            exit 1
        fi
    done
}

# CMake flags for a local -dev sysroot (no-op when MCRF_SYSROOT is unset)
SYSROOT_CMAKE=()
if [ -n "${MCRF_SYSROOT:-}" ]; then
    S="$MCRF_SYSROOT/usr"
    MULTIARCH="$(gcc -print-multiarch 2>/dev/null || echo x86_64-linux-gnu)"
    SYSROOT_CMAKE=(
        "-DCMAKE_PREFIX_PATH=$S"
        "-DCMAKE_INCLUDE_PATH=$S/include"
        "-DCMAKE_LIBRARY_PATH=$S/lib/$MULTIARCH"
        "-DCMAKE_C_FLAGS=-isystem $S/include"
        "-DCMAKE_CXX_FLAGS=-isystem $S/include"
    )
    log "Using dev-header sysroot $MCRF_SYSROOT"
fi

cd "$PROJECT_ROOT"

# --- Submodules -------------------------------------------------------------
# Shallow, and only what the native build needs (cpython is large).
log "Submodules"
git submodule update --init --depth 1 --jobs 6 \
    modules/SFML modules/libtcod-headless modules/cpython \
    modules/imgui modules/imgui-sfml modules/json modules/RapidXML modules/ghostty
# libtcod vendors utf8proc as a nested submodule (see LIBTCOD_UTF8PROC below)
git -C modules/libtcod-headless submodule update --init --depth 1 src/vendor/utf8proc

mkdir -p "$LIB_DIR"

# --- SFML -------------------------------------------------------------------
# Also re-run for a checkout staged before #525: no libFLAC, or SFML with a RUNPATH that is
# not $ORIGIN (the build tree's), which packaging can't use.
sfml_staged() {
    ls "$LIB_DIR"/libsfml-graphics.so.* >/dev/null 2>&1 || return 1
    ls "$LIB_DIR"/libFLAC.so.* >/dev/null 2>&1 || return 1
    local m
    for m in "$LIB_DIR"/libsfml-*.so.?.?.?; do
        [ "$(sfml_runpath "$m")" = '$ORIGIN' ] || return 1
    done
}
sfml_runpath() { readelf -d "$1" | sed -n 's/.*(\(RUNPATH\|RPATH\)).*\[\(.*\)\]/\2/p'; }

if [ "$CLEAN" -eq 1 ] || ! sfml_staged; then
    log "SFML"
    B="$PROJECT_ROOT/modules/SFML/build"
    [ "$CLEAN" -eq 1 ] && rm -rf "$B"
    # RUNPATH=$ORIGIN, not the build tree: a RUNPATH is not searched for the dependencies of
    # dependencies, so what SFML needs (libFLAC, staged below) is found next to it, in lib/,
    # wherever the package is unpacked (#525).
    cmake -S modules/SFML -B "$B" -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
        -DSFML_BUILD_NETWORK=OFF \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON -DCMAKE_INSTALL_RPATH='$ORIGIN' \
        "${SYSROOT_CMAKE[@]}" > /dev/null
    cmake --build "$B" -j"$JOBS" > "$B/build.log" 2>&1 || { tail -30 "$B/build.log"; exit 1; }
    # libFLAC goes too: the new SFML would resolve it from here, and a stale one from
    # another host must be replaced, not kept.
    rm -f "$LIB_DIR"/libsfml-*.so* "$LIB_DIR"/libFLAC.so*
    cp -a "$B"/lib/libsfml-*.so* "$LIB_DIR/"
    for m in "$LIB_DIR"/libsfml-*.so.?.?.?; do
        if [ "$(sfml_runpath "$m")" != '$ORIGIN' ]; then
            echo "ERROR: $m has RUNPATH '$(sfml_runpath "$m")', expected \$ORIGIN"
            exit 1
        fi
    done
    # libFLAC is the one SFML dependency the package ships: its soname differs between
    # distros (.8, .12, .14), so a package built here can't rely on the user's. The name is
    # whatever libsfml-audio records; the file is the one the loader resolves for it here.
    # openal, vorbis, ogg, X11, GL and freetype stay host-provided.
    FLAC="$(readelf -d "$LIB_DIR/libsfml-audio.so" | sed -n 's/.*Shared library: \[\(libFLAC\.so\.[0-9.]*\)\].*/\1/p')"
    if [ -z "$FLAC" ]; then
        echo "ERROR: libsfml-audio does not record a libFLAC dependency"
        exit 1
    fi
    # Resolve it as the host would: through SFML's build-tree copy, whose RUNPATH ($ORIGIN)
    # is the build dir, which holds no FLAC -- never through __lib/.
    FLAC_PATH="$(ldd "$B/lib/libsfml-audio.so" | awk -v n="$FLAC" '$1 == n && $3 ~ /^\// {print $3}')"
    if [ -z "$FLAC_PATH" ]; then
        echo "ERROR: $FLAC (needed by libsfml-audio) does not resolve on this machine"
        exit 1
    fi
    cp -L "$FLAC_PATH" "$LIB_DIR/$FLAC"
else
    log "SFML already staged (skip)"
fi

# --- libtcod-headless -------------------------------------------------------
if [ "$CLEAN" -eq 1 ] || [ ! -e "$LIB_DIR/libtcod.so.2" ]; then
    log "libtcod-headless"
    B="$PROJECT_ROOT/modules/libtcod-headless/build"
    [ "$CLEAN" -eq 1 ] && rm -rf "$B"
    # SDL3=OFF: no SDL fetch. vendored: utf8proc/lodepng/stb compiled into
    # libtcod.so -- otherwise libtcod needs a libutf8proc.so.3 found only via a
    # RUNPATH into this build tree. PIC: static vendored code in a shared lib.
    cmake -S modules/libtcod-headless -B "$B" -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=ON -DLIBTCOD_SDL3=OFF \
        -DLIBTCOD_UTF8PROC=vendored -DLIBTCOD_LODEPNG=vendored -DLIBTCOD_STB=vendored \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON > /dev/null
    cmake --build "$B" -j"$JOBS" > "$B/build.log" 2>&1 || { tail -30 "$B/build.log"; exit 1; }
    rm -f "$LIB_DIR"/libtcod.so*
    cp -a "$B"/libtcod.so* "$LIB_DIR/"
    if readelf -d "$LIB_DIR/libtcod.so.2" | grep -qE "RUNPATH|RPATH|libutf8proc"; then
        echo "ERROR: libtcod.so.2 is not self-contained:"
        readelf -d "$LIB_DIR/libtcod.so.2" | grep -E "NEEDED|RUNPATH|RPATH"
        exit 1
    fi
else
    log "libtcod already staged (skip)"
fi

# --- CPython ----------------------------------------------------------------
PY_ARGS=()
[ "$CLEAN" -eq 1 ] && PY_ARGS+=(--clean)
# The pinned version, not any libpython3.*: a __lib/ staged before a submodule
# bump still holds the old interpreter, and would otherwise be "already staged".
PY_VER="$(sed -n 's/^#define PY_VERSION[[:space:]]*"\([0-9]*\.[0-9]*\).*/\1/p' modules/cpython/Include/patchlevel.h)"
if [ "$CLEAN" -eq 1 ] || [ ! -e "$LIB_DIR/libpython${PY_VER}.so.1.0" ]; then
    log "CPython"
    "$SCRIPT_DIR/build_python.sh" "${PY_ARGS[@]}"
else
    log "CPython already staged (skip)"
fi
if [ "$FT" -eq 1 ]; then
    log "CPython (free-threaded)"
    "$SCRIPT_DIR/build_python.sh" --free-threaded "${PY_ARGS[@]}"
fi
verify_stdlib "$LIB_DIR"
[ "$FT" -eq 1 ] && verify_stdlib "$PROJECT_ROOT/__lib_ft"

# --- libghostty-vt (static; Zig toolchain provisioned by the script) ---------
LG_ARGS=()
[ "$CLEAN" -eq 1 ] && LG_ARGS+=(--clean)
"$SCRIPT_DIR/build_libghostty.sh" native "${LG_ARGS[@]}"

# --- deps/ include links ----------------------------------------------------
log "deps/ links"
mkdir -p deps
ln -sfn ../modules/cpython deps/cpython
ln -sfn ../modules/cpython/Include deps/Python
ln -sfn ../modules/libtcod-headless/src/libtcod deps/libtcod
ln -sfn ../modules/SFML/include/SFML deps/SFML

echo
echo "Dependencies staged in $LIB_DIR. Next: make"
