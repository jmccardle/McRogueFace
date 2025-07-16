#!/usr/bin/env python3
"""Generate API reference documentation for McRogueFace.

This script generates comprehensive API documentation in multiple formats:
- Markdown for GitHub/documentation sites
- HTML for local browsing
- RST for Sphinx integration (future)
"""

import os
import sys
import inspect
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# We need to run this with McRogueFace as the interpreter
# so mcrfpy is available
import mcrfpy

def escape_markdown(text: str) -> str:
    """Escape special markdown characters."""
    if not text:
        return ""
    # Escape backticks in inline code
    return text.replace("`", "\\`")

def format_signature(name: str, doc: str) -> str:
    """Extract and format function signature from docstring."""
    if not doc:
        return f"{name}(...)"
    
    lines = doc.strip().split('\n')
    if lines and '(' in lines[0]:
        # First line contains signature
        return lines[0].split('->')[0].strip()
    
    return f"{name}(...)"

def get_class_info(cls: type) -> Dict[str, Any]:
    """Extract comprehensive information about a class."""
    info = {
        'name': cls.__name__,
        'doc': cls.__doc__ or "",
        'methods': [],
        'properties': [],
        'bases': [base.__name__ for base in cls.__bases__ if base.__name__ != 'object'],
    }
    
    # Get all attributes
    for attr_name in sorted(dir(cls)):
        if attr_name.startswith('_') and not attr_name.startswith('__'):
            continue
        
        try:
            attr = getattr(cls, attr_name)
            
            if isinstance(attr, property):
                prop_info = {
                    'name': attr_name,
                    'doc': (attr.fget.__doc__ if attr.fget else "") or "",
                    'readonly': attr.fset is None
                }
                info['properties'].append(prop_info)
            elif callable(attr) and not attr_name.startswith('__'):
                method_info = {
                    'name': attr_name,
                    'doc': attr.__doc__ or "",
                    'signature': format_signature(attr_name, attr.__doc__)
                }
                info['methods'].append(method_info)
        except:
            pass
    
    return info

def get_function_info(func: Any, name: str) -> Dict[str, Any]:
    """Extract information about a function."""
    return {
        'name': name,
        'doc': func.__doc__ or "",
        'signature': format_signature(name, func.__doc__)
    }

def generate_markdown_class(cls_info: Dict[str, Any]) -> List[str]:
    """Generate markdown documentation for a class."""
    lines = []
    
    # Class header
    lines.append(f"### class `{cls_info['name']}`")
    if cls_info['bases']:
        lines.append(f"*Inherits from: {', '.join(cls_info['bases'])}*")
    lines.append("")
    
    # Class description
    if cls_info['doc']:
        doc_lines = cls_info['doc'].strip().split('\n')
        # First line is usually the constructor signature
        if doc_lines and '(' in doc_lines[0]:
            lines.append(f"```python")
            lines.append(doc_lines[0])
            lines.append("```")
            lines.append("")
            # Rest is description
            if len(doc_lines) > 2:
                lines.extend(doc_lines[2:])
                lines.append("")
        else:
            lines.extend(doc_lines)
            lines.append("")
    
    # Properties
    if cls_info['properties']:
        lines.append("#### Properties")
        lines.append("")
        for prop in cls_info['properties']:
            readonly = " *(readonly)*" if prop['readonly'] else ""
            lines.append(f"- **`{prop['name']}`**{readonly}")
            if prop['doc']:
                lines.append(f"  - {prop['doc'].strip()}")
        lines.append("")
    
    # Methods
    if cls_info['methods']:
        lines.append("#### Methods")
        lines.append("")
        for method in cls_info['methods']:
            lines.append(f"##### `{method['signature']}`")
            if method['doc']:
                # Parse docstring for better formatting
                doc_lines = method['doc'].strip().split('\n')
                # Skip the signature line if it's repeated
                start = 1 if doc_lines and method['name'] in doc_lines[0] else 0
                for line in doc_lines[start:]:
                    lines.append(line)
            lines.append("")
    
    lines.append("---")
    lines.append("")
    return lines

def generate_markdown_function(func_info: Dict[str, Any]) -> List[str]:
    """Generate markdown documentation for a function."""
    lines = []
    
    lines.append(f"### `{func_info['signature']}`")
    lines.append("")
    
    if func_info['doc']:
        doc_lines = func_info['doc'].strip().split('\n')
        # Skip signature line if present
        start = 1 if doc_lines and func_info['name'] in doc_lines[0] else 0
        
        # Process documentation sections
        in_section = None
        for line in doc_lines[start:]:
            if line.strip() in ['Args:', 'Returns:', 'Raises:', 'Note:', 'Example:']:
                in_section = line.strip()
                lines.append(f"**{in_section}**")
            elif in_section and line.strip():
                # Indent content under sections
                lines.append(f"{line}")
            else:
                lines.append(line)
        lines.append("")
    
    lines.append("---")
    lines.append("")
    return lines

