#!/usr/bin/env bash
#
# Build the embedded CPython from modules/cpython and stage it for linking.
#
# Usage:
#   tools/build_python.sh                    # default (GIL) build  -> __lib/
#   tools/build_python.sh --free-threaded    # PEP 703 build (3.Xt) -> __lib_ft/
#   tools/build_python.sh --clean ...        # wipe the out-of-tree build dir first
#
# Environment:
#   MCRF_SYSROOT   Optional prefix holding extra -dev headers/libs (e.g. extracted
#                  with `apt-get download` + `dpkg -x` on a machine without root).
#                  Used for libzstd (_zstd) and libuuid (_uuid).
#
# Output layout (what CMakeLists.txt and McRFPy_API.cpp expect):
#   <out>/libpython3.X[t].so{,.1.0}
#   <out>/Python/Lib/                         pure-Python stdlib
#   <out>/Python/lib.linux-x86_64-3.X/        extension modules + _sysconfigdata
#
# The free-threaded build stages to __lib_ft/ and is overlaid on top of __lib/
# by CMake when MCRF_FREE_THREADED_PYTHON=ON. Extension module filenames carry
# the ABI tag (cpython-315 vs cpython-315t), so both sets can share one dir.
#
# Note (3.15+): configure no longer falls back to the bundled libmpdec, and
# without it `decimal` silently degrades to _pydecimal. We pass
# --without-system-libmpdec so _decimal is self-contained in the bundle.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CPYTHON_DIR="$PROJECT_ROOT/modules/cpython"
JOBS="$(nproc 2>/dev/null || echo 4)"

FT=0
CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --free-threaded) FT=1 ;;
        --clean) CLEAN=1 ;;
        --help|-h)
            sed -n '2,25p' "$0"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg"
            exit 1
            ;;
    esac
done

if [ ! -f "$CPYTHON_DIR/configure" ]; then
    echo "ERROR: $CPYTHON_DIR/configure not found - initialize the cpython submodule"
    exit 1
fi

# Derive "3.15" from Include/patchlevel.h so nothing here is version-pinned
PY_VER="$(sed -n 's/^#define PY_VERSION[[:space:]]*"\([0-9]*\.[0-9]*\).*/\1/p' "$CPYTHON_DIR/Include/patchlevel.h")"
PY_VER_FULL="$(sed -n 's/^#define PY_VERSION[[:space:]]*"\(.*\)"/\1/p' "$CPYTHON_DIR/Include/patchlevel.h")"
PY_NODOT="${PY_VER/./}"

if [ "$FT" -eq 1 ]; then
    ABI_T="t"
    BUILD_DIR="$PROJECT_ROOT/build-cpython${PY_NODOT}t"
    OUT_DIR="$PROJECT_ROOT/__lib_ft"
    EXTRA_CONFIGURE=(--disable-gil)
else
    ABI_T=""
    BUILD_DIR="$PROJECT_ROOT/build-cpython${PY_NODOT}"
    OUT_DIR="$PROJECT_ROOT/__lib"
    EXTRA_CONFIGURE=()
fi

echo "=== CPython $PY_VER_FULL ${ABI_T:+(free-threaded)} -> $OUT_DIR ==="

if [ "$CLEAN" -eq 1 ]; then
    rm -rf "$BUILD_DIR"
fi
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

if [ -n "${MCRF_SYSROOT:-}" ]; then
    SYSLIB="$MCRF_SYSROOT/usr/lib/x86_64-linux-gnu"
    export LIBZSTD_CFLAGS="-I$MCRF_SYSROOT/usr/include"
    export LIBZSTD_LIBS="-L$SYSLIB -lzstd"
    export LIBUUID_CFLAGS="-I$MCRF_SYSROOT/usr/include/uuid"
    export LIBUUID_LIBS="-L$SYSLIB -luuid"
fi

if [ ! -f Makefile ]; then
    "$CPYTHON_DIR/configure" \
        --enable-shared \
        --without-system-libmpdec \
        "${EXTRA_CONFIGURE[@]}" > configure.log 2>&1 \
        || { tail -30 configure.log; exit 1; }
fi

make -j"$JOBS" > make.log 2>&1 || { tail -40 make.log; exit 1; }
grep -A4 "necessary bits" make.log || true

# --- Stage ---
LIBNAME="libpython${PY_VER}${ABI_T}.so.1.0"
PYBUILDDIR="$BUILD_DIR/$(cat pybuilddir.txt)"
DEST_EXT="$OUT_DIR/Python/lib.linux-x86_64-${PY_VER}"

mkdir -p "$OUT_DIR" "$DEST_EXT"
install -m 755 "$LIBNAME" "$OUT_DIR/$LIBNAME"
strip --strip-unneeded "$OUT_DIR/$LIBNAME"
ln -sf "$LIBNAME" "$OUT_DIR/libpython${PY_VER}${ABI_T}.so"

# pyconfig.h is generated per build (the free-threaded one defines
# Py_GIL_DISABLED), so it lives with the lib rather than in deps/cpython.
mkdir -p "$OUT_DIR/include"
cp pyconfig.h "$OUT_DIR/include/pyconfig.h"

# Extension modules (skip CPython's own test-only modules)
# (pybuilddir entries are symlinks into Modules/, hence -L / cp -L)
find -L "$PYBUILDDIR" -maxdepth 1 -type f \( -name '*.so' -o -name '_sysconfig*' \) \
    ! -name '_test*' ! -name 'xxsubtype*' ! -name 'xxlimited*' ! -name '_ctypes_test*' \
    -exec cp -L {} "$DEST_EXT/" \;
strip --strip-unneeded "$DEST_EXT"/*.so

# Pure-Python stdlib (shared by both builds; tests excluded to save ~40 MB)
rsync -a --delete --exclude '__pycache__' --exclude 'test/' \
    "$CPYTHON_DIR/Lib/" "$OUT_DIR/Python/Lib/"

echo "Staged $(ls "$DEST_EXT" | wc -l) extension modules and $LIBNAME into $OUT_DIR"
