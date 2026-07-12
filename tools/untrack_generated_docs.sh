#!/bin/bash
#
# untrack_generated_docs.sh
#
# One-shot migration helper: stops tracking the generated/rendered docs and
# personal-notes docs that the new .gitignore "generated-docs" block now
# ignores, WITHOUT deleting them from your working tree.
#
# It reads the pattern block delimited by the BEGIN/END markers below out of
# the repo's .gitignore, then asks git which CURRENTLY-TRACKED files those
# patterns match (via `git ls-files --cached -i -X <patterns>`). Because the
# pattern source is the .gitignore block itself, this can never drift from what
# is actually ignored.
#
# Usage:
#   tools/untrack_generated_docs.sh            # dry run: print the git rm --cached commands
#   tools/untrack_generated_docs.sh --apply    # actually run them
#
# NOTE: `git rm --cached` only removes the files from the index (they stay on
# disk). You still need to `git commit` afterwards to record the removal.
#
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
GITIGNORE="$REPO_ROOT/.gitignore"

BEGIN_MARKER='# >>> generated-docs (untrack via tools/untrack_generated_docs.sh) >>>'
END_MARKER='# <<< generated-docs <<<'

APPLY=0
case "${1:-}" in
    --apply) APPLY=1 ;;
    ""|--dry-run) APPLY=0 ;;
    -h|--help)
        echo "Usage: $0 [--apply]"
        echo "  (no args)  dry run -- print the git rm --cached commands"
        echo "  --apply    execute the git rm --cached commands"
        exit 0
        ;;
    *)
        echo "Unknown argument: $1 (use --apply or no argument)" >&2
        exit 1
        ;;
esac

if [ ! -f "$GITIGNORE" ]; then
    echo "ERROR: $GITIGNORE not found" >&2
    exit 1
fi

# Extract the pattern lines strictly between the markers, dropping comments and
# blank lines, into a temp exclude file that git can consume.
PATTERNS_FILE="$(mktemp -t mcrf-untrack-patterns.XXXXXX)"
trap 'rm -f "$PATTERNS_FILE"' EXIT

awk -v b="$BEGIN_MARKER" -v e="$END_MARKER" '
    $0 == b { inblock=1; next }
    $0 == e { inblock=0; next }
    inblock {
        line=$0
        # strip leading/trailing whitespace
        gsub(/^[ \t]+|[ \t]+$/, "", line)
        if (line == "" || line ~ /^#/) next
        print line
    }
' "$GITIGNORE" > "$PATTERNS_FILE"

if [ ! -s "$PATTERNS_FILE" ]; then
    echo "ERROR: no patterns found between markers in .gitignore" >&2
    echo "  expected block delimited by:" >&2
    echo "    $BEGIN_MARKER" >&2
    echo "    $END_MARKER" >&2
    exit 1
fi

# Ask git which tracked files match those ignore patterns.
# -c = cached (tracked), -i = show ignored, -X = exclude-pattern file.
mapfile -t TRACKED < <(cd "$REPO_ROOT" && git ls-files --cached -i -X "$PATTERNS_FILE" | sort -u)

if [ "${#TRACKED[@]}" -eq 0 ]; then
    echo "No currently-tracked files match the generated-docs ignore block. Nothing to do."
    exit 0
fi

echo "The following ${#TRACKED[@]} tracked file(s) are now covered by the generated-docs .gitignore block:"
echo ""
for f in "${TRACKED[@]}"; do
    echo "    git rm --cached -- \"$f\""
done
echo ""

if [ "$APPLY" -eq 0 ]; then
    echo "Dry run only. Re-run with --apply to execute, then commit the removals."
    echo "(Files remain on disk; only the git index entries are removed.)"
    exit 0
fi

echo "Applying: git rm --cached ..."
# Remove in one batch; --cached keeps the working-tree files.
( cd "$REPO_ROOT" && git rm --cached --quiet -- "${TRACKED[@]}" )
echo ""
echo "Done. ${#TRACKED[@]} file(s) removed from the index (still present on disk)."
echo "Review with 'git status', then commit the removals."
