"""What an engine runtime is: the files a game needs next to it to run.

This is the one definition, used both for the engine's own release packages
(tools/package.sh) and for packaging games (``mcrf_project dist``), so the two can't
disagree about it again (#420: a copy of these rules frozen into every game's Makefile
kept naming Python 3.14 after the engine moved to 3.15).

A runtime is read from a built engine directory: ``build/`` or ``build-windows/`` in a
source tree, or an extracted release package. Everything version-dependent (the Python
and SFML library names, the extension-module directory) is read from that directory,
never written down here.
"""
import fnmatch
import os
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path

from .errors import ProjectError

# Left out of the stdlib a package ships.
STDLIB_EXCLUDED_DIRS = ("test", "tests", "idlelib", "tkinter", "turtledemo", "pydoc_data",
                        "lib2to3", "ensurepip", "_pyrepl", "__pycache__")
STDLIB_EXCLUDED_FILES = ("*.pyc", "*.pyo", "test_*.py", "*_test.py")
# Left out of the extension modules (Linux).
EXTENSION_EXCLUDED = ("*test*", "xxlimited*", "_ctypes_test*", "_xxtestfuzz*")

SFML_MODULES = ("graphics", "window", "system", "audio")

# Rendered API docs bundled into the engine's own packages: (source in the engine source
# tree, destination under <package>/docs).
RELEASE_DOCS = (
    ("docs/API_REFERENCE_DYNAMIC.md", "API_REFERENCE_DYNAMIC.md"),
    ("docs/api_reference_dynamic.html", "api_reference_dynamic.html"),
    ("docs/mcrfpy.3", "mcrfpy.3"),
    ("stubs/mcrfpy.pyi", "mcrfpy.pyi"),
    ("docs/generated/api_full.json", "generated/api_full.json"),
    ("api/manifest.json", "manifest.json"),
)

RUN_SH = """#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="$SCRIPT_DIR/lib:$LD_LIBRARY_PATH"
exec "$SCRIPT_DIR/mcrogueface" "$@"
"""

PLATFORM_TITLES = {"linux": "Linux", "windows": "Windows"}


def _one(paths, what, where):
    """The single match in `paths`, or a ProjectError naming what was found."""
    paths = sorted(paths)
    if len(paths) == 1:
        return paths[0]
    if not paths:
        raise ProjectError("no %s in %s" % (what, where))
    raise ProjectError("more than one %s in %s: %s"
                       % (what, where, ", ".join(p.name for p in paths)))


