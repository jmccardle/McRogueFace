"""Gate for the snippet tooling added under #541.

Covers tools/snippet_regions.py (region markers), tools/lint_snippet_batch.py (the
agent-independent batch lint), and tools/stamp_snippets.py --only.

Runs under the engine like every test here; the tools are plain python3 scripts, imported
by path, and the CLI cases shell out to python3 exactly as a developer would.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)



def _read(path):
    with open(path) as f:
        return f.read()

def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


regions = load("snippet_regions")
lint = load("lint_snippet_batch")
stamp = load("stamp_snippets")

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def region_error(src):
    try:
        regions.parse(src)
    except regions.RegionError as e:
        return e.problems
    return None


# ---- regions ---------------------------------------------------------------------
GOOD = "import mcrfpy\n# region: a\n    x = 1\n    y = 2\n# endregion\nz = 3\n# region: b-2\nq = 4\n# endregion\n"
r = regions.parse(GOOD)
check(r == {"a": (3, 4), "b-2": (8, 8)}, f"parse finds both regions with body line ranges: {r}")
check(regions.region_text(GOOD, "a") == "x = 1\ny = 2\n", "region_text dedents and drops marker lines")
check(regions.strip_markers(GOOD) == "import mcrfpy\n    x = 1\n    y = 2\nz = 3\nq = 4\n",
      "strip_markers removes only marker lines")
check(regions.parse("print(1)\n") == {}, "a file with no regions is valid")

for label, src, needle in [
    ("unclosed", "# region: a\nx = 1\n", "never closed"),
    ("duplicate", "# region: a\nx=1\n# endregion\n# region: a\ny=1\n# endregion\n", "duplicate"),
    ("nested", "# region: a\n# region: b\nx=1\n# endregion\n# endregion\n", "do not nest"),
    ("stray endregion", "x = 1\n# endregion\n", "no open region"),
    ("empty", "# region: a\n# endregion\n", "empty"),
    ("bad name", "# region: 1a\nx=1\n# endregion\n", "bad region name"),
    ("missing name", "# region:\nx=1\n# endregion\n", "bad region name"),
    ("near miss", "# region foo\nx=1\n# endregion\n", "looks like a region marker"),
    ("near miss end", "# region: a\nx=1\n# end region\n", "looks like a region marker"),
]:
    probs = region_error(src)
    check(probs is not None and any(needle in m for _, m in probs),
          f"{label} is an error mentioning {needle!r}: {probs}")

try:
    regions.region_text(GOOD, "nope")
    check(False, "region_text of a missing region raises")
except KeyError as e:
    check("a" in str(e) and "nope" in str(e), "missing region raises KeyError naming the regions that exist")

# ---- batch lint -------------------------------------------------------------------
KNOWN = {"Frame", "Scene", "Timer", "Color", "current_scene", "step", "exit"}


def rules(new, old=None, defs=None):
    return sorted({rule for _l, rule, _m in lint.lint_source(new, old, KNOWN, defs, {"current_scene"})})


check(rules("import mcrfpy\ns = mcrfpy.Scene('x')\nmcrfpy.current_scene = s\n") == [], "clean snippet passes")
check(rules("try:\n    pass\nexcept Exception:\n    pass\n") == ["R1"], "try/except in a new file is R1")
check(rules("import sys\nsys.exit(0)\n") == ["R2"], "sys.exit is R2")
check(rules("exit()\n") == ["R2"], "bare exit() is R2")
check(rules("import mcrfpy\nmcrfpy.exit()\n") == ["R2"], "mcrfpy.exit() is R2 (a function the manifest knows, still banned)")
check(rules("from mcrfpy import automation\n") == ["R3"], "importing automation is R3")
check(rules("import mcrfpy\nmcrfpy.automation.screenshot('x')\n") == ["R3", "R4"],
      "mcrfpy.automation use is R3 (and not in the manifest, R4)")
# exit inside a function body is handler code (allowed); at module level, in a class body, a
# decorator or a default value it runs at import (still R2)
check(rules("import sys\ndef quit_now():\n    sys.exit(0)\n") == [], "sys.exit inside a def is allowed")
check(rules("import mcrfpy\ndef f():\n    mcrfpy.exit()\n") == [], "mcrfpy.exit() inside a def is allowed")
check(rules("import sys\nclass A:\n    def m(self):\n        sys.exit(0)\n") == [], "sys.exit inside a method is allowed")
check(rules("import sys\nf = lambda: sys.exit(0)\n") == [], "sys.exit inside a lambda is allowed")
check(rules("import sys\ndef f():\n    def g():\n        exit()\n") == [], "exit inside a nested def is allowed")
check(rules("import sys\nclass A:\n    sys.exit(0)\n") == ["R2"], "sys.exit in a class body is R2")
check(rules("import sys\ndef f(x=sys.exit(0)):\n    pass\n") == ["R2"], "sys.exit in a default value is R2")
check(rules("import sys\n@sys.exit\ndef f():\n    pass\n") == ["R2"], "sys.exit as a decorator is R2")
check(rules("import sys\nif True:\n    sys.exit(0)\n") == ["R2"], "sys.exit in a module-level if is R2")
check(rules("import sys\ndef f():\n    pass\nsys.exit(0)\n") == ["R2"], "module-level exit after a def is R2")
# automation opt-in: an explicit header marker, nothing else
MARK = "# snippet: allow-automation\n"
check(rules('"""Doc."""\n' + MARK + "from mcrfpy import automation\nautomation.screenshot('x')\n") == [],
      "allow-automation after the docstring allows automation")
check(rules(MARK + "import mcrfpy\nmcrfpy.automation.screenshot('x')\n") == [],
      "allow-automation also lets mcrfpy.automation through R4")
check(rules("import mcrfpy\n" + MARK + "from mcrfpy import automation\n") == ["R3"],
      "the marker after the first statement is not a header: R3")
check(rules("from mcrfpy import automation\n" + MARK) == ["R3"], "the marker below the code is R3")
check(rules("# snippet: allow-automation please\nfrom mcrfpy import automation\n") == ["R3"],
      "a marker with extra text is not the marker")
check(rules("# snippet: allow-automation\nimport sys\nsys.exit(0)\n") == ["R2"],
      "allow-automation does not allow a module-level exit")
check(rules(MARK + "import mcrfpy\nmcrfpy.Nope()\n") == ["R4"], "allow-automation does not weaken R4 for other names")
check(rules("import mcrfpy\nmcrfpy.setTimer('a', None, 1)\n") == ["R4"], "unknown mcrfpy name is R4")
check(rules("import mcrfpy\nmcrfpy.Animation(1)\n") == ["R4"], "mcrfpy.Animation (not exported) is R4")
check(rules("from mcrfpy import Frame, Nope\n") == ["R4"], "from mcrfpy import <unknown> is R4")
check(rules("def f(:\n") == ["syntax"], "a syntax error is reported, not raised")
bad = lint.lint_source("import mcrfpy\nmcrfpy.setTimer(1)\n", None, KNOWN)
check(bad and bad[0][0] == 2, f"violations carry the line number: {bad}")

# R1-R3 only judge lines the batch added; R4 judges the whole file
OLD = "import mcrfpy\ntry:\n    pass\nexcept Exception:\n    pass\n"
check(rules(OLD + "x = 1\n", OLD) == [], "a try/except that predates the batch is not charged to it")
check(rules(OLD + "try:\n    pass\nexcept Exception:\n    pass\n", OLD) == ["R1"],
      "a try/except the batch ADDED is R1 even when the file already had one")
check(rules("import mcrfpy\nmcrfpy.nope\n", "import mcrfpy\nmcrfpy.nope\n") == ["R4"],
      "R4 covers the whole file, added or not")

# R5: defs survive a conversion
BEFORE = "def keep():\n    pass\nclass Thing:\n    def method(self):\n        pass\ndef gone():\n    pass\n"
AFTER = "def keep():\n    pass\nclass Thing:\n    def method(self):\n        pass\n"
r5 = lint.lint_source(AFTER, BEFORE, KNOWN, BEFORE)
check([m for _l, r_, m in r5 if r_ == "R5" and "'gone'" in m], f"deleting a function is R5: {r5}")
check(rules(BEFORE + "def extra():\n    pass\n", BEFORE, BEFORE) == [], "adding a function is fine")
check(rules("def other():\n    pass\n", None, "def keep():\n    pass\n") == ["R5"],
      "R5 applies to a --pair original (no same-path predecessor)")
check(rules("def x():\n    pass\nclass Thing:\n    pass\n", None, "def x(:\n    pass\nclass Thing:\n    pass\n") == [],
      "an unparseable original is compared by its def/class lines")
check(rules("# region: a\nx = 1\n") == ["R6"], "a malformed region is R6")

# ---- batch lint on real git repos ----------------------------------------------------
import contextlib
import io
import json
import shutil

MANIFEST = {"objects": {"Frame": {}, "Scene": {}, "Timer": {}, "Color": {}},
            "functions": {"exit": {}, "step": {}},
            "module_attributes": {"current_scene": {}}}
GOOD_SNIP = "import mcrfpy\nscene = mcrfpy.Scene('x')\nmcrfpy.current_scene = scene\n"
RUN_TMP = tempfile.mkdtemp()


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t.invalid",
                        *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"git {args}: {p.stderr}")
    return p.stdout


def make_repo(files):
    d = tempfile.mkdtemp(dir=RUN_TMP)
    git(d, "init", "-q")
    write_files(d, files)
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "base")
    # A case edits a file right after this commit. If the edit lands in the same
    # timestamp tick as the commit and keeps the size ("c\n" -> "d\n"), git's stat cache
    # can call it unchanged, and the linter sees no diff -- seen once under heavy CI
    # load (goblin task 2020). Backdate the committed files and refresh the index, so
    # any later write has a different mtime than the one the index recorded.
    old = time.time() - 60
    for rel in files:
        os.utime(os.path.join(d, rel), (old, old))
    git(d, "update-index", "-q", "--refresh")
    return d


def write_files(d, files):
    for rel, text in files.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(text)


MANIFEST_PATH = os.path.join(RUN_TMP, "manifest.json")
with open(MANIFEST_PATH, "w") as f:
    json.dump(MANIFEST, f)


def lint_repo(repo, rng="900-999", extra=()):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = lint.main(["--repo", repo, "--base", "HEAD", "--range", rng,
                          "--manifest", MANIFEST_PATH, *extra])
    return code, buf.getvalue()


BASE_FILES = {
    "tests/snippets/147_a.py": "# mcrf: objects=[] verified=1 status=ok\nimport mcrfpy\n\ndef f():\n    return 1\n",
    "tests/snippets/148_b.py": GOOD_SNIP,
    "tests/snippets/_harness.py": "print('h')\n",
    "tools/tool.py": "x = 1\n",
    "docs/cookbook/procgen/01_x.py": '"""demo"""\nimport mcrfpy\n\ndef keep():\n    return 1\n\ndef also():\n    return 2\n\nkeep()\n',
    "docs/cookbook/procgen/run_all.py": "def runner():\n    pass\n",
    "docs/cookbook/procgen/shot.png": "png",
    "docs/cookbook/ui/ui_x_basic.py": '"""X\n\nDocumentation: https://example.invalid/cookbook/ui_x\n"""\n\ndef foo():\n    pass\n\ndef update(dt):\n    pass\n',
    "docs/cookbook/ui/nodoc.py": "def lonely():\n    pass\n",
    "tests/snippets/700_ui_x_1.py": "import mcrfpy\n\ndef foo():\n    return 1\n",
    "CONTRIB.md": "c\n",
}


