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
#   add --clean to rebuild from scratch; --zig-only to just provision Zig and print its path
#
# Why not in __lib/: the build copies all of __lib/ next to the executable and packages it.
# libghostty-vt is linked statically, so its archive is a build input, not a runtime file.
#
# Target CPU: the native archive is built for the baseline of the host's architecture
# (x86_64 or aarch64, glibc), never for the build machine's own CPU: a cached or packaged
# archive must run on other machines. All targets are built with -Dstrip=true (no debug
# info, no build-host paths in the shipped binary).
#
# Zig: libghostty-vt is built with Zig, and its build stops on anything but 0.17.x; we pin
# 0.17.1 exactly. In order:
#   1. $ZIG (a path, or a bare name looked up on PATH): must be exactly ZIG_VERSION, else error.
#   2. a `zig` on PATH that is exactly ZIG_VERSION.
#   3. otherwise (including a PATH zig of another version, which is ignored with a message)
#      the official x86_64-Linux tarball is downloaded into build-deps/ (gitignored),
#      checked against a pinned sha256 (from ziglang.org/download/index.json) and unpacked.
# Nothing falls back to a different Zig version. Zig is only needed when a build is due: an
# up-to-date staged archive (stamp) is accepted without touching Zig or the network.
#
# Network: Ghostty's Zig package dependencies are fetched over https during the build.
# `zig build --fetch` does not pull the lazy dependencies this target needs (they are only
# resolved while the build runs), so the fetch is not a separate step: the zig build is run
# up to 3 times, and a failed run is repeated ONLY when its log shows a network-fetch error
# (each failure is printed). Packages already fetched are kept between runs, so a repeat
# resumes. Any other failure is final. Caches, all under build-deps/ (gitignored; nothing is
# written inside modules/ghostty): zig-global-cache (or $ZIG_GLOBAL_CACHE_DIR), zig-pkg
# (fetched packages), ghostty-cache-<target>. CI caches build-deps/dl, zig-global-cache and
# zig-pkg; a warm run does no network fetches.
#
# Rebuilt when the submodule commit, the target flags, Zig's version or this script change
# (a stamp beside the output). Uncommitted edits inside modules/ghostty do not change the
# stamp: use --clean after making them.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/build_libghostty.sh"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ZIG_VERSION=0.17.1
ZIG_SHA256=3581863e3cbcfd0fce0efc682ce7e9e93da96668a977791d356a26d2a7e9b17a  # x86_64-linux, ziglang.org/download/index.json
ZIG_ARCHIVE="zig-x86_64-linux-$ZIG_VERSION.tar.xz"
ZIG_URL="https://ziglang.org/download/$ZIG_VERSION/$ZIG_ARCHIVE"

DEPS_DIR="$ROOT/build-deps"
export ZIG_GLOBAL_CACHE_DIR="${ZIG_GLOBAL_CACHE_DIR:-$DEPS_DIR/zig-global-cache}"
FETCH_TRIES=3

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "=== $* ==="; }

TARGET=""; CLEAN=0; ZIG_ONLY=0
for arg in "$@"; do
    case "$arg" in
        native|windows|wasm) TARGET="$arg" ;;
        --clean) CLEAN=1 ;;
        --zig-only) ZIG_ONLY=1 ;;
        --help|-h) sed -n '2,43p' "$0"; exit 0 ;;
        *) die "unknown argument: $arg" ;;
    esac
done

# --- Zig --------------------------------------------------------------------
zig_version_of() { "$1" version 2>/dev/null || true; }

