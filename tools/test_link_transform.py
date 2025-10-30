#!/usr/bin/env python3
"""Test script for link transformation function."""

import re

def transform_doc_links(docstring, format='html', base_url=''):
    """Transform MCRF_LINK patterns based on output format.

    Detects pattern: "See also: TEXT (docs/path.md)"
    Transforms to appropriate format for output type.
    """
    if not docstring:
        return docstring

    link_pattern = r'See also: ([^(]+) \(([^)]+)\)'

    def replace_link(match):
        text, ref = match.group(1).strip(), match.group(2).strip()

        if format == 'html':
            # Convert docs/foo.md → foo.html
            href = ref.replace('docs/', '').replace('.md', '.html')
            return f'<p class="see-also">See also: <a href="{href}">{text}</a></p>'

        elif format == 'web':
            # Link to hosted docs
            web_path = ref.replace('docs/', '').replace('.md', '')
            return f'<p class="see-also">See also: <a href="{base_url}/{web_path}">{text}</a></p>'

        elif format == 'markdown':
            # Markdown link
            return f'\n**See also:** [{text}]({ref})'

        else:  # 'python' or default
            # Keep as plain text for Python docstrings
            return match.group(0)

    return re.sub(link_pattern, replace_link, docstring)

# Test cases
test_doc = "Description text.\n\nSee also: Tutorial Guide (docs/guide.md)\n\nMore text."

html_result = transform_doc_links(test_doc, format='html')
print("HTML:", html_result)
assert '<a href="guide.html">Tutorial Guide</a>' in html_result

md_result = transform_doc_links(test_doc, format='markdown')
print("Markdown:", md_result)
assert '[Tutorial Guide](docs/guide.md)' in md_result

plain_result = transform_doc_links(test_doc, format='python')
print("Python:", plain_result)
assert 'See also: Tutorial Guide (docs/guide.md)' in plain_result

print("\nSUCCESS: All transformations work correctly")
