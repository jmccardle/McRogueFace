#!/usr/bin/env python3
"""
Comprehensive test for Issue #37: Windows scripts subdirectory bug

This test comprehensively tests script loading from different working directories,
particularly focusing on the Windows issue where relative paths fail.

The bug: On Windows, when mcrogueface.exe is run from a different directory,
it fails to find scripts/game.py because fopen uses relative paths.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import platform

def create_test_script(content=""):
    """Create a minimal test script"""
    if not content:
        content = """
import mcrfpy
print("TEST_SCRIPT_LOADED_FROM_PATH")
mcrfpy.createScene("test_scene")
# Exit cleanly to avoid hanging
import sys
sys.exit(0)
"""
    return content

def run_mcrogueface(exe_path, cwd, timeout=5):
    """Run mcrogueface from a specific directory and capture output"""
    cmd = [exe_path, "--headless"]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1

def test_script_loading():
    """Test script loading from various directories"""
    # Detect platform
    is_windows = platform.system() == "Windows"
    print(f"Platform: {platform.system()}")
    
    # Get paths
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    build_dir = os.path.join(repo_root, "build")
    exe_name = "mcrogueface.exe" if is_windows else "mcrogueface"
    exe_path = os.path.join(build_dir, exe_name)
    
    if not os.path.exists(exe_path):
        print(f"FAIL: Executable not found at {exe_path}")
        print("Please build the project first")
        return
    
    # Backup original game.py
    scripts_dir = os.path.join(build_dir, "scripts")
    game_py_path = os.path.join(scripts_dir, "game.py")
    game_py_backup = game_py_path + ".backup"
    
    if os.path.exists(game_py_path):
        shutil.copy(game_py_path, game_py_backup)
    
    try:
        # Create test script
        os.makedirs(scripts_dir, exist_ok=True)
        with open(game_py_path, "w") as f:
            f.write(create_test_script())
        
        print("\n=== Test 1: Run from build directory (baseline) ===")
        stdout, stderr, code = run_mcrogueface(exe_path, build_dir)
        if "TEST_SCRIPT_LOADED_FROM_PATH" in stdout:
            print("✓ PASS: Script loaded when running from build directory")
        else:
            print("✗ FAIL: Script not loaded from build directory")
            print(f"  stdout: {stdout[:200]}")
            print(f"  stderr: {stderr[:200]}")
        
        print("\n=== Test 2: Run from parent directory ===")
        stdout, stderr, code = run_mcrogueface(exe_path, repo_root)
        if "TEST_SCRIPT_LOADED_FROM_PATH" in stdout:
            print("✓ PASS: Script loaded from parent directory")
        else:
            print("✗ FAIL: Script not loaded from parent directory")
            print("  This might indicate Issue #37")
            print(f"  stdout: {stdout[:200]}")
            print(f"  stderr: {stderr[:200]}")
        
        print("\n=== Test 3: Run from system temp directory ===")
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_mcrogueface(exe_path, tmpdir)
            if "TEST_SCRIPT_LOADED_FROM_PATH" in stdout:
                print("✓ PASS: Script loaded from temp directory")
            else:
                print("✗ FAIL: Script not loaded from temp directory")
                print("  This is the core Issue #37 bug!")
                print(f"  Working directory: {tmpdir}")
                print(f"  stdout: {stdout[:200]}")
                print(f"  stderr: {stderr[:200]}")
        
        print("\n=== Test 4: Run with absolute path from different directory ===")
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use absolute path to executable
            abs_exe = os.path.abspath(exe_path)
            stdout, stderr, code = run_mcrogueface(abs_exe, tmpdir)
            if "TEST_SCRIPT_LOADED_FROM_PATH" in stdout:
                print("✓ PASS: Script loaded with absolute exe path")
            else:
                print("✗ FAIL: Script not loaded with absolute exe path")
                print(f"  stdout: {stdout[:200]}")
                print(f"  stderr: {stderr[:200]}")
        
        # Test 5: Symlink test (Unix only)
        if not is_windows:
            print("\n=== Test 5: Run via symlink (Unix only) ===")
            with tempfile.TemporaryDirectory() as tmpdir:
                symlink_path = os.path.join(tmpdir, "mcrogueface_link")
                os.symlink(exe_path, symlink_path)
                stdout, stderr, code = run_mcrogueface(symlink_path, tmpdir)
                if "TEST_SCRIPT_LOADED_FROM_PATH" in stdout:
                    print("✓ PASS: Script loaded via symlink")
                else:
                    print("✗ FAIL: Script not loaded via symlink")
                    print(f"  stdout: {stdout[:200]}")
                    print(f"  stderr: {stderr[:200]}")
        
        # Summary
        print("\n=== SUMMARY ===")
        print("Issue #37 is about script loading failing when the executable")
        print("is run from a different working directory than where it's located.")
        print("The fix should resolve the script path relative to the executable,")
        print("not the current working directory.")
        
    finally:
        # Restore original game.py
        if os.path.exists(game_py_backup):
            shutil.move(game_py_backup, game_py_path)
        print("\nTest cleanup complete")

if __name__ == "__main__":
    test_script_loading()