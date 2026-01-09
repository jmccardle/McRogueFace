#!/bin/bash
#
# McRogueFace Distribution Packager
#
# Creates clean distribution packages for Windows and Linux
# Supports light (minimal stdlib) and full (complete stdlib) variants
#
# Usage:
#   ./tools/package.sh windows light    # Windows light build
#   ./tools/package.sh windows full     # Windows full build
#   ./tools/package.sh linux light      # Linux light build
#   ./tools/package.sh linux full       # Linux full build
#   ./tools/package.sh all              # All variants
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"

# Version from git or default
VERSION=$(cd "$PROJECT_ROOT" && git describe --tags --always 2>/dev/null || echo "dev")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Files and directories to exclude from distribution
EXCLUDE_PATTERNS=(
    "CMakeFiles"
    "CMakeCache.txt"
    "cmake_install.cmake"
    "Makefile"
    "*.o"
    "*.obj"
    ".git"
    ".gitignore"
    "__pycache__"
    "*.pyc"
    "*.pyo"
)

# Platform-specific excludes
WINDOWS_EXCLUDES=(
    "*.so"
    "*.so.*"
    "lib.linux-*"
)

LINUX_EXCLUDES=(
    "*.dll"
    "*.exe"
    "*.pdb"
)

check_build_exists() {
    local platform=$1
    local build_dir

    if [ "$platform" = "windows" ]; then
        build_dir="$PROJECT_ROOT/build-windows"
        if [ ! -f "$build_dir/mcrogueface.exe" ]; then
            log_error "Windows build not found. Run 'make windows' first."
            return 1
        fi
    else
        build_dir="$PROJECT_ROOT/build"
        if [ ! -f "$build_dir/mcrogueface" ]; then
            log_error "Linux build not found. Run 'make' first."
            return 1
        fi
    fi
    return 0
}

create_stdlib_zip() {
    local platform=$1
    local preset=$2
    local output_dir=$3

    log_info "Creating stdlib zip: platform=$platform preset=$preset"

    # Use Python 3 to run our stdlib packager
    python3 "$SCRIPT_DIR/package_stdlib.py" \
        --platform "$platform" \
        --preset "$preset" \
        --output "$output_dir"
}

