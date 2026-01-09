#!/usr/bin/env python3
"""
McRogueFace Standard Library Packager

Creates light/full stdlib variants from Python source or existing stdlib.
Compiles to .pyc bytecode and creates platform-appropriate zip archives.

Usage:
    python3 package_stdlib.py --preset light --platform windows --output dist/
    python3 package_stdlib.py --preset full --platform linux --output dist/
"""

import argparse
import compileall
import fnmatch
import os
import py_compile
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

# Try to import yaml, fall back to simple parser if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_FILE = SCRIPT_DIR / "stdlib_modules.yaml"

# Default module lists if YAML not available or for fallback
DEFAULT_CORE = [
    'abc', 'codecs', 'encodings', 'enum', 'genericpath', 'io', 'os',
    'posixpath', 'ntpath', 'stat', '_collections_abc', '_sitebuiltins',
    'site', 'types', 'warnings', 'reprlib', 'keyword', 'operator',
    'linecache', 'tokenize', 'token'
]

DEFAULT_GAMEDEV = [
    'random', 'json', 'collections', 'dataclasses', 'pathlib', 're',
    'functools', 'itertools', 'bisect', 'heapq', 'copy', 'weakref', 'colorsys'
]

DEFAULT_UTILITY = [
    'contextlib', 'datetime', 'time', 'calendar', 'string', 'textwrap',
    'shutil', 'tempfile', 'glob', 'fnmatch', 'hashlib', 'hmac', 'base64',
    'binascii', 'struct', 'array', 'queue', 'threading', '_threading_local'
]

DEFAULT_TYPING = ['typing', 'annotationlib']

DEFAULT_DATA = [
    'pickle', 'csv', 'configparser', 'zipfile', 'tarfile',
    'gzip', 'bz2', 'lzma'
]

DEFAULT_EXCLUDE = [
    'test', 'tests', 'idlelib', 'idle', 'ensurepip', 'tkinter', 'turtle',
    'turtledemo', 'pydoc', 'pydoc_data', 'lib2to3', 'distutils', 'venv',
    '__phello__', '_pyrepl'
]

EXCLUDE_PATTERNS = [
    '**/test_*.py', '**/tests/**', '**/*_test.py', '**/__pycache__/**',
    '**/*.pyc', '**/*.pyo'
]


def parse_yaml_config():
    """Parse the YAML configuration file."""
    if not HAS_YAML:
        return None

    if not CONFIG_FILE.exists():
        return None

    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)


def get_module_list(preset: str, config: dict = None) -> tuple:
    """Get the list of modules to include and patterns to exclude."""
    if config and 'presets' in config and preset in config['presets']:
        preset_config = config['presets'][preset]
        include_categories = preset_config.get('include', [])
        exclude_patterns = preset_config.get('exclude_patterns', EXCLUDE_PATTERNS)

        modules = []
        for category in include_categories:
            if category in config:
                modules.extend(config[category])

        # Always add exclude list
        exclude_modules = config.get('exclude', DEFAULT_EXCLUDE)

        return modules, exclude_modules, exclude_patterns

    # Fallback to defaults
    if preset == 'light':
        modules = DEFAULT_CORE + DEFAULT_GAMEDEV + DEFAULT_UTILITY + DEFAULT_TYPING + DEFAULT_DATA
    else:  # full
        modules = DEFAULT_CORE + DEFAULT_GAMEDEV + DEFAULT_UTILITY + DEFAULT_TYPING + DEFAULT_DATA
        # Add more for full build (text, debug, network, async, system would be added here)

    return modules, DEFAULT_EXCLUDE, EXCLUDE_PATTERNS


def should_include_file(filepath: Path, include_modules: list, exclude_modules: list,
                        exclude_patterns: list) -> bool:
    """Determine if a file should be included in the stdlib."""
    rel_path = str(filepath)

    # Check exclude patterns first
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return False

    # Get the top-level module name
    parts = filepath.parts
    if not parts:
        return False

    # Remove file extension properly (handle .pyc before .py to avoid partial match)
    top_module = parts[0]
    if top_module.endswith('.pyc'):
        top_module = top_module[:-4]
    elif top_module.endswith('.py'):
        top_module = top_module[:-3]

    # Check if explicitly excluded
    if top_module in exclude_modules:
        return False

    # For preset-based filtering, check if module is in include list
    # But be permissive - include if it's a submodule of an included module
    # or if it's a standalone .py file that matches
    for mod in include_modules:
        if top_module == mod or top_module.startswith(mod + '.'):
            return True
        # Check for directory modules
        if mod in parts:
            return True

    return False