def generate_markdown_docs() -> str:
    """Generate complete markdown API documentation."""
    lines = []
    
    # Header
    lines.append("# McRogueFace API Reference")
    lines.append("")
    lines.append(f"*Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")
    
    # Module description
    if mcrfpy.__doc__:
        lines.append("## Overview")
        lines.append("")
        lines.extend(mcrfpy.__doc__.strip().split('\n'))
        lines.append("")
    
    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")
    lines.append("- [Classes](#classes)")
    lines.append("- [Functions](#functions)")
    lines.append("- [Automation Module](#automation-module)")
    lines.append("")
    
    # Collect all components
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
    
    # Document classes
    lines.append("## Classes")
    lines.append("")
    
    # Group classes by category
    ui_classes = []
    collection_classes = []
    system_classes = []
    other_classes = []
    
    for name, cls in classes:
        if name in ['Frame', 'Caption', 'Sprite', 'Grid', 'Entity']:
            ui_classes.append((name, cls))
        elif 'Collection' in name:
            collection_classes.append((name, cls))
        elif name in ['Color', 'Vector', 'Texture', 'Font']:
            system_classes.append((name, cls))
        else:
            other_classes.append((name, cls))
    
    # UI Classes
    if ui_classes:
        lines.append("### UI Components")
        lines.append("")
        for name, cls in ui_classes:
            lines.extend(generate_markdown_class(get_class_info(cls)))
    
    # Collections
    if collection_classes:
        lines.append("### Collections")
        lines.append("")
        for name, cls in collection_classes:
            lines.extend(generate_markdown_class(get_class_info(cls)))
    
    # System Classes
    if system_classes:
        lines.append("### System Types")
        lines.append("")
        for name, cls in system_classes:
            lines.extend(generate_markdown_class(get_class_info(cls)))
    
    # Other Classes
    if other_classes:
        lines.append("### Other Classes")
        lines.append("")
        for name, cls in other_classes:
            lines.extend(generate_markdown_class(get_class_info(cls)))
    
    # Document functions
    lines.append("## Functions")
    lines.append("")
    
    # Group functions by category
    scene_funcs = []
    audio_funcs = []
    ui_funcs = []
    system_funcs = []
    
    for name, func in functions:
        if 'scene' in name.lower() or name in ['createScene', 'setScene']:
            scene_funcs.append((name, func))
        elif any(x in name.lower() for x in ['sound', 'music', 'volume']):
            audio_funcs.append((name, func))
        elif name in ['find', 'findAll']:
            ui_funcs.append((name, func))
        else:
            system_funcs.append((name, func))
    
    # Scene Management
    if scene_funcs:
        lines.append("### Scene Management")
        lines.append("")
        for name, func in scene_funcs:
            lines.extend(generate_markdown_function(get_function_info(func, name)))
    
    # Audio
    if audio_funcs:
        lines.append("### Audio")
        lines.append("")
        for name, func in audio_funcs:
            lines.extend(generate_markdown_function(get_function_info(func, name)))
    
    # UI Utilities
    if ui_funcs:
        lines.append("### UI Utilities")
        lines.append("")
        for name, func in ui_funcs:
            lines.extend(generate_markdown_function(get_function_info(func, name)))
    
    # System
    if system_funcs:
        lines.append("### System")
        lines.append("")
        for name, func in system_funcs:
            lines.extend(generate_markdown_function(get_function_info(func, name)))
    
    # Automation module
    if hasattr(mcrfpy, 'automation'):
        lines.append("## Automation Module")
        lines.append("")
        lines.append("The `mcrfpy.automation` module provides testing and automation capabilities.")
        lines.append("")
        
        automation = mcrfpy.automation
        auto_funcs = []
        
        for name in sorted(dir(automation)):
            if not name.startswith('_'):
                obj = getattr(automation, name)
                if callable(obj):
                    auto_funcs.append((name, obj))
        
        for name, func in auto_funcs:
            # Format as static method
            func_info = get_function_info(func, name)
            lines.append(f"### `automation.{func_info['signature']}`")
            lines.append("")
            if func_info['doc']:
                lines.append(func_info['doc'])
                lines.append("")
            lines.append("---")
            lines.append("")
    
    return '\n'.join(lines)

