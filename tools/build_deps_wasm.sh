#!/usr/bin/env bash
#
# Build the Emscripten inputs CMakeLists.txt links a web build against, in the
# places it looks for them. Needs an active emsdk (source emsdk_env.sh).
#
#   deps/stb/stb_image.h                           (SDL2Renderer's image loader)
#   modules/libtcod-headless/build-emscripten/     libtcod.a plus its fetched
#                                                  lodepng-c and utf8proc builds
#   modules/cpython/cross-build/wasm32-emscripten/ via tools/build_python_wasm.sh
#
# Each step is skipped when its output exists; --clean rebuilds libtcod.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
JOBS="$(nproc 2>/dev/null || echo 4)"
CLEAN=0
[ "${1:-}" = "--clean" ] && CLEAN=1

log() { echo "== build_deps_wasm: $*"; }

if ! command -v emcmake >/dev/null 2>&1; then
    echo "ERROR: emcmake not found -- source emsdk_env.sh first" >&2
    exit 1
fi

cd "$PROJECT_ROOT"
git submodule update --init --depth 1 modules/SFML modules/libtcod-headless modules/cpython
git -C modules/libtcod-headless submodule update --init --depth 1 src/vendor/utf8proc

# --- stb_image.h ------------------------------------------------------------
# The copy SFML vendors, which the desktop build already decodes images with.
mkdir -p deps
ln -sfn ../modules/SFML/extlibs/headers/stb_image deps/stb
[ -f deps/stb/stb_image.h ] || { echo "ERROR: deps/stb/stb_image.h missing" >&2; exit 1; }

# --- libtcod ----------------------------------------------------------------
# CMakeLists.txt links build-emscripten/libtcod.a and the FetchContent builds
# under build-emscripten/_deps/, so lodepng and utf8proc stay "ON" (fetched),
# not vendored as in the native build.
B="$PROJECT_ROOT/modules/libtcod-headless/build-emscripten"
if [ "$CLEAN" -eq 1 ] || [ ! -f "$B/libtcod.a" ]; then
    log "libtcod"
    [ "$CLEAN" -eq 1 ] && rm -rf "$B"
    emcmake cmake -S modules/libtcod-headless -B "$B" -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=OFF -DLIBTCOD_SDL3=OFF > /dev/null
    cmake --build "$B" -j"$JOBS" > "$B/build.log" 2>&1 || { tail -30 "$B/build.log"; exit 1; }
    for f in libtcod.a _deps/lodepng-c-build/liblodepng-c.a _deps/utf8proc-build/libutf8proc.a; do
        [ -f "$B/$f" ] || { echo "ERROR: libtcod build did not produce $f" >&2; exit 1; }
    done
else
    log "libtcod already built (skip)"
fi

# --- CPython ----------------------------------------------------------------
if ls modules/cpython/cross-build/wasm32-emscripten/build/python/libpython3.*.a >/dev/null 2>&1; then
    log "CPython already built (skip)"
else
    log "CPython"
    "$SCRIPT_DIR/build_python_wasm.sh"
fi
