#!/usr/bin/env python3
"""
Test for Issue #37: Windows scripts subdirectory not checked for .py files

This test checks if the game can find and load scripts/game.py from different working directories.
On Windows, this often fails because fopen uses relative paths without resolving them.
"""

import os
import sys
import subprocess
import tempfile
import shutil

def test_script_loading():
    # Create a temporary directory to test from
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Testing from directory: {tmpdir}")
        
        # Get the build directory (assuming we're running from the repo root)
        build_dir = os.path.abspath("build")
        mcrogueface_exe = os.path.join(build_dir, "mcrogueface")
        if os.name == "nt":  # Windows
            mcrogueface_exe += ".exe"
        
        # Create a simple test script that the game should load
        test_script = """
import mcrfpy
print("TEST SCRIPT LOADED SUCCESSFULLY")
test_scene = mcrfpy.Scene("test_scene")
"""
        
        # Save the original game.py
        game_py_path = os.path.join(build_dir, "scripts", "game.py")
        game_py_backup = game_py_path + ".backup"
        if os.path.exists(game_py_path):
            shutil.copy(game_py_path, game_py_backup)
        
        try:
            # Replace game.py with our test script
            os.makedirs(os.path.dirname(game_py_path), exist_ok=True)
            with open(game_py_path, "w") as f:
                f.write(test_script)
            
            # Test 1: Run from build directory (should work)
            print("\nTest 1: Running from build directory...")
            result = subprocess.run(
                [mcrogueface_exe, "--headless", "-c", "print('Test 1 complete')"],
                cwd=build_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if "TEST SCRIPT LOADED SUCCESSFULLY" in result.stdout:
                print("✓ Test 1 PASSED: Script loaded from build directory")
            else:
                print("✗ Test 1 FAILED: Script not loaded from build directory")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
            
            # Test 2: Run from temporary directory (often fails on Windows)
            print("\nTest 2: Running from different working directory...")
            result = subprocess.run(
                [mcrogueface_exe, "--headless", "-c", "print('Test 2 complete')"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if "TEST SCRIPT LOADED SUCCESSFULLY" in result.stdout:
                print("✓ Test 2 PASSED: Script loaded from different directory")
            else:
                print("✗ Test 2 FAILED: Script not loaded from different directory")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                print("\nThis is the bug described in Issue #37!")
            
        finally:
            # Restore original game.py
            if os.path.exists(game_py_backup):
                shutil.move(game_py_backup, game_py_path)

if __name__ == "__main__":
    test_script_loading()