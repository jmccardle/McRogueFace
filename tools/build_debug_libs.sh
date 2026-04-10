#!/usr/bin/env bash
#
# Build libtcod-headless with sanitizer instrumentation.
#
# Usage:
#   tools/build_debug_libs.sh              # Build with debug symbols only
#   tools/build_debug_libs.sh --asan       # Build with AddressSanitizer
#   tools/build_debug_libs.sh --tsan       # Build with ThreadSanitizer
#   tools/build_debug_libs.sh --clean      # Remove build artifacts first
#
# Output: __lib_debug/libtcod.so (instrumented)
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
        --tsan)  MODE="tsan" ;;
        --clean) CLEAN=1 ;;
        --help|-h)
            echo "Usage: $0 [--asan|--tsan] [--clean]"
            echo ""
            echo "Flags:"
            echo "  (default)  Debug symbols only (-g -O1)"
            echo "  --asan     AddressSanitizer + UBSan instrumentation"
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
        echo "=== Building libtcod-headless with ASan + UBSan ==="
        ;;
    tsan)
        SANITIZER_FLAGS="-fsanitize=thread"
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

CMAKE_EXTRA_FLAGS=""
if [ -n "$SANITIZER_FLAGS" ]; then
    CMAKE_EXTRA_FLAGS="-DCMAKE_C_FLAGS=$SANITIZER_FLAGS -DCMAKE_CXX_FLAGS=$SANITIZER_FLAGS"
fi

if [ ! -f Makefile ]; then
    echo "Configuring libtcod-headless ($MODE)..."
    # shellcheck disable=SC2086
    cmake "$LIBTCOD_DIR" \
        -DCMAKE_BUILD_TYPE=Debug \
        -DBUILD_SHARED_LIBS=ON \
        $CMAKE_EXTRA_FLAGS
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
echo "The existing 'make asan' / 'make tsan' targets link __lib_debug/ first,"
echo "so the instrumented libtcod will be picked up automatically."
