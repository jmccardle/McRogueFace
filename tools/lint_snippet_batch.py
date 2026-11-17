#!/usr/bin/env python3
"""
lint_snippet_batch.py -- agent-independent checks on a batch of snippet work (#541).

The snippet gate (stamp_snippets.py / _harness.py) proves a snippet RUNS and leaves a
populated scene. It cannot see the ways work gets made to pass dishonestly, or the ways a
batch strays outside what it was asked to do. This tool judges the whole batch -- everything
that differs from the commit it started at -- and does not care who produced it.

    python3 tools/lint_snippet_batch.py --base REF --range A-B [options]

--base REF         the commit the batch started from (required)
--range A-B        the snippet numbers this batch may CREATE (required)
--page-snippets P=N,N,...
                   the snippet numbers that belong to cookbook page P (the page stem in a
                   stale file's `Documentation:` header); repeatable. Needed only when the
                   batch deletes stale docs/cookbook .py files (rule R9)
--pair OLD:NEW     force NEW to be judged as a conversion of OLD (conversions are normally
                   detected from `git diff -M`; this is only an override)
--repo DIR         the checkout to judge (default: the checkout this script is in)
--manifest FILE    api/manifest.json by default

WHAT A BATCH MAY CHANGE (anything else is a violation, R8)
  * new tests/snippets/NNN_*.py with NNN inside --range
  * existing tests/snippets/*.py: region marker comments and the `# mcrf:` header only (R16)
  * deletions of docs/cookbook files, and renames out of docs/cookbook into a new snippet
    (a conversion; every def/class of the original must survive, R5). A deleted stale .py
    must have all its defs/classes DEFINED in its page's snippets (R9).
  Not allowed: deleting or renaming any snippet, editing _harness.py, _screenshot.py, tools/,
  src/, api/, tools/generate_snippet_shots.py, tests outside tests/snippets/, ...

RULES, on lines the batch added (every line, for a new file):
  R1  try/except
  R2  exit()/quit()/sys.exit()/os._exit()/mcrfpy.exit()/builtins.exit, even as a bare reference
  R3  `automation`
  R7  hiding names from the manifest check: `import mcrfpy as X`, `from mcrfpy import a as b`,
      `from mcrfpy import *`, `m = mcrfpy`, getattr/setattr/delattr/vars on mcrfpy, sys, os or
      builtins, assigning to or deleting an mcrfpy name that is not a module attribute,
      aliasing sys/os/builtins, `from sys|os|builtins import ...`, eval/exec/__import__/compile
  R10 contextlib.suppress
  R11 SystemExit (raise it, catch it, name it)
  R12 atexit
  R13 dead code: `if False:`, `if 0:`, `while False:` and friends
  R14 file or network access: open(), Path-style read/write, socket/urllib/http/subprocess...
  R15 the harness's own marker strings (SNIPPET_OK, SHOT_OK, ...), even in a comment
Whole file:
  R4  every `mcrfpy.X` / `from mcrfpy import X` is in the manifest
  R5  conversions: every def/class of the original is still defined
  R6  `# region:` markers well formed
Warnings (printed, do not fail): a def whose body is only pass / ... / a docstring.

Exits non-zero, with file:line, on any violation.
"""

import argparse
import ast
import difflib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snippet_regions  # noqa: E402

DEFAULT_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNIPPET_REL = "tests/snippets"
COOKBOOK_REL = "docs/cookbook/"
SNIPPET_RE = re.compile(r"^tests/snippets/(\d+)_[^/]*\.py$")
HEADER_RE = re.compile(r"^\s*#\s*mcrf:")
DOC_PAGE_RE = re.compile(r"/cookbook/(\w+)")
EXIT_NAMES = {"exit", "quit"}
WATCHED_MODULES = {"mcrfpy", "sys", "os", "builtins"}
HARNESS_STRINGS = ("SNIPPET_OK", "SNIPPET_FAIL", "SHOT_OK", "SHOT_FAIL")
IO_MODULES = {"socket", "ssl", "urllib", "http", "requests", "ftplib", "smtplib",
              "subprocess", "shutil", "pathlib", "tempfile", "glob", "asyncio"}
IO_METHODS = {"open", "read_text", "write_text", "read_bytes", "write_bytes", "urlopen"}
DYNAMIC_CALLS = {"eval", "exec", "__import__", "compile"}


# --- manifest ---------------------------------------------------------------------------
def load_manifest(path):
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    attrs = set(m.get("module_attributes", {}))
    known = set(m.get("objects", {})) | set(m.get("functions", {})) | attrs
    if not known:
        sys.exit(f"{path} lists no objects/functions/attributes")
    return known, attrs