def case(label, edit, want_code, needles=(), rng="900-999", extra=(), absent=()):
    d = make_repo(BASE_FILES)
    edit(d)
    code, out = lint_repo(d, rng, extra)
    ok = code == want_code and all(n in out for n in needles) and not any(a in out for a in absent)
    check(ok, f"{label}: exit {code} (want {want_code}), needles {needles}" + ("" if ok else f"\n{out}"))
    return out


def new_snip(name, text):
    return lambda d: write_files(d, {f"tests/snippets/{name}": text})


case("clean new snippet in range passes", new_snip("900_ok.py", GOOD_SNIP), 0)
case("no changes passes", lambda d: None, 0)
case("new snippet outside --range", new_snip("901_ok.py", GOOD_SNIP), 1, ["R8", "outside --range"], rng="900-900")
case("new non-snippet file in tests/snippets", new_snip("notes.md", "x"), 1, ["R8"])
case("new file outside tests/snippets", lambda d: write_files(d, {"tools/new.py": "x=1\n"}), 1, ["R8"])


def delete_snippet(d):
    os.remove(os.path.join(d, "tests/snippets/148_b.py"))


def rename_snippet(d):
    os.rename(os.path.join(d, "tests/snippets/147_a.py"), os.path.join(d, "tests/snippets/901_a.py"))


