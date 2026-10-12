#!/bin/sh
# Print the engine version: the MCRFPY_VERSION string in src/McRogueFaceVersion.h.
#
# That header is the only source of truth for the version, "-dev" suffix included
# (#475): master says "0.3.1-dev" between releases and a release commit drops the
# suffix. Nothing derives the version from git tags.
set -e
HEADER="$(cd "$(dirname "$0")/.." && pwd)/src/McRogueFaceVersion.h"
v=$(sed -n 's/^#define MCRFPY_VERSION "\(.*\)"$/\1/p' "$HEADER")
if [ -z "$v" ]; then
    echo "version.sh: no MCRFPY_VERSION in $HEADER" >&2
    exit 1
fi
echo "$v"
