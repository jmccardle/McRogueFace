"""#474: one definition of a web package, with index.html at the zip root.

The release WASM zip was hand-zipped in the Makefile (mcrogueface.html at the root, no
index.html), while `mcrf_project dist --platform web` nested index.html in a folder. Both
now come from mcrf_project.runtime.web_archive: a flat zip of index.html (the build's
mcrogueface.html) plus mcrogueface.{js,wasm,data}. A flat zip is what itch.io, static
hosts and a folder URL all serve.

It refuses a build that isn't a game-shell web build: the dev/playground shell carries the
REPL code panel (the 0.2.8 WASM zip shipped that by mistake), and a desktop build has no
web files. No emsdk needed: the build directories here are stand-ins.
"""
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
FILES = {"mcrogueface.html": b"<html>game shell</html>", "mcrogueface.js": b"js",
         "mcrogueface.wasm": b"\0asm", "mcrogueface.data": b"data"}


def fake_build(root, name, game_shell=True, sdl2=True, skip=()):
    d = Path(root) / name
    d.mkdir()
    (d / "CMakeCache.txt").write_text(
        "MCRF_SDL2:BOOL=%s\nMCRF_GAME_SHELL:BOOL=%s\n"
        % ("ON" if sdl2 else "OFF", "ON" if game_shell else "OFF"))
    for n, data in FILES.items():
        if n not in skip:
            (d / n).write_bytes(data)
    return d


def package_web(build, out, version="9.9.9"):
    r = subprocess.run([str(ENGINE), "-m", "mcrf_project", "package-web", "--build", str(build),
                        "--version", version, "--out", str(out)],
                       capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    out = tmp / "dist"

    print("1. a game-shell build packages flat, with index.html at the root")
    rc, log = package_web(fake_build(tmp, "game"), out)
    z = out / "McRogueFace-9.9.9-WASM.zip"
    check(rc == 0 and z.is_file(), "package-web exits 0 and writes %s (%d)%s"
          % (z.name, rc, "" if rc == 0 else "\n" + log[-400:]))
    if z.is_file():
        with zipfile.ZipFile(z) as zf:
            names = sorted(zf.namelist())
            check(names == ["index.html", "mcrogueface.data", "mcrogueface.js", "mcrogueface.wasm"],
                  "exactly index.html + js/wasm/data at the root: %s" % names)
            check(zf.read("index.html") == FILES["mcrogueface.html"],
                  "index.html is the build's mcrogueface.html")

    print("2. it refuses builds that would ship the wrong thing")
    for label, build, needle in [
        ("dev/playground shell", fake_build(tmp, "dev", game_shell=False), "MCRF_GAME_SHELL"),
        ("desktop build", fake_build(tmp, "desktop", sdl2=False), "MCRF_SDL2"),
        ("missing .wasm", fake_build(tmp, "partial", skip=("mcrogueface.wasm",)), "mcrogueface.wasm"),
    ]:
        rc, log = package_web(build, tmp / ("out-" + build.name))
        check(rc != 0 and needle in log, "%s: refused, naming %s (rc=%d) %s"
              % (label, needle, rc, log.strip().splitlines()[-1:] if log.strip() else ""))
        check(not list((tmp / ("out-" + build.name)).glob("*.zip")), "%s: no zip written" % label)
    nocache = tmp / "nocache"
    nocache.mkdir()
    rc, log = package_web(nocache, tmp / "out-nocache")
    check(rc != 0 and "CMakeCache.txt" in log, "a directory that isn't a build: refused (rc=%d)" % rc)

    print("3. a game's web dist uses the same definition")
    from mcrf_project import runtime
    z2 = runtime.web_archive(fake_build(tmp, "game2"), tmp / "My-Game-0.1.0-Web.zip")
    with zipfile.ZipFile(z2) as zf:
        check("index.html" in zf.namelist() and not any("/" in n for n in zf.namelist()),
              "web_archive output is flat with index.html: %s" % zf.namelist())

print("=" * 50)
if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
