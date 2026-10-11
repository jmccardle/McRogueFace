#!/usr/bin/env bash
#
# Build libtcod-headless with sanitizer instrumentation.
#
# Usage:
#   tools/build_debug_libs.sh              # Build with debug symbols only
#   tools/build_debug_libs.sh --asan       # Build with AddressSanitizer (default compiler, for make asan)
#   tools/build_debug_libs.sh --fuzz       # Build with ASan + UBSan using clang-18 (for make fuzz-build)
#   tools/build_debug_libs.sh --tsan       # Build with ThreadSanitizer
#   tools/build_debug_libs.sh --clean      # Remove build artifacts first
#
# Output: __lib_debug/libtcod.so (debug), __lib_asan/libtcod.so (asan),
#         __lib_fuzz/libtcod.so (fuzz), __lib_tsan/libtcod.so (tsan, next to its
#         CPython). Each instrumented build has its own directory because each links
#         only into the build made with the same compiler and sanitizer runtime: an
#         ASan libtcod in __lib_debug/ leaves the plain debug build with undefined
#         __asan_* symbols, and clang's ASan library doesn't link into a GCC ASan build.
#
# Why: The pre-built libtcod in __lib/ is uninstrumented. ASan/TSan can
# detect bugs in our code that corrupt libtcod's memory, but cannot detect
# bugs originating inside libtcod (FOV, pathfinding) that touch our data.
# Building libtcod with the same sanitizer flags closes this gap.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LIBTCOD_DIR="$PROJECT_ROOT/modules/libtcod-headless"
OUTPUT_DIR="$PROJECT_ROOT/__lib_debug"
JOBS="$(nproc 2>/dev/null || echo 4)"

MODE="debug"
CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --asan)  MODE="asan" ;;
        --fuzz)  MODE="fuzz" ;;
        --tsan)  MODE="tsan" ;;
        --clean) CLEAN=1 ;;
        --help|-h)
            echo "Usage: $0 [--asan|--fuzz|--tsan] [--clean]"
            echo ""
            echo "Flags:"
            echo "  (default)  Debug symbols only (-g -O1)"
            echo "  --asan     AddressSanitizer + UBSan instrumentation (default compiler)"
            echo "  --fuzz     AddressSanitizer + UBSan with clang-18 (the fuzz build's compiler)"
            echo "  --tsan     ThreadSanitizer instrumentation"
            echo "  --clean    Remove build artifacts before building"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Run '$0 --help' for usage."
            exit 1
            ;;
    esac
done

BUILD_DIR="$LIBTCOD_DIR/build-debug-$MODE"

case "$MODE" in
    debug)
        SANITIZER_FLAGS=""
        echo "=== Building libtcod-headless with debug symbols ==="
        ;;
    asan)
        SANITIZER_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer"
        OUTPUT_DIR="$PROJECT_ROOT/__lib_asan"
        echo "=== Building libtcod-headless with ASan + UBSan ==="
        ;;
    fuzz)
        SANITIZER_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer"
        OUTPUT_DIR="$PROJECT_ROOT/__lib_fuzz"
        export CC=clang-18 CXX=clang++-18
        echo "=== Building libtcod-headless with ASan + UBSan (clang-18, for the fuzz build) ==="
        ;;
    tsan)
        SANITIZER_FLAGS="-fsanitize=thread"
        OUTPUT_DIR="$PROJECT_ROOT/__lib_tsan"
        echo "=== Building libtcod-headless with TSan ==="
        ;;
esac

if [ "$CLEAN" -eq 1 ]; then
    echo "Cleaning $BUILD_DIR..."
    rm -rf "$BUILD_DIR"
fi

if [ ! -f "$LIBTCOD_DIR/CMakeLists.txt" ]; then
    echo "ERROR: libtcod-headless not found at $LIBTCOD_DIR/CMakeLists.txt"
    echo "Make sure the submodule is initialized:"
    echo "  git submodule update --init modules/libtcod-headless"
    exit 1
fi

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Use an array so multi-word sanitizer flags stay a single -D argument each.
# (A plain string word-splits, sending e.g. -fno-omit-frame-pointer to cmake as
# a bare unknown argument.)
CMAKE_EXTRA_FLAGS=()
if [ -n "$SANITIZER_FLAGS" ]; then
    CMAKE_EXTRA_FLAGS=("-DCMAKE_C_FLAGS=$SANITIZER_FLAGS" "-DCMAKE_CXX_FLAGS=$SANITIZER_FLAGS")
fi

if [ ! -f Makefile ]; then
    echo "Configuring libtcod-headless ($MODE)..."
    # The shipped libtcod's configuration (no SDL3, vendored lodepng/stb/utf8proc), so
    # the instrumented library has the same code and dependencies as the one in __lib/.
    # PIC: the vendored static deps are linked into the shared library.
    cmake "$LIBTCOD_DIR" \
        -DCMAKE_BUILD_TYPE=Debug \
        -DBUILD_SHARED_LIBS=ON \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
        -DLIBTCOD_SDL3=OFF \
        -DLIBTCOD_LODEPNG=vendored \
        -DLIBTCOD_STB=vendored \
        -DLIBTCOD_UTF8PROC=vendored \
        -DLIBTCOD_SAMPLES=OFF \
        -DLIBTCOD_TESTS=OFF \
        "${CMAKE_EXTRA_FLAGS[@]}"
    echo "Configuration complete."
else
    echo "Makefile exists, skipping configure (use --clean to reconfigure)."
fi

echo "Building libtcod-headless (-j$JOBS)..."
make -j"$JOBS"

BUILT_LIB=""
for candidate in "$BUILD_DIR/libtcod.so" "$BUILD_DIR/libtcod"*.so*; do
    if [ -f "$candidate" ] && [ ! -L "$candidate" ]; then
        BUILT_LIB="$candidate"
        break
    fi
done

if [ -z "$BUILT_LIB" ]; then
    echo "ERROR: Could not find built libtcod.so in $BUILD_DIR"
    echo "Contents:"
    ls -la "$BUILD_DIR"/libtcod* 2>/dev/null || echo "  (no libtcod files found)"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

BASENAME="$(basename "$BUILT_LIB")"
echo "Copying $BUILT_LIB -> $OUTPUT_DIR/$BASENAME"
cp "$BUILT_LIB" "$OUTPUT_DIR/$BASENAME"

cd "$OUTPUT_DIR"
for link_name in libtcod.so libtcod.so.2 libtcod.so.2.2; do
    if [ "$link_name" != "$BASENAME" ]; then
        ln -sf "$BASENAME" "$link_name"
    fi
done

echo ""
echo "=== Instrumented libtcod build complete ==="
echo "  Mode:    $MODE"
echo "  Library: $OUTPUT_DIR/$BASENAME"
echo "  Size:    $(du -h "$OUTPUT_DIR/$BASENAME" | cut -f1)"
echo ""
echo "'make asan' uses __lib_asan/, 'make fuzz-build' __lib_fuzz/ and 'make tsan'"
echo "__lib_tsan/ ahead of __lib/; re-run cmake in that build (or its make target)."
