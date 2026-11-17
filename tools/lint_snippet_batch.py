#!/usr/bin/env python3
"""
lint_snippet_batch.py -- agent-independent checks on a batch of new/changed snippets (#541).

The snippet gate (stamp_snippets.py / _harness.py) proves a snippet RUNS and leaves a
populated scene. It cannot see the ways a snippet gets made to pass dishonestly:

  * wrapped in try/except so a failing call is swallowed
  * ended with exit()/sys.exit(), which a published, copy-pasteable sample must not do
  * driven by `automation.` (a test API, not something a reader's game calls)
  * calling an mcrfpy name that does not exist (the harness only notices if that line runs)
  * a CONVERSION of an older file that quietly drops a function or class to make it run

This tool checks those, for exactly the snippets a batch touched, and does not depend on
who (or what) produced the batch. It exits non-zero with file:line for every violation.

    python3 tools/lint_snippet_batch.py --base <ref> [FILE ...]
    python3 tools/lint_snippet_batch.py --base <ref> --pair OLD:NEW [--pair ...]

--base REF   the commit the batch started from. REQUIRED (no guessing what "changed" means).
FILE ...     snippets to check. With none, every tests/snippets/*.py added or modified
             relative to REF (committed, staged, unstaged or untracked) is checked.
--pair O:N   NEW is a conversion of OLD (a different path, e.g. a docs/cookbook demo that
             became a snippet): OLD is read from REF, and every function/class name in OLD
             must still be defined in NEW.
--manifest   api/manifest.json by default.

Rules, per snippet:
  R1 try/except     no `try` statement on a line the batch added
  R2 exit           no exit()/quit()/sys.exit()/os._exit()/mcrfpy.exit() on an added line
  R3 automation     no `automation` import or attribute on an added line
  R4 manifest       every `mcrfpy.X` (and `from mcrfpy import X`) names something in the
                    manifest's objects / functions / module_attributes -- whole file
  R5 defs           for a modified file or a --pair: every def/class name in the BEFORE
                    source is still defined in the AFTER source (renames count as deletion)
  R6 regions        `# region:` markers are well formed (tools/snippet_regions.py)

For a NEW file every line is "added", so R1-R3 cover the whole file.
"""

import argparse
import ast
import difflib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snippet_regions  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNIPPET_REL = "tests/snippets"
EXIT_NAMES = {"exit", "quit"}


def load_known_names(manifest_path):
    with open(manifest_path, encoding="utf-8") as f:
        m = json.load(f)
    known = set(m.get("objects", {})) | set(m.get("functions", {})) | \
        set(m.get("module_attributes", {}))
    if not known:
        sys.exit(f"{manifest_path} lists no objects/functions/attributes")
    return known


def added_lines(old, new):
    """1-based line numbers of `new` that are not matched by a line of `old`."""
    if old is None:
        return set(range(1, len(new.splitlines()) + 1))
    a, b = old.splitlines(), new.splitlines()
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    added = set()
    for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "insert"):
            added.update(range(j1 + 1, j2 + 1))
    return added


