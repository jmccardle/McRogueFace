"""
Pytest configuration for McRogueFace tests.

Provides fixtures for running McRogueFace scripts in headless mode.

Usage:
    pytest tests/ -q                    # Run all tests quietly
    pytest tests/ -k "bsp"              # Run tests matching "bsp"
    pytest tests/ -x                    # Stop on first failure
    pytest tests/ --tb=short            # Short tracebacks
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

# Default timeout for tests (can be overridden with --timeout)
DEFAULT_TIMEOUT = 10


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--mcrf-timeout",
        action="store",
        default=DEFAULT_TIMEOUT,
        type=int,
        help="Timeout in seconds for each McRogueFace test"
    )


@pytest.fixture
def mcrf_timeout(request):
    """Get the configured timeout."""
    return request.config.getoption("--mcrf-timeout")


@pytest.fixture
def mcrf_env():
    """Environment with LD_LIBRARY_PATH set for McRogueFace."""
    env = os.environ.copy()
    existing_ld = env.get('LD_LIBRARY_PATH', '')
    env['LD_LIBRARY_PATH'] = f"{LIB_DIR}:{existing_ld}" if existing_ld else str(LIB_DIR)
    return env


@pytest.fixture
def mcrf_exec(mcrf_env, mcrf_timeout):
    """
    Fixture that returns a function to execute McRogueFace scripts.

    Usage in tests:
        def test_something(mcrf_exec):
            passed, output = mcrf_exec("unit/my_test.py")
            assert passed
    """
    def _exec(script_path, timeout=None):
        """
        Execute a McRogueFace script in headless mode.

        Args:
            script_path: Path relative to tests/ directory
            timeout: Override default timeout

        Returns:
            (passed: bool, output: str)
        """
        if timeout is None:
            timeout = mcrf_timeout

        full_path = TESTS_DIR / script_path

        try:
            result = subprocess.run(
                [str(MCROGUEFACE), '--headless', '--exec', str(full_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(BUILD_DIR),
                env=mcrf_env
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

    return _exec


def pytest_collect_file(parent, file_path):
    """Auto-discover McRogueFace test scripts."""
    # Only collect from unit/, integration/, regression/ directories
    try:
        rel_path = file_path.relative_to(TESTS_DIR)
    except ValueError:
        return None

    if rel_path.parts and rel_path.parts[0] in ('unit', 'integration', 'regression', 'docs', 'demo'):
        if file_path.suffix == '.py' and file_path.name not in ('__init__.py', 'conftest.py'):
            return McRFTestFile.from_parent(parent, path=file_path)
    return None


def pytest_ignore_collect(collection_path, config):
    """Prevent pytest from trying to import test scripts as Python modules."""
    try:
        rel_path = collection_path.relative_to(TESTS_DIR)
        if rel_path.parts and rel_path.parts[0] in ('unit', 'integration', 'regression', 'docs', 'demo'):
            # Let our custom collector handle these, don't import them
            return False  # Don't ignore - we'll collect them our way
    except ValueError:
        pass
    return None


class McRFTestFile(pytest.File):
    """Custom test file for McRogueFace scripts."""

    def collect(self):
        """Yield a single test item for this script."""
        yield McRFTestItem.from_parent(self, name=self.path.stem)


class McRFTestItem(pytest.Item):
    """Test item that runs a McRogueFace script."""

    def runtest(self):
        """Run the McRogueFace script."""
        timeout = self.config.getoption("--mcrf-timeout")

        env = os.environ.copy()
        existing_ld = env.get('LD_LIBRARY_PATH', '')
        env['LD_LIBRARY_PATH'] = f"{LIB_DIR}:{existing_ld}" if existing_ld else str(LIB_DIR)

        try:
            result = subprocess.run(
                [str(MCROGUEFACE), '--headless', '--exec', str(self.path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(BUILD_DIR),
                env=env
            )

            self.output = result.stdout + result.stderr
            passed = result.returncode == 0

            if 'FAIL' in self.output and 'PASS' not in self.output.split('FAIL')[-1]:
                passed = False

            if not passed:
                raise McRFTestException(self.output)

        except subprocess.TimeoutExpired:
            self.output = "TIMEOUT"
            raise McRFTestException("TIMEOUT")

    def repr_failure(self, excinfo):
        """Format failure output."""
        if isinstance(excinfo.value, McRFTestException):
            output = str(excinfo.value)
            # Show last 10 lines
            lines = output.strip().split('\n')[-10:]
            return '\n'.join(lines)
        return super().repr_failure(excinfo)

    def reportinfo(self):
        """Report test location."""
        return self.path, None, f"mcrf:{self.path.relative_to(TESTS_DIR)}"


class McRFTestException(Exception):
    """Exception raised when a McRogueFace test fails."""
    pass
