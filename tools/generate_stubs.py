#!/usr/bin/env python3
"""Generate .pyi type stub files for McRogueFace Python API.

This script introspects the mcrfpy module and generates type stubs
for better IDE support and type checking.
"""

import os
import sys
import inspect
import types
from typing import Dict, List, Set, Any

# Add the build directory to path to import mcrfpy
sys.path.insert(0, './build')

try:
    import mcrfpy
except ImportError:
    print("Error: Could not import mcrfpy. Make sure to run this from the project root after building.")
    sys.exit(1)

def parse_docstring_signature(doc: str) -> tuple[str, str]:
    """Extract signature and description from docstring."""
    if not doc:
        return "", ""
    
    lines = doc.strip().split('\n')
    if lines:
        # First line often contains the signature
        first_line = lines[0]
        if '(' in first_line and ')' in first_line:
            # Extract just the part after the function name
            start = first_line.find('(')
            end = first_line.rfind(')') + 1
            if start != -1 and end != 0:
                sig = first_line[start:end]
                # Get return type if present
                if '->' in first_line:
                    ret_start = first_line.find('->')
                    ret_type = first_line[ret_start:].strip()
                    return sig, ret_type
                return sig, ""
    return "", ""

def get_type_hint(obj_type: type) -> str:
    """Convert Python type to type hint string."""
    if obj_type == int:
        return "int"
    elif obj_type == float:
        return "float"
    elif obj_type == str:
        return "str"
    elif obj_type == bool:
        return "bool"
    elif obj_type == list:
        return "List[Any]"
    elif obj_type == dict:
        return "Dict[Any, Any]"
    elif obj_type == tuple:
        return "Tuple[Any, ...]"
    elif obj_type == type(None):
        return "None"
    else:
        return "Any"

def generate_class_stub(class_name: str, cls: type) -> List[str]:
    """Generate stub for a class."""
    lines = []
    
    # Get class docstring
    if cls.__doc__:
        doc_lines = cls.__doc__.strip().split('\n')
        # Use only the first paragraph for the stub
        lines.append(f'class {class_name}:')
        lines.append(f'    """{doc_lines[0]}"""')
    else:
        lines.append(f'class {class_name}:')
    
    # Check for __init__ method
    if hasattr(cls, '__init__'):
        init_doc = cls.__init__.__doc__ or cls.__doc__
        if init_doc:
            sig, ret = parse_docstring_signature(init_doc)
            if sig:
                lines.append(f'    def __init__(self{sig[1:-1]}) -> None: ...')
            else:
                lines.append(f'    def __init__(self, *args, **kwargs) -> None: ...')
        else:
            lines.append(f'    def __init__(self, *args, **kwargs) -> None: ...')
    
    # Get properties and methods
    properties = []
    methods = []
    
    for attr_name in dir(cls):
        if attr_name.startswith('_') and not attr_name.startswith('__'):
            continue
            
        try:
            attr = getattr(cls, attr_name)
            
            if isinstance(attr, property):
                properties.append((attr_name, attr))
            elif callable(attr) and not attr_name.startswith('__'):
                methods.append((attr_name, attr))
        except:
            pass
    
    # Add properties
    if properties:
        lines.append('')
        for prop_name, prop in properties:
            # Try to determine property type from docstring
            if prop.fget and prop.fget.__doc__:
                lines.append(f'    @property')
                lines.append(f'    def {prop_name}(self) -> Any: ...')
                if prop.fset:
                    lines.append(f'    @{prop_name}.setter')
                    lines.append(f'    def {prop_name}(self, value: Any) -> None: ...')
            else:
                lines.append(f'    {prop_name}: Any')
    
    # Add methods
    if methods:
        lines.append('')
        for method_name, method in methods:
            if method.__doc__:
                sig, ret = parse_docstring_signature(method.__doc__)
                if sig and ret:
                    lines.append(f'    def {method_name}(self{sig[1:-1]}) {ret}: ...')
                elif sig:
                    lines.append(f'    def {method_name}(self{sig[1:-1]}) -> Any: ...')
                else:
                    lines.append(f'    def {method_name}(self, *args, **kwargs) -> Any: ...')
            else:
                lines.append(f'    def {method_name}(self, *args, **kwargs) -> Any: ...')
    
    lines.append('')
    return lines

