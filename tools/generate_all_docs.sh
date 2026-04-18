#!/bin/bash
set -e  # Exit on any error

echo "=== McRogueFace Documentation Generation ==="

# Verify build exists
if [ ! -f "./build/mcrogueface" ]; then
    echo "ERROR: build/mcrogueface not found. Run 'make' first."
    exit 1
fi

# Generate API docs (HTML + Markdown)
echo "Generating API documentation..."
./build/mcrogueface --headless --exec tools/generate_dynamic_docs.py

# Generate type stubs (using v2 - manually maintained high-quality stubs)
echo "Generating type stubs..."
./build/mcrogueface --headless --exec tools/generate_stubs_v2.py

# Generate man page
echo "Generating man page..."
./tools/generate_man_page.sh

echo "=== Documentation generation complete ==="
echo "  HTML:     docs/api_reference_dynamic.html"
echo "  Markdown: docs/API_REFERENCE_DYNAMIC.md"
echo "  Man page: docs/mcrfpy.3"
echo "  Stubs:    stubs/mcrfpy.pyi"

# ---------------------------------------------------------------------------
# Static-analysis audit: report MCRF_METHOD / MCRF_PROPERTY macro compliance
# across every PyMethodDef / PyGetSetDef array in src/. This is informational
# only (no --strict) so it cannot break the doc build, but the summary makes
# pre-1.0 documentation drift visible alongside doc generation.
#
# Requires the .venv-audit virtual environment with tree-sitter +
# tree-sitter-cpp installed. The audit is skipped silently if absent so
# contributors without the venv aren't blocked.
# ---------------------------------------------------------------------------
if [ -x "./.venv-audit/bin/python3" ] && [ -f "./tools/audit_pymethoddef.py" ]; then
    echo ""
    echo "=== PyMethodDef / PyGetSetDef Macro Compliance Audit ==="
    ./.venv-audit/bin/python3 ./tools/audit_pymethoddef.py --quiet || true
elif [ -f "./tools/audit_pymethoddef.py" ]; then
    echo ""
    echo "(skipping audit_pymethoddef.py: .venv-audit not found - run"
    echo " 'python3 -m venv .venv-audit && .venv-audit/bin/pip install"
    echo " tree-sitter tree-sitter-cpp' to enable)"
fi
