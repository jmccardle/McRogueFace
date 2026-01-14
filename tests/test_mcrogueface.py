"""
Pytest wrapper for McRogueFace test scripts.

This file discovers and runs all McRogueFace test scripts in unit/, integration/,
and regression/ directories via subprocess.

Usage:
    pytest tests/test_mcrogueface.py -q                  # Quiet output
    pytest tests/test_mcrogueface.py -k "bsp"            # Filter by name
    pytest tests/test_mcrogueface.py --mcrf-timeout=30   # Custom timeout
    pytest tests/test_mcrogueface.py -x                  # Stop on first failure
"""
import os
import subprocess
import pytest
from pathlib import Path

# Paths
TESTS_DIR = Path(__file__).parent
BUILD_DIR = TESTS_DIR.parent / "build"
LIB_DIR = TESTS_DIR.parent / "__lib"
MCROGUEFACE = BUILD_DIR / "mcrogueface"

# Test directories
TEST_DIRS = ['unit', 'integration', 'regression']

# Default timeout
DEFAULT_TIMEOUT = 10


def discover_tests():
    """Find all test scripts in test directories."""
    tests = []
    for test_dir in TEST_DIRS:
        dir_path = TESTS_DIR / test_dir
        if dir_path.exists():
            for test_file in sorted(dir_path.glob("*.py")):
                if test_file.name != '__init__.py':
                    rel_path = f"{test_dir}/{test_file.name}"
                    tests.append(rel_path)
    return tests


def get_env():
    """Get environment with LD_LIBRARY_PATH set."""
    env = os.environ.copy()
    existing_ld = env.get('LD_LIBRARY_PATH', '')
    env['LD_LIBRARY_PATH'] = f"{LIB_DIR}:{existing_ld}" if existing_ld else str(LIB_DIR)
    return env


def run_mcrf_test(script_path, timeout=DEFAULT_TIMEOUT):
    """Run a McRogueFace test script and return (passed, output)."""
    full_path = TESTS_DIR / script_path
    env = get_env()

    try:
        result = subprocess.run(
            [str(MCROGUEFACE), '--headless', '--exec', str(full_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(BUILD_DIR),
            env=env
        )

        output = result.stdout + result.stderr
        passed = result.returncode == 0

        # Check for PASS/FAIL in output
        if 'FAIL' in output and 'PASS' not in output.split('FAIL')[-1]:
            passed = False

        return passed, output

    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)


# Discover tests at module load time
ALL_TESTS = discover_tests()


@pytest.fixture
def mcrf_timeout(request):
    """Get timeout from command line or default."""
    return request.config.getoption("--mcrf-timeout", default=DEFAULT_TIMEOUT)


def pytest_addoption(parser):
    """Add --mcrf-timeout option."""
    try:
        parser.addoption(
            "--mcrf-timeout",
            action="store",
            default=DEFAULT_TIMEOUT,
            type=int,
            help="Timeout in seconds for McRogueFace tests"
        )
    except ValueError:
        # Option already added
        pass


@pytest.mark.parametrize("script_path", ALL_TESTS, ids=lambda x: x.replace('/', '::'))
def test_mcrogueface_script(script_path, request):
    """Run a McRogueFace test script."""
    timeout = request.config.getoption("--mcrf-timeout", default=DEFAULT_TIMEOUT)
    passed, output = run_mcrf_test(script_path, timeout=timeout)

    if not passed:
        # Show last 15 lines of output on failure
        lines = output.strip().split('\n')[-15:]
        pytest.fail('\n'.join(lines))