provision_zig() {
    if [ -n "${ZIG:-}" ]; then
        local explicit; explicit="$(command -v "$ZIG" || true)"
        [ -n "$explicit" ] && [ -x "$explicit" ] || die "ZIG=$ZIG is not an executable file or a command on PATH"
        [ "$(zig_version_of "$explicit")" = "$ZIG_VERSION" ] \
            || die "ZIG=$ZIG is Zig '$(zig_version_of "$explicit")'; libghostty-vt needs exactly $ZIG_VERSION"
        ZIG="$explicit"
        return
    fi
    if command -v zig >/dev/null 2>&1; then
        local found; found="$(command -v zig)"
        if [ "$(zig_version_of "$found")" = "$ZIG_VERSION" ]; then
            ZIG="$found"
            return
        fi
        echo "note: ignoring $found (Zig '$(zig_version_of "$found")'); libghostty-vt needs exactly $ZIG_VERSION, using the pinned download"
    fi
    local home="$DEPS_DIR/zig-$ZIG_VERSION" archive="$DEPS_DIR/dl/$ZIG_ARCHIVE"
    [ "$(uname -s)-$(uname -m)" = "Linux-x86_64" ] \
        || die "no Zig $ZIG_VERSION on PATH, and the pinned download is x86_64 Linux only (this host: $(uname -s)-$(uname -m)); install Zig $ZIG_VERSION and set ZIG="
    if [ ! -x "$home/zig" ]; then
        command -v curl >/dev/null || die "curl not found"
        command -v sha256sum >/dev/null || die "sha256sum not found"
        command -v xz >/dev/null || die "xz not found (apt install xz-utils)"
        mkdir -p "$DEPS_DIR/dl"
        if [ ! -f "$archive" ]; then
            log "Downloading $ZIG_URL"
            rm -f "$archive.part"
            curl -fsSL --retry 3 --retry-delay 5 -o "$archive.part" "$ZIG_URL"
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

if [ "$ZIG_ONLY" -eq 1 ]; then provision_zig; echo "$ZIG"; exit 0; fi
[ -n "$TARGET" ] || die "usage: build_libghostty.sh native|windows|wasm [--clean]"

# --- Target -----------------------------------------------------------------
ARCHIVE_NAME="libghostty-vt.a"
case "$TARGET" in
    native)
        case "$(uname -m)" in
            x86_64|aarch64) ARCH="$(uname -m)" ;;
            *) die "unsupported host architecture $(uname -m) (x86_64 and aarch64 only)" ;;
        esac
        DEST="$ROOT/__lib_static/ghostty-vt"
        ZIG_ARGS=("-Dtarget=$ARCH-linux-gnu" -Dcpu=baseline -Dstrip=true -Doptimize=ReleaseFast) ;;
    windows)
        DEST="$ROOT/__lib_windows/ghostty-vt"
        ARCHIVE_NAME="ghostty-vt-static.lib"
        ZIG_ARGS=(-Dtarget=x86_64-windows-gnu -Dcpu=baseline -Dstrip=true -Doptimize=ReleaseFast) ;;
    wasm)
        DEST="$ROOT/__lib_wasm/ghostty-vt"
        ZIG_ARGS=(-Dtarget=wasm32-emscripten -Dcpu=generic -Dstrip=true -Doptimize=ReleaseFast) ;;
esac

cd "$ROOT"
log "Submodule modules/ghostty"
git submodule update --init --depth 1 modules/ghostty
SRC="$ROOT/modules/ghostty"
[ -f "$SRC/build.zig" ] || die "modules/ghostty is not checked out"

# Checked before Zig is provisioned: an up-to-date archive needs neither Zig nor the network.
STAMP_FILE="$DEST/.stamp"
STAMP="$(git -C "$SRC" rev-parse HEAD) zig-$ZIG_VERSION ${ZIG_ARGS[*]} $(sha256sum "$SCRIPT" | cut -c1-16)"
if [ "$CLEAN" -eq 0 ] && [ -f "$STAMP_FILE" ] && [ "$(cat "$STAMP_FILE")" = "$STAMP" ] \
        && [ -f "$DEST/lib/$ARCHIVE_NAME" ] && [ -f "$DEST/include/ghostty/vt.h" ]; then
    log "libghostty-vt ($TARGET) already staged (skip)"
    exit 0
fi

provision_zig
log "libghostty-vt ($TARGET), Zig $ZIG_VERSION"
PREFIX="$DEPS_DIR/ghostty-prefix-$TARGET"
CACHE="$DEPS_DIR/ghostty-cache-$TARGET"
PKGS="$DEPS_DIR/zig-pkg"
LOG="$DEPS_DIR/ghostty-$TARGET.log"
mkdir -p "$ZIG_GLOBAL_CACHE_DIR" "$PKGS"
rm -rf "$DEST" "$PREFIX"
[ "$CLEAN" -eq 1 ] && rm -rf "$CACHE"