case("deleting an existing snippet", delete_snippet, 1, ["R8", "148_b.py", "deleting"])
case("renaming 147 -> 901 (even inside the range)", rename_snippet, 1, ["R8", "147_a.py", "renamed"], rng="900-999")


def modify(text_fn):
    return lambda d: write_files(d, {"tests/snippets/147_a.py": text_fn(_read(os.path.join(d, "tests/snippets/147_a.py")))})


case("existing snippet: region markers + header are the only allowed change",
     modify(lambda s: "# mcrf: objects=[Frame] verified=2 status=ok\n" + s.split("\n", 1)[1].replace(
         "def f():\n    return 1\n", "# region: r\ndef f():\n    return 1\n# endregion\n")), 0)
case("existing snippet: code change", modify(lambda s: s.replace("return 1", "return 2")), 1, ["R16"])
case("existing snippet: added statement", modify(lambda s: s + "mcrfpy.step(1)\n"), 1, ["R16"])
case("existing snippet: added non-region comment", modify(lambda s: s + "# note\n"), 1, ["R16", "only `# region:"])
case("existing snippet: malformed region is R6", modify(lambda s: s + "# region: a\n"), 1, ["R6"])

# conversions are detected without --pair
def convert(drop):
    def edit(d):
        src = _read(os.path.join(d, "docs/cookbook/procgen/01_x.py"))
        if drop:
            src = src.replace("def also():\n    return 2\n", "")
        os.remove(os.path.join(d, "docs/cookbook/procgen/01_x.py"))
        write_files(d, {"tests/snippets/900_procgen_x.py": src})   # plain files, not git mv
    return edit


