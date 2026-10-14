"""Which engine a project uses (#500).

A project doesn't know where the engine's source tree is. The engine for a command is the
first of these that names one:

  1. ``--engine DIR``                          (an explicit choice; a bad one is an error)
  2. the ``MCROGUEFACE`` environment variable  (a directory, or the mcrogueface binary)
  3. ``engine`` in the project's mcrf.toml     (a directory; ``engine-version`` below)
  4. a per-user install: ``$XDG_DATA_HOME/mcrogueface/<version>/`` (default
     ``~/.local/share/mcrogueface/<version>/``): the newest version, or the one
     ``engine-version`` in mcrf.toml names
  5. the engine running ``mcrf_project``

A source that is set but wrong (no such directory, not an engine) is an error: it never
falls through to the next. A source that is a *different platform's* engine than the one
asked for (``dist --platform windows`` with a Linux ``MCROGUEFACE``) is passed over, and
listed in the error if nothing else matches. ``info`` says which one was chosen.
The engine is read-only to projects: nothing here or in ``run``/``dist``/``deps`` writes
under it.
"""
import os
import re
from pathlib import Path

from .errors import ProjectError
from .runtime import Runtime

ENV_VAR = "MCROGUEFACE"
_VERSION_DIR = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$")


def user_engine_root(environ=None):
    environ = os.environ if environ is None else environ
    data = environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(data) / "mcrogueface"


def _version_key(name):
    """Sort key for an install directory name, or None if it isn't a version. A release
    sorts after its own -dev/-rc builds."""
    m = _VERSION_DIR.match(name)
    if not m:
        return None
    major, minor, patch, suffix = m.groups()
    return (int(major), int(minor), int(patch), suffix is None, suffix or "")


def installed_versions(root):
    """(version name, directory) of each version installed under `root`, oldest first."""
    if not root.is_dir():
        return []
    found = [(_version_key(p.name), p.name, p) for p in root.iterdir() if p.is_dir()]
    return [(name, path) for key, name, path in sorted(f for f in found if f[0] is not None)]


def _engine_dir(value, what):
    """The directory a user-supplied engine location means: a directory, or the binary."""
    path = Path(value).expanduser()
    if path.is_file() and path.name in ("mcrogueface", "mcrogueface.exe"):
        path = path.parent
    if not path.is_dir():
        raise ProjectError("%s names %s, which is not a directory" % (what, value))
    return path


class Located:
    """The engine chosen, and why."""

    def __init__(self, runtime, source, detail):
        self.runtime = runtime
        self.source = source      # short name of the rule that chose it
        self.detail = detail      # what that rule looked at

    def describe(self):
        return "%s (%s)" % (self.source, self.detail)


def locate(project, platform=None, flag=None, running=None, environ=None):
    """The engine for `project` on `platform` (default: the running engine's), as a
    Located. Raises ProjectError naming every source tried if there is none."""
    environ = os.environ if environ is None else environ
    running = running or Runtime.running()
    platform = platform or running.platform
    rejected = []

    def offer(directory, source, detail, explicit=False):
        engine = Runtime(directory)  # raises ProjectError: set but not an engine
        if engine.platform != platform:
            if explicit:
                raise ProjectError("%s is a %s engine, not %s" % (engine.dir, engine.platform, platform))
            rejected.append("%s: %s is a %s engine" % (source, engine.dir, engine.platform))
            return None
        return Located(engine, source, detail)

    if flag:
        found = offer(_engine_dir(flag, "--engine"), "--engine", flag, explicit=True)
        if found:
            return found

    if environ.get(ENV_VAR):
        found = offer(_engine_dir(environ[ENV_VAR], "$" + ENV_VAR), "$" + ENV_VAR, environ[ENV_VAR])
        if found:
            return found

    config = project.config
    if "engine" in config:
        found = offer(_engine_dir(config["engine"], "engine in %s" % project.config_path),
                      "engine in mcrf.toml", config["engine"])
        if found:
            return found

    root = user_engine_root(environ)
    pinned = config.get("engine-version")
    if pinned is not None:
        wanted = [(n, p) for n, p in installed_versions(root) if n == pinned]
        if not wanted:
            raise ProjectError("%s wants engine %s, but there is no %s"
                               % (project.config_path.name, pinned, root / pinned))
        candidates = wanted
    else:
        candidates = list(reversed(installed_versions(root)))  # newest first
    for name, path in candidates:
        found = offer(path, "user install", "%s, %s" % (
            path, "engine-version %s" % pinned if pinned else "the newest installed"))
        if found:
            return found

    if running.platform == platform:
        return Located(running, "running engine",
                       "nothing set %s, no engine under %s" % (ENV_VAR, root))
    sibling = running.source_root / "build-windows" if running.source_root and platform == "windows" else None
    if sibling is not None and (sibling / "mcrogueface.exe").is_file():
        return Located(Runtime(sibling), "source tree", "%s beside the running engine" % sibling)
    raise ProjectError("no %s engine found. Tried: %s. Pass --engine DIR (a %s build or an "
                       "extracted release package), set %s, or install one under %s"
                       % (platform, "; ".join(rejected) or "nothing set; the running engine is %s"
                          % running.platform, platform, ENV_VAR, root))
