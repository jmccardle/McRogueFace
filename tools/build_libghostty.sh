#!/usr/bin/env bash
#
# Build libghostty-vt (Ghostty's terminal emulator core, MIT) from modules/ghostty as a
# STATIC library for one target, and stage it where CMakeLists.txt looks for it. Called by
# build_deps.sh, build_deps_windows.sh and build_deps_wasm.sh; also usable alone.
#
# Usage:
#   tools/build_libghostty.sh native    # -> __lib_static/ghostty-vt/{include,lib}
#   tools/build_libghostty.sh windows   # -> __lib_windows/ghostty-vt/{include,lib}  (x86_64-windows-gnu)
#   tools/build_libghostty.sh wasm      # -> __lib_wasm/ghostty-vt/{include,lib}     (wasm32-emscripten)
#   add --clean to rebuild; --zig-only to just provision Zig and print its path
#
# Why not in __lib/: the build copies all of __lib/ next to the executable and packages it.
# libghostty-vt is linked statically, so its archive is a build input, not a runtime file.
#
# Zig: libghostty-vt is built with Zig, and the build stops on anything but 0.17.x; we pin
# 0.17.1 exactly. In order: $ZIG (must be exactly ZIG_VERSION), a `zig` on PATH that is
# exactly ZIG_VERSION, else the official tarball is downloaded into build-deps/ (gitignored),
# checked against a pinned sha256 (from ziglang.org/download/index.json) and unpacked. Any
# other Zig version is an error: there is no fallback to a different compiler.
#
# Network: Ghostty's Zig package dependencies are fetched over https into
# build-deps/zig-global-cache and modules/ghostty/zig-pkg (gitignored) during this step, so
# the engine build proper needs none. Set ZIG_GLOBAL_CACHE_DIR to relocate the cache (CI
# caches it).
#
# Rebuilt when the submodule commit or this script changes (a stamp beside the output).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ZIG_VERSION=0.17.1
ZIG_SHA256=3581863e3cbcfd0fce0efc682ce7e9e93da96668a977791d356a26d2a7e9b17a  # x86_64-linux, ziglang.org/download/index.json
ZIG_ARCHIVE="zig-x86_64-linux-$ZIG_VERSION.tar.xz"
ZIG_URL="https://ziglang.org/download/$ZIG_VERSION/$ZIG_ARCHIVE"

DEPS_DIR="$ROOT/build-deps"
export ZIG_GLOBAL_CACHE_DIR="${ZIG_GLOBAL_CACHE_DIR:-$DEPS_DIR/zig-global-cache}"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "=== $* ==="; }

TARGET=""; CLEAN=0; ZIG_ONLY=0
for arg in "$@"; do
    case "$arg" in
        native|windows|wasm) TARGET="$arg" ;;
        --clean) CLEAN=1 ;;
        --zig-only) ZIG_ONLY=1 ;;
        --help|-h) sed -n '2,29p' "$0"; exit 0 ;;
        *) die "unknown argument: $arg" ;;
    esac
done

# --- Zig --------------------------------------------------------------------
zig_version_of() { "$1" version 2>/dev/null || true; }

provision_zig() {
    if [ -n "${ZIG:-}" ]; then
        [ -x "$ZIG" ] || die "ZIG=$ZIG is not an executable file"
        [ "$(zig_version_of "$ZIG")" = "$ZIG_VERSION" ] \
            || die "ZIG=$ZIG is Zig '$(zig_version_of "$ZIG")'; libghostty-vt needs exactly $ZIG_VERSION"
        return
    fi
    if command -v zig >/dev/null 2>&1; then
        local found; found="$(command -v zig)"
        [ "$(zig_version_of "$found")" = "$ZIG_VERSION" ] \
            || die "$found is Zig '$(zig_version_of "$found")'; libghostty-vt needs exactly $ZIG_VERSION. Put Zig $ZIG_VERSION first on PATH, set ZIG=/path/to/zig, or remove that zig and this script will download $ZIG_VERSION into build-deps/"
        ZIG="$found"
        return
    fi
    local home="$DEPS_DIR/zig-$ZIG_VERSION" archive="$DEPS_DIR/dl/$ZIG_ARCHIVE"
    [ "$(uname -s)-$(uname -m)" = "Linux-x86_64" ] \
        || die "no zig on PATH, and the pinned download is x86_64 Linux only (this host: $(uname -s)-$(uname -m)); install Zig $ZIG_VERSION and set ZIG="
    if [ ! -x "$home/zig" ]; then
        command -v curl >/dev/null || die "curl not found"
        command -v sha256sum >/dev/null || die "sha256sum not found"
        command -v xz >/dev/null || die "xz not found (apt install xz-utils)"
        mkdir -p "$DEPS_DIR/dl"
        if [ ! -f "$archive" ]; then
            log "Downloading $ZIG_URL"
            rm -f "$archive.part"
            curl -fsSL -o "$archive.part" "$ZIG_URL"
            mv "$archive.part" "$archive"
        fi
        if ! echo "$ZIG_SHA256  $archive" | sha256sum -c - >/dev/null; then
            rm -f "$archive"
            die "$ZIG_ARCHIVE does not match its pinned sha256 $ZIG_SHA256; deleted it"
        fi
        rm -rf "$home" "$home.tmp"
        mkdir -p "$home.tmp"
        tar -xJf "$archive" -C "$home.tmp" --strip-components=1
        mv "$home.tmp" "$home"
    fi
    ZIG="$home/zig"
    [ "$(zig_version_of "$ZIG")" = "$ZIG_VERSION" ] || die "$ZIG reports '$(zig_version_of "$ZIG")', expected $ZIG_VERSION"
}