# --- small helpers ----------------------------------------------------------------------
def added_lines(old, new):
    """1-based line numbers of `new` that are not matched by a line of `old`."""
    if old is None:
        return set(range(1, len(new.splitlines()) + 1))
    sm = difflib.SequenceMatcher(None, old.splitlines(), new.splitlines(), autojunk=False)
    added = set()
    for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "insert"):
            added.update(range(j1 + 1, j2 + 1))
    return added


def defined_names(source):
    """def/class names in `source`; an unparseable original (several stale extractions are)
    is scanned by its `def NAME` / `class NAME` lines instead."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set(re.findall(r"^\s*(?:async\s+)?(?:def|class)\s+(\w+)", source, re.M))
    return {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def _name_of(node):
    return node.id if isinstance(node, ast.Name) else None


def _is_exit_reference(node):
    if isinstance(node, ast.Name):
        return node.id in EXIT_NAMES and isinstance(node.ctx, ast.Load)
    if isinstance(node, ast.Attribute) and node.attr in ("exit", "_exit", "quit"):
        return _name_of(node.value) in ("sys", "os", "mcrfpy", "builtins")
    return False


def _mentions_automation(node):
    if isinstance(node, ast.Attribute):
        return node.attr == "automation" or _name_of(node.value) == "automation"
    if isinstance(node, ast.Name):
        return node.id == "automation"
    if isinstance(node, ast.ImportFrom):
        return (node.module or "").split(".")[-1] == "automation" or \
            any(a.name == "automation" for a in node.names)
    if isinstance(node, ast.Import):
        return any(a.name.split(".")[-1] == "automation" for a in node.names)
    return False


def _falsy_constant(test):
    if isinstance(test, ast.Constant):
        return not test.value
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not) \
            and isinstance(test.operand, ast.Constant):
        return bool(test.operand.value)
    return False


def _targets(node):
    if isinstance(node, ast.Assign):
        return list(node.targets)
    if isinstance(node, (ast.AugAssign, ast.AnnAssign)):
        return [node.target]
    if isinstance(node, ast.Delete):
        return list(node.targets)
    return []


def _flatten(target):
    if isinstance(target, (ast.Tuple, ast.List)):
        for t in target.elts:
            yield from _flatten(t)
    else:
        yield target


def _is_stub(fn):
    for stmt in fn.body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) \
                and (stmt.value.value is Ellipsis or isinstance(stmt.value.value, str)):
            continue
        return False
    return True


# --- per-file judgement -------------------------------------------------------------------
def lint_source(new, old=None, known=frozenset(), before_defs_src=None,
                settable=frozenset(), warnings=None):
    """Return a sorted list of (line, rule, message) for one NEW or converted snippet.

    new             the snippet source being checked
    old             the previous version of the SAME file (None: a new file)
    known           mcrfpy names from the manifest
    before_defs_src source whose def/class names must survive (a conversion's original)
    settable        manifest module_attributes (the only mcrfpy names that may be assigned)
    warnings        list that receives (line, message) warnings
    """
    out = []
    try:
        tree = ast.parse(new)
    except SyntaxError as e:
        return [(e.lineno or 1, "syntax", f"does not parse: {e.msg}")]
    added = added_lines(old, new)
    lines = new.splitlines()

    for i, text in enumerate(lines, start=1):
        if i in added:
            for s in HARNESS_STRINGS:
                if s in text:
                    out.append((i, "R15", f"{s} is the harness's own marker; a snippet must not print or contain it"))

    for node in ast.walk(tree):
        line = getattr(node, "lineno", None)
        if line is None:
            continue

        # whole-file rule R4
        if isinstance(node, ast.Attribute) and _name_of(node.value) == "mcrfpy" \
                and node.attr not in known:
            out.append((line, "R4", f"mcrfpy.{node.attr} is not in api/manifest.json"))
        if isinstance(node, ast.ImportFrom) and node.module == "mcrfpy":
            for a in node.names:
                if a.name not in ("automation", "*") and a.name not in known:
                    out.append((line, "R4", f"from mcrfpy import {a.name}: not in api/manifest.json"))

        if line not in added:
            continue

        if isinstance(node, ast.Try) or type(node).__name__ == "TryStar":
            out.append((line, "R1", "try/except is not allowed: a snippet must fail loudly"))
        if _is_exit_reference(node):
            out.append((line, "R2", "exit/quit/sys.exit is not allowed in a snippet"))
        if _mentions_automation(node):
            out.append((line, "R3", "automation is a test API; a reader's game does not call it"))

        # R7: hiding or rewriting names
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname and a.name.split(".")[0] in WATCHED_MODULES:
                    out.append((line, "R7", f"`import {a.name} as {a.asname}` hides names from the manifest check"))
        if isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod == "mcrfpy":
                for a in node.names:
                    if a.asname or a.name == "*":
                        out.append((line, "R7", "`from mcrfpy import` may not alias or use *"))
            elif mod in ("sys", "os", "builtins"):
                out.append((line, "R7", f"`from {mod} import ...` is not allowed (it reaches exit)"))
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and \
                _name_of(getattr(node, "value", None)) in WATCHED_MODULES:
            out.append((line, "R7", "aliasing mcrfpy/sys/os/builtins by assignment is not allowed"))
        if isinstance(node, ast.Call):
            fname = _name_of(node.func)
            if fname in ("getattr", "setattr", "delattr", "vars") and node.args and \
                    _name_of(node.args[0]) in WATCHED_MODULES:
                out.append((line, "R7", f"{fname}() on {_name_of(node.args[0])} hides names from the manifest check"))
            if fname in DYNAMIC_CALLS:
                out.append((line, "R7", f"{fname}() is not allowed"))
        for tgt in _targets(node):
            for t in _flatten(tgt):
                if isinstance(t, ast.Attribute) and _name_of(t.value) == "mcrfpy" \
                        and t.attr not in settable:
                    out.append((line, "R7", f"assigning/deleting mcrfpy.{t.attr}: only module attributes "
                                            f"({', '.join(sorted(settable)) or 'none'}) may be set"))

        # R10 / R11 / R12
        if (isinstance(node, ast.Name) and node.id == "suppress") or \
                (isinstance(node, ast.Attribute) and node.attr == "suppress") or \
                (isinstance(node, ast.ImportFrom) and any(a.name == "suppress" for a in node.names)):
            out.append((line, "R10", "contextlib.suppress swallows errors"))
        if (isinstance(node, ast.Name) and node.id == "SystemExit") or \
                (isinstance(node, ast.Attribute) and node.attr == "SystemExit") or \
                (isinstance(node, ast.ImportFrom) and any(a.name == "SystemExit" for a in node.names)):
            out.append((line, "R11", "SystemExit is not allowed in a snippet"))
        if (isinstance(node, ast.Name) and node.id == "atexit") or \
                (isinstance(node, ast.Import) and any(a.name.split(".")[0] == "atexit" for a in node.names)) or \
                (isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "atexit"):
            out.append((line, "R12", "atexit is not allowed in a snippet"))

        # R13 dead code
        if isinstance(node, (ast.If, ast.While)) and _falsy_constant(node.test):
            out.append((line, "R13", "a block that can never run hides code from the gate"))

        # R14 file / network
        if isinstance(node, ast.Call):
            if _name_of(node.func) == "open" or \
                    (isinstance(node.func, ast.Attribute) and node.func.attr in IO_METHODS):
                out.append((line, "R14", "file/network access is not allowed in a snippet"))
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in IO_MODULES:
                    out.append((line, "R14", f"import {a.name}: file/network modules are not allowed"))
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in IO_MODULES:
            out.append((line, "R14", f"from {node.module} import ...: file/network modules are not allowed"))

        if warnings is not None and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and _is_stub(node):
            warnings.append((line, f"{node.name}() has an empty body (pass / ... / docstring only)"))

    if before_defs_src is not None:
        missing = sorted(defined_names(before_defs_src) -
                         {n.name for n in ast.walk(tree)
                          if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))})
        for name in missing:
            out.append((1, "R5", f"{name!r} is defined in the original but not here "
                                 f"(a conversion must not delete functions or classes)"))

    try:
        snippet_regions.parse(new)
    except snippet_regions.RegionError as e:
        out.extend((n, "R6", msg) for n, msg in e.problems)

    return sorted(set(out))


def _significant_tokens(src):
    toks = tokenize.generate_tokens(io.StringIO(src).readline)
    return [(t.type, t.string) for t in toks
            if t.type not in (tokenize.COMMENT, tokenize.NL)]


def check_modified(old, new):
    """An existing snippet may change only by region marker comments and its `# mcrf:` header.

    Returns a sorted list of (line, rule, message)."""
    out = []
    a, b = old.splitlines(), new.splitlines()
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        for k, text in enumerate(a[i1:i2]):
            if not (snippet_regions.is_marker(text) or HEADER_RE.match(text)):
                out.append((j1 + 1, "R16", f"existing snippet: removed line {i1 + k + 1} is not a "
                                           f"region marker or the mcrf header: {text.strip()[:50]!r}"))
        for k, text in enumerate(b[j1:j2]):
            if not (snippet_regions.is_marker(text) or HEADER_RE.match(text)):
                out.append((j1 + k + 1, "R16", "existing snippet: only `# region:` / `# endregion` "
                                               f"comments may be added, not {text.strip()[:50]!r}"))
    try:
        if ast.dump(ast.parse(old)) != ast.dump(ast.parse(new)):
            out.append((1, "R16", "existing snippet: the code (AST) changed"))
        if _significant_tokens(old) != _significant_tokens(new):
            out.append((1, "R16", "existing snippet: the non-comment token stream changed"))
    except (SyntaxError, tokenize.TokenError) as e:
        out.append((1, "R16", f"existing snippet does not parse: {e}"))
    try:
        snippet_regions.parse(new)
    except snippet_regions.RegionError as e:
        out.extend((n, "R6", msg) for n, msg in e.problems)
    return sorted(set(out))


# --- git access ---------------------------------------------------------------------------
class Repo:
    def __init__(self, root):
        self.root = os.path.abspath(root)

    def git(self, *args, env=None, check=False):
        p = subprocess.run(["git", "-C", self.root, *args], capture_output=True, text=True, env=env)
        if check and p.returncode != 0:
            sys.exit(f"git {' '.join(args)} failed: {p.stderr.strip()}")
        return p

    def show(self, ref, rel):
        p = self.git("show", f"{ref}:{rel}")
        return p.stdout if p.returncode == 0 else None

    def changes(self, base):
        """[(status, old, new)] for the working tree (tracked, staged and untracked, not
        ignored) against `base`, with renames detected. Uses a throwaway index so the
        repository is not touched."""
        if self.git("rev-parse", "--verify", f"{base}^{{commit}}").returncode != 0:
            sys.exit(f"--base {base!r} is not a commit")
        idx = self.git("rev-parse", "--git-path", "index", check=True).stdout.strip()
        idx = idx if os.path.isabs(idx) else os.path.join(self.root, idx)
        with tempfile.TemporaryDirectory() as d:
            tmp = os.path.join(d, "index")
            if os.path.exists(idx):
                shutil.copy(idx, tmp)
            env = dict(os.environ, GIT_INDEX_FILE=tmp)
            self.git("add", "-A", env=env, check=True)
            p = self.git("diff", "--cached", "-M30%", "--name-status", "-z", base, env=env, check=True)
        parts = p.stdout.split("\0")
        out, i = [], 0
        while i < len(parts) and parts[i]:
            st = parts[i]
            if st[0] in "RC":
                out.append((st[0], parts[i + 1], parts[i + 2]))
                i += 3
            else:
                out.append((st[0], parts[i + 1], parts[i + 1]))
                i += 2
        return out

    def read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return f.read()

    def snippet_files(self, number):
        d = os.path.join(self.root, SNIPPET_REL)
        return sorted(os.path.join(SNIPPET_REL, n) for n in os.listdir(d)
                      if SNIPPET_RE.match(f"{SNIPPET_REL}/{n}") and int(n.split("_")[0]) == number)


def parse_range(text):
    m = re.fullmatch(r"(\d+)-(\d+)", text)
    if not m or int(m.group(1)) > int(m.group(2)):
        sys.exit(f"--range {text!r}: want A-B with A <= B")
    return int(m.group(1)), int(m.group(2))


def parse_page_snippets(specs):
    out = {}
    for spec in specs:
        if "=" not in spec:
            sys.exit(f"--page-snippets {spec!r}: want PAGE=N,N,...")
        page, nums = spec.split("=", 1)
        try:
            out[page] = [int(n) for n in nums.split(",") if n.strip()]
        except ValueError:
            sys.exit(f"--page-snippets {spec!r}: snippet numbers must be integers")
        if not out[page]:
            sys.exit(f"--page-snippets {spec!r}: no numbers")
    return out


# --- the batch ------------------------------------------------------------------------------
def judge(repo, base, rng, known, settable, pairs=None, page_map=None):
    """Judge every change of `repo` against `base`. Returns (problems, warnings, files) where
    problems/warnings are lists of (path, line, rule, message) and files counts snippets
    examined."""
    pairs = dict(pairs or {})
    page_map = page_map or {}
    problems, warnings = [], []
    lo, hi = rng
    entries = repo.changes(base)
    converted_old = set(pairs.values())
    examined = 0

    def add(path, line, rule, msg):
        problems.append((path, line, rule, msg))

    def judge_new(path, defs_src):
        nonlocal examined
        examined += 1
        warn = []
        for line, rule, msg in lint_source(repo.read(path), None, known, defs_src, settable, warn):
            add(path, line, rule, msg)
        warnings.extend((path, ln, "warning", m) for ln, m in warn)

    for status, old, new in entries:
        sm = SNIPPET_RE.match(new)
        if status == "A":
            if not sm:
                add(new, 1, "R8", "outside the allowlist: a batch adds only tests/snippets/NNN_*.py")
            elif not lo <= int(sm.group(1)) <= hi:
                add(new, 1, "R8", f"snippet number {int(sm.group(1))} is outside --range {lo}-{hi}")
            else:
                judge_new(new, repo.show(base, pairs[new]) if new in pairs else None)
        elif status == "M":
            if not sm:
                add(new, 1, "R8", "outside the allowlist: this file may not be modified")
            else:
                examined += 1
                for line, rule, msg in check_modified(repo.show(base, new) or "", repo.read(new)):
                    add(new, line, rule, msg)
        elif status == "D":
            if SNIPPET_RE.match(old):
                add(old, 1, "R8", "deleting an existing snippet is not allowed")
            elif old.startswith(COOKBOOK_REL):
                if old.endswith(".py") and old not in converted_old:
                    _judge_cookbook_deletion(repo, base, old, page_map, add)
            else:
                add(old, 1, "R8", "outside the allowlist: this file may not be deleted")
        elif status in ("R", "C"):
            if SNIPPET_RE.match(old):
                add(old, 1, "R8", f"a snippet may not be {'renamed' if status == 'R' else 'copied'} (to {new})")
            elif old.startswith(COOKBOOK_REL) and sm and lo <= int(sm.group(1)) <= hi:
                defs_src = repo.show(base, pairs.get(new, old))
                judge_new(new, defs_src)
                if status == "C":
                    pass  # the original stays; nothing else to judge
            else:
                add(new, 1, "R8", f"outside the allowlist: {old} -> {new} (only docs/cookbook -> "
                                  f"a snippet inside --range is a conversion)")
        else:
            add(new, 1, "R8", f"change type {status!r} is not allowed")

    changed_new = {n for _s, _o, n in entries}
    for new, old in pairs.items():
        if new not in changed_new:
            add(new, 1, "R8", f"--pair names {new}, which the batch did not add")
    return problems, warnings, examined


def _judge_cookbook_deletion(repo, base, old, page_map, add):
    src = repo.show(base, old)
    if src is None:
        add(old, 1, "R9", "deleted, but it does not exist at --base")
        return
    names = defined_names(src)
    if not names:
        return
    m = DOC_PAGE_RE.search(src[:600])
    stem = m.group(1) if m else None
    if stem is None:
        add(old, 1, "R9", "cannot tell which page this file belongs to (no Documentation: header); "
                          "restore it for the page batch")
        return
    if stem not in page_map:
        add(old, 1, "R9", f"deleted, but --page-snippets {stem}=N,N,... was not given")
        return
    defined = set()
    for number in page_map[stem]:
        files = repo.snippet_files(number)
        if not files:
            add(old, 1, "R9", f"--page-snippets {stem}: no snippet numbered {number}")
            return
        for f in files:
            defined |= {n.name for n in ast.walk(ast.parse(repo.read(f)))
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    for name in sorted(names - defined):
        add(old, 1, "R9", f"deleted, but {name!r} is not DEFINED in the snippets of page {stem} "
                          f"({','.join(str(n) for n in page_map[stem])}); keep the file for the page batch")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint a batch of snippet work.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--base", required=True, help="commit the batch started from")
    ap.add_argument("--range", required=True, dest="rng", metavar="A-B")
    ap.add_argument("--page-snippets", action="append", default=[], metavar="PAGE=N,N")
    ap.add_argument("--pair", action="append", default=[], metavar="OLD:NEW")
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--manifest")
    args = ap.parse_args(argv)

    repo = Repo(args.repo)
    known, settable = load_manifest(args.manifest or os.path.join(repo.root, "api", "manifest.json"))
    pairs = {}
    for spec in args.pair:
        if ":" not in spec:
            sys.exit(f"--pair {spec!r}: want OLD:NEW")
        old, new = spec.split(":", 1)
        pairs[os.path.normpath(new)] = os.path.normpath(old)

    problems, warnings, examined = judge(repo, args.base, parse_range(args.rng), known, settable,
                                         pairs, parse_page_snippets(args.page_snippets))
    for path, line, rule, msg in warnings:
        print(f"{path}:{line}: warning: {msg}")
    for path, line, rule, msg in sorted(problems):
        print(f"{path}:{line}: {rule}: {msg}")
    print(f"lint_snippet_batch: {examined} snippet(s) examined, {len(problems)} violation(s), "
          f"{len(warnings)} warning(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