package_windows() {
    local preset=$1
    local build_dir="$PROJECT_ROOT/build-windows"
    local package_name="McRogueFace-${VERSION}-Windows-${preset}"
    local package_dir="$DIST_DIR/$package_name"

    log_info "Packaging Windows ($preset): $package_name"

    # Check build exists
    check_build_exists windows || return 1

    # Clean and create package directory
    rm -rf "$package_dir"
    mkdir -p "$package_dir"

    # Copy executable
    cp "$build_dir/mcrogueface.exe" "$package_dir/"

    # Copy DLLs (excluding build artifacts)
    for dll in "$build_dir"/*.dll; do
        [ -f "$dll" ] && cp "$dll" "$package_dir/"
    done

    # Copy assets
    if [ -d "$build_dir/assets" ]; then
        cp -r "$build_dir/assets" "$package_dir/"
    fi

    # Copy scripts
    if [ -d "$build_dir/scripts" ]; then
        cp -r "$build_dir/scripts" "$package_dir/"
    fi

    # Copy Python stdlib directory structure (same as Linux)
    # Python home is set to <exe>/lib/Python, so stdlib must be there
    mkdir -p "$package_dir/lib/Python"

    # Copy the Lib directory from build (matches Linux structure)
    if [ -d "$build_dir/lib/Python/Lib" ]; then
        log_info "Copying Python stdlib (preset: $preset)"
        cp -r "$build_dir/lib/Python/Lib" "$package_dir/lib/Python/"

        # Remove test directories and other excludes to save space
        rm -rf "$package_dir/lib/Python/Lib/test"
        rm -rf "$package_dir/lib/Python/Lib/tests"
        rm -rf "$package_dir/lib/Python/Lib/idlelib"
        rm -rf "$package_dir/lib/Python/Lib/tkinter"
        rm -rf "$package_dir/lib/Python/Lib/turtledemo"
        rm -rf "$package_dir/lib/Python/Lib/pydoc_data"
        rm -rf "$package_dir/lib/Python/Lib/lib2to3"
        rm -rf "$package_dir/lib/Python/Lib/ensurepip"
        rm -rf "$package_dir/lib/Python/Lib/_pyrepl"
        find "$package_dir/lib/Python/Lib" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        find "$package_dir/lib/Python/Lib" -name "*.pyc" -delete 2>/dev/null || true
        find "$package_dir/lib/Python/Lib" -name "test_*.py" -delete 2>/dev/null || true
        find "$package_dir/lib/Python/Lib" -name "*_test.py" -delete 2>/dev/null || true
    fi

    # Also copy python314.zip for backwards compatibility (some deployments use it)
    if [ -f "$build_dir/python314.zip" ]; then
        cp "$build_dir/python314.zip" "$package_dir/"
    fi

    # Create the distribution archive
    log_info "Creating archive: ${package_name}.zip"
    (cd "$DIST_DIR" && zip -r "${package_name}.zip" "$package_name")

    # Report size
    local size=$(du -h "$DIST_DIR/${package_name}.zip" | cut -f1)
    log_info "Created: $DIST_DIR/${package_name}.zip ($size)"

    # Cleanup uncompressed directory
    rm -rf "$package_dir"
}

package_linux() {
    local preset=$1
    local build_dir="$PROJECT_ROOT/build"
    local package_name="McRogueFace-${VERSION}-Linux-${preset}"
    local package_dir="$DIST_DIR/$package_name"

    log_info "Packaging Linux ($preset): $package_name"

    # Check build exists
    check_build_exists linux || return 1

    # Clean and create package directory
    rm -rf "$package_dir"
    mkdir -p "$package_dir"
    mkdir -p "$package_dir/lib"

    # Copy executable
    cp "$build_dir/mcrogueface" "$package_dir/"

    # Copy shared libraries from __lib (not from build dir which has artifacts)
    if [ -d "$PROJECT_ROOT/__lib" ]; then
        # Copy only essential runtime libraries (not test modules)
        # Core libraries: libpython, libsfml-*, libtcod
        for lib in libpython3.14.so.1.0 libsfml-graphics.so.2.6.1 libsfml-window.so.2.6.1 \
                   libsfml-system.so.2.6.1 libsfml-audio.so.2.6.1 libtcod.so; do
            [ -f "$PROJECT_ROOT/__lib/$lib" ] && cp "$PROJECT_ROOT/__lib/$lib" "$package_dir/lib/"
        done

        # Create necessary symlinks
        (cd "$package_dir/lib" && \
            ln -sf libpython3.14.so.1.0 libpython3.14.so && \
            ln -sf libsfml-graphics.so.2.6.1 libsfml-graphics.so.2.6 && \
            ln -sf libsfml-graphics.so.2.6.1 libsfml-graphics.so && \
            ln -sf libsfml-window.so.2.6.1 libsfml-window.so.2.6 && \
            ln -sf libsfml-window.so.2.6.1 libsfml-window.so && \
            ln -sf libsfml-system.so.2.6.1 libsfml-system.so.2.6 && \
            ln -sf libsfml-system.so.2.6.1 libsfml-system.so && \
            ln -sf libsfml-audio.so.2.6.1 libsfml-audio.so.2.6 && \
            ln -sf libsfml-audio.so.2.6.1 libsfml-audio.so)

        # Copy Python extension modules to correct location (excluding test modules)
        # Must match structure: lib/Python/lib.linux-x86_64-3.14/
        local pylib_dir="$PROJECT_ROOT/__lib/Python/lib.linux-x86_64-3.14"
        if [ -d "$pylib_dir" ]; then
            mkdir -p "$package_dir/lib/Python/lib.linux-x86_64-3.14"
            for so in "$pylib_dir"/*.so; do
                local basename=$(basename "$so")
                # Skip test modules
                case "$basename" in
                    *test*|xxlimited*|_ctypes_test*|_xxtestfuzz*)
                        continue
                        ;;
                    *)
                        cp "$so" "$package_dir/lib/Python/lib.linux-x86_64-3.14/"
                        ;;
                esac
            done
        fi
    fi

    # Copy assets
    if [ -d "$build_dir/assets" ]; then
        cp -r "$build_dir/assets" "$package_dir/"
    fi

    # Copy scripts
    if [ -d "$build_dir/scripts" ]; then
        cp -r "$build_dir/scripts" "$package_dir/"
    fi

    # Copy Python stdlib directory
    # Python home is set to <exe>/lib/Python, stdlib must be in lib/Python/Lib/
    mkdir -p "$package_dir/lib/Python"

    # Copy the Lib directory from __lib/Python/Lib (filtered by preset)
    if [ -d "$PROJECT_ROOT/__lib/Python/Lib" ]; then
        log_info "Copying Python stdlib (preset: $preset)"

        # For now, copy entire Lib - filtering happens via package_stdlib.py for zip
        # TODO: Implement directory-based filtering for light preset
        cp -r "$PROJECT_ROOT/__lib/Python/Lib" "$package_dir/lib/Python/"

        # Remove test directories and other excludes to save space
        rm -rf "$package_dir/lib/Python/Lib/test"
        rm -rf "$package_dir/lib/Python/Lib/tests"
        rm -rf "$package_dir/lib/Python/Lib/idlelib"
        rm -rf "$package_dir/lib/Python/Lib/tkinter"
        rm -rf "$package_dir/lib/Python/Lib/turtledemo"
        rm -rf "$package_dir/lib/Python/Lib/pydoc_data"
        rm -rf "$package_dir/lib/Python/Lib/lib2to3"
        rm -rf "$package_dir/lib/Python/Lib/ensurepip"
        rm -rf "$package_dir/lib/Python/Lib/_pyrepl"
        find "$package_dir/lib/Python/Lib" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        find "$package_dir/lib/Python/Lib" -name "*.pyc" -delete 2>/dev/null || true
        find "$package_dir/lib/Python/Lib" -name "test_*.py" -delete 2>/dev/null || true
        find "$package_dir/lib/Python/Lib" -name "*_test.py" -delete 2>/dev/null || true
    fi

    # Create run script
    cat > "$package_dir/run.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="$SCRIPT_DIR/lib:$LD_LIBRARY_PATH"
exec "$SCRIPT_DIR/mcrogueface" "$@"
EOF
    chmod +x "$package_dir/run.sh"

    # Create the distribution archive
    log_info "Creating archive: ${package_name}.tar.gz"
    (cd "$DIST_DIR" && tar -czf "${package_name}.tar.gz" "$package_name")

    # Report size
    local size=$(du -h "$DIST_DIR/${package_name}.tar.gz" | cut -f1)
    log_info "Created: $DIST_DIR/${package_name}.tar.gz ($size)"

    # Cleanup uncompressed directory
    rm -rf "$package_dir"
}

show_usage() {
    echo "McRogueFace Distribution Packager"
    echo ""
    echo "Usage: $0 <platform> <preset>"
    echo ""
    echo "Platforms:"
    echo "  windows    - Windows build (requires 'make windows' first)"
    echo "  linux      - Linux build (requires 'make' first)"
    echo "  all        - Build all variants"
    echo ""
    echo "Presets:"
    echo "  light      - Minimal stdlib (~2-3 MB)"
    echo "  full       - Complete stdlib (~8-10 MB)"
    echo ""
    echo "Examples:"
    echo "  $0 windows light     # Small Windows package"
    echo "  $0 linux full        # Full Linux package"
    echo "  $0 all               # All platform/preset combinations"
}

main() {
    local platform=${1:-}
    local preset=${2:-full}

    # Create dist directory
    mkdir -p "$DIST_DIR"

    case "$platform" in
        windows)
            package_windows "$preset"
            ;;
        linux)
            package_linux "$preset"
            ;;
        all)
            log_info "Building all distribution variants..."
            package_windows light || true
            package_windows full || true
            package_linux light || true
            package_linux full || true
            log_info "All packages created in $DIST_DIR"
            ls -lh "$DIST_DIR"/*.zip "$DIST_DIR"/*.tar.gz 2>/dev/null || true
            ;;
        -h|--help|"")
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown platform: $platform"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
