#!/bin/bash
# Cut a McRogueFace release (#475):  make release VERSION=0.3.1 [NEXT_VERSION=0.3.2-dev]
#
# The version header (src/McRogueFaceVersion.h) is the only source of truth: between
# releases master says "0.3.1-dev", the release commit says "0.3.1", and the tag is
# applied LAST, so a tag only ever marks a commit that passed everything below.
#
#   1. check   clean master, tag free, the tools each step needs are present
#   2. bump    header -> VERSION, build
#   3. test    full suite + check-snippets
#   4. docs    docs + manifest, stamp snippets (verified=VERSION), snippet shots
#   5. package Linux, Windows, WASM -- each unpacked and run (tools/smoke_package.py)
#   6. commit  "Release VERSION": header, manifest, snippet stamps
#   7. tag     VERSION
#   8. site    reference + library pinned to the tag (left uncommitted for review)
#   9. bump    header -> NEXT_VERSION, commit
#
# The site is built at step 8, while the working tree is still the tag: after the
# bump the manifest says NEXT_VERSION.
#
# It never pushes and never publishes: those stay manual. A failure before step 7
# leaves an uncommitted, untagged tree; `git checkout .` resets it.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="${1:-}"
NEXT_VERSION="${2:-}"
SITE_DIR="${SITE_DIR:-$ROOT/../mcrogueface.github.io}"
HEADER=src/McRogueFaceVersion.h
STEP="setup"

die() { echo "release: $*" >&2; exit 1; }
step() { STEP="$1"; echo; echo "=== [$STEP] $2 ==="; }
on_error() {
    echo >&2
    echo "release: FAILED in step '$STEP'." >&2
    if git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null; then
        echo "  $VERSION is committed and tagged, and its packages are in dist/." >&2
        echo "  Finish by hand from step '$STEP': rebuild the site pinned to $VERSION" >&2
        echo "  (tools/build_reference.py; tools/build_library.py --ref $VERSION --snippet-ref $VERSION)," >&2
        echo "  then set the header to $NEXT_VERSION and commit \"Begin $NEXT_VERSION\"." >&2
    elif git log -1 --format=%s | grep -qx "Release $VERSION"; then
        echo "  'Release $VERSION' is committed but NOT tagged. Inspect it, then: git reset --hard HEAD~1" >&2
    else
        echo "  Nothing is committed or tagged. Reset with: git checkout ." >&2
    fi
}
trap on_error ERR

set_version() {
    sed -i "s|^#define MCRFPY_VERSION \".*\"$|#define MCRFPY_VERSION \"$1\"|" "$HEADER"
    [ "$(tools/version.sh)" = "$1" ] || die "could not set $HEADER to $1"
}

# A tracked-file view of the tree: submodules dirty themselves when built.
tracked_changes() { git status --porcelain --untracked-files=no | grep -v ' modules/' || true; }

[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] \
    || die "usage: make release VERSION=x.y.z [NEXT_VERSION=x.y.z-dev] (a release version has no suffix)"
if [ -z "$NEXT_VERSION" ]; then
    IFS=. read -r MAJ MIN PAT <<< "$VERSION"
    NEXT_VERSION="$MAJ.$MIN.$((PAT + 1))-dev"
