#!/bin/bash
#
# McRogueFace Distribution Packager
#
# Creates the engine's release packages for Windows and Linux. What goes into a package
# (the runtime) is defined once, in the mcrf_project module that ships with the engine
# (src/pylib/mcrf_project/runtime.py), and games are packaged by the same code
# (`mcrogueface -m mcrf_project dist`), so the two can't drift apart (#420).
#
# This script only supplies the release version and runs it with the Linux build's
# interpreter; that build must exist to package either platform.
#
# Usage:
#   ./tools/package.sh windows    # McRogueFace-<version>-Windows.zip
#   ./tools/package.sh linux      # McRogueFace-<version>-Linux.tar.gz
#   ./tools/package.sh all        # both
#
# There is one package per platform (#435): the whole stdlib minus the exclusions in
# runtime.py. There is no light/full split.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"
ENGINE="$PROJECT_ROOT/build/mcrogueface"

# The version header is the source of truth (#475), never a git tag.
VERSION=$("$SCRIPT_DIR/version.sh")

package() {
    local platform=$1 engine_dir
    case "$platform" in
        linux)   engine_dir="$PROJECT_ROOT/build" ;;
        windows) engine_dir="$PROJECT_ROOT/build-windows" ;;
    esac
    if [ ! -x "$ENGINE" ]; then
        echo "[ERROR] $ENGINE not found: packaging runs on the Linux build's interpreter. Run 'make' first." >&2
        return 1
    fi
    "$ENGINE" -m mcrf_project package-engine --engine "$engine_dir" \
        --version "$VERSION" --out "$DIST_DIR" --docs-from "$PROJECT_ROOT"
}

show_usage() {
    echo "McRogueFace Distribution Packager"
    echo ""
    echo "Usage: $0 <platform>"
    echo ""
    echo "Platforms: windows (needs 'make windows'), linux (needs 'make'), all"
}

case "${1:-}" in
    windows|linux)
        package "$1"
        ;;
    all)
        status=0
        for platform in windows linux; do
            package "$platform" || status=1
        done
        ls -lh "$DIST_DIR"/*.zip "$DIST_DIR"/*.tar.gz 2>/dev/null || true
        exit $status
        ;;
    -h|--help|"")
        show_usage
        ;;
    *)
        echo "[ERROR] Unknown platform: $1" >&2
        show_usage
        exit 1
        ;;
esac
