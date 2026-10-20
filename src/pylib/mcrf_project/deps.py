"""Project dependencies (#499, #517): third-party packages a game imports.

``mcrf_project deps`` makes ``<project>/.venv`` a real PEP 405 virtual environment with the
engine (``<engine> -m venv .venv``, #505) and installs the project's requirements (mcrf.toml:
``requirements``, ``requirements-file``) into it with the venv's own pip
(``.venv/bin/python -m pip install``). pip then does everything it does in any venv, console
scripts included: ``.venv/bin/<name>`` runs under ``.venv/bin/python``. Nothing is written
under the engine.

``run`` launches the game through ``.venv/bin/mcrogueface``, which finds ``.venv`` the way
CPython finds a venv. ``dist`` ships only the venv's site-packages, laid out the way the
packaged engine's sibling ``venv/`` rule expects: ``<package>/venv/lib/python3.X/site-packages``.
No ``bin/``, ``pyvenv.cfg`` or ``include/``, and not the pip that ``-m venv`` bootstrapped.

Binary wheels only (``--only-binary=:all:``): pure-Python packages and wheels for the engine's
Python (same ABI) work.

Windows engines: unsupported. ``deps`` refuses them with one message.
"""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from .errors import ProjectError

STAMP = "mcrf-deps.json"
NATIVE_SUFFIX = {"linux": ".so", "windows": ".pyd"}

def venv_dir(project):
    return project.dir / ".venv"


def venv_python(project):
    return venv_dir(project) / "bin" / "python"


def site_packages(project, engine):
    return venv_dir(project) / "lib" / ("python%s" % engine.python_version) / "site-packages"


def package_site_packages(engine):
    """Where a dist package keeps them: the engine's sibling venv/ (McRFPy_API.cpp)."""
    if engine.platform == "windows":
        return Path("venv") / "Lib" / "site-packages"
    return Path("venv") / "lib" / ("python%s" % engine.python_version) / "site-packages"


def run_executable(project, engine):
    """What `run` launches: the venv's engine link if `deps` installed one (`require_installed`
    has checked), otherwise the engine itself."""
    if require_installed(project, engine) is not None:
        return venv_dir(project) / "bin" / "mcrogueface"
    return engine.exe


def requirements(project):
    """The pip arguments naming the project's requirements, or [] if it has none."""
    config = project.config
    args = list(config.get("requirements", []))
    if "requirements-file" in config:
        path = project.dir / config["requirements-file"]
        if not path.is_file():
            raise ProjectError("%s: requirements-file %s does not exist"
                               % (project.config_path, path))
        args += ["-r", str(path)]
    return args


def _fingerprint(project, engine):
    """What an install depends on: the requirements, the requirements file's contents and
    the engine's Python. If it changes, the installed packages are stale."""
    config = project.config
    digest = hashlib.sha256()
    if "requirements-file" in config:
        digest.update((project.dir / config["requirements-file"]).read_bytes())
    return {"requirements": config.get("requirements", []),
            "requirements-file": config.get("requirements-file"),
            "requirements-file-sha256": digest.hexdigest() if "requirements-file" in config else None,
            "python": engine.python_version}


def _require_replaceable(project):
    """`install` replaces .venv; refuse unless it is absent, empty, or ours (#509). A
    developer's own virtualenv often lives at <project>/.venv."""
    path = venv_dir(project)
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink() and (
            (path / STAMP).is_file() or not any(path.iterdir())):
        return
    raise ProjectError("%s exists and was not made by `deps` (it has no %s); `deps` replaces "
                       "that directory, so move or remove it yourself first"
                       % (path, STAMP))


def install(project, engine, log):
    """Make .venv with `engine` and install the project's requirements into it. Returns the
    site-packages path."""
    args = requirements(project)
    if not args:
        raise ProjectError("%s names no requirements (requirements or requirements-file)"
                           % project.config_path)
    if engine.platform == "windows":
        raise ProjectError("`deps` is not supported for Windows engines (%s): it makes a venv "
                           "with the engine and runs pip in it; use a Linux engine"
                           % engine.dir)
    flags = engine._python_abiflags()
    if flags:
        raise ProjectError("%s is a Python %s%s build; dependencies are installed for Release "
                           "engines" % (engine.dir, engine.python_version, flags))
    _require_replaceable(project)
    if venv_dir(project).exists():
        shutil.rmtree(venv_dir(project))  # ours; a removed requirement must not linger
    venv_dir(project).mkdir()
    # Claimed before anything runs: an interrupted install is still ours to replace, and its
    # stamp matches no fingerprint, so require_installed() calls it not installed.
    (venv_dir(project) / STAMP).write_text(json.dumps({"incomplete": True}))
    log("creating %s with %s" % (venv_dir(project), engine.exe))
    steps = [([str(engine.exe), "-m", "venv", str(venv_dir(project))], "venv creation"),
             ([str(venv_python(project)), "-m", "pip", "install", "--only-binary=:all:",
               "--disable-pip-version-check"] + args, "pip")]
    for cmd, what in steps:
        result = subprocess.call(cmd, cwd=project.dir)
        if result != 0:
            shutil.rmtree(venv_dir(project))  # never leave a half-installed set looking installed
            raise ProjectError("%s failed (exit %d); see its output above" % (what, result))
    (venv_dir(project) / STAMP).write_text(json.dumps(_fingerprint(project, engine), indent=2))
    return site_packages(project, engine)


def require_installed(project, engine):
    """The project's installed site-packages, or None if it has no requirements. Raises if
    it has requirements that `deps` hasn't installed (or that changed since)."""
    if not requirements(project):
        return None
    stamp = venv_dir(project) / STAMP
    installed = site_packages(project, engine)
    if (not installed.is_dir() or not stamp.is_file() or not venv_python(project).exists()
            or not (venv_dir(project) / "pyvenv.cfg").is_file()):
        raise ProjectError("%s names requirements but %s has none installed for Python %s; "
                           "run: mcrogueface -m mcrf_project deps"
                           % (project.config_path.name, venv_dir(project), engine.python_version))
    recorded = json.loads(stamp.read_text())
    if recorded != _fingerprint(project, engine):
        raise ProjectError("the requirements in %s (or the engine's Python) changed since `deps` "
                           "last ran; run: mcrogueface -m mcrf_project deps" % project.config_path.name)
    return installed


def stage(project, engine, dest):
    """Copy the installed packages into the staged package at the engine's venv/ location.
    No-op without requirements. Refuses native extensions built for another platform."""
    target = require_installed(project, engine)
    if target is None:
        return
    foreign = ".pyd" if engine.platform == "linux" else ".so"
    for path in target.rglob("*"):
        if path.name.endswith(foreign) or (foreign == ".so" and ".so." in path.name):
            raise ProjectError("the installed dependencies include %s, native code for another "
                               "platform than %s; install them with a %s engine's `deps`"
                               % (path.relative_to(target), engine.title, engine.title))
    # pip is the venv's bootstrap (ensurepip), not the game's dependency, and the package
    # ships its own pip in the engine's lib/
    def ignore(directory, names):
        skip = set(shutil.ignore_patterns("__pycache__", "*.pyc")(directory, names))
        if Path(directory) == target:
            skip |= {n for n in names if n == "pip" or (n.startswith("pip-") and n.endswith(".dist-info"))}
        return skip

    shutil.copytree(target, Path(dest) / package_site_packages(engine), ignore=ignore)
