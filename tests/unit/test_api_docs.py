#!/usr/bin/env python3
"""Test that API documentation generator works correctly."""

import os
import sys
from pathlib import Path

def test_api_docs_exist():
    """Test that API documentation was generated."""
    docs_path = Path("docs/API_REFERENCE.md")
    
    if not docs_path.exists():
        print("ERROR: API documentation not found at docs/API_REFERENCE.md")
        return False
    
    print("✓ API documentation file exists")
    
    # Check file size
    size = docs_path.stat().st_size
    if size < 1000:
        print(f"ERROR: API documentation seems too small ({size} bytes)")
        return False
    
    print(f"✓ API documentation has reasonable size ({size} bytes)")
    
    # Read content
    with open(docs_path, 'r') as f:
        content = f.read()
    
    # Check for expected sections
    expected_sections = [
        "# McRogueFace API Reference",
        "## Overview", 
        "## Classes",
        "## Functions",
        "## Automation Module"
    ]
    
    missing = []
    for section in expected_sections:
        if section not in content:
            missing.append(section)
    
    if missing:
        print(f"ERROR: Missing sections: {missing}")
        return False
    
    print("✓ All expected sections present")
    
    # Check for key classes
    key_classes = ["Frame", "Caption", "Sprite", "Grid", "Entity", "Scene"]
    missing_classes = []
    for cls in key_classes:
        if f"### class {cls}" not in content:
            missing_classes.append(cls)
    
    if missing_classes:
        print(f"ERROR: Missing classes: {missing_classes}")
        return False
    
    print("✓ All key classes documented")
    
    # Check for key functions
    key_functions = ["createScene", "setScene", "currentScene", "find", "setTimer"]
    missing_funcs = []
    for func in key_functions:
        if f"### {func}" not in content:
            missing_funcs.append(func)
    
    if missing_funcs:
        print(f"ERROR: Missing functions: {missing_funcs}")
        return False
    
    print("✓ All key functions documented")
    
    # Check automation module
    if "automation.screenshot" in content:
        print("✓ Automation module documented")
    else:
        print("ERROR: Automation module not properly documented")
        return False
    
    # Count documentation entries
    class_count = content.count("### class ")
    func_count = content.count("### ") - class_count - content.count("### automation.")
    auto_count = content.count("### automation.")
    
    print(f"\nDocumentation Coverage:")
    print(f"- Classes: {class_count}")
    print(f"- Functions: {func_count}")
    print(f"- Automation methods: {auto_count}")
    
    return True

def test_doc_accuracy():
    """Test that documentation matches actual API."""
    # Import mcrfpy to check
    import mcrfpy
    
    print("\nVerifying documentation accuracy...")
    
    # Read documentation
    with open("docs/API_REFERENCE.md", 'r') as f:
        content = f.read()
    
    # Check that all public classes are documented
    actual_classes = [name for name in dir(mcrfpy) 
                      if isinstance(getattr(mcrfpy, name), type) and not name.startswith('_')]
    
    undocumented = []
    for cls in actual_classes:
        if f"### class {cls}" not in content:
            undocumented.append(cls)
    
    if undocumented:
        print(f"WARNING: Undocumented classes: {undocumented}")
    else:
        print("✓ All public classes are documented")
    
    # Check functions
    actual_funcs = [name for name in dir(mcrfpy) 
                    if callable(getattr(mcrfpy, name)) and not name.startswith('_') 
                    and not isinstance(getattr(mcrfpy, name), type)]
    
    undoc_funcs = []
    for func in actual_funcs:
        if f"### {func}" not in content:
            undoc_funcs.append(func)
    
    if undoc_funcs:
        print(f"WARNING: Undocumented functions: {undoc_funcs}")
    else:
        print("✓ All public functions are documented")
    
    return True

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
        print("✅ All API documentation tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()