def defined_names(tree):
    return {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def _is_exit_call(node):
    f = node.func
    if isinstance(f, ast.Name) and f.id in EXIT_NAMES:
        return True
    if isinstance(f, ast.Attribute) and f.attr in ("exit", "_exit"):
        v = f.value
        return isinstance(v, ast.Name) and v.id in ("sys", "os", "mcrfpy")
    return False


def _mentions_automation(node):
    if isinstance(node, ast.Attribute):
        if node.attr == "automation":
            return True
        return isinstance(node.value, ast.Name) and node.value.id == "automation"
    if isinstance(node, ast.Name):
        return node.id == "automation"
    if isinstance(node, ast.ImportFrom):
        return (node.module or "").split(".")[-1] == "automation" or \
            any(a.name == "automation" for a in node.names)
    if isinstance(node, ast.Import):
        return any(a.name.split(".")[-1] == "automation" for a in node.names)
    return False


def lint_source(new, old=None, known=frozenset(), before_defs_src=None):
    """Return a sorted list of (line, rule, message) for one snippet.

    new             the snippet source being checked
    old             the previous version of the SAME file (None: a new file)
    known           mcrfpy names from the manifest
    before_defs_src source whose def/class names must survive (old, or a --pair's OLD)
    """
    out = []
    try:
        tree = ast.parse(new)
    except SyntaxError as e:
        return [(e.lineno or 1, "syntax", f"does not parse: {e.msg}")]
    added = added_lines(old, new)

    for node in ast.walk(tree):
        line = getattr(node, "lineno", None)
        if line is None:
            continue
        if line in added:
            if isinstance(node, ast.Try) or type(node).__name__ == "TryStar":
                out.append((line, "R1", "try/except is not allowed: a snippet must fail loudly"))
            if isinstance(node, ast.Call) and _is_exit_call(node):
                out.append((line, "R2", "exit()/sys.exit() is not allowed in a snippet"))
            if _mentions_automation(node):
                out.append((line, "R3", "automation is a test API; a reader's game does not call it"))
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                and node.value.id == "mcrfpy" and node.attr not in known:
            out.append((line, "R4", f"mcrfpy.{node.attr} is not in api/manifest.json"))
        if isinstance(node, ast.ImportFrom) and node.module == "mcrfpy":
            for a in node.names:
                if a.name != "automation" and a.name not in known:
                    out.append((line, "R4", f"from mcrfpy import {a.name}: not in api/manifest.json"))

    if before_defs_src is not None:
        try:
            before = defined_names(ast.parse(before_defs_src))
        except SyntaxError:
            # An unparseable original (several stale extractions are) has no reliable
            # def list; fall back to scanning its text for `def NAME` / `class NAME`.
            import re
            before = set(re.findall(r"^\s*(?:async\s+)?(?:def|class)\s+(\w+)",
                                    before_defs_src, re.M))
        missing = sorted(before - defined_names(tree))
        for name in missing:
            out.append((1, "R5", f"{name!r} is defined in the original but not here "
                                 f"(a conversion must not delete functions or classes)"))

    try:
        snippet_regions.parse(new)
    except snippet_regions.RegionError as e:
        out.extend((n, "R6", msg) for n, msg in e.problems)

    return sorted(set(out))


# --- git access ---------------------------------------------------------------------
def _git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)


def show_at(ref, relpath):
    """Contents of `relpath` at `ref`, or None if the path does not exist there."""
    p = _git("show", f"{ref}:{relpath}")
    return p.stdout if p.returncode == 0 else None


def changed_snippets(ref):
    """tests/snippets/*.py added or modified since `ref` (including untracked)."""
    if _git("rev-parse", "--verify", f"{ref}^{{commit}}").returncode != 0:
        sys.exit(f"--base {ref!r} is not a commit")
    names = set()
    d = _git("diff", "--name-only", "--diff-filter=AM", ref, "--", SNIPPET_REL)
    names.update(d.stdout.split())
    u = _git("ls-files", "--others", "--exclude-standard", "--", SNIPPET_REL)
    names.update(u.stdout.split())
    return sorted(n for n in names
                  if n.endswith(".py") and not os.path.basename(n).startswith("_"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint a batch of new/changed snippets.")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--base", required=True, help="commit the batch started from")
    ap.add_argument("--pair", action="append", default=[], metavar="OLD:NEW")
    ap.add_argument("--manifest", default=os.path.join(ROOT, "api", "manifest.json"))
    args = ap.parse_args(argv)

    known = load_known_names(args.manifest)
    pairs = {}
    for spec in args.pair:
        if ":" not in spec:
            sys.exit(f"--pair {spec!r}: want OLD:NEW")
        old, new = spec.split(":", 1)
        pairs[os.path.normpath(new)] = os.path.normpath(old)

    targets = [os.path.normpath(os.path.relpath(os.path.abspath(f), ROOT)) for f in args.files] \
        if args.files else changed_snippets(args.base)
    for new in pairs:
        if new not in targets:
            targets.append(new)
    if not targets:
        print("lint_snippet_batch: no snippets changed since", args.base)
        return 0

    bad = 0
    for rel in sorted(targets):
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print(f"{rel}:1: file does not exist")
            bad += 1
            continue
        with open(path, encoding="utf-8") as f:
            new = f.read()
        old_same = show_at(args.base, rel)
        defs_src = old_same
        if rel in pairs:
            defs_src = show_at(args.base, pairs[rel])
            if defs_src is None:
                print(f"{rel}:1: --pair original {pairs[rel]} does not exist at {args.base}")
                bad += 1
                continue
        problems = lint_source(new, old_same, known, defs_src)
        for line, rule, msg in problems:
            print(f"{rel}:{line}: {rule}: {msg}")
        bad += bool(problems)

    print(f"lint_snippet_batch: {len(targets)} snippet(s), "
          f"{bad} with violations")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