case("conversion that drops a function is caught with no --pair", convert(True), 1, ["R5", "'also'"])
case("faithful conversion passes with no --pair", convert(False), 0)


def convert_pair(d):
    src = _read(os.path.join(d, "docs/cookbook/procgen/01_x.py")).replace("def also():\n    return 2\n", "def x():\n    pass\n")
    write_files(d, {"tests/snippets/900_procgen_x.py": src})


case("--pair override judges a non-renamed new file against the original", convert_pair, 1, ["R5", "'also'"],
     extra=["--pair", "docs/cookbook/procgen/01_x.py:tests/snippets/900_procgen_x.py"])

# allowlist
case("editing the harness", lambda d: write_files(d, {"tests/snippets/_harness.py": "print('x')\n"}), 1, ["R8", "_harness.py"])
case("editing tools/", lambda d: write_files(d, {"tools/tool.py": "x = 2\n"}), 1, ["R8", "tools/tool.py"])
case("editing CONTRIBUTING-like docs", lambda d: write_files(d, {"CONTRIB.md": "d\n"}), 1, ["R8"])
case("modifying a docs/cookbook file", lambda d: write_files(d, {"docs/cookbook/procgen/01_x.py": "x\n"}), 1, ["R8"])
case("deleting an outside file", lambda d: os.remove(os.path.join(d, "tools/tool.py")), 1, ["R8"])
case("deleting a non-python cookbook file is allowed", lambda d: os.remove(os.path.join(d, "docs/cookbook/procgen/shot.png")), 0)

# deletion rule R9
def rm(path):
    return lambda d: os.remove(os.path.join(d, path))


case("deleting a stale file with no --page-snippets", rm("docs/cookbook/ui/ui_x_basic.py"), 1, ["R9", "ui_x=N"])
case("deleting a stale file whose def is not defined in the page's snippets (update)",
     rm("docs/cookbook/ui/ui_x_basic.py"), 1, ["R9", "'update'"], extra=["--page-snippets", "ui_x=700"],
     absent=["'foo'"])


def add_update_and_delete(d):
    write_files(d, {"tests/snippets/900_ui_x_2.py": GOOD_SNIP + "\ndef update(dt):\n    return dt\n"})
    os.remove(os.path.join(d, "docs/cookbook/ui/ui_x_basic.py"))


case("deleting a stale file once its defs are defined in the page's snippets", add_update_and_delete, 0,
     extra=["--page-snippets", "ui_x=700,900"])
case("a name that is only CALLED in the snippets does not count",
     lambda d: (write_files(d, {"tests/snippets/900_ui_x_2.py": GOOD_SNIP + "\nupdate(0.1)\n"}),
                os.remove(os.path.join(d, "docs/cookbook/ui/ui_x_basic.py"))),
     1, ["R9", "'update'"], extra=["--page-snippets", "ui_x=700,900"])
case("deleting a stale file with no Documentation header", rm("docs/cookbook/ui/nodoc.py"), 1, ["R9", "no Documentation"])
case("--page-snippets naming a missing snippet", rm("docs/cookbook/ui/ui_x_basic.py"), 1, ["R9", "no snippet numbered 123"],
     extra=["--page-snippets", "ui_x=123"])