provision_zig
if [ "$ZIG_ONLY" -eq 1 ]; then echo "$ZIG"; exit 0; fi
[ -n "$TARGET" ] || die "usage: build_libghostty.sh native|windows|wasm [--clean]"

# --- Target -----------------------------------------------------------------
case "$TARGET" in
    native)  DEST="$ROOT/__lib_static/ghostty-vt"
             ZIG_ARGS=(-Doptimize=ReleaseFast) ;;
    windows) DEST="$ROOT/__lib_windows/ghostty-vt"
             ZIG_ARGS=(-Dtarget=x86_64-windows-gnu -Doptimize=ReleaseFast) ;;
    wasm)    DEST="$ROOT/__lib_wasm/ghostty-vt"
             ZIG_ARGS=(-Dtarget=wasm32-emscripten -Dcpu=generic -Doptimize=ReleaseFast) ;;
esac
ARCHIVE_NAME="libghostty-vt.a"
[ "$TARGET" = windows ] && ARCHIVE_NAME="ghostty-vt-static.lib"

cd "$ROOT"
log "Submodule modules/ghostty"
git submodule update --init --depth 1 modules/ghostty
SRC="$ROOT/modules/ghostty"
[ -f "$SRC/build.zig" ] || die "modules/ghostty is not checked out"

STAMP_FILE="$DEST/.stamp"
STAMP="$(git -C "$SRC" rev-parse HEAD) zig-$ZIG_VERSION $(sha256sum "$0" | cut -c1-16)"
if [ "$CLEAN" -eq 0 ] && [ -f "$STAMP_FILE" ] && [ "$(cat "$STAMP_FILE")" = "$STAMP" ] \
        && [ -f "$DEST/lib/$ARCHIVE_NAME" ] && [ -f "$DEST/include/ghostty/vt.h" ]; then
    log "libghostty-vt ($TARGET) already staged (skip)"
    exit 0
fi

log "libghostty-vt ($TARGET), Zig $ZIG_VERSION"
mkdir -p "$ZIG_GLOBAL_CACHE_DIR"
rm -rf "$DEST"
PREFIX="$DEPS_DIR/ghostty-prefix-$TARGET"
CACHE="$DEPS_DIR/ghostty-cache-$TARGET"
rm -rf "$PREFIX"
[ "$CLEAN" -eq 1 ] && rm -rf "$CACHE"
# Only the static archive and the headers are staged: the same build also emits a shared
# library the engine does not use.
LOG="$DEPS_DIR/ghostty-$TARGET.log"
mkdir -p "$DEPS_DIR"
(cd "$SRC" && "$ZIG" build -Demit-lib-vt "${ZIG_ARGS[@]}" \
    --prefix "$PREFIX" --cache-dir "$CACHE") > "$LOG" 2>&1 \
    || { tail -40 "$LOG"; die "zig build failed (full log: $LOG)"; }

mkdir -p "$DEST/lib" "$DEST/include"
[ -f "$PREFIX/lib/$ARCHIVE_NAME" ] || { ls -R "$PREFIX" >&2; die "zig build did not produce lib/$ARCHIVE_NAME"; }
cp "$PREFIX/lib/$ARCHIVE_NAME" "$DEST/lib/"
cp -a "$PREFIX/include/ghostty" "$DEST/include/"
[ -f "$DEST/include/ghostty/vt.h" ] || die "headers not staged: include/ghostty/vt.h missing"
echo "$STAMP" > "$STAMP_FILE"
echo "libghostty-vt staged in $DEST ($(du -h "$DEST/lib/$ARCHIVE_NAME" | cut -f1))"
