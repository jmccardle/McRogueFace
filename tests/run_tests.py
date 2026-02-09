#!/usr/bin/env python3
"""
McRogueFace Test Runner
Runs all headless tests and reports results.

Usage:
    python3 tests/run_tests.py           # Run all tests
    python3 tests/run_tests.py unit      # Run only unit tests
    python3 tests/run_tests.py -v        # Verbose output (show failure details)
    python3 tests/run_tests.py --checksums  # Show screenshot checksums
    python3 tests/run_tests.py --timeout=30  # Custom timeout
"""
import os
import subprocess
import sys
import time
import hashlib
from pathlib import Path

# Configuration
TESTS_DIR = Path(__file__).parent
BUILD_DIR = TESTS_DIR.parent / "build"
LIB_DIR = TESTS_DIR.parent / "__lib"
MCROGUEFACE = BUILD_DIR / "mcrogueface"
DEFAULT_TIMEOUT = 10  # seconds per test

# Test directories to run (in order)
TEST_DIRS = ['unit', 'integration', 'regression']

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def get_screenshot_checksum(test_dir):
    """Get checksums of test-generated PNG files in build directory."""
    checksums = {}
    for png in BUILD_DIR.glob("test_*.png"):
        with open(png, 'rb') as f:
            checksums[png.name] = hashlib.md5(f.read()).hexdigest()[:8]
    return checksums

def run_test(test_path, verbose=False, timeout=DEFAULT_TIMEOUT):
    """Run a single test and return (passed, duration, output)."""
    start = time.time()

    # Clean any existing screenshots
    for png in BUILD_DIR.glob("test_*.png"):
        png.unlink()

    # Set up environment with library path
    env = os.environ.copy()
    existing_ld = env.get('LD_LIBRARY_PATH', '')
    env['LD_LIBRARY_PATH'] = f"{LIB_DIR}:{existing_ld}" if existing_ld else str(LIB_DIR)

    try:
        result = subprocess.run(
            [str(MCROGUEFACE), '--headless', '--exec', str(test_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(BUILD_DIR),
            env=env
        )
        duration = time.time() - start
        passed = result.returncode == 0
        output = result.stdout + result.stderr

        # Check for PASS/FAIL in output
        if 'FAIL' in output and 'PASS' not in output.split('FAIL')[-1]:
            passed = False

        return passed, duration, output

    except subprocess.TimeoutExpired:
        return False, timeout, "TIMEOUT"
    except Exception as e:
        return False, 0, str(e)

def find_tests(directory):
    """Find all test files in a directory."""
    test_dir = TESTS_DIR / directory
    if not test_dir.exists():
        return []
    return sorted(test_dir.glob("*.py"))

def main():
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    show_checksums = '--checksums' in sys.argv  # off by default; use --checksums to show

    # Parse --timeout=N
    timeout = DEFAULT_TIMEOUT
    for arg in sys.argv[1:]:
        if arg.startswith('--timeout='):
            try:
                timeout = int(arg.split('=')[1])
            except ValueError:
                pass

    # Determine which directories to test
    dirs_to_test = []
    for arg in sys.argv[1:]:
        if arg in TEST_DIRS:
            dirs_to_test.append(arg)
    if not dirs_to_test:
        dirs_to_test = TEST_DIRS

    print(f"{BOLD}McRogueFace Test Runner{RESET}")
    print(f"Testing: {', '.join(dirs_to_test)} (timeout: {timeout}s)")
    print("=" * 60)

    results = {'pass': 0, 'fail': 0, 'total_time': 0}
    failures = []

    for test_dir in dirs_to_test:
        tests = find_tests(test_dir)
        if not tests:
            continue

        print(f"\n{BOLD}{test_dir}/{RESET} ({len(tests)} tests)")

        for test_path in tests:
            test_name = test_path.name
            passed, duration, output = run_test(test_path, verbose, timeout)
            results['total_time'] += duration

            if passed:
                results['pass'] += 1
                status = f"{GREEN}PASS{RESET}"
            else:
                results['fail'] += 1
                status = f"{RED}FAIL{RESET}"
                failures.append((test_dir, test_name, output))

            # Get screenshot checksums if any were generated
            checksum_str = ""
            if show_checksums:
                checksums = get_screenshot_checksum(BUILD_DIR)
                if checksums:
                    checksum_str = f" [{', '.join(f'{k}:{v}' for k,v in checksums.items())}]"

            print(f"  {status} {test_name} ({duration:.2f}s){checksum_str}")

            if verbose and not passed:
                print(f"    Output: {output[:200]}...")

    # Summary
    print("\n" + "=" * 60)
    total = results['pass'] + results['fail']
    pass_rate = (results['pass'] / total * 100) if total > 0 else 0

    print(f"{BOLD}Results:{RESET} {results['pass']}/{total} passed ({pass_rate:.1f}%)")
    print(f"{BOLD}Time:{RESET} {results['total_time']:.2f}s")

    if failures:
        print(f"\n{RED}{BOLD}Failures:{RESET}")
        for test_dir, test_name, output in failures:
            print(f"  {test_dir}/{test_name}")
            if verbose:
                # Show last few lines of output
                lines = output.strip().split('\n')[-5:]
                for line in lines:
                    print(f"    {line}")

    sys.exit(0 if results['fail'] == 0 else 1)

if __name__ == '__main__':
    main()
