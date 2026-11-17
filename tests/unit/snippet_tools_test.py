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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)


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
    return sorted({rule for _l, rule, _m in lint.lint_source(new, old, KNOWN, defs)})


check(rules("import mcrfpy\ns = mcrfpy.Scene('x')\nmcrfpy.current_scene = s\n") == [], "clean snippet passes")
check(rules("try:\n    pass\nexcept Exception:\n    pass\n") == ["R1"], "try/except in a new file is R1")
check(rules("import sys\nsys.exit(0)\n") == ["R2"], "sys.exit is R2")
check(rules("exit()\n") == ["R2"], "bare exit() is R2")
check(rules("import mcrfpy\nmcrfpy.exit()\n") == ["R2"], "mcrfpy.exit() is R2 (a function the manifest knows, still banned)")
check(rules("from mcrfpy import automation\n") == ["R3"], "importing automation is R3")
check(rules("import mcrfpy\nmcrfpy.automation.screenshot('x')\n") == ["R3", "R4"],
      "mcrfpy.automation use is R3 (and not in the manifest, R4)")
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

# ---- the CLI exits non-zero with file:line ----------------------------------------
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "bad_snippet.py")
    with open(p, "w") as f:
        f.write("import mcrfpy\ntry:\n    mcrfpy.setTimer(1)\nexcept Exception:\n    pass\n")
    proc = subprocess.run(["python3",
                           os.path.join(TOOLS, "lint_snippet_batch.py"), "--base", "HEAD", p],
                          capture_output=True, text=True)
    check(proc.returncode == 1, f"CLI exits 1 on violations (got {proc.returncode})")
    check(":2: R1" in proc.stdout and ":3: R4" in proc.stdout,
          f"CLI prints file:line for each violation: {proc.stdout!r}")
    q = os.path.join(d, "good_snippet.py")
    with open(q, "w") as f:
        f.write("import mcrfpy\ns = mcrfpy.Scene('x')\nmcrfpy.current_scene = s\n")
    proc = subprocess.run(["python3", os.path.join(TOOLS, "lint_snippet_batch.py"),
                           "--base", "HEAD", q], capture_output=True, text=True)
    check(proc.returncode == 0, f"CLI exits 0 on a clean snippet: {proc.stdout!r} {proc.stderr!r}")
    proc = subprocess.run(["python3", os.path.join(TOOLS, "lint_snippet_batch.py"), q],
                          capture_output=True, text=True)
    check(proc.returncode != 0, "CLI refuses to run without --base")

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
proc = subprocess.run(["python3", os.path.join(TOOLS, "stamp_snippets.py"), "--check", "--only", "001"],
                      capture_output=True, text=True, env=env)
check(proc.returncode == 0 and "1/1 snippets ok" in proc.stdout,
      f"stamp_snippets --check --only 001 runs exactly one snippet: {proc.stdout!r}")
proc = subprocess.run(["python3", os.path.join(TOOLS, "stamp_snippets.py"), "--check", "--only", "999999"],
                      capture_output=True, text=True, env=env)
check(proc.returncode != 0, "stamp_snippets --only 999999 fails")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("PASS")
sys.exit(0)