# A network-fetch failure, as Zig reports it, not a compile error.
NET_ERR='error:.*(HTTP|ConnectionResetByPeer|ConnectionTimedOut|ConnectionRefused|NetworkUnreachable|TemporaryNameServerFailure|UnknownHostName|TlsInitializationFailed|UnexpectedConnectionFailure)'
ok=0
for try in $(seq 1 "$FETCH_TRIES"); do
    if (cd "$SRC" && "$ZIG" build -Demit-lib-vt "${ZIG_ARGS[@]}" \
            --prefix "$PREFIX" --cache-dir "$CACHE" --pkg-dir "$PKGS") > "$LOG" 2>&1; then
        ok=1; break
    fi
    if ! grep -qE "$NET_ERR" "$LOG"; then
        tail -40 "$LOG"; die "zig build failed (full log: $LOG)"
    fi
    echo "zig build: network error fetching dependencies (attempt $try of $FETCH_TRIES):" >&2
    grep -E "$NET_ERR" "$LOG" | head -3 >&2
    if [ "$try" -lt "$FETCH_TRIES" ]; then sleep $((try * 10)); fi
done
[ "$ok" -eq 1 ] || { tail -20 "$LOG"; die "zig build still failing on network errors after $FETCH_TRIES attempts (full log: $LOG)"; }

[ -f "$PREFIX/lib/$ARCHIVE_NAME" ] || { ls -R "$PREFIX" >&2; die "zig build did not produce lib/$ARCHIVE_NAME"; }

# --- Post-process the archive -------------------------------------------------
# Members are named by their absolute path in the build cache; repack them under their
# base names. On ELF/wasm targets Zig's compiler_rt member is dropped: it holds weak
# definitions of memcpy, memset, strlen, __stack_chk_fail, ... that the linker would bind
# the ENGINE's own calls to (bypassing libc, and the sanitizers' interceptors). What it
# also provides (128-bit integer and soft-float helpers) comes from libgcc / the toolchain.
# (A Windows .lib is left as built; see BUILD_FROM_SOURCE.md.)
STAGE="$DEPS_DIR/ghostty-repack-$TARGET"
rm -rf "$STAGE"; mkdir -p "$STAGE/x"
members="$("$ZIG" ar t "$PREFIX/lib/$ARCHIVE_NAME")"
dups="$(echo "$members" | sed 's#.*/##' | sort | uniq -d)"
[ -z "$dups" ] || die "archive has members with the same base name: $dups"
if [ "$TARGET" = windows ]; then
    cp "$PREFIX/lib/$ARCHIVE_NAME" "$STAGE/$ARCHIVE_NAME"
else
    (cd "$STAGE/x" && "$ZIG" ar x "$PREFIX/lib/$ARCHIVE_NAME")
    rm -f "$STAGE"/x/compiler_rt.o
    [ -z "$(ls "$STAGE/x" | grep -i 'compiler_rt' || true)" ] || die "compiler_rt member not removed"
    if [ "$TARGET" = native ]; then
        # The C++ members carry the build host's absolute paths (ELF file symbols);
        # dropping local symbols leaves everything the linker needs.
        command -v objcopy >/dev/null || die "objcopy not found (apt install binutils)"
        for o in "$STAGE"/x/*.o; do objcopy --strip-unneeded "$o"; done
    fi
    (cd "$STAGE/x" && "$ZIG" ar crs "$STAGE/$ARCHIVE_NAME" *)
fi

mkdir -p "$DEST/lib" "$DEST/include"
cp "$STAGE/$ARCHIVE_NAME" "$DEST/lib/"
cp -a "$PREFIX/include/ghostty" "$DEST/include/"
[ -f "$DEST/include/ghostty/vt.h" ] || die "headers not staged: include/ghostty/vt.h missing"
rm -rf "$STAGE"
echo "$STAMP" > "$STAMP_FILE"
echo "libghostty-vt staged in $DEST ($(du -h "$DEST/lib/$ARCHIVE_NAME" | cut -f1))"
