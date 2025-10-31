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
