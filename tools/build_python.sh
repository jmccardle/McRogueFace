#!/usr/bin/env bash
#
# Build the embedded CPython from modules/cpython and stage it for linking.
#
# Usage:
#   tools/build_python.sh                    # default (GIL) build  -> __lib/
#   tools/build_python.sh --free-threaded    # PEP 703 build (3.Xt) -> __lib_ft/
#   tools/build_python.sh --debug            # pydebug (3.Xd) -> __lib_debug/  (make debug/asan/fuzz)
#   tools/build_python.sh --tsan             # free-threaded pydebug + ThreadSanitizer
#                                            #   (3.Xtd) -> __lib_tsan/        (make tsan)
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
# The variant builds stage to their own dir and are overlaid on top of __lib/
# by CMake (MCRF_FREE_THREADED_PYTHON / MCRF_DEBUG_PYTHON). Extension module
# filenames carry the ABI tag (cpython-315, -315t, -315d, -315td), so they can
# share one lib.linux-x86_64-3.X dir with the default build's modules.
#
# Note (3.15+): configure no longer falls back to the bundled libmpdec, and
# without it `decimal` silently degrades to _pydecimal. We pass
# --without-system-libmpdec so _decimal is self-contained in the bundle.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CPYTHON_DIR="$PROJECT_ROOT/modules/cpython"
JOBS="$(nproc 2>/dev/null || echo 4)"

VARIANT=default
CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --free-threaded) VARIANT=ft ;;
        --debug) VARIANT=debug ;;
        --tsan) VARIANT=tsan ;;
        --clean) CLEAN=1 ;;
        --help|-h)
            sed -n '2,29p' "$0"
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

# Include/Python.h does #include "pyconfig.h", which searches Include/ before
# the build dir: a stray in-tree copy (older tooling put one there) silently
# replaces this build's configure results -- or breaks cross builds outright.
for stray in "$CPYTHON_DIR/Include/pyconfig.h" "$CPYTHON_DIR/pyconfig.h"; do
    if [ -e "$stray" ]; then
        echo "ERROR: $stray exists and would shadow the build's own pyconfig.h."
        echo "       Remove it (the staged copy lives in <lib dir>/include/pyconfig.h)."
        exit 1
    fi
done

# Derive "3.15" from Include/patchlevel.h so nothing here is version-pinned
PY_VER="$(sed -n 's/^#define PY_VERSION[[:space:]]*"\([0-9]*\.[0-9]*\).*/\1/p' "$CPYTHON_DIR/Include/patchlevel.h")"
PY_VER_FULL="$(sed -n 's/^#define PY_VERSION[[:space:]]*"\(.*\)"/\1/p' "$CPYTHON_DIR/Include/patchlevel.h")"
PY_NODOT="${PY_VER/./}"

case "$VARIANT" in
    default) ABI_T="";   OUT_DIR="$PROJECT_ROOT/__lib";       EXTRA_CONFIGURE=() ;;
    ft)      ABI_T="t";  OUT_DIR="$PROJECT_ROOT/__lib_ft";    EXTRA_CONFIGURE=(--disable-gil) ;;
    debug)   ABI_T="d";  OUT_DIR="$PROJECT_ROOT/__lib_debug"; EXTRA_CONFIGURE=(--with-pydebug) ;;
    tsan)    ABI_T="td"; OUT_DIR="$PROJECT_ROOT/__lib_tsan"
             EXTRA_CONFIGURE=(--with-pydebug --disable-gil --with-thread-sanitizer) ;;
esac
BUILD_DIR="$PROJECT_ROOT/build-cpython${PY_NODOT}${ABI_T}"
if [ "$VARIANT" = tsan ]; then BUILD_DIR="${BUILD_DIR}-tsan"; fi

echo "=== CPython $PY_VER_FULL ($VARIANT, abiflags '${ABI_T}') -> $OUT_DIR ==="

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
# One interpreter per staging dir: the stdlib below is replaced wholesale, so
# a libpython / extension dir left over from a previous pin would be loadable
# against the wrong stdlib (and package.sh would pick it up by name).
for stale in "$OUT_DIR"/libpython3.*"${ABI_T}".so* "$OUT_DIR"/Python/lib.linux-x86_64-3.*; do
    case "$stale" in
        "$OUT_DIR/libpython${PY_VER}${ABI_T}.so"*|"$DEST_EXT") ;;
        *) [ -e "$stale" ] && { echo "Removing stale $(basename "$stale")"; rm -rf "$stale"; } ;;
    esac
done
install -m 755 "$LIBNAME" "$OUT_DIR/$LIBNAME"
STRIP=1
case "$VARIANT" in debug|tsan) STRIP=0 ;; esac   # keep symbols for sanitizer/gdb traces
if [ "$STRIP" -eq 1 ]; then strip --strip-unneeded "$OUT_DIR/$LIBNAME"; fi
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
if [ "$STRIP" -eq 1 ]; then strip --strip-unneeded "$DEST_EXT"/*.so; fi

# Pure-Python stdlib (shared by both builds; tests excluded to save ~40 MB)
rsync -a --delete --exclude '__pycache__' --exclude 'test/' \
    "$CPYTHON_DIR/Lib/" "$OUT_DIR/Python/Lib/"

echo "Staged $(ls "$DEST_EXT" | wc -l) extension modules and $LIBNAME into $OUT_DIR"
