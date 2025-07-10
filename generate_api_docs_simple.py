#!/usr/bin/env python3
"""Generate API reference documentation for McRogueFace - Simple version."""

import os
import sys
import datetime
from pathlib import Path

import mcrfpy

def generate_markdown_docs():
    """Generate markdown API documentation."""
    lines = []
    
    # Header
    lines.append("# McRogueFace API Reference")
    lines.append("")
    lines.append("*Generated on {}*".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    lines.append("")
    
    # Module description
    if mcrfpy.__doc__:
        lines.append("## Overview")
        lines.append("")
        lines.extend(mcrfpy.__doc__.strip().split('\n'))
        lines.append("")
    
    # Collect all components
    classes = []
    functions = []
    
    for name in sorted(dir(mcrfpy)):
        if name.startswith('_'):
            continue
        
        obj = getattr(mcrfpy, name)
        
        if isinstance(obj, type):
            classes.append((name, obj))
        elif callable(obj):
            functions.append((name, obj))
    
    # Document classes
    lines.append("## Classes")
    lines.append("")
    
    for name, cls in classes:
        lines.append("### class {}".format(name))
        if cls.__doc__:
            doc_lines = cls.__doc__.strip().split('\n')
            for line in doc_lines[:5]:  # First 5 lines
                lines.append(line)
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Document functions  
    lines.append("## Functions")
    lines.append("")
    
    for name, func in functions:
        lines.append("### {}".format(name))
        if func.__doc__:
            doc_lines = func.__doc__.strip().split('\n')
            for line in doc_lines[:5]:  # First 5 lines
                lines.append(line)
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Automation module
    if hasattr(mcrfpy, 'automation'):
        lines.append("## Automation Module")
        lines.append("")
        
        automation = mcrfpy.automation
        for name in sorted(dir(automation)):
            if not name.startswith('_'):
                obj = getattr(automation, name)
                if callable(obj):
                    lines.append("### automation.{}".format(name))
                    if obj.__doc__:
                        lines.append(obj.__doc__.strip().split('\n')[0])
                    lines.append("")
    
    return '\n'.join(lines)

def main():
    """Generate API documentation."""
    print("Generating McRogueFace API Documentation...")
    
    # Create docs directory
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Generate markdown
    markdown_content = generate_markdown_docs()
    
    # Write markdown
    md_path = docs_dir / "API_REFERENCE.md"
    with open(md_path, 'w') as f:
        f.write(markdown_content)
    print("Written to {}".format(md_path))
    
    # Summary
    lines = markdown_content.split('\n')
    class_count = markdown_content.count('### class')
    func_count = markdown_content.count('### ') - class_count - markdown_content.count('### automation.')
    
    print("\nDocumentation Statistics:")
    print("- Classes documented: {}".format(class_count))
    print("- Functions documented: {}".format(func_count))
    print("- Total lines: {}".format(len(lines)))
    
    print("\nAPI documentation generated successfully!")
    sys.exit(0)

if __name__ == '__main__':
    main()