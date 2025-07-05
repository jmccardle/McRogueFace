#!/usr/bin/env python3
"""
Test runner for high-priority McRogueFace issues

This script runs comprehensive tests for the highest priority bugs that can be fixed rapidly.
Each test is designed to fail initially (demonstrating the bug) and pass after the fix.
"""

import os
import sys
import subprocess
import time

# Test configurations
TESTS = [
    {
        "issue": "37",
        "name": "Windows scripts subdirectory bug",
        "script": "issue_37_windows_scripts_comprehensive_test.py",
        "needs_game_loop": False,
        "description": "Tests script loading from different working directories"
    },
    {
        "issue": "76", 
        "name": "UIEntityCollection returns wrong type",
        "script": "issue_76_uientitycollection_type_test.py",
        "needs_game_loop": True,
        "description": "Tests type preservation for derived Entity classes in collections"
    },
    {
        "issue": "9",
        "name": "RenderTexture resize bug",
        "script": "issue_9_rendertexture_resize_test.py", 
        "needs_game_loop": True,
        "description": "Tests UIGrid rendering with sizes beyond 1920x1080"
    },
    {
        "issue": "26/28",
        "name": "Iterator implementation for collections",
        "script": "issue_26_28_iterator_comprehensive_test.py",
        "needs_game_loop": True,
        "description": "Tests Python sequence protocol for UI collections"
    }
]

def run_test(test_config, mcrogueface_path):
    """Run a single test and return the result"""
    script_path = os.path.join(os.path.dirname(__file__), test_config["script"])
    
    if not os.path.exists(script_path):
        return f"SKIP - Test script not found: {script_path}"
    
    print(f"\n{'='*60}")
    print(f"Running test for Issue #{test_config['issue']}: {test_config['name']}")
    print(f"Description: {test_config['description']}")
    print(f"Script: {test_config['script']}")
    print(f"{'='*60}\n")
    
    if test_config["needs_game_loop"]:
        # Run with game loop using --exec
        cmd = [mcrogueface_path, "--headless", "--exec", script_path]
    else:
        # Run directly as Python script
        cmd = [sys.executable, script_path]
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        elapsed = time.time() - start_time
        
        # Check for pass/fail in output
        output = result.stdout + result.stderr
        
        if "PASS" in output and "FAIL" not in output:
            status = "PASS"
        elif "FAIL" in output:
            status = "FAIL"
        else:
            status = "UNKNOWN"
        
        # Look for specific bug indicators
        bug_found = False
        if test_config["issue"] == "37" and "Script not loaded from different directory" in output:
            bug_found = True
        elif test_config["issue"] == "76" and "type lost!" in output:
            bug_found = True
        elif test_config["issue"] == "9" and "clipped at 1920x1080" in output:
            bug_found = True
        elif test_config["issue"] == "26/28" and "not implemented" in output:
            bug_found = True
        
        return {
            "status": status,
            "bug_found": bug_found,
            "elapsed": elapsed,
            "output": output if len(output) < 1000 else output[:1000] + "\n... (truncated)"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "bug_found": False,
            "elapsed": 30,
            "output": "Test timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "status": "ERROR", 
            "bug_found": False,
            "elapsed": 0,
            "output": str(e)
        }

def main():
    """Run all tests and provide summary"""
    # Find mcrogueface executable
    build_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "build")
    mcrogueface_path = os.path.join(build_dir, "mcrogueface")
    
    if not os.path.exists(mcrogueface_path):
        print(f"ERROR: mcrogueface executable not found at {mcrogueface_path}")
        print("Please build the project first with 'make'")
        return 1
    
    print("McRogueFace Issue Test Suite")
    print(f"Executable: {mcrogueface_path}")
    print(f"Running {len(TESTS)} tests...\n")
    
    results = []
    
    for test in TESTS:
        result = run_test(test, mcrogueface_path)
        results.append((test, result))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}\n")
    
    bugs_found = 0
    tests_passed = 0
    
    for test, result in results:
        if isinstance(result, str):
            print(f"Issue #{test['issue']}: {result}")
        else:
            status_str = result['status']
            if result['bug_found']:
                status_str += " (BUG CONFIRMED)"
                bugs_found += 1
            elif result['status'] == 'PASS':
                tests_passed += 1
            
            print(f"Issue #{test['issue']}: {status_str} ({result['elapsed']:.2f}s)")
            
            if result['status'] not in ['PASS', 'UNKNOWN']:
                print(f"  Details: {result['output'].splitlines()[0] if result['output'] else 'No output'}")
    
    print(f"\nBugs confirmed: {bugs_found}/{len(TESTS)}")
    print(f"Tests passed: {tests_passed}/{len(TESTS)}")
    
    if bugs_found > 0:
        print("\nThese tests demonstrate bugs that need fixing.")
        print("After fixing, the tests should pass instead of confirming bugs.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())