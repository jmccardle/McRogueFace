"""#509: `mcrf_project deps` must not delete a .venv it did not make.

`deps` replaces <project>/.venv on every run (a removed requirement must not linger), but
it removed whatever was there: a developer's own virtualenv, with their files in it, went
with no warning. It now replaces only an empty directory or one holding its own stamp
(mcrf-deps.json), and refuses anything else -- before pip runs, so a failed install
can't delete it either.

No network: the requirement is a pure-Python wheel this test writes.
"""
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


ENGINE = Path(sys.executable).resolve()
ENV = {k: v for k, v in os.environ.items()
       if k not in ("DISPLAY", "WAYLAND_DISPLAY", "MCROGUEFACE", "PYTHONPATH", "PYTHONHOME",
                    "VIRTUAL_ENV")}
ENV["ALSOFT_DRIVERS"] = "null"
ENV["XDG_DATA_HOME"] = tempfile.mkdtemp()


def tool(*args, cwd):
    out = subprocess.run([str(ENGINE), "-m", "mcrf_project"] + list(args), cwd=str(cwd),
                         capture_output=True, text=True, timeout=300, env=ENV)
    return out.returncode, out.stdout + out.stderr


def make_wheel(directory, name, version):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ("%s-%s-py3-none-any.whl" % (name, version))
    info = "%s-%s.dist-info" % (name, version)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("%s/__init__.py" % name, "VALUE = 1\n")
        zf.writestr("%s/METADATA" % info, "Metadata-Version: 2.1\nName: %s\nVersion: %s\n" % (name, version))
        zf.writestr("%s/WHEEL" % info, "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\n"
                                       "Tag: py3-none-any\n")
        zf.writestr("%s/RECORD" % info, "")
    return path


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp).resolve()
    wheel = make_wheel(tmp / "wheels", "mcrf_dep_509", "1.0")
    game = tmp / "game"
    rc, out = tool("init", str(game), cwd=tmp)
    check(rc == 0, "init works")
    (game / "mcrf.toml").write_text('requirements = ["%s"]\n' % wheel)
    venv = game / ".venv"

    # A virtualenv someone made: deps refuses and leaves every file alone
    (venv / "bin").mkdir(parents=True)
    (venv / "pyvenv.cfg").write_text("home = /usr/bin\n")
    (venv / "keep.txt").write_text("mine")
    rc, out = tool("deps", cwd=game)
    check(rc == 1 and "Traceback" not in out, "deps refuses a .venv it did not make (rc=%d)" % rc)
    check(str(venv) in out and "mcrf-deps.json" in out, "the refusal names the directory and the stamp")
    check((venv / "keep.txt").read_text() == "mine" and (venv / "bin").is_dir(),
          "keep.txt and bin/ survive")

    # ...including when the install would have failed (the old failure path also removed it)
    (game / "mcrf.toml").write_text('requirements = ["%s"]\n' % (tmp / "no-such-1.0-py3-none-any.whl"))
    rc, out = tool("deps", cwd=game)
    check(rc == 1 and (venv / "keep.txt").is_file(), "a would-fail install leaves it alone too")
    (game / "mcrf.toml").write_text('requirements = ["%s"]\n' % wheel)

    # .venv as a file is refused, not removed
    for p in sorted(venv.rglob("*"), reverse=True):
        p.rmdir() if p.is_dir() else p.unlink()
    venv.rmdir()
    venv.write_text("not a directory")
    rc, out = tool("deps", cwd=game)
    check(rc == 1 and venv.is_file() and "Traceback" not in out, "a .venv file is refused and kept")
    venv.unlink()

    # An empty directory is fine to fill
    venv.mkdir()
    rc, out = tool("deps", cwd=game)
    check(rc == 0 and (venv / "mcrf-deps.json").is_file(), "an empty .venv is installed into")

    # Its own install is replaced on the next run, stray files and all
    (venv / "stray.txt").write_text("from an older install")
    rc, out = tool("deps", cwd=game)
    check(rc == 0 and not (venv / "stray.txt").exists() and (venv / "mcrf-deps.json").is_file(),
          "deps replaces its own .venv")

    # A failed install of its own .venv still leaves nothing looking installed
    (game / "mcrf.toml").write_text('requirements = ["%s"]\n' % (tmp / "no-such-1.0-py3-none-any.whl"))
    rc, out = tool("deps", cwd=game)
    check(rc == 1 and not venv.exists(), "a failed install removes the .venv it was replacing")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
