#!/usr/bin/env bash
# Cross-build the embedded CPython (modules/cpython) for Emscripten, for
# `make wasm` / `make wasm-game` / `make playground`.
#
# Output (what CMakeLists.txt links):
#   modules/cpython/cross-build/wasm32-emscripten/build/python/libpython3.X.a
#   modules/cpython/cross-build/wasm32-emscripten/prefix/lib/{libffi,libmpdec}.a
#
# Usage: source ~/emsdk/emsdk_env.sh && tools/build_python_wasm.sh [--clean]
#
# This drives CPython's own Platforms/emscripten tooling, with two local
# adjustments:
#  - That script needs Python >= 3.12. The native "build python" it compiles
#    first works with any python3, so the remaining steps re-run under it.
#  - It wants Node (via nvm) only as the runner for CPython's own test suite;
#    linking libpython.a into McRogueFace never executes it. We pass whatever
#    `node` is on PATH (emsdk_env.sh provides one), or MCRF_WASM_NODE.
#
# The emsdk on PATH is used as-is (no --emsdk-cache), so libpython is built
# by the same emcc that links the engine.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CPYTHON_DIR="$ROOT/modules/cpython"

CLEAN=()
for arg in "$@"; do
    case "$arg" in
        --clean) CLEAN=(--clean) ;;
        *) sed -n '2,20p' "$0"; exit 2 ;;
    esac
done

command -v emcc >/dev/null || { echo "error: emcc not found -- source ~/emsdk/emsdk_env.sh first" >&2; exit 1; }
[ -f "$CPYTHON_DIR/Platforms/emscripten/__main__.py" ] || {
    echo "error: $CPYTHON_DIR/Platforms/emscripten missing (cpython submodule not initialized, or < 3.15)" >&2; exit 1; }
for stray in "$CPYTHON_DIR/Include/pyconfig.h" "$CPYTHON_DIR/pyconfig.h"; do
    [ -e "$stray" ] && { echo "error: $stray shadows the build's pyconfig.h (wrong LONG_BIT on wasm32); remove it" >&2; exit 1; }
done
NODE="${MCRF_WASM_NODE:-$(command -v node || true)}"
[ -n "$NODE" ] || { echo "error: no node on PATH; set MCRF_WASM_NODE" >&2; exit 1; }

cd "$CPYTHON_DIR"
EMS=Platforms/emscripten
python3 "$EMS" configure-build-python "${CLEAN[@]}"
python3 "$EMS" make-build-python
BUILD_PY=cross-build/build/python
"$BUILD_PY" "$EMS" make-dependencies
"$BUILD_PY" "$EMS" configure-host --host-runner "$NODE" "${CLEAN[@]}"
"$BUILD_PY" "$EMS" make-host

PY_VER="$(sed -n 's/^#define PY_VERSION[[:space:]]*"\([0-9]*\.[0-9]*\).*/\1/p' Include/patchlevel.h)"
LIB="cross-build/wasm32-emscripten/build/python/libpython${PY_VER}.a"
[ -f "$LIB" ] || { echo "error: $LIB was not produced" >&2; exit 1; }
echo "Built $CPYTHON_DIR/$LIB with $(emcc --version | head -1)"
