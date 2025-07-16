#!/usr/bin/env python3
"""
Dynamic documentation generator for McRogueFace.
Extracts all documentation directly from the compiled module using introspection.
"""

import os
import sys
import inspect
import datetime
import html
import re
from pathlib import Path

# Must be run with McRogueFace as interpreter
try:
    import mcrfpy
except ImportError:
    print("Error: This script must be run with McRogueFace as the interpreter")
    print("Usage: ./build/mcrogueface --exec generate_dynamic_docs.py")
    sys.exit(1)

def parse_docstring(docstring):
    """Parse a docstring to extract signature, description, args, and returns."""
    if not docstring:
        return {"signature": "", "description": "", "args": [], "returns": "", "example": ""}
    
    lines = docstring.strip().split('\n')
    result = {
        "signature": "",
        "description": "",
        "args": [],
        "returns": "",
        "example": ""
    }
    
    # First line often contains the signature
    if lines and '(' in lines[0] and ')' in lines[0]:
        result["signature"] = lines[0].strip()
        lines = lines[1:] if len(lines) > 1 else []
    
    # Parse the rest
    current_section = "description"
    description_lines = []
    example_lines = []
    in_example = False
    
    for line in lines:
        line_lower = line.strip().lower()
        
        if line_lower.startswith("args:") or line_lower.startswith("arguments:"):
            current_section = "args"
            continue
        elif line_lower.startswith("returns:") or line_lower.startswith("return:"):
            current_section = "returns"
            result["returns"] = line[line.find(':')+1:].strip()
            continue
        elif line_lower.startswith("example:") or line_lower.startswith("examples:"):
            in_example = True
            continue
        elif line_lower.startswith("note:"):
            if description_lines:
                description_lines.append("")
            description_lines.append(line)
            continue
            
        if in_example:
            example_lines.append(line)
        elif current_section == "description" and not line.startswith("    "):
            description_lines.append(line)
        elif current_section == "args" and line.strip():
            # Parse argument lines like "    x: X coordinate"
            match = re.match(r'\s+(\w+):\s*(.+)', line)
            if match:
                result["args"].append({
                    "name": match.group(1),
                    "description": match.group(2).strip()
                })
        elif current_section == "returns" and line.strip() and line.startswith("    "):
            result["returns"] += " " + line.strip()
    
    result["description"] = '\n'.join(description_lines).strip()
    result["example"] = '\n'.join(example_lines).strip()
    
    return result

def get_all_functions():
    """Get all module-level functions."""
    functions = {}
    for name in dir(mcrfpy):
        if name.startswith('_'):
            continue
        obj = getattr(mcrfpy, name)
        if inspect.isbuiltin(obj) or inspect.isfunction(obj):
            doc_info = parse_docstring(obj.__doc__)
            functions[name] = {
                "name": name,
                "doc": obj.__doc__ or "",
                "parsed": doc_info
            }
    return functions

def get_all_classes():
    """Get all classes and their methods/properties."""
    classes = {}
    for name in dir(mcrfpy):
        if name.startswith('_'):
            continue
        obj = getattr(mcrfpy, name)
        if inspect.isclass(obj):
            class_info = {
                "name": name,
                "doc": obj.__doc__ or "",
                "methods": {},
                "properties": {},
                "bases": [base.__name__ for base in obj.__bases__ if base.__name__ != 'object']
            }
            
            # Get methods and properties
            for attr_name in dir(obj):
                if attr_name.startswith('__') and attr_name != '__init__':
                    continue
                    
                try:
                    attr = getattr(obj, attr_name)
                    if callable(attr):
                        method_doc = attr.__doc__ or ""
                        class_info["methods"][attr_name] = {
                            "doc": method_doc,
                            "parsed": parse_docstring(method_doc)
                        }
                    elif isinstance(attr, property):
                        prop_doc = (attr.fget.__doc__ if attr.fget else "") or ""
                        class_info["properties"][attr_name] = {
                            "doc": prop_doc,
                            "readonly": attr.fset is None
                        }
                except:
                    pass
            
            classes[name] = class_info
    return classes

def get_constants():
    """Get module constants."""
    constants = {}
    for name in dir(mcrfpy):
        if name.startswith('_') or name[0].islower():
            continue
        obj = getattr(mcrfpy, name)
        if not (inspect.isclass(obj) or callable(obj)):
            constants[name] = {
                "name": name,
                "value": repr(obj) if not name.startswith('default_') else f"<{name}>",
                "type": type(obj).__name__
            }
    return constants