# bans (R1-R3, R7, R10-R15)
BANS = [
    ("try", "import mcrfpy\ntry:\n    pass\nexcept Exception:\n    pass\n", "R1"),
    ("sys.exit", "import sys\nsys.exit(0)\n", "R2"),
    ("bare exit()", "exit()\n", "R2"),
    ("quit", "quit()\n", "R2"),
    ("mcrfpy.exit()", "import mcrfpy\nmcrfpy.exit()\n", "R2"),
    ("exit as a value", "import sys\nq = sys.exit\n", "R2"),
    ("builtins.exit", "import builtins\nbuiltins.exit()\n", "R2"),
    ("os._exit", "import os\nos._exit(1)\n", "R2"),
    ("automation import", "from mcrfpy import automation\n", "R3"),
    ("import mcrfpy as X", "import mcrfpy as m\nm.Frame()\n", "R7"),
    ("from mcrfpy import a as b", "from mcrfpy import Frame as F\n", "R7"),
    ("from mcrfpy import *", "from mcrfpy import *\n", "R7"),
    ("m = mcrfpy", "import mcrfpy\nm = mcrfpy\n", "R7"),
    ("getattr(mcrfpy)", "import mcrfpy\ngetattr(mcrfpy, 'setTimer')\n", "R7"),
    ("setattr(mcrfpy)", "import mcrfpy\nsetattr(mcrfpy, 'Frame', 1)\n", "R7"),
    ("vars(mcrfpy)", "import mcrfpy\nvars(mcrfpy)\n", "R7"),
    ("getattr(sys)", "import sys\ngetattr(sys, 'exit')\n", "R7"),
    ("assign mcrfpy.Frame", "import mcrfpy\nmcrfpy.Frame = 1\n", "R7"),
    ("del mcrfpy.Frame", "import mcrfpy\ndel mcrfpy.Frame\n", "R7"),
    ("import sys as s", "import sys as s\n", "R7"),
    ("from sys import exit", "from sys import exit\n", "R7"),
    ("from os import _exit", "from os import _exit\n", "R7"),
    ("eval", "eval('1')\n", "R7"),
    ("__import__", "__import__('sys')\n", "R7"),
    ("contextlib.suppress", "import contextlib\nwith contextlib.suppress(Exception):\n    pass\n", "R10"),
    ("from contextlib import suppress", "from contextlib import suppress\n", "R10"),
    ("raise SystemExit", "raise SystemExit\n", "R11"),
    ("SystemExit reference", "e = SystemExit\n", "R11"),
    ("except SystemExit", "try:\n    pass\nexcept SystemExit:\n    pass\n", "R11"),
    ("atexit", "import atexit\n", "R12"),
    ("if False", "if False:\n    x = 1\n", "R13"),
    ("if 0", "if 0:\n    x = 1\n", "R13"),
    ("while False", "while False:\n    x = 1\n", "R13"),
    ("if not True", "if not True:\n    x = 1\n", "R13"),
    ("open()", "f = open('x')\n", "R14"),
    ("Path.read_text", "p.read_text()\n", "R14"),
    ("import socket", "import socket\n", "R14"),
    ("from urllib import request", "from urllib import request\n", "R14"),
    ("import subprocess", "import subprocess\n", "R14"),
    ("SNIPPET_OK in a string", "print('SNIPPET_OK')\n", "R15"),
    ("SHOT_OK in a comment", "# SHOT_OK\nx = 1\n", "R15"),
    ("unknown mcrfpy name (R4)", "import mcrfpy\nmcrfpy.setTimer(1)\n", "R4"),
    ("syntax error", "def f(:\n", "syntax"),
]
for label, text, rule in BANS:
    got = {r for _l, r, _m in lint.lint_source(text, None, KNOWN | {"Frame"}, None, {"current_scene"})}
    check(rule in got, f"ban {label}: {rule} in {sorted(got)}")

ALLOWED = [
    ("assigning a module attribute", "import mcrfpy\nscene = mcrfpy.Scene('x')\nmcrfpy.current_scene = scene\n"),
    ("a plain from-import of a manifest name", "from mcrfpy import Frame\nFrame()\n"),
    ("getattr on a non-watched object", "class A:\n    x = 1\ngetattr(A, 'x')\n"),
    ("a function named exit_game", "def exit_game():\n    return 1\nexit_game()\n"),
    ("if True", "if True:\n    x = 1\n"),
]
for label, text in ALLOWED:
    got = lint.lint_source(text, None, KNOWN | {"Frame"}, None, {"current_scene"})
    check(got == [], f"allowed: {label}: {got}")