def generate_function_stub(func_name: str, func: Any) -> str:
    """Generate stub for a function."""
    if func.__doc__:
        sig, ret = parse_docstring_signature(func.__doc__)
        if sig and ret:
            return f'def {func_name}{sig} {ret}: ...'
        elif sig:
            return f'def {func_name}{sig} -> Any: ...'
    
    return f'def {func_name}(*args, **kwargs) -> Any: ...'

def generate_stubs():
    """Generate the main mcrfpy.pyi file."""
    lines = [
        '"""Type stubs for McRogueFace Python API.',
        '',
        'Auto-generated - do not edit directly.',
        '"""',
        '',
        'from typing import Any, List, Dict, Tuple, Optional, Callable, Union',
        '',
        '# Module documentation',
    ]
    
    # Add module docstring as comment
    if mcrfpy.__doc__:
        for line in mcrfpy.__doc__.strip().split('\n')[:3]:
            lines.append(f'# {line}')
    
    lines.extend(['', '# Classes', ''])
    
    # Collect all classes
    classes = []
    functions = []
    constants = []
    
    for name in sorted(dir(mcrfpy)):
        if name.startswith('_'):
            continue
            
        obj = getattr(mcrfpy, name)
        
        if isinstance(obj, type):
            classes.append((name, obj))
        elif callable(obj):
            functions.append((name, obj))
        elif not inspect.ismodule(obj):
            constants.append((name, obj))
    
    # Generate class stubs
    for class_name, cls in classes:
        lines.extend(generate_class_stub(class_name, cls))
    
    # Generate function stubs
    if functions:
        lines.extend(['# Functions', ''])
        for func_name, func in functions:
            lines.append(generate_function_stub(func_name, func))
        lines.append('')
    
    # Generate constants
    if constants:
        lines.extend(['# Constants', ''])
        for const_name, const in constants:
            const_type = get_type_hint(type(const))
            lines.append(f'{const_name}: {const_type}')
    
    return '\n'.join(lines)

def generate_automation_stubs():
    """Generate stubs for the automation submodule."""
    if not hasattr(mcrfpy, 'automation'):
        return None
        
    automation = mcrfpy.automation
    
    lines = [
        '"""Type stubs for McRogueFace automation API."""',
        '',
        'from typing import Optional, Tuple',
        '',
    ]
    
    # Get all automation functions
    for name in sorted(dir(automation)):
        if name.startswith('_'):
            continue
            
        obj = getattr(automation, name)
        if callable(obj):
            lines.append(generate_function_stub(name, obj))
    
    return '\n'.join(lines)

def main():
    """Main entry point."""
    print("Generating type stubs for McRogueFace...")
    
    # Generate main module stubs
    stubs = generate_stubs()
    
    # Create stubs directory
    os.makedirs('stubs', exist_ok=True)
    
    # Write main module stubs
    with open('stubs/mcrfpy.pyi', 'w') as f:
        f.write(stubs)
    print("Generated stubs/mcrfpy.pyi")
    
    # Generate automation module stubs if available
    automation_stubs = generate_automation_stubs()
    if automation_stubs:
        os.makedirs('stubs/mcrfpy', exist_ok=True)
        with open('stubs/mcrfpy/__init__.pyi', 'w') as f:
            f.write(stubs)
        with open('stubs/mcrfpy/automation.pyi', 'w') as f:
            f.write(automation_stubs)
        print("Generated stubs/mcrfpy/automation.pyi")
    
    print("\nType stubs generated successfully!")
    print("\nTo use in your IDE:")
    print("1. Add the 'stubs' directory to your PYTHONPATH")
    print("2. Or configure your IDE to look for stubs in the 'stubs' directory")
    print("3. Most IDEs will automatically detect .pyi files")

if __name__ == '__main__':
    main()