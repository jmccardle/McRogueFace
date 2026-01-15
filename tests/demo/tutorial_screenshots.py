#!/usr/bin/env python3
"""
Tutorial Screenshot Generator

Usage:
    ./mcrogueface --headless --exec tests/demo/tutorial_screenshots.py

Extracts code from tutorial markdown files and generates screenshots.
"""
import mcrfpy
from mcrfpy import automation
import sys
import os
import re

# Paths
DOCS_REPO = "/opt/goblincorps/repos/mcrogueface.github.io"
TUTORIAL_DIR = os.path.join(DOCS_REPO, "tutorial")
OUTPUT_DIR = os.path.join(DOCS_REPO, "images", "tutorials")

# Tutorials to process (in order)
TUTORIALS = [
    "part_01_grid_movement.md",
    "part_02_tiles_collision.md",
    "part_03_dungeon_generation.md",
    "part_04_fov.md",
    "part_05_enemies.md",
    "part_06_combat.md",
    "part_07_ui.md",
]


def extract_code_from_markdown(filepath):
    """Extract the main Python code block from a tutorial markdown file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Find code blocks after "## The Complete Code" header
    # Look for the first python code block after that header
    complete_code_match = re.search(
        r'##\s+The Complete Code.*?```python\s*\n(.*?)```',
        content,
        re.DOTALL | re.IGNORECASE
    )

    if complete_code_match:
        return complete_code_match.group(1)

    # Fallback: just get the first large python code block
    code_blocks = re.findall(r'```python\s*\n(.*?)```', content, re.DOTALL)
    if code_blocks:
        # Return the largest code block (likely the main example)
        return max(code_blocks, key=len)

    return None


def add_screenshot_hook(code, screenshot_path):
    """Add screenshot capture code to the end of the script."""
    # Add code to take screenshot after a brief delay
    hook_code = f'''

# === Screenshot capture hook (added by tutorial_screenshots.py) ===
import mcrfpy
from mcrfpy import automation
import sys

_screenshot_taken = [False]

def _take_screenshot(timer, runtime):
    if not _screenshot_taken[0]:
        _screenshot_taken[0] = True
        automation.screenshot("{screenshot_path}")
        print(f"Screenshot saved: {screenshot_path}")
        sys.exit(0)

# Wait a moment for scene to render, then capture
mcrfpy.Timer("_screenshot_hook", _take_screenshot, 200)
'''
    return code + hook_code


class TutorialScreenshotter:
    """Manages tutorial screenshot generation."""

    def __init__(self):
        self.tutorials = []
        self.current_index = 0

    def load_tutorials(self):
        """Load and parse all tutorial files."""
        for filename in TUTORIALS:
            filepath = os.path.join(TUTORIAL_DIR, filename)
            if not os.path.exists(filepath):
                print(f"Warning: {filepath} not found, skipping")
                continue

            code = extract_code_from_markdown(filepath)
            if code:
                # Generate output filename
                base = os.path.splitext(filename)[0]
                screenshot_name = f"{base}.png"
                self.tutorials.append({
                    'name': filename,
                    'code': code,
                    'screenshot': screenshot_name,
                    'filepath': filepath,
                })
                print(f"Loaded: {filename}")
            else:
                print(f"Warning: No code found in {filename}")

    def run(self):
        """Generate all screenshots."""
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        print(f"\nGenerating {len(self.tutorials)} tutorial screenshots...")
        print(f"Output directory: {OUTPUT_DIR}\n")

        self.process_next()

    def process_next(self):
        """Process the next tutorial."""
        if self.current_index >= len(self.tutorials):
            print("\nAll screenshots generated!")
            sys.exit(0)
            return

        tutorial = self.tutorials[self.current_index]
        print(f"[{self.current_index + 1}/{len(self.tutorials)}] Processing {tutorial['name']}...")

        # Add screenshot hook to the code
        screenshot_path = os.path.join(OUTPUT_DIR, tutorial['screenshot'])
        modified_code = add_screenshot_hook(tutorial['code'], screenshot_path)

        # Write to temp file and execute
        temp_path = f"/tmp/tutorial_screenshot_{self.current_index}.py"
        with open(temp_path, 'w') as f:
            f.write(modified_code)

        try:
            # Execute the code
            exec(compile(modified_code, temp_path, 'exec'), {'__name__': '__main__'})
        except Exception as e:
            print(f"Error processing {tutorial['name']}: {e}")
            self.current_index += 1
            self.process_next()
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass


def main():
    """Main entry point."""
    screenshotter = TutorialScreenshotter()
    screenshotter.load_tutorials()

    if not screenshotter.tutorials:
        print("No tutorials found to process!")
        sys.exit(1)

    screenshotter.run()


# Run when executed
main()