# the bans apply through the repo path too, with file:line output
out = case("a banned construct in a new snippet is reported file:line and exits 1",
           new_snip("900_bad.py", "import mcrfpy\ntry:\n    mcrfpy.setTimer(1)\nexcept Exception:\n    pass\n"),
           1, ["tests/snippets/900_bad.py:2: R1", "tests/snippets/900_bad.py:3: R4"])

# warnings do not fail
out = case("an empty-bodied def is a warning, not a failure",
           new_snip("900_stub.py", GOOD_SNIP + "\ndef todo():\n    pass\n\ndef doc():\n    '''x'''\n\ndef dots():\n    ...\n"),
           0, ["warning: todo() has an empty body", "warning: doc()", "warning: dots()"])

# bad invocations
for label, argv in [("no --base", ["--range", "1-2"]), ("no --range", ["--base", "HEAD"]),
                    ("reversed --range", ["--base", "HEAD", "--range", "5-1"]),
                    ("garbage --range", ["--base", "HEAD", "--range", "x"]),
                    ("bad --page-snippets", ["--base", "HEAD", "--range", "1-2", "--page-snippets", "nope"])]:
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            lint.main(["--repo", make_repo(BASE_FILES), "--manifest", MANIFEST_PATH, *argv])
        check(False, f"{label} is refused")
    except SystemExit as e:
        check(bool(e.code), f"{label} is refused")
try:
    with contextlib.redirect_stderr(io.StringIO()):
        lint.main(["--repo", make_repo(BASE_FILES), "--manifest", MANIFEST_PATH, "--base", "nope", "--range", "1-2"])
    check(False, "an unknown --base is refused")
except SystemExit as e:
    check(bool(e.code), "an unknown --base is refused")

shutil.rmtree(RUN_TMP, ignore_errors=True)

# ---- stamp_snippets --only ----------------------------------------------------------
allp = stamp.snippet_paths()
check(len(allp) > 100, "stamp_snippets sees the corpus")
sel = stamp.select_paths(allp, ["001,076", "188"])
check([os.path.basename(p).split("_")[0] for p in sel] == ["001", "076", "188"],
      f"--only selects exactly the named numbers: {[os.path.basename(p) for p in sel]}")
check(stamp.select_paths(allp, None) == allp, "no --only means everything")
for label, spec in [("unknown number", ["999999"]), ("non-number", ["abc"]), ("empty", [","])]:
    try:
        stamp.select_paths(allp, spec)
        check(False, f"--only with {label} exits")
    except SystemExit as e:
        check(bool(e.code), f"--only with {label} exits with a message")

env = dict(os.environ)
build_dir = env.get("MCRF_BUILD_DIR") or os.path.join(ROOT, "build")
engine = os.path.join(build_dir, "mcrogueface")
check(os.path.exists(engine),
      f"no engine at {engine}: build one (make) or set MCRF_BUILD_DIR to a built engine's build directory")
if os.path.exists(engine):
    proc = subprocess.run(["python3", os.path.join(TOOLS, "stamp_snippets.py"), "--check", "--only", "001"],
                          capture_output=True, text=True, env=env)
    check(proc.returncode == 0 and "1/1 snippets ok" in proc.stdout,
          f"stamp_snippets --check --only 001 runs exactly one snippet: rc={proc.returncode} "
          f"stdout={proc.stdout!r} stderr={proc.stderr!r}")
proc = subprocess.run(["python3", os.path.join(TOOLS, "stamp_snippets.py"), "--check", "--only", "999999"],
                      capture_output=True, text=True, env=env)
check(proc.returncode != 0, "stamp_snippets --only 999999 fails")

# generate_snippet_shots: an unknown number is an error, not "0 captured, 0 failed"
shots = load("generate_snippet_shots")
for argv in (["999999"], ["001", "999999"], ["abc"]):
    proc = subprocess.run(["python3", os.path.join(TOOLS, "generate_snippet_shots.py"), *argv],
                          capture_output=True, text=True, env=env)
    check(proc.returncode != 0 and ("999999" in proc.stderr + proc.stdout or "abc" in proc.stderr + proc.stdout),
          f"generate_snippet_shots {argv} fails and names the bad number: rc={proc.returncode} "
          f"{proc.stdout!r} {proc.stderr!r}")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("PASS")
sys.exit(0)
