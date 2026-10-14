"""Project dependencies (#499): third-party packages a game imports.

``mcrf_project deps`` installs the project's requirements (mcrf.toml: ``requirements``,
``requirements-file``) into ``<project>/.venv/lib/python3.X/site-packages`` (Windows
engines: ``.venv/Lib/site-packages``), using the pip the engine ships
(``lib/Python/Lib/ensurepip/_bundled``), run by the engine's own interpreter so the
packages are for exactly its Python. Nothing is written under the engine.

``.venv`` is not a real virtual environment (the engine can't be a venv's interpreter);
it is a site-packages directory laid out the way the engine's sibling ``venv/`` rule
expects, which is how ``mcrf_project dist`` ships it: ``<package>/venv/...``.

Binary wheels only (``--only-binary=:all:``): building from source needs a build
environment made from a Python executable, and the engine isn't one. Pure-Python
packages and wheels for the engine's Python (same ABI) both work.
"""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from .errors import ProjectError
from .runtime import _one

STAMP = "mcrf-deps.json"
NATIVE_SUFFIX = {"linux": ".so", "windows": ".pyd"}

def venv_dir(project):
    return project.dir / ".venv"


def site_packages(project, engine):
    if engine.platform == "windows":
        return venv_dir(project) / "Lib" / "site-packages"
    return venv_dir(project) / "lib" / ("python%s" % engine.python_version) / "site-packages"


def package_site_packages(engine):
    """Where a dist package keeps them: the engine's sibling venv/ (McRFPy_API.cpp)."""
    if engine.platform == "windows":
        return Path("venv") / "Lib" / "site-packages"
    return Path("venv") / "lib" / ("python%s" % engine.python_version) / "site-packages"


def pip_wheel(engine):
    bundled = engine.dir / "lib" / "Python" / "Lib" / "ensurepip" / "_bundled"
    return _one(bundled.glob("pip-*.whl"), "bundled pip wheel", bundled)


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


def install(project, engine, log):
    """Install the project's requirements with `engine`. Returns the site-packages path."""
    args = requirements(project)
    if not args:
        raise ProjectError("%s names no requirements (requirements or requirements-file)"
                           % project.config_path)
    if engine.platform != "linux" and not engine.is_running:
        raise ProjectError("%s is a %s engine; `deps` runs pip with the engine's interpreter, "
                           "which must run on this machine" % (engine.dir, engine.platform))
    flags = engine._python_abiflags()
    if flags:
        raise ProjectError("%s is a Python %s%s build; dependencies are installed for Release "
                           "engines" % (engine.dir, engine.python_version, flags))
    target = site_packages(project, engine)
    wheel = pip_wheel(engine)
    if venv_dir(project).exists():
        shutil.rmtree(venv_dir(project))  # ours; a removed requirement must not linger
    target.mkdir(parents=True)
    pip_args = ["install", "--target", str(target), "--only-binary=:all:",
                "--disable-pip-version-check"] + args
    log("installing into %s with pip from %s" % (target, wheel.name))
    code = ("import sys\nsys.path.insert(0, %r)\n"
            "from pip._internal.cli.main import main\nsys.exit(main(%r))\n" % (str(wheel), pip_args))
    result = subprocess.call([str(engine.exe), "--headless", "-c", code], cwd=project.dir)
    if result != 0:
        shutil.rmtree(venv_dir(project))  # never leave a half-installed set looking installed
        raise ProjectError("pip failed (exit %d); see its output above" % result)
    (venv_dir(project) / STAMP).write_text(json.dumps(_fingerprint(project, engine), indent=2))
    return target


def require_installed(project, engine):
    """The project's installed site-packages, or None if it has no requirements. Raises if
    it has requirements that `deps` hasn't installed (or that changed since). The packages
    are whatever platform's `deps` installed them; `stage` checks that fits."""
    if not requirements(project):
        return None
    stamp = venv_dir(project) / STAMP
    installed = [p for p in (venv_dir(project) / "lib" / ("python%s" % engine.python_version) / "site-packages",
                             venv_dir(project) / "Lib" / "site-packages") if p.is_dir()]
    if not installed or not stamp.is_file():
        raise ProjectError("%s names requirements but %s has none installed for Python %s; "
                           "run: mcrogueface -m mcrf_project deps"
                           % (project.config_path.name, venv_dir(project), engine.python_version))
    recorded = json.loads(stamp.read_text())
    if recorded != _fingerprint(project, engine):
        raise ProjectError("the requirements in %s (or the engine's Python) changed since `deps` "
                           "last ran; run: mcrogueface -m mcrf_project deps" % project.config_path.name)
    return installed[0]


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
    shutil.copytree(target, Path(dest) / package_site_packages(engine),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