fi
[[ "$NEXT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+-[0-9A-Za-z.]+$ ]] \
    || die "NEXT_VERSION ($NEXT_VERSION) must be a pre-release version such as 0.3.2-dev"

# --- 1. check ------------------------------------------------------------------------
step check "preflight for $VERSION (next: $NEXT_VERSION)"
CURRENT="$(tools/version.sh)"
[[ "$CURRENT" == *-dev ]] || die "the header says $CURRENT; master should say a -dev version between releases"
[ "$CURRENT" = "$VERSION-dev" ] || echo "note: releasing $VERSION from $CURRENT"
[ "$(git rev-parse --abbrev-ref HEAD)" = master ] || die "not on master"
[ -z "$(tracked_changes)" ] || { tracked_changes >&2; die "tracked files have uncommitted changes"; }
! git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null || die "tag $VERSION already exists"
BASE_REF="$(git describe --tags --abbrev=0 2>/dev/null)" || die "no previous release tag to measure the API delta from"
command -v emcmake >/dev/null || die "emcmake not found: source ~/emsdk/emsdk_env.sh"
command -v wine >/dev/null || die "wine not found: it runs the Windows package's smoke test"
[ -x .venv-wasmtest/bin/python ] || die "Playwright venv missing: make test-wasm-setup"
[ -d "$SITE_DIR" ] || die "SITE_DIR not found: $SITE_DIR"
[ -z "$(git -C "$SITE_DIR" status --porcelain)" ] \
    || die "the site repo ($SITE_DIR) has uncommitted changes; the release rebuilds it, so commit or discard them first"
if [ -n "${DISPLAY:-}" ]; then
    WITH_DISPLAY=()
elif command -v xvfb-run >/dev/null; then
    WITH_DISPLAY=(xvfb-run -a)
else
    die "rendering tests need a display: set DISPLAY or install xvfb-run"
fi
echo "ok: master at $(git rev-parse --short HEAD), $CURRENT -> $VERSION, previous release $BASE_REF"

# --- 2. bump -------------------------------------------------------------------------
step bump "header -> $VERSION, build"
set_version "$VERSION"
make -j"$(nproc)"

# --- 3. test -------------------------------------------------------------------------
step test "full suite and snippet check"
(cd tests && ALSOFT_DRIVERS=null "${WITH_DISPLAY[@]}" python3 run_tests.py)
"${WITH_DISPLAY[@]}" make check-snippets

# --- 4. docs -------------------------------------------------------------------------
step docs "docs, manifest, snippet stamps and shots"
"${WITH_DISPLAY[@]}" make docs
make stamp-snippets
"${WITH_DISPLAY[@]}" make snippet-shots
[ "$(python3 -c 'import json; m = json.load(open("api/manifest.json")); print(m["version"], m["commit"])')" = "$VERSION None" ] \
    || die "api/manifest.json should say version $VERSION with commit null"

# --- 5. package ----------------------------------------------------------------------
step package "Linux, Windows and WASM packages, each smoke-tested"
rm -f -- dist/McRogueFace-"$VERSION"-*
make package-linux-full package-windows-full package-web
PACKAGES=(dist/McRogueFace-"$VERSION"-Linux-full.tar.gz
          dist/McRogueFace-"$VERSION"-Windows-full.zip
          dist/McRogueFace-"$VERSION"-WASM.zip)
python3 tools/smoke_package.py --version "$VERSION" "${PACKAGES[@]}"

# --- 6. commit -----------------------------------------------------------------------
step commit "Release $VERSION"
git add "$HEADER" api/manifest.json tests/snippets
git commit -q -m "Release $VERSION" -m "Packages built and smoke-tested by tools/release.sh (#475)."
[ -z "$(tracked_changes)" ] || { tracked_changes >&2; die "the release commit left tracked changes behind"; }

# --- 7. tag --------------------------------------------------------------------------
step tag "$VERSION"
git tag "$VERSION"

# --- 8. site -------------------------------------------------------------------------
step site "rebuild $SITE_DIR pinned to $VERSION"
(cd "$SITE_DIR" && python3 tools/build_reference.py)
(cd "$SITE_DIR" && python3 tools/build_library.py --ref "$VERSION" --snippet-ref "$VERSION")
# The working tree is the tag here, so "." is $VERSION.
python3 tools/api_delta.py "$BASE_REF" . --site-dir "$SITE_DIR" --format md

# --- 9. bump -------------------------------------------------------------------------
step next "header -> $NEXT_VERSION"
set_version "$NEXT_VERSION"
git add "$HEADER"
git commit -q -m "Begin $NEXT_VERSION"

trap - ERR
echo
echo "=== Released $VERSION ==="
echo "Tag:      $VERSION ($(git rev-parse --short "$VERSION"))"
echo "Master:   $NEXT_VERSION ($(git rev-parse --short HEAD))"
echo "Packages: ${PACKAGES[*]}"
echo "Site:     $SITE_DIR (uncommitted; review the API delta above, then commit)"
echo "Next:     push master and the tag, then publish the GitHub release with the packages."
