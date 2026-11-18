"""#525: the Linux package carries what its own libraries need, and nothing build-host specific.

`libsfml-audio` records the libFLAC it was linked against (a soname that differs between
distros), and used to carry a RUNPATH into the build tree; the package shipped no FLAC, so
it failed to start on a distro with another one. Stages a package with
`mcrf_project package-engine`, then reads the ELF headers of what it ships:

  1. the libFLAC named by libsfml-audio's DT_NEEDED is a real file in lib/
  2. every DT_NEEDED of the engine binary and of the libraries directly in lib/ is either
     shipped in lib/ or one of the host-provided libraries documented in README.md
  3. the binary, and every lib/*.so that needs another library from lib/, carries a RUNPATH
     containing $ORIGIN (a RUNPATH is not used for the dependencies of dependencies, so each
     library must find its siblings itself), and no shipped ELF has an absolute one
  4. README.md documents every host package the clean-distro gate installs

No containers needed; the clean-distro run itself is in tools/smoke_package.py.
"""
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "build" / "mcrogueface"

# Provided by the host, not the package: glibc/libstdc++/libgcc, and the audio, video and
# input libraries README.md lists as requirements. libGL.so.1 and libOpenGL.so.0 are both
# there because SFML links whichever of them its build host's CMake found: the libgl1
# package (README.md, ENGINE_PACKAGES) provides libGL.so.1 and libopengl0 the other, and
# the clean-distro gate installs both.
HOST_PROVIDED = re.compile(
    r"^(ld-linux-x86-64\.so\.2|lib(c|m|dl|pthread|rt|util|stdc\+\+|gcc_s)\.so\.[0-9.]+"
    r"|libopenal\.so\.1|libvorbis(file|enc)?\.so\.[0-9]+|libogg\.so\.0|libfreetype\.so\.6"
    r"|libX11\.so\.6|libXrandr\.so\.2|libXcursor\.so\.1|libudev\.so\.1|libOpenGL\.so\.0"
    r"|libGL\.so\.1|libz\.so\.1)$")


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def runpaths(path):
    return [e for m in re.finditer(r"\((?:RUNPATH|RPATH)\)\s+Library (?:runpath|rpath): \[(.*?)\]",
                                   dynamic(path)) for e in m.group(1).split(":") if e]


def dynamic(path):
    r = subprocess.run(["readelf", "-d", str(path)], capture_output=True, text=True)
    if r.returncode != 0:
        fail("readelf -d %s: %s" % (path, r.stderr))
    return r.stdout


def needed(path):
    return re.findall(r"\(NEEDED\)\s+Shared library: \[(.*?)\]", dynamic(path))


def is_elf(path):
    with open(path, "rb") as f:
        return f.read(4) == b"\x7fELF"


with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "out"
    r = subprocess.run([str(ENGINE), "-m", "mcrf_project", "package-engine",
                        "--version", "0.0.0-test", "--out", str(out)],
                       capture_output=True, text=True, timeout=170)
    if r.returncode != 0:
        fail("package-engine failed:\n" + r.stdout + r.stderr)
    with tarfile.open(out / "McRogueFace-0.0.0-test-Linux.tar.gz") as tf:
        tf.extractall(out, filter="data")
    pkg = out / "McRogueFace-0.0.0-test-Linux"
    lib = pkg / "lib"

    audio = [p for p in lib.glob("libsfml-audio.so.*.*.*") if not p.is_symlink()]
    if len(audio) != 1:
        fail("expected one libsfml-audio.so.X.Y.Z in lib/, got %r" % audio)
    audio = audio[0]
    flac = [n for n in needed(audio) if n.startswith("libFLAC.so.")]
    if len(flac) != 1:
        fail("libsfml-audio records %r, expected exactly one libFLAC" % flac)
    shipped = lib / flac[0]
    if not shipped.is_file() or shipped.is_symlink() or not is_elf(shipped):
        fail("%s (needed by libsfml-audio) is not a real file in the package's lib/" % flac[0])
    print("ok: libsfml-audio needs %s, shipped in lib/" % flac[0])

    undocumented = []
    for path in [pkg / "mcrogueface"] + sorted(p for p in lib.iterdir()
                                              if p.is_file() and not p.is_symlink()
                                              and ".so" in p.name):
        for name in needed(path):
            if not (lib / name).exists() and not HOST_PROVIDED.match(name):
                undocumented.append("%s needs %s" % (path.relative_to(pkg), name))
    if undocumented:  # all of them at once: one CI round trip, not one per library
        fail("neither in lib/ nor a documented host library:\n  " + "\n  ".join(undocumented))
    print("ok: every dependency of the binary and lib/*.so is shipped or documented as host-provided")

    real_libs = sorted(p for p in lib.iterdir()
                       if p.is_file() and not p.is_symlink() and ".so" in p.name)
    for path in [pkg / "mcrogueface"] + real_libs:
        if any((lib / n).exists() for n in needed(path)):
            if not any(e.startswith("$ORIGIN") for e in runpaths(path)):
                fail("%s needs a library from lib/ but has RUNPATH %r, no $ORIGIN entry: "
                     "it only starts through LD_LIBRARY_PATH" % (path.relative_to(pkg), runpaths(path)))
    print("ok: everything that needs a sibling library has an $ORIGIN RUNPATH")

    for path in [pkg / "mcrogueface"] + sorted(p for p in lib.rglob("*")
                                              if p.is_file() and not p.is_symlink()
                                              and is_elf(p)):
        for entry in runpaths(path):
            if entry.startswith("/"):
                fail("%s has an absolute RUNPATH entry %r (a build-host path)"
                     % (path.relative_to(pkg), entry))
    print("ok: no shipped ELF has an absolute RUNPATH/RPATH")

sys.path.insert(0, str(ROOT / "tools"))
import smoke_package  # noqa: E402  (the gate's constants are the one list of host packages)
readme = (ROOT / "README.md").read_text()
for pkg_name in (smoke_package.ENGINE_PACKAGES + " " + smoke_package.STDLIB_PACKAGES).split():
    if pkg_name not in readme:
        fail("README.md does not document %s, which the clean-distro gate installs" % pkg_name)
print("ok: README.md lists every package the clean-distro gate installs")
print("PASS")
sys.exit(0)
