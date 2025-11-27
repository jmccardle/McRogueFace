"""
McRogueFace Virtual Environment Bootstrap

Reference implementation for self-contained deployment with pip-installed packages.

Usage:
    import mcrf_venv

    # Check if venv needs setup
    if not mcrf_venv.venv_exists():
        mcrf_venv.create_venv()
        mcrf_venv.install_requirements("requirements.txt")

    # Now safe to import third-party packages
    import numpy

This module provides utilities for creating and managing a venv/ directory
alongside the McRogueFace executable. The C++ runtime automatically adds
venv/lib/python3.14/site-packages (or venv/Lib/site-packages on Windows)
to sys.path if it exists.

Pip Support:
    Option A (recommended): Bundle pip in your distribution
        - Copy pip to lib/Python/Lib/pip/
        - pip will be available via `python -m pip`

    Option B: Bootstrap pip from ensurepip wheel
        - Call mcrf_venv.bootstrap_pip() to extract pip from bundled wheel
        - Slower first run, but no extra distribution size
"""

import os
import sys
import subprocess
import zipfile
import glob
from pathlib import Path


def get_executable_dir() -> Path:
    """Get the directory containing the McRogueFace executable."""
    return Path(sys.executable).parent


def get_venv_path() -> Path:
    """Get the path to the venv directory (sibling to executable)."""
    return get_executable_dir() / "venv"


def get_site_packages() -> Path:
    """Get the platform-appropriate site-packages path."""
    venv = get_venv_path()
    if sys.platform == "win32":
        return venv / "Lib" / "site-packages"
    else:
        return venv / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"


def venv_exists() -> bool:
    """Check if the venv directory exists with site-packages."""
    return get_site_packages().exists()


def create_venv() -> None:
    """
    Create the venv directory structure.

    This creates the minimal directory structure needed for pip to install
    packages. It does NOT copy the Python interpreter or create activation
    scripts - McRogueFace IS the interpreter.
    """
    site_packages = get_site_packages()
    site_packages.mkdir(parents=True, exist_ok=True)


def pip_available() -> bool:
    """Check if pip is available for import."""
    try:
        import pip
        return True
    except ImportError:
        return False


def get_ensurepip_wheel() -> Path | None:
    """
    Find the pip wheel bundled with ensurepip.

    Returns:
        Path to pip wheel, or None if not found
    """
    exe_dir = get_executable_dir()
    bundled_dir = exe_dir / "lib" / "Python" / "Lib" / "ensurepip" / "_bundled"

    if not bundled_dir.exists():
        return None

    # Find pip wheel (pattern: pip-*.whl)
    wheels = list(bundled_dir.glob("pip-*.whl"))
    if wheels:
        return wheels[0]
    return None


def bootstrap_pip() -> bool:
    """
    Bootstrap pip by extracting from ensurepip's bundled wheel.

    This extracts pip to the venv's site-packages directory, making it
    available for subsequent pip_install() calls.

    Returns:
        True if pip was successfully bootstrapped, False otherwise

    Note:
        This modifies sys.path to include the newly extracted pip.
        After calling this, `import pip` will work.
    """
    wheel_path = get_ensurepip_wheel()
    if not wheel_path:
        return False

    site_packages = get_site_packages()
    if not site_packages.exists():
        create_venv()

    # Extract pip from the wheel
    with zipfile.ZipFile(wheel_path, 'r') as whl:
        whl.extractall(site_packages)

    # Add to sys.path so pip is immediately importable
    site_str = str(site_packages)
    if site_str not in sys.path:
        sys.path.insert(0, site_str)

    return pip_available()


def pip_install(*packages: str, requirements: str = None, quiet: bool = True) -> int:
    """
    Install packages using pip.

    If pip is not available, attempts to bootstrap it from ensurepip.

    Args:
        *packages: Package names to install (e.g., "numpy", "pygame-ce")
        requirements: Path to requirements.txt file
        quiet: Suppress pip output (default True)

    Returns:
        pip exit code (0 = success)

    Raises:
        RuntimeError: If pip cannot be bootstrapped

    Example:
        pip_install("numpy", "requests")
        pip_install(requirements="requirements.txt")
    """
    # Ensure venv exists
    if not venv_exists():
        create_venv()

    # Bootstrap pip if not available
    if not pip_available():
        if not bootstrap_pip():
            raise RuntimeError(
                "pip is not available and could not be bootstrapped. "
                "Ensure ensurepip/_bundled/pip-*.whl exists in your distribution."
            )

    site_packages = get_site_packages()

    # Build pip command
    cmd = [sys.executable, "-m", "pip", "install", "--target", str(site_packages)]

    if quiet:
        cmd.append("--quiet")

    if requirements:
        req_path = Path(requirements)
        if not req_path.is_absolute():
            req_path = get_executable_dir() / req_path
        if req_path.exists():
            cmd.extend(["-r", str(req_path)])
        else:
            # No requirements file, nothing to install
            return 0

    cmd.extend(packages)

    # Only run if we have something to install
    if not packages and not requirements:
        return 0

    result = subprocess.run(cmd, check=False)
    return result.returncode


def install_requirements(requirements_path: str = "requirements.txt") -> int:
    """
    Install packages from a requirements.txt file.

    Args:
        requirements_path: Path to requirements file (relative to executable or absolute)

    Returns:
        pip exit code (0 = success), or 0 if file doesn't exist
    """
    return pip_install(requirements=requirements_path)


def ensure_environment(requirements: str = None) -> bool:
    """
    Ensure venv exists and optionally install requirements.

    This is the high-level convenience function for simple use cases.
    Call at the start of your game.py before importing dependencies.

    Args:
        requirements: Optional path to requirements.txt

    Returns:
        True if venv was created (first run), False if it already existed

    Example:
        import mcrf_venv
        created = mcrf_venv.ensure_environment("requirements.txt")
        if created:
            print("Environment initialized!")

        # Now safe to import
        import numpy
    """
    created = False

    if not venv_exists():
        create_venv()
        created = True

    if requirements:
        install_requirements(requirements)

    return created


def list_installed() -> list:
    """
    List installed packages in the venv.

    Returns:
        List of (name, version) tuples
    """
    site_packages = get_site_packages()
    if not site_packages.exists():
        return []

    packages = []
    for item in site_packages.iterdir():
        if item.suffix == ".dist-info":
            # Parse package name and version from dist-info directory name
            # Format: package_name-version.dist-info
            name_version = item.stem
            if "-" in name_version:
                parts = name_version.rsplit("-", 1)
                packages.append((parts[0].replace("_", "-"), parts[1]))

    return sorted(packages)


# Convenience: if run directly, show status
if __name__ == "__main__":
    print(f"McRogueFace venv utility")
    print(f"  Executable: {sys.executable}")
    print(f"  Venv path:  {get_venv_path()}")
    print(f"  Site-packages: {get_site_packages()}")
    print(f"  Venv exists: {venv_exists()}")

    if venv_exists():
        installed = list_installed()
        if installed:
            print(f"\nInstalled packages:")
            for name, version in installed:
                print(f"  {name} ({version})")
        else:
            print(f"\nNo packages installed in venv.")
    else:
        print(f"\nVenv not created. Run create_venv() to initialize.")