def generate_html_docs(markdown_content: str) -> str:
    """Convert markdown to HTML."""
    # Simple conversion - in production use a proper markdown parser
    html = ['<!DOCTYPE html>']
    html.append('<html><head>')
    html.append('<meta charset="UTF-8">')
    html.append('<title>McRogueFace API Reference</title>')
    html.append('<style>')
    html.append('''
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
               line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; }
        h1, h2, h3, h4, h5 { color: #2c3e50; margin-top: 24px; }
        h1 { border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        h2 { border-bottom: 1px solid #ecf0f1; padding-bottom: 8px; }
        code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-size: 90%; }
        pre { background: #f4f4f4; padding: 12px; border-radius: 5px; overflow-x: auto; }
        pre code { background: none; padding: 0; }
        blockquote { border-left: 4px solid #3498db; margin: 0; padding-left: 16px; color: #7f8c8d; }
        hr { border: none; border-top: 1px solid #ecf0f1; margin: 24px 0; }
        a { color: #3498db; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .property { color: #27ae60; }
        .method { color: #2980b9; }
        .class-name { color: #8e44ad; font-weight: bold; }
        ul { padding-left: 24px; }
        li { margin: 4px 0; }
    ''')
    html.append('</style>')
    html.append('</head><body>')
    
    # Very basic markdown to HTML conversion
    lines = markdown_content.split('\n')
    in_code_block = False
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith('```'):
            if in_code_block:
                html.append('</code></pre>')
                in_code_block = False
            else:
                lang = stripped[3:] or 'python'
                html.append(f'<pre><code class="language-{lang}">')
                in_code_block = True
            continue
        
        if in_code_block:
            html.append(line)
            continue
        
        # Headers
        if stripped.startswith('#'):
            level = len(stripped.split()[0])
            text = stripped[level:].strip()
            html.append(f'<h{level}>{text}</h{level}>')
        # Lists
        elif stripped.startswith('- '):
            if not in_list:
                html.append('<ul>')
                in_list = True
            html.append(f'<li>{stripped[2:]}</li>')
        # Horizontal rule
        elif stripped == '---':
            if in_list:
                html.append('</ul>')
                in_list = False
            html.append('<hr>')
        # Emphasis
        elif stripped.startswith('*') and stripped.endswith('*') and len(stripped) > 2:
            html.append(f'<em>{stripped[1:-1]}</em>')
        # Bold
        elif stripped.startswith('**') and stripped.endswith('**'):
            html.append(f'<strong>{stripped[2:-2]}</strong>')
        # Regular paragraph
        elif stripped:
            if in_list:
                html.append('</ul>')
                in_list = False
            # Convert inline code
            text = stripped
            if '`' in text:
                import re
                text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
            html.append(f'<p>{text}</p>')
        else:
            if in_list:
                html.append('</ul>')
                in_list = False
            # Empty line
            html.append('')
    
    if in_list:
        html.append('</ul>')
    if in_code_block:
        html.append('</code></pre>')
    
    html.append('</body></html>')
    return '\n'.join(html)

def main():
    """Generate API documentation in multiple formats."""
    print("Generating McRogueFace API Documentation...")
    
    # Create docs directory
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Generate markdown documentation
    print("- Generating Markdown documentation...")
    markdown_content = generate_markdown_docs()
    
    # Write markdown
    md_path = docs_dir / "API_REFERENCE.md"
    with open(md_path, 'w') as f:
        f.write(markdown_content)
    print(f"  ✓ Written to {md_path}")
    
    # Generate HTML
    print("- Generating HTML documentation...")
    html_content = generate_html_docs(markdown_content)
    
    # Write HTML
    html_path = docs_dir / "api_reference.html"
    with open(html_path, 'w') as f:
        f.write(html_content)
    print(f"  ✓ Written to {html_path}")
    
    # Summary statistics
    lines = markdown_content.split('\n')
    class_count = markdown_content.count('### class')
    func_count = len([l for l in lines if l.strip().startswith('### `') and 'class' not in l])
    
    print("\nDocumentation Statistics:")
    print(f"- Classes documented: {class_count}")
    print(f"- Functions documented: {func_count}")
    print(f"- Total lines: {len(lines)}")
    print(f"- File size: {len(markdown_content):,} bytes")
    
    print("\nAPI documentation generated successfully!")

if __name__ == '__main__':
    main()