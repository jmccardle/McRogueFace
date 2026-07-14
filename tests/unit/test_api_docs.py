#!/usr/bin/env python3
"""Test that API documentation generator works correctly.

The hand-written docs/API_REFERENCE.md is gone; the canonical API reference is now
docs/API_REFERENCE_DYNAMIC.md, generated from the compiled module by
tools/generate_dynamic_docs.py (MCRF_* docstring macros -> introspection -> markdown).
This test verifies that generated artifact exists, is well-formed, and stays in sync
with the live mcrfpy module.
"""

import os
import sys
from pathlib import Path

# tests/unit/test_api_docs.py -> repo root -> docs/
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_PATH = REPO_ROOT / "docs" / "API_REFERENCE_DYNAMIC.md"


def test_api_docs_exist():
    """Test that API documentation was generated."""
    if not DOCS_PATH.exists():
        print(f"ERROR: API documentation not found at {DOCS_PATH}")
        return False

    print("+ API documentation file exists")

    # Check file size
    size = DOCS_PATH.stat().st_size
    if size < 1000:
        print(f"ERROR: API documentation seems too small ({size} bytes)")
        return False

    print(f"+ API documentation has reasonable size ({size} bytes)")

    # Read content
    with open(DOCS_PATH, 'r') as f:
        content = f.read()

    # Check for expected sections (current generated layout)
    expected_sections = [
        "# McRogueFace API Reference",
        "## Table of Contents",
        "## Module Attributes",
        "## Functions",
        "## Classes",
    ]

    missing = [s for s in expected_sections if s not in content]
    if missing:
        print(f"ERROR: Missing sections: {missing}")
        return False

    print("+ All expected sections present")

    # Check for key classes ("### ClassName" headings)
    key_classes = ["Frame", "Caption", "Sprite", "Grid", "Entity", "Scene"]
    missing_classes = [c for c in key_classes if f"\n### {c}\n" not in content]
    if missing_classes:
        print(f"ERROR: Missing classes: {missing_classes}")
        return False

    print("+ All key classes documented")

    # Check for key module-level functions ("### `name(...)`" headings)
    key_functions = ["find", "find_all", "step", "get_metrics", "set_scale", "exit"]
    missing_funcs = [f for f in key_functions if f"\n### `{f}(" not in content]
    if missing_funcs:
        print(f"ERROR: Missing functions: {missing_funcs}")
        return False

    print("+ All key functions documented")

    # Scene management moved from functions to the mcrfpy.current_scene attribute
    if "### `mcrfpy.current_scene`" not in content:
        print("ERROR: mcrfpy.current_scene not documented under Module Attributes")
        return False

    print("+ Module attributes documented")

    # Count documentation entries
    class_count = sum(1 for line in content.splitlines()
                      if line.startswith("### ") and not line.startswith("### `"))
    func_count = sum(1 for line in content.splitlines() if line.startswith("### `"))
    member_count = sum(1 for line in content.splitlines() if line.startswith("#### "))

    print(f"\nDocumentation Coverage:")
    print(f"- Classes: {class_count}")
    print(f"- Functions/attributes: {func_count}")
    print(f"- Class members: {member_count}")

    if class_count == 0 or func_count == 0 or member_count == 0:
        print("ERROR: documentation contains no entries")
        return False

    return True


def test_doc_accuracy():
    """Test that documentation matches actual API."""
    import mcrfpy

    print("\nVerifying documentation accuracy...")

    with open(DOCS_PATH, 'r') as f:
        content = f.read()

    passed = True

    # Check that all public classes are documented
    actual_classes = [name for name in dir(mcrfpy)
                      if isinstance(getattr(mcrfpy, name), type) and not name.startswith('_')]

    undocumented = [c for c in actual_classes if f"\n### {c}\n" not in content]
    if undocumented:
        print(f"ERROR: Undocumented classes: {undocumented}")
        passed = False
    else:
        print(f"+ All {len(actual_classes)} public classes are documented")

    # Check functions
    actual_funcs = [name for name in dir(mcrfpy)
                    if callable(getattr(mcrfpy, name)) and not name.startswith('_')
                    and not isinstance(getattr(mcrfpy, name), type)]

    undoc_funcs = [f for f in actual_funcs if f"\n### `{f}(" not in content]
    if undoc_funcs:
        print(f"ERROR: Undocumented functions: {undoc_funcs}")
        passed = False
    else:
        print(f"+ All {len(actual_funcs)} public functions are documented")

    return passed


def main():
    """Run all API documentation tests."""
    print("API Documentation Tests")
    print("======================\n")

    all_passed = True

    # Test 1: Documentation exists and is complete
    print("Test 1: Documentation Generation")
    if not test_api_docs_exist():
        all_passed = False
    print()

    # Test 2: Documentation accuracy
    print("Test 2: Documentation Accuracy")
    if not test_doc_accuracy():
        all_passed = False
    print()

    if all_passed:
        print("PASS: All API documentation tests passed!")
        sys.exit(0)
    else:
        print("FAIL: Some tests failed.")
        sys.exit(1)


if __name__ == '__main__':
    main()