class Runtime:
    """A built engine directory, Linux or Windows."""

    def __init__(self, engine_dir):
        self.dir = Path(engine_dir).resolve()
        if (self.dir / "mcrogueface.exe").is_file():
            self.platform = "windows"
            self.exe = self.dir / "mcrogueface.exe"
        elif (self.dir / "mcrogueface").is_file():
            self.platform = "linux"
            self.exe = self.dir / "mcrogueface"
        else:
            raise ProjectError("%s is not an engine directory (no mcrogueface binary)" % self.dir)
        self.python_version = self._python_version()

    @classmethod
    def running(cls):
        """The engine running this code."""
        return cls(Path(sys.executable).resolve().parent)

    @property
    def title(self):
        return PLATFORM_TITLES[self.platform]

    @property
    def is_running(self):
        return self.dir == Path(sys.executable).resolve().parent

    @property
    def source_root(self):
        """The engine source tree this was built in, or None for a release package."""
        root = self.dir.parent
        return root if (root / "CMakeLists.txt").is_file() and (root / "src").is_dir() else None

    def _python_version(self):
        # The running interpreter is the authority for itself. A dev build's lib/ can hold
        # stale libraries for an older Python, so its files aren't.
        if self.is_running:
            return "%d.%d" % sys.version_info[:2]
        if self.platform == "linux":
            lib = _one((self.dir / "lib").glob("libpython3.*.so.1.0"), "libpython", self.dir / "lib")
            return lib.name[len("libpython"):-len(".so.1.0")]
        dll = _one((p for p in self.dir.glob("python3*.dll") if p.name != "python3.dll"),
                   "python3X.dll", self.dir)
        digits = dll.stem[len("python"):]
        return "%s.%s" % (digits[0], digits[1:])

    @property
    def python_nodot(self):
        return self.python_version.replace(".", "")

    # --- staging ---------------------------------------------------------------------

    def stage(self, dest):
        """Copy the runtime (no game content) into the directory `dest`."""
        dest = Path(dest)
        dest.mkdir(parents=True, exist_ok=True)
        if self.platform == "linux":
            self._stage_linux(dest)
        else:
            self._stage_windows(dest)

    def _stage_linux(self, dest):
        lib = self.dir / "lib"
        out_lib = dest / "lib"
        out_lib.mkdir(exist_ok=True)
        shutil.copy2(self.exe, dest / "mcrogueface")

        # Each library under the name the binary's DT_NEEDED records, plus the short names
        # as links.
        v = self.python_version
        links = {"libpython%s.so" % v: "libpython%s.so.1.0" % v, "libtcod.so": "libtcod.so.2"}
        real = ["libpython%s.so.1.0" % v, "libtcod.so.2"]
        for module in SFML_MODULES:
            full = _one(lib.glob("libsfml-%s.so.*.*.*" % module), "libsfml-%s" % module, lib).name
            major_minor = full.rsplit(".", 1)[0]
            real.append(full)
            links[major_minor[:major_minor.rindex(".so") + 3]] = full
            links[major_minor] = full
        for name in real:
            if not (lib / name).exists():
                raise ProjectError("missing runtime library %s" % (lib / name))
            shutil.copy2(lib / name, out_lib / name)  # follows links: ships the real object
        for name, target in links.items():
            os.symlink(target, out_lib / name)

        ext = _one((lib / "Python").glob("lib.linux-*-%s" % v), "extension-module directory",
                   lib / "Python")
        out_ext = out_lib / "Python" / ext.name
        out_ext.mkdir(parents=True)
        for so in sorted(ext.glob("*.so")):
            if not any(fnmatch.fnmatch(so.name, pat) for pat in EXTENSION_EXCLUDED):
                shutil.copy2(so, out_ext / so.name)

        self._stage_stdlib(dest)
        run_sh = dest / "run.sh"
        run_sh.write_text(RUN_SH)
        run_sh.chmod(0o755)

    def _stage_windows(self, dest):
        shutil.copy2(self.exe, dest / "mcrogueface.exe")
        for dll in sorted(self.dir.glob("*.dll")):
            shutil.copy2(dll, dest / dll.name)
        self._stage_stdlib(dest)
        dlls = self.dir / "lib" / "Python" / "DLLs"
        if not dlls.is_dir():
            raise ProjectError("%s is missing: socket, ssl, asyncio and ctypes would not import"
                               % dlls)
        shutil.copytree(dlls, dest / "lib" / "Python" / "DLLs")
        stdlib_zip = self.dir / ("python%s.zip" % self.python_nodot)
        if stdlib_zip.is_file():
            shutil.copy2(stdlib_zip, dest / stdlib_zip.name)

    def _stage_stdlib(self, dest):
        src = self.dir / "lib" / "Python" / "Lib"
        if not src.is_dir():
            raise ProjectError("no Python stdlib at %s" % src)

        def ignore(directory, names):
            skip = set()
            for name in names:
                if os.path.isdir(os.path.join(directory, name)):
                    if name in STDLIB_EXCLUDED_DIRS:
                        skip.add(name)
                elif any(fnmatch.fnmatch(name, pat) for pat in STDLIB_EXCLUDED_FILES):
                    skip.add(name)
            return skip

        shutil.copytree(src, dest / "lib" / "Python" / "Lib", ignore=ignore)


# --- content and archives -------------------------------------------------------------

def copy_content(dest, assets, scripts):
    """Copy a game's assets/ and scripts/ into a staged package."""
    dest = Path(dest)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    for name, src in (("assets", assets), ("scripts", scripts)):
        if src is not None:
            shutil.copytree(src, dest / name, ignore=ignore)


def copy_release_docs(dest, source_root):
    """Bundle the rendered API docs. Returns the ones that were missing."""
    missing = []
    for src, dst in RELEASE_DOCS:
        path = Path(source_root) / src
        if not path.is_file():
            missing.append(src)
            continue
        out = Path(dest) / "docs" / dst
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out)
    return missing


def archive(staged, platform):
    """Archive the staged directory beside itself (tar.gz for Linux, zip for Windows),
    remove the directory, and return the archive's path."""
    staged = Path(staged)
    if platform == "linux":
        out = staged.with_name(staged.name + ".tar.gz")
        with tarfile.open(out, "w:gz") as tar:
            tar.add(staged, arcname=staged.name)
    else:
        out = staged.with_name(staged.name + ".zip")
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(staged.rglob("*")):
                zf.write(path, Path(staged.name) / path.relative_to(staged))
    shutil.rmtree(staged)
    return out


def fresh_dir(path):
    path = Path(path)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path
