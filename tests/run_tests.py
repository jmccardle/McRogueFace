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
    python3 tests/run_tests.py --sanitizer  # Detect ASan/UBSan errors in output
    python3 tests/run_tests.py --valgrind   # Run tests under Valgrind memcheck

Environment variables:
    MCRF_BUILD_DIR          Build directory (default: ../build)
    MCRF_LIB_DIR            Library directory for LD_LIBRARY_PATH (default: ../__lib)
    MCRF_TIMEOUT_MULTIPLIER Multiply per-test timeout (default: 1, use 50 for valgrind)
"""
import os
import subprocess
import sys
import time
import hashlib
import re
from pathlib import Path

# Configuration — respect environment overrides for debug/sanitizer builds
TESTS_DIR = Path(__file__).parent
BUILD_DIR = Path(os.environ.get('MCRF_BUILD_DIR', str(TESTS_DIR.parent / "build")))
LIB_DIR = Path(os.environ.get('MCRF_LIB_DIR', str(TESTS_DIR.parent / "__lib")))
MCROGUEFACE = BUILD_DIR / "mcrogueface"
DEFAULT_TIMEOUT = 10  # seconds per test

# Sanitizer error patterns to scan for in stderr
SANITIZER_PATTERNS = [
    re.compile(r'ERROR: AddressSanitizer'),
    re.compile(r'ERROR: LeakSanitizer'),
    re.compile(r'runtime error:'),  # UBSan
    re.compile(r'ERROR: ThreadSanitizer'),
]

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

def check_sanitizer_output(output):
    """Check output for sanitizer error messages. Returns list of matches."""
    errors = []
    for pattern in SANITIZER_PATTERNS:
        matches = pattern.findall(output)
        if matches:
            errors.extend(matches)
    return errors

def run_test(test_path, verbose=False, timeout=DEFAULT_TIMEOUT,
             sanitizer_mode=False, valgrind_mode=False):
    """Run a single test and return (passed, duration, output, sanitizer_errors)."""
    start = time.time()

    # Clean any existing screenshots
    for png in BUILD_DIR.glob("test_*.png"):
        png.unlink()

    # Set up environment with library path
    env = os.environ.copy()
    existing_ld = env.get('LD_LIBRARY_PATH', '')
    env['LD_LIBRARY_PATH'] = f"{LIB_DIR}:{existing_ld}" if existing_ld else str(LIB_DIR)

    # Build the command
    cmd = []
    valgrind_log = None

    if valgrind_mode:
        valgrind_log = BUILD_DIR / f"valgrind-{test_path.stem}.log"
        supp_file = TESTS_DIR.parent / "sanitizers" / "valgrind-mcrf.supp"
        cmd.extend([
            'valgrind',
            '--tool=memcheck',
            '--leak-check=full',
            '--error-exitcode=42',
            f'--log-file={valgrind_log}',
        ])
        if supp_file.exists():
            cmd.append(f'--suppressions={supp_file}')

    cmd.extend([str(MCROGUEFACE), '--headless', '--exec', str(test_path)])

    try:
        result = subprocess.run(
            cmd,
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

        # Check for sanitizer errors in output
        sanitizer_errors = []
        if sanitizer_mode:
            sanitizer_errors = check_sanitizer_output(output)
            if sanitizer_errors:
                passed = False

        # Check valgrind results
        if valgrind_mode:
            if result.returncode == 42:
                passed = False
                if valgrind_log and valgrind_log.exists():
                    vg_output = valgrind_log.read_text()
                    # Extract error summary
                    error_lines = [l for l in vg_output.split('\n')
                                   if 'ERROR SUMMARY' in l or 'definitely lost' in l
                                   or 'Invalid' in l]
                    sanitizer_errors.extend(error_lines[:5])
                    output += f"\n--- Valgrind log: {valgrind_log} ---\n"
                    output += '\n'.join(error_lines)

        return passed, duration, output, sanitizer_errors

    except subprocess.TimeoutExpired:
        return False, timeout, "TIMEOUT", []
    except Exception as e:
        return False, 0, str(e), []

def find_tests(directory):
    """Find all test files in a directory."""
    test_dir = TESTS_DIR / directory
    if not test_dir.exists():
        return []
    return sorted(test_dir.glob("*.py"))

def main():
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    show_checksums = '--checksums' in sys.argv
    sanitizer_mode = '--sanitizer' in sys.argv
    valgrind_mode = '--valgrind' in sys.argv

    # Parse --timeout=N
    timeout = DEFAULT_TIMEOUT
    for arg in sys.argv[1:]:
        if arg.startswith('--timeout='):
            try:
                timeout = int(arg.split('=')[1])
            except ValueError:
                pass

    # Apply timeout multiplier from environment
    timeout_multiplier = float(os.environ.get('MCRF_TIMEOUT_MULTIPLIER', '1'))
    effective_timeout = timeout * timeout_multiplier

    # Determine which directories to test
    dirs_to_test = []
    for arg in sys.argv[1:]:
        if arg in TEST_DIRS:
            dirs_to_test.append(arg)
    if not dirs_to_test:
        dirs_to_test = TEST_DIRS

    # Header
    mode_str = ""
    if sanitizer_mode:
        mode_str = f" {YELLOW}[ASan/UBSan]{RESET}"
    elif valgrind_mode:
        mode_str = f" {YELLOW}[Valgrind]{RESET}"

    print(f"{BOLD}McRogueFace Test Runner{RESET}{mode_str}")
    print(f"Build: {BUILD_DIR}")
    print(f"Testing: {', '.join(dirs_to_test)} (timeout: {effective_timeout:.0f}s)")
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
            passed, duration, output, san_errors = run_test(
                test_path, verbose, effective_timeout,
                sanitizer_mode=sanitizer_mode,
                valgrind_mode=valgrind_mode
            )
            results['total_time'] += duration

            if passed:
                results['pass'] += 1
                status = f"{GREEN}PASS{RESET}"
            else:
                results['fail'] += 1
                status = f"{RED}FAIL{RESET}"
                failures.append((test_dir, test_name, output, san_errors))

            # Get screenshot checksums if any were generated
            checksum_str = ""
            if show_checksums:
                checksums = get_screenshot_checksum(BUILD_DIR)
                if checksums:
                    checksum_str = f" [{', '.join(f'{k}:{v}' for k,v in checksums.items())}]"

            # Show sanitizer error indicator
            san_str = ""
            if san_errors:
                san_str = f" {RED}[SANITIZER]{RESET}"

            print(f"  {status} {test_name} ({duration:.2f}s){checksum_str}{san_str}")

            if verbose and not passed:
                print(f"    Output: {output[:200]}...")
                if san_errors:
                    for err in san_errors[:3]:
                        print(f"    {RED}>> {err}{RESET}")

    # Summary
    print("\n" + "=" * 60)
    total = results['pass'] + results['fail']
    pass_rate = (results['pass'] / total * 100) if total > 0 else 0

    print(f"{BOLD}Results:{RESET} {results['pass']}/{total} passed ({pass_rate:.1f}%)")
    print(f"{BOLD}Time:{RESET} {results['total_time']:.2f}s")

    if valgrind_mode:
        print(f"{BOLD}Valgrind logs:{RESET} {BUILD_DIR}/valgrind-*.log")

    if failures:
        print(f"\n{RED}{BOLD}Failures:{RESET}")
        for test_dir, test_name, output, san_errors in failures:
            print(f"  {test_dir}/{test_name}")
            if san_errors:
                for err in san_errors[:3]:
                    print(f"    {RED}>> {err}{RESET}")
            if verbose:
                # Show last few lines of output
                lines = output.strip().split('\n')[-5:]
                for line in lines:
                    print(f"    {line}")

    sys.exit(0 if results['fail'] == 0 else 1)

if __name__ == '__main__':
    main()
