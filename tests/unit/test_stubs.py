#!/usr/bin/env python3
"""Test that type stubs are correctly formatted and usable."""

import os
import sys
import ast

def test_stub_syntax():
    """Test that the stub file has valid Python syntax."""
    stub_path = 'stubs/mcrfpy.pyi'
    
    if not os.path.exists(stub_path):
        print(f"ERROR: Stub file not found at {stub_path}")
        return False
    
    try:
        with open(stub_path, 'r') as f:
            content = f.read()
        
        # Parse the stub file
        tree = ast.parse(content)
        print(f"✓ Stub file has valid Python syntax ({len(content)} bytes)")
        
        # Count definitions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        print(f"✓ Found {len(classes)} class definitions")
        print(f"✓ Found {len(functions)} function/method definitions")
        
        # Check for key classes
        class_names = {cls.name for cls in classes}
        expected_classes = {'Frame', 'Caption', 'Sprite', 'Grid', 'Entity', 'Color', 'Vector', 'Scene', 'Window'}
        missing = expected_classes - class_names
        
        if missing:
            print(f"✗ Missing classes: {missing}")
            return False
        else:
            print("✓ All expected classes are defined")
        
        # Check for key functions
        top_level_funcs = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        expected_funcs = {'createScene', 'setScene', 'currentScene', 'find', 'findAll', 'setTimer'}
        func_set = set(top_level_funcs)
        missing_funcs = expected_funcs - func_set
        
        if missing_funcs:
            print(f"✗ Missing functions: {missing_funcs}")
            return False
        else:
            print("✓ All expected functions are defined")
            
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error in stub file: {e}")
        return False
    except Exception as e:
        print(f"✗ Error parsing stub file: {e}")
        return False

def test_type_annotations():
    """Test that type annotations are present and well-formed."""
    stub_path = 'stubs/mcrfpy.pyi'
    
    with open(stub_path, 'r') as f:
        content = f.read()
    
    # Check for proper type imports
    if 'from typing import' not in content:
        print("✗ Missing typing imports")
        return False
    else:
        print("✓ Has typing imports")
    
    # Check for Optional usage
    if 'Optional[' in content:
        print("✓ Uses Optional type hints")
    
    # Check for Union usage
    if 'Union[' in content:
        print("✓ Uses Union type hints")
    
    # Check for overload usage
    if '@overload' in content:
        print("✓ Uses @overload decorators")
    
    # Check return type annotations
    if '-> None:' in content and '-> int:' in content and '-> str:' in content:
        print("✓ Has return type annotations")
    else:
        print("✗ Missing some return type annotations")
    
    return True

def test_docstrings():
    """Test that docstrings are preserved in stubs."""
    stub_path = 'stubs/mcrfpy.pyi'
    
    with open(stub_path, 'r') as f:
        content = f.read()
    
    # Count docstrings
    docstring_count = content.count('"""')
    if docstring_count > 10:  # Should have many docstrings
        print(f"✓ Found {docstring_count // 2} docstrings")
    else:
        print(f"✗ Too few docstrings found: {docstring_count // 2}")
    
    # Check for specific docstrings
    if 'Core game engine interface' in content:
        print("✓ Module docstring present")
    
    if 'A rectangular frame UI element' in content:
        print("✓ Frame class docstring present")
    
    if 'Load a sound effect from a file' in content:
        print("✓ Function docstrings present")
    
    return True

def test_automation_module():
    """Test that automation module is properly defined."""
    stub_path = 'stubs/mcrfpy.pyi'
    
    with open(stub_path, 'r') as f:
        content = f.read()
    
    if 'class automation:' in content:
        print("✓ automation class defined")
    else:
        print("✗ automation class missing")
        return False
    
    # Check for key automation methods
    automation_methods = ['screenshot', 'click', 'moveTo', 'keyDown', 'typewrite']
    missing = []
    for method in automation_methods:
        if f'def {method}' not in content:
            missing.append(method)
    
    if missing:
        print(f"✗ Missing automation methods: {missing}")
        return False
    else:
        print("✓ All key automation methods defined")
    
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
        print("✅ All tests passed! Type stubs are valid and complete.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please review the stub file.")
        sys.exit(1)

if __name__ == '__main__':
    main()