def generate_html_docs():
    """Generate HTML documentation."""
    functions = get_all_functions()
    classes = get_all_classes()
    constants = get_constants()
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>McRogueFace API Reference</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3, h4, h5 {{
            color: #2c3e50;
        }}
        .toc {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 4px;
            margin-bottom: 30px;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 20px;
        }}
        .toc > ul {{
            padding-left: 0;
        }}
        .toc a {{
            text-decoration: none;
            color: #3498db;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        .method-section {{
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border-left: 4px solid #3498db;
        }}
        .function-signature {{
            font-family: 'Consolas', 'Monaco', monospace;
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .class-name {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .method-name {{
            color: #3498db;
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        .property-name {{
            color: #27ae60;
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        .arg-name {{
            color: #8b4513;
            font-weight: bold;
        }}
        .arg-type {{
            color: #666;
            font-style: italic;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .deprecated {{
            text-decoration: line-through;
            opacity: 0.6;
        }}
        .note {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
        }}
        .returns {{
            color: #28a745;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>McRogueFace API Reference</h1>
        <p><em>Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        <p><em>This documentation was dynamically generated from the compiled module.</em></p>
        
        <div class="toc">
            <h2>Table of Contents</h2>
            <ul>
                <li><a href="#functions">Functions</a></li>
                <li><a href="#classes">Classes</a>
                    <ul>
"""
    
    # Add classes to TOC
    for class_name in sorted(classes.keys()):
        html_content += f'                        <li><a href="#{class_name}">{class_name}</a></li>\n'
    
    html_content += """                    </ul>
                </li>
                <li><a href="#constants">Constants</a></li>
            </ul>
        </div>
        
        <h2 id="functions">Functions</h2>
"""
    
    # Generate function documentation
    for func_name in sorted(functions.keys()):
        func_info = functions[func_name]
        parsed = func_info["parsed"]
        
        html_content += f"""
        <div class="method-section">
            <h3><code class="function-signature">{func_name}{parsed['signature'] if parsed['signature'] else '(...)'}</code></h3>
            <p>{html.escape(parsed['description'])}</p>
"""
        
        if parsed['args']:
            html_content += "            <h4>Arguments:</h4>\n            <ul>\n"
            for arg in parsed['args']:
                html_content += f"                <li><span class='arg-name'>{arg['name']}</span>: {html.escape(arg['description'])}</li>\n"
            html_content += "            </ul>\n"
        
        if parsed['returns']:
            html_content += f"            <p><span class='returns'>Returns:</span> {html.escape(parsed['returns'])}</p>\n"
        
        if parsed['example']:
            html_content += f"            <h4>Example:</h4>\n            <pre><code>{html.escape(parsed['example'])}</code></pre>\n"
        
        html_content += "        </div>\n"
    
    # Generate class documentation
    html_content += "\n        <h2 id='classes'>Classes</h2>\n"
    
    for class_name in sorted(classes.keys()):
        class_info = classes[class_name]
        
        html_content += f"""
        <div class="method-section">
            <h3 id="{class_name}"><span class="class-name">{class_name}</span></h3>
"""
        
        if class_info['bases']:
            html_content += f"            <p><em>Inherits from: {', '.join(class_info['bases'])}</em></p>\n"
        
        if class_info['doc']:
            html_content += f"            <p>{html.escape(class_info['doc'])}</p>\n"
        
        # Properties
        if class_info['properties']:
            html_content += "            <h4>Properties:</h4>\n            <ul>\n"
            for prop_name, prop_info in sorted(class_info['properties'].items()):
                readonly = " (read-only)" if prop_info['readonly'] else ""
                html_content += f"                <li><span class='property-name'>{prop_name}</span>{readonly}"
                if prop_info['doc']:
                    html_content += f": {html.escape(prop_info['doc'])}"
                html_content += "</li>\n"
            html_content += "            </ul>\n"
        
        # Methods
        if class_info['methods']:
            html_content += "            <h4>Methods:</h4>\n"
            for method_name, method_info in sorted(class_info['methods'].items()):
                if method_name == '__init__':
                    continue
                parsed = method_info['parsed']
                
                html_content += f"""
            <div style="margin-left: 20px; margin-bottom: 15px;">
                <h5><code class="method-name">{method_name}{parsed['signature'] if parsed['signature'] else '(...)'}</code></h5>
"""
                
                if parsed['description']:
                    html_content += f"                <p>{html.escape(parsed['description'])}</p>\n"
                
                if parsed['args']:
                    html_content += "                <div style='margin-left: 20px;'>\n"
                    for arg in parsed['args']:
                        html_content += f"                    <div><span class='arg-name'>{arg['name']}</span>: {html.escape(arg['description'])}</div>\n"
                    html_content += "                </div>\n"
                
                if parsed['returns']:
                    html_content += f"                <p style='margin-left: 20px;'><span class='returns'>Returns:</span> {html.escape(parsed['returns'])}</p>\n"
                
                html_content += "            </div>\n"
        
        html_content += "        </div>\n"
    
    # Constants
    html_content += "\n        <h2 id='constants'>Constants</h2>\n        <ul>\n"
    for const_name, const_info in sorted(constants.items()):
        html_content += f"            <li><code>{const_name}</code> ({const_info['type']}): {const_info['value']}</li>\n"
    html_content += "        </ul>\n"
    
    html_content += """
    </div>
</body>
</html>
"""
    
    # Write the file
    output_path = Path("docs/api_reference_dynamic.html")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(html_content)
    print(f"Generated {output_path}")
    print(f"Found {len(functions)} functions, {len(classes)} classes, {len(constants)} constants")

def generate_markdown_docs():
    """Generate Markdown documentation."""
    functions = get_all_functions()
    classes = get_all_classes()
    constants = get_constants()
    
    md_content = f"""# McRogueFace API Reference

*Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

*This documentation was dynamically generated from the compiled module.*

## Table of Contents

- [Functions](#functions)
- [Classes](#classes)
"""
    
    # Add classes to TOC
    for class_name in sorted(classes.keys()):
        md_content += f"  - [{class_name}](#{class_name.lower()})\n"
    
    md_content += "- [Constants](#constants)\n\n"
    
    # Functions
    md_content += "## Functions\n\n"
    
    for func_name in sorted(functions.keys()):
        func_info = functions[func_name]
        parsed = func_info["parsed"]
        
        md_content += f"### `{func_name}{parsed['signature'] if parsed['signature'] else '(...)'}`\n\n"
        
        if parsed['description']:
            md_content += f"{parsed['description']}\n\n"
        
        if parsed['args']:
            md_content += "**Arguments:**\n"
            for arg in parsed['args']:
                md_content += f"- `{arg['name']}`: {arg['description']}\n"
            md_content += "\n"
        
        if parsed['returns']:
            md_content += f"**Returns:** {parsed['returns']}\n\n"
        
        if parsed['example']:
            md_content += f"**Example:**\n```python\n{parsed['example']}\n```\n\n"
    
    # Classes
    md_content += "## Classes\n\n"
    
    for class_name in sorted(classes.keys()):
        class_info = classes[class_name]
        
        md_content += f"### {class_name}\n\n"
        
        if class_info['bases']:
            md_content += f"*Inherits from: {', '.join(class_info['bases'])}*\n\n"
        
        if class_info['doc']:
            md_content += f"{class_info['doc']}\n\n"
        
        # Properties
        if class_info['properties']:
            md_content += "**Properties:**\n"
            for prop_name, prop_info in sorted(class_info['properties'].items()):
                readonly = " *(read-only)*" if prop_info['readonly'] else ""
                md_content += f"- `{prop_name}`{readonly}"
                if prop_info['doc']:
                    md_content += f": {prop_info['doc']}"
                md_content += "\n"
            md_content += "\n"
        
        # Methods
        if class_info['methods']:
            md_content += "**Methods:**\n\n"
            for method_name, method_info in sorted(class_info['methods'].items()):
                if method_name == '__init__':
                    continue
                parsed = method_info['parsed']
                
                md_content += f"#### `{method_name}{parsed['signature'] if parsed['signature'] else '(...)'}`\n\n"
                
                if parsed['description']:
                    md_content += f"{parsed['description']}\n\n"
                
                if parsed['args']:
                    md_content += "**Arguments:**\n"
                    for arg in parsed['args']:
                        md_content += f"- `{arg['name']}`: {arg['description']}\n"
                    md_content += "\n"
                
                if parsed['returns']:
                    md_content += f"**Returns:** {parsed['returns']}\n\n"
    
    # Constants
    md_content += "## Constants\n\n"
    for const_name, const_info in sorted(constants.items()):
        md_content += f"- `{const_name}` ({const_info['type']}): {const_info['value']}\n"
    
    # Write the file
    output_path = Path("docs/API_REFERENCE_DYNAMIC.md")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(md_content)
    print(f"Generated {output_path}")

if __name__ == "__main__":
    print("Generating dynamic documentation from mcrfpy module...")
    generate_html_docs()
    generate_markdown_docs()
    print("Documentation generation complete!")