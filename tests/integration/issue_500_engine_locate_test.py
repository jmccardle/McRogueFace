"""#500: `mcrf_project run/info/dist` locate an installed engine.

Order: --engine, $MCROGUEFACE, `engine` in mcrf.toml, the newest per-user install
(~/.local/share/mcrogueface/<version>/, honouring XDG_DATA_HOME), then the running
engine. A source that is set but wrong is an error, never a fall-through. `info` says
which one it chose. Fake engines (a shell script and an empty libpython) tell them apart.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


ENGINE = Path(sys.executable).resolve()
PY = "%d.%d" % sys.version_info[:2]
BASE_ENV = {k: v for k, v in os.environ.items()
            if k not in ("DISPLAY", "WAYLAND_DISPLAY", "MCROGUEFACE", "XDG_DATA_HOME")}
BASE_ENV["ALSOFT_DRIVERS"] = "null"


def tool(*args, cwd, engine=None, **env):
    e = dict(BASE_ENV, **env)
    out = subprocess.run([str(engine or ENGINE), "-m", "mcrf_project"] + list(args), cwd=str(cwd),
                         capture_output=True, text=True, timeout=120, env=e)
    return out.returncode, out.stdout + out.stderr


def fake_engine(directory):
    """A directory that is an engine as far as mcrf_project can tell, and says who it is."""
    directory.mkdir(parents=True)
    exe = directory / "mcrogueface"
    exe.write_text('#!/bin/sh\necho "FAKE-ENGINE $(dirname "$0")"\n')
    exe.chmod(0o755)
    (directory / "lib").mkdir()
    (directory / "lib" / ("libpython%s.so.1.0" % PY)).write_text("")
    return directory


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp).resolve()
    data = tmp / "data"                     # XDG_DATA_HOME: empty unless a case fills it
    xdg = {"XDG_DATA_HOME": str(data)}
    game = tmp / "game"
    rc, out = tool("init", str(game), cwd=tmp, **xdg)
    check(rc == 0, "init works (%d)" % rc)
    check((game / "mcrf.toml").is_file(), "init writes a commented mcrf.toml")
    (game / "scripts" / "game.py").write_text("import sys\nprint('GAME RAN')\nsys.exit(0)\n")

    a = fake_engine(tmp / "engine-a")
    b = fake_engine(tmp / "engine-b")

    # 5. nothing set: the running engine, and info says so
    rc, out = tool("info", cwd=game, **xdg)
    check(rc == 0 and "running engine" in out and str(ENGINE.parent) in out,
          "with nothing set, info chooses the running engine\n" + out)
    rc, out = tool("run", "--", "--headless", cwd=game, **xdg)
    check(rc == 0 and "GAME RAN" in out, "run uses the running engine by default")

    # 2. $MCROGUEFACE, as a directory or as the binary
    rc, out = tool("run", cwd=game, MCROGUEFACE=str(a), **xdg)
    check(rc == 0 and "FAKE-ENGINE %s" % a in out, "run uses the engine $MCROGUEFACE names")
    rc, out = tool("run", cwd=game, MCROGUEFACE=str(a / "mcrogueface"), **xdg)
    check(rc == 0 and "FAKE-ENGINE %s" % a in out, "$MCROGUEFACE may name the binary")
    rc, out = tool("info", cwd=game, MCROGUEFACE=str(a), **xdg)
    check(rc == 0 and "$MCROGUEFACE" in out and str(a) in out, "info says $MCROGUEFACE chose it\n" + out)
    rc, out = tool("run", cwd=game, MCROGUEFACE=str(tmp / "nope"), **xdg)
    check(rc == 1 and "nope" in out and "GAME RAN" not in out and "Traceback" not in out,
          "a bad $MCROGUEFACE is an error, not a fall-through")
    rc, out = tool("run", cwd=game, MCROGUEFACE=str(tmp), **xdg)
    check(rc == 1 and "not an engine directory" in out, "a directory with no engine in it is an error")

    # 3. mcrf.toml, beaten by the environment, and validated
    (game / "mcrf.toml").write_text('engine = "%s"\n' % b)
    rc, out = tool("run", cwd=game, **xdg)
    check(rc == 0 and "FAKE-ENGINE %s" % b in out, "run uses engine from mcrf.toml")
    rc, out = tool("run", cwd=game, MCROGUEFACE=str(a), **xdg)
    check("FAKE-ENGINE %s" % a in out, "$MCROGUEFACE beats mcrf.toml")
    # 1. --engine beats both
    rc, out = tool("run", "--engine", str(b), cwd=game, MCROGUEFACE=str(a), **xdg)
    check("FAKE-ENGINE %s" % b in out, "--engine beats $MCROGUEFACE")
    (game / "mcrf.toml").write_text('engin = "%s"\n' % b)
    rc, out = tool("info", cwd=game, **xdg)
    check(rc == 1 and "unknown key" in out and "engin" in out, "a misspelled mcrf.toml key is an error")

    # 4. per-user install: newest wins numerically, a release beats its -dev, engine-version pins
    (game / "mcrf.toml").write_text("")
    root = data / "mcrogueface"
    for v in ("0.3.9", "0.3.10", "0.3.10-dev", "0.2.0"):
        fake_engine(root / v)
    (root / "not-a-version").mkdir()
    rc, out = tool("run", cwd=game, **xdg)
    check("FAKE-ENGINE %s" % (root / "0.3.10") in out, "the newest installed version is used (0.3.10 > 0.3.9)\n" + out)
    rc, out = tool("info", cwd=game, **xdg)
    check("user install" in out and str(root / "0.3.10") in out, "info says it is a user install")
    (game / "mcrf.toml").write_text('engine-version = "0.3.9"\n')
    rc, out = tool("run", cwd=game, **xdg)
    check("FAKE-ENGINE %s" % (root / "0.3.9") in out, "engine-version picks that install")
    (game / "mcrf.toml").write_text('engine-version = "9.9.9"\n')
    rc, out = tool("run", cwd=game, **xdg)
    check(rc == 1 and "9.9.9" in out and "GAME RAN" not in out, "engine-version with no such install is an error")

    # platform: a Linux engine from $MCROGUEFACE is passed over for a Windows package, and
    # the error says what was tried; --engine naming the wrong platform is an error.
    # The running engine is a private copy with nothing beside it: a dev checkout that has a
    # build-windows/ next to build/ would otherwise satisfy the "source tree" rule.
    private = tmp / "private" / "engine"
    private.mkdir(parents=True)
    shutil.copy2(ENGINE, private / ENGINE.name)
    for name in ("lib", "assets", "scripts"):
        os.symlink(str(ENGINE.parent / name), str(private / name))
    pengine = private / ENGINE.name
    (game / "mcrf.toml").write_text("")
    rc, out = tool("dist", "--platform", "windows", cwd=game, engine=pengine, MCROGUEFACE=str(ENGINE.parent), **xdg)
    check(rc == 1 and "$MCROGUEFACE" in out and "linux" in out and "Traceback" not in out,
          "dist --platform windows names what it rejected\n" + out)
    rc, out = tool("dist", "--platform", "windows", "--engine", str(ENGINE.parent), cwd=game, engine=pengine, **xdg)
    check(rc == 1 and "not windows" in out, "--engine of the wrong platform is an error")

    # the engine is read-only to a project: nothing was written under the fakes
    check(sorted(p.name for p in a.iterdir()) == ["lib", "mcrogueface"], "nothing written under an engine")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