def compile_to_pyc(src_dir: Path, dest_dir: Path, include_modules: list,
                   exclude_modules: list, exclude_patterns: list) -> int:
    """Compile Python source files to .pyc bytecode."""
    count = 0

    for src_file in src_dir.rglob('*.py'):
        rel_path = src_file.relative_to(src_dir)

        if not should_include_file(rel_path, include_modules, exclude_modules, exclude_patterns):
            continue

        # Determine destination path (replace .py with .pyc)
        dest_file = dest_dir / rel_path.with_suffix('.pyc')
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Compile to bytecode
            py_compile.compile(str(src_file), str(dest_file), doraise=True)
            count += 1
        except py_compile.PyCompileError as e:
            print(f"Warning: Failed to compile {src_file}: {e}", file=sys.stderr)

    return count


def repackage_existing_zip(src_zip: Path, dest_zip: Path, include_modules: list,
                           exclude_modules: list, exclude_patterns: list) -> int:
    """Repackage an existing stdlib zip with filtering."""
    count = 0

    with zipfile.ZipFile(src_zip, 'r') as src:
        with zipfile.ZipFile(dest_zip, 'w', zipfile.ZIP_DEFLATED) as dest:
            for info in src.infolist():
                rel_path = Path(info.filename)

                if not should_include_file(rel_path, include_modules, exclude_modules, exclude_patterns):
                    continue

                # Copy the file
                data = src.read(info.filename)
                dest.writestr(info, data)
                count += 1

    return count


def create_stdlib_zip(source: Path, output: Path, preset: str,
                      platform: str, config: dict = None) -> Path:
    """Create a stdlib zip file from source directory or existing zip."""
    include_modules, exclude_modules, exclude_patterns = get_module_list(preset, config)

    # Determine output filename
    output_name = f"python314-{preset}.zip"
    output_path = output / output_name
    output.mkdir(parents=True, exist_ok=True)

    if source.suffix == '.zip':
        # Repackage existing zip
        print(f"Repackaging {source} -> {output_path}")
        count = repackage_existing_zip(source, output_path, include_modules,
                                       exclude_modules, exclude_patterns)
    else:
        # Compile from source directory
        print(f"Compiling {source} -> {output_path}")
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            count = compile_to_pyc(source, tmp_path, include_modules,
                                   exclude_modules, exclude_patterns)

            # Create zip from compiled files
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for pyc_file in tmp_path.rglob('*.pyc'):
                    arc_name = pyc_file.relative_to(tmp_path)
                    zf.write(pyc_file, arc_name)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Created {output_path} ({count} files, {size_mb:.2f} MB)")

    return output_path


def find_stdlib_source(platform: str) -> Path:
    """Find the stdlib source for the given platform."""
    if platform == 'windows':
        # Check for existing Windows stdlib zip
        win_stdlib = PROJECT_ROOT / '__lib_windows' / 'python314.zip'
        if win_stdlib.exists():
            return win_stdlib

        # Fall back to cpython source
        cpython_lib = PROJECT_ROOT / 'modules' / 'cpython' / 'Lib'
        if cpython_lib.exists():
            return cpython_lib
    else:  # linux
        # Check for existing Linux stdlib
        linux_stdlib = PROJECT_ROOT / '__lib' / 'Python' / 'Lib'
        if linux_stdlib.exists():
            return linux_stdlib

        # Fall back to cpython source
        cpython_lib = PROJECT_ROOT / 'modules' / 'cpython' / 'Lib'
        if cpython_lib.exists():
            return cpython_lib

    raise FileNotFoundError(f"Could not find stdlib source for {platform}")


def main():
    parser = argparse.ArgumentParser(description='Package McRogueFace Python stdlib')
    parser.add_argument('--preset', choices=['light', 'full'], default='full',
                        help='Stdlib preset (default: full)')
    parser.add_argument('--platform', choices=['windows', 'linux'], required=True,
                        help='Target platform')
    parser.add_argument('--output', type=Path, default=Path('dist'),
                        help='Output directory (default: dist)')
    parser.add_argument('--source', type=Path, default=None,
                        help='Override stdlib source (zip or directory)')
    parser.add_argument('--list-modules', action='store_true',
                        help='List modules for preset and exit')

    args = parser.parse_args()

    # Parse config
    config = parse_yaml_config()

    if args.list_modules:
        include, exclude, patterns = get_module_list(args.preset, config)
        print(f"Preset: {args.preset}")
        print(f"Include modules ({len(include)}):")
        for mod in sorted(include):
            print(f"  {mod}")
        print(f"\nExclude modules ({len(exclude)}):")
        for mod in sorted(exclude):
            print(f"  {mod}")
        return 0

    # Find source
    if args.source:
        source = args.source
    else:
        source = find_stdlib_source(args.platform)

    print(f"Source: {source}")
    print(f"Preset: {args.preset}")
    print(f"Platform: {args.platform}")

    # Create stdlib zip
    create_stdlib_zip(source, args.output, args.preset, args.platform, config)

    return 0


if __name__ == '__main__':
    sys.exit(main())
