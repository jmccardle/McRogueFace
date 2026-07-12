#!/usr/bin/env python3
"""
API manifest generator for McRogueFace.

Runs INSIDE the engine (mcrfpy embedded interpreter) and introspects the
compiled `mcrfpy` module to emit two artifacts:

  api/manifest.json           -- compact, committed, deterministic baseline
  docs/generated/api_full.json -- same tree plus full docstring text

Invoke:
    cd build && ./mcrogueface --headless --exec ../tools/generate_api_manifest.py

The manifest tracks per-object / per-member lifecycle (since / modified) by
diffing against the previous committed manifest (git show HEAD:api/manifest.json).
Renderers must tolerate optional future lifecycle keys "deprecated" and "removed".

Pure ASCII source (embedded interpreter constraint).
"""

import os
import sys
import json
import types
import hashlib
import subprocess

try:
    import mcrfpy
except ImportError:
    print("Error: this script must be run with McRogueFace as the interpreter")
    print("Usage: ./build/mcrogueface --headless --exec ../tools/generate_api_manifest.py")
    sys.exit(1)

SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# Git / version helpers
# ---------------------------------------------------------------------------

def run_git(args, repo):
    """Return (returncode, stdout_text). Never raises."""
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return proc.returncode, proc.stdout.decode("utf-8", "replace")
    except Exception:
        return 1, ""


def find_repo_root():
    rc, out = run_git(["rev-parse", "--show-toplevel"], os.getcwd())
    if rc == 0 and out.strip():
        return out.strip()
    # Fall back to the tools/ directory's parent.
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


def parse_base_version(repo):
    """Parse MCRFPY_VERSION from src/McRogueFaceVersion.h."""
    header = os.path.join(repo, "src", "McRogueFaceVersion.h")
    with open(header, "r") as f:
        text = f.read()
    marker = "#define MCRFPY_VERSION"
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(marker):
            q1 = line.find('"')
            q2 = line.find('"', q1 + 1)
            if q1 != -1 and q2 != -1:
                return line[q1 + 1:q2]
    raise RuntimeError("Could not parse MCRFPY_VERSION from " + header)


def compute_version_info(repo):
    base = parse_base_version(repo)
    rc, _ = run_git(["describe", "--tags", "--exact-match"], repo)
    exact_tag = (rc == 0)
    version = base if exact_tag else (base + "-dev")

    rc, out = run_git(["rev-parse", "--short", "HEAD"], repo)
    commit = out.strip() if rc == 0 else ""

    rc, out = run_git(["status", "--porcelain", "--", "src/"], repo)
    dirty = bool(out.strip()) if rc == 0 else False

    return base, version, commit, dirty


def load_previous_manifest(repo):
    """Return the previous committed manifest dict, or None on first run."""
    rc, out = run_git(["show", "HEAD:api/manifest.json"], repo)
    if rc != 0 or not out.strip():
        return None
    try:
        return json.loads(out)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Introspection helpers
# ---------------------------------------------------------------------------

def doc_hash(doc):
    """First 16 hex chars of sha256 of the docstring (hash empty string if absent)."""
    return hashlib.sha256((doc or "").encode("utf-8")).hexdigest()[:16]


def looks_like_signature(line):
    """A line looks like a signature if it is an optional identifier followed by
    a parenthesised argument list: e.g. 'step(dt: float) -> float' or '(a, b)'."""
    s = line.strip()
    i = 0
    n = len(s)
    # optional leading identifier
    while i < n and (s[i].isalnum() or s[i] == "_"):
        i += 1
    # optional spaces
    while i < n and s[i] == " ":
        i += 1
    if i >= n or s[i] != "(":
        return False
    return ")" in s[i:]


def extract_signature(doc, text_signature):
    """First docstring line when it looks like a signature, else __text_signature__,
    else empty string."""
    if doc:
        first = doc.strip().split("\n", 1)[0].strip()
        if looks_like_signature(first):
            return first
    if text_signature:
        return text_signature
    return ""


def raw_descriptor(cls, name):
    for base in getattr(cls, "__mro__", (cls,)):
        if name in base.__dict__:
            return base.__dict__[name]
    return None


def classify_member(cls, name, attr):
    """Return one of method|classmethod|staticmethod|property, or None if the
    attribute is not a documented API member (e.g. a plain enum value)."""
    raw = raw_descriptor(cls, name)
    raw_type = type(raw).__name__

    if isinstance(raw, staticmethod):
        return "staticmethod"
    if raw_type == "classmethod_descriptor":
        return "classmethod"
    if isinstance(raw, property):
        return "property"
    if isinstance(raw, (types.GetSetDescriptorType, types.MemberDescriptorType)):
        return "property"
    if raw_type in ("method_descriptor", "wrapper_descriptor",
                    "builtin_function_or_method", "function") and callable(attr):
        return "method"
    return None


def member_entry(cls, name):
    """Build a full member entry (with 'doc'), or None if not an API member."""
    try:
        attr = getattr(cls, name)
    except Exception:
        return None
    kind = classify_member(cls, name, attr)
    if kind is None:
        return None
    doc = getattr(attr, "__doc__", None) or ""
    text_sig = getattr(attr, "__text_signature__", None)
    sig = extract_signature(doc, text_sig)
    return {
        "kind": kind,
        "signature": sig,
        "doc": doc,
        "doc_sha": doc_hash(doc),
    }


