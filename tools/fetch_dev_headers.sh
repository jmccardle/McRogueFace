#!/usr/bin/env bash
#
# Unpack the -dev packages McRogueFace's dependencies need into a local prefix,
# for machines where you can't `sudo apt install` them (Debian/Ubuntu only).
#
# Usage:
#   tools/fetch_dev_headers.sh [SYSROOT]     # default: build-sysroot/
#   export MCRF_SYSROOT=$PWD/build-sysroot  # then: make deps && make
#
# -dev packages are only headers plus unversioned .so symlinks; the runtime
# libraries they point at must already be installed (they normally are on any
# desktop/X11 machine). The symlinks are re-pointed at /usr/lib/<multiarch>.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SYSROOT="$(realpath -m "${1:-$PROJECT_ROOT/build-sysroot}")"
MULTIARCH="$(gcc -print-multiarch 2>/dev/null || echo x86_64-linux-gnu)"

PACKAGES=(
    # SFML: window/graphics
    libx11-dev libxrandr-dev libxcursor-dev libxrender-dev libxext-dev libxfixes-dev
    libxi-dev x11proto-dev libxcb1-dev libxau-dev libxdmcp-dev libudev-dev
    libgl-dev libglx-dev libopengl-dev libegl-dev
    libfreetype-dev libpng-dev libbrotli-dev
    # SFML: audio
    libopenal-dev libflac-dev libogg-dev libvorbis-dev
    # CPython optional modules (_zstd, _uuid)
    libzstd-dev uuid-dev
)

command -v apt-get >/dev/null || { echo "ERROR: apt-get not found (Debian/Ubuntu only)"; exit 1; }

mkdir -p "$SYSROOT/debs"
cd "$SYSROOT/debs"
echo "Downloading ${#PACKAGES[@]} -dev packages into $SYSROOT/debs ..."
apt-get download "${PACKAGES[@]}" > download.log 2>&1 || { tail -20 download.log; exit 1; }
for f in *.deb; do dpkg -x "$f" "$SYSROOT"; done

LIBDIR="$SYSROOT/usr/lib/$MULTIARCH"
cd "$LIBDIR"
rm -f ./*.a
missing=0
for l in *.so; do
    t="$(readlink "$l" || true)"
    [ -z "$t" ] || [ -e "$t" ] && continue
    if [ -e "/usr/lib/$MULTIARCH/$t" ]; then
        ln -sf "/usr/lib/$MULTIARCH/$t" "$l"
    else
        echo "WARNING: runtime library for $l ($t) is not installed"
        missing=1
    fi
done

echo
echo "Dev headers unpacked to $SYSROOT"
echo "Use with:  export MCRF_SYSROOT=$SYSROOT"
[ "$missing" -eq 0 ] || echo "Some runtime libraries are missing (see warnings); their features may not build."
