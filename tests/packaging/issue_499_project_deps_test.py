"""#499: project dependencies. mcrf.toml requirements -> <project>/.venv (a real venv, #517), bundled by dist.

No network: the "package" is a pure-Python wheel this test writes. Checks `deps` installs
with the engine's own interpreter and shipped pip into the project (not the engine), that a
stale or missing install is an error rather than a silently broken package, that `dist`
ships the packages where the packaged engine's sibling venv/ rule finds them (the
packaged binary then imports one), and that an extracted package can run `deps` itself
(it ships pip).
"""
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


ENGINE = Path(sys.executable).resolve()
PY = "%d.%d" % sys.version_info[:2]
ENV = {k: v for k, v in os.environ.items()
       if k not in ("DISPLAY", "WAYLAND_DISPLAY", "MCROGUEFACE", "PYTHONPATH", "PYTHONHOME")}
ENV["ALSOFT_DRIVERS"] = "null"
ENV["XDG_DATA_HOME"] = tempfile.mkdtemp()


def tool(*args, cwd, exe=ENGINE):
    out = subprocess.run([str(exe), "-m", "mcrf_project"] + list(args), cwd=str(cwd),
                         capture_output=True, text=True, timeout=300, env=ENV)
    return out.returncode, out.stdout + out.stderr