def collect_classes():
    """Return {class_name: full_entry_without_lifecycle}."""
    classes = {}
    for name in sorted(dir(mcrfpy)):
        if name.startswith("_"):
            continue
        obj = getattr(mcrfpy, name)
        if not isinstance(obj, type):
            continue
        doc = obj.__doc__ or ""
        members = {}
        for mname in sorted(dir(obj)):
            if mname.startswith("__"):
                continue
            entry = member_entry(obj, mname)
            if entry is not None:
                members[mname] = entry
        classes[name] = {
            "kind": "class",
            "doc": doc,
            "doc_sha": doc_hash(doc),
            "members": members,
        }
    return classes


def collect_functions():
    """Return {func_name: full_entry_without_lifecycle}."""
    functions = {}
    for name in sorted(dir(mcrfpy)):
        if name.startswith("_"):
            continue
        obj = getattr(mcrfpy, name)
        if isinstance(obj, type):
            continue
        if not callable(obj):
            continue
        doc = getattr(obj, "__doc__", None) or ""
        text_sig = getattr(obj, "__text_signature__", None)
        sig = extract_signature(doc, text_sig)
        functions[name] = {
            "kind": "function",
            "signature": sig,
            "doc": doc,
            "doc_sha": doc_hash(doc),
        }
    return functions


# ---------------------------------------------------------------------------
# Lifecycle assignment
# ---------------------------------------------------------------------------

def assign_lifecycle(cur, prev, new_since, version, commit, has_signature):
    """Attach a 'lifecycle' dict to cur based on the previous entry.

    - new (prev is None)            -> {"since": new_since}
    - doc_sha or signature changed  -> copy prev lifecycle, set modified={version,commit}
    - unchanged                     -> copy prev lifecycle verbatim
    """
    if prev is None:
        return {"since": new_since}

    prev_lc = prev.get("lifecycle", {})
    lifecycle = json.loads(json.dumps(prev_lc))  # deep copy, verbatim
    if "since" not in lifecycle:
        lifecycle["since"] = new_since

    changed = prev.get("doc_sha") != cur["doc_sha"]
    if has_signature:
        changed = changed or (prev.get("signature", "") != cur.get("signature", ""))

    if changed:
        lifecycle["modified"] = {"version": version, "commit": commit}
    return lifecycle


def build_tree(classes, functions, prev, first_run, base_version, version, commit):
    """Produce the full tree (entries retain 'doc'); lifecycle is computed here."""
    new_since = base_version if first_run else version
    prev_objects = (prev or {}).get("objects", {})
    prev_functions = (prev or {}).get("functions", {})

    objects_out = {}
    for cname, centry in classes.items():
        prev_obj = prev_objects.get(cname)
        obj_lifecycle = assign_lifecycle(
            centry, prev_obj, new_since, version, commit, has_signature=False)

        prev_members = (prev_obj or {}).get("members", {})
        members_out = {}
        for mname, mentry in centry["members"].items():
            prev_member = prev_members.get(mname)
            mentry = dict(mentry)
            mentry["lifecycle"] = assign_lifecycle(
                mentry, prev_member, new_since, version, commit, has_signature=True)
            members_out[mname] = mentry

        objects_out[cname] = {
            "kind": "class",
            "doc": centry["doc"],
            "doc_sha": centry["doc_sha"],
            "lifecycle": obj_lifecycle,
            "members": members_out,
        }

    functions_out = {}
    for fname, fentry in functions.items():
        prev_fn = prev_functions.get(fname)
        fentry = dict(fentry)
        fentry["lifecycle"] = assign_lifecycle(
            fentry, prev_fn, new_since, version, commit, has_signature=True)
        functions_out[fname] = fentry

    return objects_out, functions_out


def strip_docs(node):
    """Recursively remove 'doc' keys, returning a new structure for the compact manifest."""
    if isinstance(node, dict):
        return {k: strip_docs(v) for k, v in node.items() if k != "doc"}
    if isinstance(node, list):
        return [strip_docs(v) for v in node]
    return node


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    repo = find_repo_root()
    base_version, version, commit, dirty = compute_version_info(repo)

    prev = load_previous_manifest(repo)
    first_run = prev is None

    classes = collect_classes()
    functions = collect_functions()

    objects_out, functions_out = build_tree(
        classes, functions, prev, first_run, base_version, version, commit)

    full = {
        "schema": SCHEMA_VERSION,
        "version": version,
        "commit": commit,
        "dirty": dirty,
        "seeded": first_run,
        "objects": objects_out,
        "functions": functions_out,
    }

    manifest = strip_docs(full)

    api_dir = os.path.join(repo, "api")
    gen_dir = os.path.join(repo, "docs", "generated")
    os.makedirs(api_dir, exist_ok=True)
    os.makedirs(gen_dir, exist_ok=True)

    manifest_path = os.path.join(api_dir, "manifest.json")
    full_path = os.path.join(gen_dir, "api_full.json")

    with open(manifest_path, "w") as f:
        f.write(json.dumps(manifest, sort_keys=True, separators=(",", ":")))
        f.write("\n")

    with open(full_path, "w") as f:
        f.write(json.dumps(full, sort_keys=True, indent=2))
        f.write("\n")

    n_obj = len(objects_out)
    n_fn = len(functions_out)
    n_mem = sum(len(o["members"]) for o in objects_out.values())
    print("manifest: %s" % manifest_path)
    print("full:     %s" % full_path)
    print("version=%s commit=%s dirty=%s seeded=%s" % (version, commit, dirty, first_run))
    print("objects=%d members=%d functions=%d" % (n_obj, n_mem, n_fn))


if __name__ == "__main__":
    main()
    sys.exit(0)
