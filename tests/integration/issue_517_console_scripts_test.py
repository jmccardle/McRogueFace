"""#517: a requirement's console scripts work after `mcrf_project deps`.

`deps` used to run `pip install --target`, which writes console scripts nowhere useful (no
bin/, and a shebang naming no interpreter). It now makes a real venv (`<engine> -m venv
.venv`) and installs with that venv's own pip, so pip's normal `.venv/bin/<name>` appears,
runs under `.venv/bin/python` and exits. `dist` ships the venv's site-packages as
venv/lib/python3.X/site-packages and nothing else of it (no bin/, pyvenv.cfg, include/).

No network: the requirement is a wheel this test writes with zipfile, found with
--no-index --find-links in a requirements file.
"""
import os
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
       if k not in ("DISPLAY", "WAYLAND_DISPLAY", "MCROGUEFACE", "PYTHONPATH", "PYTHONHOME",
                    "VIRTUAL_ENV")}
ENV["ALSOFT_DRIVERS"] = "null"
ENV["XDG_DATA_HOME"] = tempfile.mkdtemp()

NAME = "mcrf_cli_517"
MARKER = "CLI517-MARKER-2b9d"


def tool(*args, cwd):
    out = subprocess.run([str(ENGINE), "-m", "mcrf_project"] + list(args), cwd=str(cwd),
                         capture_output=True, text=True, timeout=300, env=ENV)
    return out.returncode, out.stdout + out.stderr


def make_wheel(directory):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ("%s-1.0-py3-none-any.whl" % NAME)
    info = "%s-1.0.dist-info" % NAME
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("%s/__init__.py" % NAME,
                    "import sys\n"
                    "def main():\n"
                    "    print('PREFIX ' + sys.prefix)\n"
                    "    print('%s')\n"
                    "    return 0\n" % MARKER)
        zf.writestr("%s/METADATA" % info, "Metadata-Version: 2.1\nName: %s\nVersion: 1.0\n" % NAME)
        zf.writestr("%s/WHEEL" % info, "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\n"
                                       "Tag: py3-none-any\n")
        zf.writestr("%s/entry_points.txt" % info,
                    "[console_scripts]\n%s = %s:main\n" % (NAME, NAME))
        zf.writestr("%s/RECORD" % info, "")
    return path


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp).resolve()
    wheels = tmp / "wheels"
    make_wheel(wheels)
    game = tmp / "game"
    rc, out = tool("init", str(game), cwd=tmp)
    check(rc == 0, "init works")
    (game / "requirements.txt").write_text("--no-index\n--find-links %s\n%s==1.0\n" % (wheels, NAME))
    (game / "mcrf.toml").write_text('requirements-file = "requirements.txt"\n')

    rc, out = tool("deps", cwd=game)
    check(rc == 0, "deps succeeds%s" % ("" if rc == 0 else "\n" + out[-1200:]))
    venv = game / ".venv"
    script = venv / "bin" / NAME
    check(script.is_file() and os.access(script, os.X_OK), ".venv/bin/%s exists and is executable" % NAME)
    check((venv / "bin" / "python").exists(), ".venv/bin/python exists (a real venv)")

    if script.is_file():
        try:
            r = subprocess.run([str(script)], capture_output=True, text=True, timeout=30,
                               env=ENV, cwd=str(tmp))
            check(r.returncode == 0, ".venv/bin/%s exits 0%s" % (NAME, "" if r.returncode == 0 else "\n" + r.stdout + r.stderr))
            fields = dict(l.split(" ", 1) for l in r.stdout.splitlines() if " " in l)
            check(MARKER in r.stdout, "the entry point ran")
            check(os.path.realpath(fields.get("PREFIX", "")) == os.path.realpath(venv),
                  "sys.prefix is the project's .venv (%s)" % fields.get("PREFIX"))
        except subprocess.TimeoutExpired:
            check(False, ".venv/bin/%s exits by itself" % NAME)

    # dist ships site-packages only. Packaging needs a Release engine (debug, free-threaded
    # and sanitizer engines refuse to package; the alternate-build suites run this too).
    if sys.abiflags:
        print("  skip: dist (engine is a Python %s%s build, which cannot package)" % (PY, sys.abiflags))
    else:
        rc, out = tool("dist", "--platform", "linux", cwd=game)
        tar_path = game / "dist" / "game-0.1.0-Linux.tar.gz"
        check(rc == 0 and tar_path.is_file(), "dist builds the package%s" % ("" if rc == 0 else "\n" + out[-1200:]))
        if tar_path.is_file():
            extract = tmp / "pkg"
            with tarfile.open(tar_path) as tar:
                tar.extractall(extract, filter="data")
            pkg = extract / "game-0.1.0-Linux"
            sp = pkg / "venv" / "lib" / ("python" + PY) / "site-packages"
            check((sp / NAME / "__init__.py").is_file(), "the package ships venv/lib/python%s/site-packages/%s" % (PY, NAME))
            check(not (pkg / "venv" / "bin").exists(), "no venv/bin in the package")
            check(not (pkg / "venv" / "pyvenv.cfg").exists(), "no venv/pyvenv.cfg in the package")
            check(not (pkg / "venv" / "include").exists(), "no venv/include in the package")
            check(not (sp / "pip").exists(), "venv bootstrap pip is not shipped as a dependency")
            check(not (pkg / ".venv").exists(), ".venv/ does not ship as such")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