def make_wheel(directory, name, version, body):
    """A minimal pure-Python wheel."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ("%s-%s-py3-none-any.whl" % (name, version))
    info = "%s-%s.dist-info" % (name, version)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("%s/__init__.py" % name, body)
        zf.writestr("%s/METADATA" % info, "Metadata-Version: 2.1\nName: %s\nVersion: %s\n" % (name, version))
        zf.writestr("%s/WHEEL" % info, "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\n"
                                       "Tag: py3-none-any\n")
        zf.writestr("%s/RECORD" % info, "")
    return path


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp).resolve()
    wheels = tmp / "wheels"
    wheel = make_wheel(wheels, "mcrf_dep_demo", "1.0", "VALUE = 'from the wheel'\n")
    game = tmp / "game"
    rc, out = tool("init", str(game), cwd=tmp)
    check(rc == 0, "init works")
    (game / "scripts" / "game.py").write_text(
        "import sys, mcrf_dep_demo\nprint('DEP', mcrf_dep_demo.VALUE, mcrf_dep_demo.__file__)\nsys.exit(0)\n")
    check(".venv/" in (game / ".gitignore").read_text(), "init ignores .venv/ in git")

    # no requirements: deps says so; dist/run don't care
    rc, out = tool("deps", cwd=game)
    check(rc == 1 and "no requirements" in out and "Traceback" not in out, "deps without requirements is an error")

    (game / "mcrf.toml").write_text('requirements = ["%s"]\n' % wheel)
    rc, out = tool("dist", cwd=game)
    check(rc == 1 and "run: mcrogueface -m mcrf_project deps" in out, "dist before deps says to run deps")
    check(not list((game / "dist").glob("*")), "a refused dist leaves nothing in dist/")
    rc, out = tool("run", "--", "--headless", cwd=game)
    check(rc == 1 and "mcrf_project deps" in out, "run before deps says to run deps")

    # deps installs into the project
    rc, out = tool("deps", cwd=game)
    sp = game / ".venv" / "lib" / ("python" + PY) / "site-packages"
    check(rc == 0 and (sp / "mcrf_dep_demo" / "__init__.py").is_file(),
          "deps installs the requirement into .venv/lib/python%s/site-packages%s"
          % (PY, "" if rc == 0 else "\n" + out[-800:]))
    check(not (ENGINE.parent / "venv").exists(), "nothing was created beside the engine")
    check((game / ".venv" / "pyvenv.cfg").is_file() and (game / ".venv" / "bin" / "python").exists(),
          "deps makes a real venv (.venv/pyvenv.cfg, .venv/bin/python)")

    # run launches .venv/bin/mcrogueface, for game mode and for --exec alike
    rc, out = tool("run", "--", "--headless", cwd=game)
    check(rc == 0 and "DEP from the wheel %s" % (sp / "mcrf_dep_demo" / "__init__.py") in out,
          "run imports the dependency from .venv (game mode)%s" % ("" if rc == 0 else "\n" + out[-800:]))
    probe = tmp / "probe.py"
    probe.write_text("import sys, mcrf_dep_demo\nprint('EXEC', mcrf_dep_demo.VALUE)\nsys.exit(0)\n")
    rc, out = tool("run", "--", "--headless", "--exec", str(probe), cwd=game)
    check(rc == 0 and "EXEC from the wheel" in out, "run imports the dependency from .venv (--exec)")

    # a failing requirement is an error and leaves no half install
    (game / "mcrf.toml").write_text('requirements = ["no-such-package-mcrf-499"]\n')
    rc, out = tool("deps", cwd=game)
    check(rc == 1 and "pip failed" in out and not (game / ".venv").exists(),
          "a requirement pip can't satisfy fails and leaves no .venv")

    # requirements-file, with pip's own options inside it
    (game / "requirements.txt").write_text("--no-index\n--find-links %s\nmcrf_dep_demo==1.0\n" % wheels)
    (game / "mcrf.toml").write_text('requirements-file = "requirements.txt"\n')
    rc, out = tool("deps", cwd=game)
    check(rc == 0 and (sp / "mcrf_dep_demo").is_dir(), "requirements-file works%s"
          % ("" if rc == 0 else "\n" + out[-800:]))

    # stale: changing the file after install is an error until deps runs again
    (game / "requirements.txt").write_text("--no-index\n--find-links %s\nmcrf_dep_demo==1.0\n\n" % wheels)
    rc, out = tool("dist", cwd=game)
    check(rc == 1 and "changed since" in out, "dist after the requirements changed asks for deps")
    rc, out = tool("deps", cwd=game)
    check(rc == 0, "deps again")

    # dist ships them where the packaged engine looks (sibling venv/)
    rc, out = tool("dist", "--platform", "linux", cwd=game)
    tar_path = game / "dist" / "game-0.1.0-Linux.tar.gz"
    check(rc == 0 and tar_path.is_file(), "dist builds the package%s" % ("" if rc == 0 else "\n" + out[-800:]))
    if tar_path.is_file():
        extract = tmp / "pkg"
        with tarfile.open(tar_path) as tar:
            tar.extractall(extract, filter="data")
        pkg = extract / "game-0.1.0-Linux"
        shipped = pkg / "venv" / "lib" / ("python" + PY) / "site-packages" / "mcrf_dep_demo" / "__init__.py"
        check(shipped.is_file(), "the package ships venv/lib/python%s/site-packages/mcrf_dep_demo" % PY)
        check(not any("__pycache__" in str(p) for p in (pkg / "venv").rglob("*")), "no bytecode ships from .venv")
        check(not (pkg / ".venv").exists() and not (pkg / "mcrf.toml").exists(),
              "neither .venv/ nor mcrf.toml ships as such")
        env = {k: v for k, v in ENV.items() if k != "LD_LIBRARY_PATH"}
        out = subprocess.run([str(pkg / "mcrogueface"), "--headless"], cwd=str(pkg),
                             capture_output=True, text=True, timeout=60, env=env)
        text = out.stdout + out.stderr
        check(out.returncode == 0 and "DEP from the wheel %s" % pkg in text,
              "the packaged game imports its dependency from the package (rc=%d)\n%s"
              % (out.returncode, "" if out.returncode == 0 else text[-600:]))

        # #510: a game package marks itself, and then owns its interpreter: the player's
        # VIRTUAL_ENV (here one that isn't even a venv) is ignored, not fatal
        check((pkg / "mcrf-game.json").is_file(), "dist writes the game-package marker mcrf-game.json")
        out = subprocess.run([str(pkg / "mcrogueface"), "--headless"], cwd=str(pkg),
                             capture_output=True, text=True, timeout=60,
                             env=dict(env, VIRTUAL_ENV=str(tmp / "not-a-venv")))
        text = out.stdout + out.stderr
        check(out.returncode == 0 and "DEP from the wheel %s" % pkg in text,
              "the packaged game ignores the player's VIRTUAL_ENV (rc=%d)\n%s"
              % (out.returncode, "" if out.returncode == 0 else text[-600:]))

        # the package ships pip: it can install the project's dependencies itself
        # The package's own venv/ is on that engine's sys.path (the sibling rule), so pip in a
        # new .venv would find the dependency "already satisfied" there and install nothing:
        # remove it, leaving the package as just an engine.
        shutil.rmtree(pkg / "venv")
        rc, out = tool("deps", "--engine", str(pkg), cwd=game)
        check(rc == 0 and (sp / "mcrf_dep_demo").is_dir(),
              "an extracted package can run deps (it ships pip)%s" % ("" if rc == 0 else "\n" + out[-800:]))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
