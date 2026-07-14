#!/usr/bin/env python3
"""Test that type stubs are correctly formatted and usable."""

import os
import sys
import ast

import mcrfpy

# The stub lives in the repo, but tests run with cwd=build/. Anchor on this file.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STUB_PATH = os.path.join(REPO_ROOT, 'stubs', 'mcrfpy.pyi')

def read_stub():
    with open(STUB_PATH, 'r') as f:
        return f.read()

def test_stub_syntax():
    """Test that the stub file has valid Python syntax."""
    if not os.path.exists(STUB_PATH):
        print(f"ERROR: Stub file not found at {STUB_PATH}")
        return False

    try:
        content = read_stub()

        # Parse the stub file
        tree = ast.parse(content)
        print(f"OK  Stub file has valid Python syntax ({len(content)} bytes)")

        # Count definitions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        print(f"OK  Found {len(classes)} class definitions")
        print(f"OK  Found {len(functions)} function/method definitions")

        # Check for key classes (Timer/Scene are the successors to setTimer/createScene)
        class_names = {cls.name for cls in classes}
        expected_classes = {'Frame', 'Caption', 'Sprite', 'Grid', 'GridView', 'GridData',
                            'Entity', 'Color', 'Vector', 'Scene', 'Timer', 'Window'}
        missing = expected_classes - class_names

        if missing:
            print(f"FAIL Missing classes: {missing}")
            return False
        else:
            print("OK  All expected classes are defined")

        # Check for key module-level functions (current API: setScene/createScene/
        # currentScene/setTimer/findAll are gone; Scene objects, Timer and find_all
        # replaced them).
        top_level_funcs = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        func_set = set(top_level_funcs)
        expected_funcs = {'find', 'find_all', 'step', 'get_metrics', 'set_scale', 'exit'}
        missing_funcs = expected_funcs - func_set

        if missing_funcs:
            print(f"FAIL Missing functions: {missing_funcs}")
            return False
        else:
            print("OK  All expected functions are defined")

        # Every function the stub advertises must actually exist on the module,
        # and removed APIs must not linger in the stub.
        phantom = sorted(f for f in func_set if not hasattr(mcrfpy, f))
        if phantom:
            print(f"FAIL Stub declares functions absent from mcrfpy: {phantom}")
            return False
        print(f"OK  All {len(func_set)} stub functions exist on the mcrfpy module")

        phantom_classes = sorted(c for c in expected_classes if not hasattr(mcrfpy, c))
        if phantom_classes:
            print(f"FAIL Stub declares classes absent from mcrfpy: {phantom_classes}")
            return False
        print("OK  All expected stub classes exist on the mcrfpy module")

        return True

    except SyntaxError as e:
        print(f"FAIL Syntax error in stub file: {e}")
        return False

def test_type_annotations():
    """Test that type annotations are present and well-formed."""
    content = read_stub()

    # Check for proper type imports
    if 'from typing import' not in content:
        print("FAIL Missing typing imports")
        return False
    else:
        print("OK  Has typing imports")

    # Optional/Union/@overload are nice-to-haves; the generator currently emits
    # PEP 604 unions ("int | None") instead, so these are informational only.
    for marker, label in (('Optional[', 'Optional type hints'),
                          ('Union[', 'Union type hints'),
                          ('@overload', '@overload decorators')):
        if marker in content:
            print(f"OK  Uses {label}")

    # Check return type annotations
    if '-> None:' in content and '-> int:' in content and '-> str:' in content:
        print("OK  Has return type annotations")
    else:
        print("FAIL Missing some return type annotations")
        return False

    return True

def test_docstrings():
    """Test that docstrings are preserved in stubs."""
    content = read_stub()

    # Count docstrings
    docstring_count = content.count('"""')
    if docstring_count > 10:  # Should have many docstrings
        print(f"OK  Found {docstring_count // 2} docstrings")
    else:
        print(f"FAIL Too few docstrings found: {docstring_count // 2}")
        return False

    # Check for specific docstrings (module, class, method)
    ok = True
    for needle, label in (
        ('Type stubs for McRogueFace Python API', 'Module docstring'),
        ('A rectangular frame UI element', 'Frame class docstring'),
        ('Take a screenshot', 'Method docstring'),
    ):
        if needle in content:
            print(f"OK  {label} present")
        else:
            print(f"FAIL {label} missing")
            ok = False

    return ok

def test_automation_module():
    """Test that automation module is properly defined."""
    content = read_stub()

    # The generator emits the submodule as a _automation_module class plus an
    # `automation:` module-level binding.
    if 'class _automation_module:' in content and 'automation: _automation_module' in content:
        print("OK  automation submodule defined")
    else:
        print("FAIL automation submodule missing")
        return False

    # Check for key automation methods
    automation_methods = ['screenshot', 'click', 'moveTo', 'keyDown', 'typewrite']
    missing = []
    for method in automation_methods:
        if f'def {method}' not in content:
            missing.append(method)
        elif not hasattr(mcrfpy.automation, method):
            missing.append(method + " (stubbed but absent from mcrfpy.automation)")

    if missing:
        print(f"FAIL Missing automation methods: {missing}")
        return False
    else:
        print("OK  All key automation methods defined")

    return True

def main():
    """Run all stub tests."""
    print("Type Stub Validation Tests")
    print("==========================\n")
    
    all_passed = True
    
    print("1. Syntax Test:")
    if not test_stub_syntax():
        all_passed = False
    print()
    
    print("2. Type Annotations Test:")
    if not test_type_annotations():
        all_passed = False
    print()
    
    print("3. Docstrings Test:")
    if not test_docstrings():
        all_passed = False
    print()
    
    print("4. Automation Module Test:")
    if not test_automation_module():
        all_passed = False
    print()
    
    if all_passed:
        print("PASS - All tests passed! Type stubs are valid and complete.")
        sys.exit(0)
    else:
        print("FAIL - Some tests failed. Please review the stub file.")
        sys.exit(1)

if __name__ == '__main__':
    main()