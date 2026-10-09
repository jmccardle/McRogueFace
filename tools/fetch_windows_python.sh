#!/usr/bin/env bash
# Stage the Windows CPython runtime for MinGW cross-builds (`make windows`).
#
# Downloads python.org's embeddable amd64 package for the version pinned in
# modules/cpython (Include/patchlevel.h), unpacks it into __lib_windows/, and
# generates the MinGW import library libpython3XX.a from the DLL's export
# table. Headers come from modules/cpython (Include/ + PC/pyconfig.h), so the
# pin and the DLL must be the same version -- that is what this script keeps
# in sync.
#
# Usage: tools/fetch_windows_python.sh
#
# Files from a previously staged, different CPython version (python3YY.dll,
# .zip, ._pth, .def, libpython3YY.a) are removed: the *.pyd modules unpacked
# here only load against this version's DLL.
#
# Requires: curl, unzip, x86_64-w64-mingw32-objdump, x86_64-w64-mingw32-dlltool
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/__lib_windows"
PATCHLEVEL="$ROOT/modules/cpython/Include/patchlevel.h"
OBJDUMP="${OBJDUMP:-x86_64-w64-mingw32-objdump}"
DLLTOOL="${DLLTOOL:-x86_64-w64-mingw32-dlltool}"

[ $# -eq 0 ] || { sed -n '2,15p' "$0"; exit 2; }

[ -f "$PATCHLEVEL" ] || { echo "error: $PATCHLEVEL missing (git submodule update --init modules/cpython)" >&2; exit 1; }
for tool in curl unzip "$OBJDUMP" "$DLLTOOL"; do
    command -v "$tool" >/dev/null || { echo "error: $tool not found" >&2; exit 1; }
done

# "3.15.0rc3" -> release dir "3.15.0", file version "3.15.0rc3", nodot "315"
PY_VERSION="$(sed -n 's/^#define PY_VERSION[[:space:]]*"\([^"]*\)".*/\1/p' "$PATCHLEVEL")"
[ -n "$PY_VERSION" ] || { echo "error: could not read PY_VERSION from $PATCHLEVEL" >&2; exit 1; }
PY_VERSION="${PY_VERSION%+}"   # a dev checkout appends '+'; there is no such download
PY_RELEASE="$(echo "$PY_VERSION" | sed 's/^\([0-9]*\.[0-9]*\.[0-9]*\).*/\1/')"
PY_NODOT="$(echo "$PY_VERSION" | sed 's/^\([0-9]*\)\.\([0-9]*\).*/\1\2/')"

ZIP="python-${PY_VERSION}-embed-amd64.zip"
URL="https://www.python.org/ftp/python/${PY_RELEASE}/${ZIP}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Fetching $URL"
curl -fsSL --retry 3 -o "$TMP/$ZIP" "$URL" || {
    echo "error: download failed. modules/cpython is at $PY_VERSION; python.org publishes" >&2
    echo "       embeddable packages only for tagged releases." >&2
    exit 1
}

mkdir -p "$DEST"
for stale in "$DEST"/python3[0-9]*.{dll,zip,_pth,def} "$DEST"/python3[0-9]*_exports.txt "$DEST"/libpython3[0-9]*.a; do
    case "$(basename "$stale")" in
        python${PY_NODOT}[._]*|libpython${PY_NODOT}.a) ;;
        *) [ -e "$stale" ] && { echo "Removing stale $(basename "$stale")"; rm -f "$stale"; } ;;
    esac
done

unzip -q -o "$TMP/$ZIP" -d "$DEST"
DLL="$DEST/python${PY_NODOT}.dll"
[ -f "$DLL" ] || { echo "error: $ZIP did not contain python${PY_NODOT}.dll" >&2; exit 1; }

# Import library: export names from the PE export table -> .def -> dlltool.
"$OBJDUMP" -p "$DLL" | awk '
    /\[Ordinal\/Name Pointer\] Table/ { in_table = 1; next }
    in_table && /^[[:space:]]*\[/      { print $NF; next }
    in_table && NF == 0                { in_table = 0 }
' > "$DEST/python${PY_NODOT}_exports.txt"
NEXPORTS="$(wc -l < "$DEST/python${PY_NODOT}_exports.txt")"
[ "$NEXPORTS" -gt 1000 ] || { echo "error: only $NEXPORTS exports parsed from $DLL" >&2; exit 1; }

{ echo "LIBRARY python${PY_NODOT}.dll"; echo "EXPORTS"; sed 's/^/    /' "$DEST/python${PY_NODOT}_exports.txt"; } \
    > "$DEST/python${PY_NODOT}.def"
"$DLLTOOL" -d "$DEST/python${PY_NODOT}.def" -D "python${PY_NODOT}.dll" -l "$DEST/libpython${PY_NODOT}.a"

echo "Staged CPython $PY_VERSION for Windows in __lib_windows/ ($NEXPORTS exports -> libpython${PY_NODOT}.a)"
