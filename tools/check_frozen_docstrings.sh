#!/bin/bash
# check_frozen_docstrings.sh - strict MCRF_* docstring-macro gate over the FROZEN
# (1.0) Python-binding surface.
#
# Part of #314 F15. Mirrors the role of tests/unit/api_surface_snapshot_test.py:
# once the frozen binding files are converted to MCRF_METHOD/MCRF_PROPERTY, this
# gate prevents regression to raw docstrings. Experimental 3D/Voxel bindings
# (src/3d/) are exempt from the 1.0 freeze and intentionally excluded.
#
# Usage:
#   tools/check_frozen_docstrings.sh
#
# Exit codes:
#   0  PASS  - all frozen binding files are 100% MCRF_* compliant
#   1  FAIL  - one or more raw/missing doc slots remain in a frozen file
#   2  ERROR - missing tooling
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv-audit/bin/python3"
AUDIT="$ROOT/tools/audit_pymethoddef.py"

if [ ! -x "$PY" ]; then
    echo "ERROR: $PY not found (need .venv-audit with tree-sitter + tree-sitter-cpp)" >&2
    exit 2
fi

# Frozen surface = all binding sources EXCEPT experimental 3D/Voxel (src/3d/).
mapfile -t FILES < <(find "$ROOT/src" -name '*.cpp' -not -path '*/3d/*' | sort)
if [ "${#FILES[@]}" -eq 0 ]; then
    echo "ERROR: no source files found under $ROOT/src" >&2
    exit 2
fi

"$PY" "$AUDIT" --strict --quiet --paths "${FILES[@]}"
RC=$?
if [ "$RC" -eq 0 ]; then
    echo "FROZEN DOCSTRING GATE: PASS (frozen binding surface is 100% MCRF_* compliant)"
else
    echo "FROZEN DOCSTRING GATE: FAIL (raw/missing docstrings remain in frozen files; src/3d/ is exempt)"
fi
exit $RC
