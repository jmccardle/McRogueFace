#!/bin/bash
# validate_file_docstrings.sh - per-file MCRF_* docstring-macro compliance check.
#
# Part of #314 F15: drives one-agent-per-file docstring standardization. An agent
# converting a single .cpp runs THIS script repeatedly until it prints
# "VALIDATION: PASS", which is the completion signal for that file.
#
# Usage:
#   tools/validate_file_docstrings.sh src/SomeFile.cpp
#
# Exit codes:
#   0  PASS  - every PyMethodDef/PyGetSetDef entry uses MCRF_METHOD/MCRF_PROPERTY
#   1  FAIL  - one or more RAW_STRING / NULL / MISSING doc slots remain
#   2  ERROR - bad usage / missing tooling
set -u

FILE="${1:-}"
if [ -z "$FILE" ]; then
    echo "usage: tools/validate_file_docstrings.sh <src/file.cpp>" >&2
    exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv-audit/bin/python3"
AUDIT="$ROOT/tools/audit_pymethoddef.py"

if [ ! -x "$PY" ]; then
    echo "ERROR: $PY not found. Create it with:" >&2
    echo "  python3 -m venv .venv-audit && .venv-audit/bin/pip install tree-sitter tree-sitter-cpp" >&2
    exit 2
fi
if [ ! -f "$FILE" ]; then
    echo "ERROR: no such file: $FILE" >&2
    exit 2
fi

# A file using MCRF_* macros must include the macro header.
if ! grep -q 'McRFPy_Doc.h' "$FILE"; then
    echo "NOTE: $FILE does not yet #include \"McRFPy_Doc.h\" (required for MCRF_* macros)"
fi

OUT="$("$PY" "$AUDIT" --paths "$FILE" 2>&1)"
NONCOMP="$(printf '%s\n' "$OUT" | awk '$NF ~ /^(RAW_STRING|MISSING|NULL)$/')"

if [ -z "$NONCOMP" ]; then
    echo "VALIDATION: PASS ($FILE is 100% MCRF_* compliant)"
    exit 0
fi

echo "Remaining non-compliant entries in $FILE:"
printf '%s\n' "$NONCOMP"
N="$(printf '%s\n' "$NONCOMP" | wc -l | tr -d ' ')"
echo "VALIDATION: FAIL ($N non-compliant doc slot(s) remain)"
exit 1
