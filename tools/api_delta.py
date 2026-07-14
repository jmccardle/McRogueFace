#!/usr/bin/env python3
"""
api_delta.py -- diff two McRogueFace API manifests.

Plain python3, standard library only. Loads api/manifest.json from two git
refs (or the working tree via ".") and reports what changed in the API surface.

Usage:
    api_delta.py REF1 REF2 [--format md|json|gitea] [--site-dir PATH]

REF1 / REF2:
    A git ref (branch, tag, commit) whose api/manifest.json is read via
    `git show REF:api/manifest.json`, or "." to read the working-tree file
    at api/manifest.json.

--format:
    md    (default) human-readable Markdown tables
    json  machine-readable delta structure
    gitea a checklist-style issue body grouped by object ("- [ ]" items)

--site-dir PATH:
    Scan a Jekyll site for pages whose YAML frontmatter carries an
    `mcrf.objects` list; affected pages are attached to each object entry.
"""

import os
import re
import sys
import json
import argparse
import subprocess


# ---------------------------------------------------------------------------
# Manifest loading
# ---------------------------------------------------------------------------

def git_output(args, cwd):
    proc = subprocess.run(
        ["git"] + args, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), \
        proc.stderr.decode("utf-8", "replace")


def repo_root():
    rc, out, _ = git_output(["rev-parse", "--show-toplevel"], os.getcwd())
    if rc == 0 and out.strip():
        return out.strip()
    return os.getcwd()


def load_manifest(ref, repo):
    """Load api/manifest.json for a ref, or from the working tree when ref == '.'."""
    if ref == ".":
        path = os.path.join(repo, "api", "manifest.json")
        with open(path, "r") as f:
            return json.load(f)
    rc, out, err = git_output(["show", "%s:api/manifest.json" % ref], repo)
    if rc != 0:
        # Distinguish "this ref predates the manifest" from "the ref is broken". The
        # manifest infrastructure landed in 54624b3, so every tag older than that --
        # 0.2.8 included -- genuinely has no API baseline. That is a fact to report,
        # not a crash: there is nothing to diff against, and saying so is the honest
        # answer to "what changed since 0.2.8?". An unknown ref is still an error.
        rc_ref, _, _ = git_output(["rev-parse", "--verify", "%s^{commit}" % ref], repo)
        if rc_ref == 0:
            return None
        raise SystemExit("error: cannot read api/manifest.json at ref '%s': %s"
                         % (ref, err.strip()))
    return json.loads(out)


# ---------------------------------------------------------------------------
# Jekyll frontmatter scan (minimal, no deps)
# ---------------------------------------------------------------------------

def frontmatter_lines(raw):
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    return None


def extract_objects_list(hay):
    names = []
    # inline form: objects: [A, B, "C"]
    m = re.search(r"objects:\s*\[([^\]]*)\]", hay)
    if m:
        for part in m.group(1).split(","):
            p = part.strip().strip("'\"")
            if p:
                names.append(p)
        return names
    # block form: objects:\n  - A\n  - B
    m = re.search(r"(?m)^\s*objects:\s*$", hay)
    if m:
        for line in hay[m.end():].splitlines():
            if line.strip() == "":
                continue
            lm = re.match(r"^\s*-\s*(.+?)\s*$", line)
            if lm:
                names.append(lm.group(1).strip().strip("'\""))
                continue
            # a non-list, non-blank line ends the list
            break
    return names


def objects_from_frontmatter(raw):
    fm = frontmatter_lines(raw)
    if fm is None:
        return []
    text = "\n".join(fm)
    m = re.search(r"(?m)^mcrf:[ \t]*(.*)$", text)
    if not m:
        return []
    inline_after = m.group(1).strip()
    block = []
    for line in text[m.end():].splitlines():
        if line.strip() == "":
            block.append(line)
            continue
        if re.match(r"^\s", line):
            block.append(line)
        else:
            break
    hay = inline_after + "\n" + "\n".join(block)
    return extract_objects_list(hay)


def scan_site(site_dir):
    """Return {object_name: [relative page paths]}."""
    mapping = {}
    exts = (".md", ".markdown", ".html", ".htm")
    for root, _dirs, files in os.walk(site_dir):
        for fname in files:
            if not fname.lower().endswith(exts):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, "r", errors="replace") as f:
                    raw = f.read(8192)
            except Exception:
                continue
            objs = objects_from_frontmatter(raw)
            if not objs:
                continue
            rel = os.path.relpath(path, site_dir)
            for name in objs:
                mapping.setdefault(name, set()).add(rel)
    return {k: sorted(v) for k, v in mapping.items()}


# ---------------------------------------------------------------------------
# Delta computation
# ---------------------------------------------------------------------------

def member_changed(a, b):
    """Classify a member change: 'signature' or 'doc' or None."""
    if a.get("kind") != b.get("kind"):
        return "signature"
    if a.get("signature", "") != b.get("signature", ""):
        return "signature"
    if a.get("doc_sha") != b.get("doc_sha"):
        return "doc"
    return None


def compute_delta(a, b, object_pages):
    a_objs = a.get("objects", {})
    b_objs = b.get("objects", {})
    a_fns = a.get("functions", {})
    b_fns = b.get("functions", {})

    def pages_for(name):
        return object_pages.get(name, []) if object_pages else []

    objects_added = sorted(set(b_objs) - set(a_objs))
    objects_removed = sorted(set(a_objs) - set(b_objs))

    objects_changed = {}
    for name in sorted(set(a_objs) & set(b_objs)):
        a_mem = a_objs[name].get("members", {})
        b_mem = b_objs[name].get("members", {})
        added = sorted(set(b_mem) - set(a_mem))
        removed = sorted(set(a_mem) - set(b_mem))
        sig_changed = []
        doc_changed = []
        for m in sorted(set(a_mem) & set(b_mem)):
            kind = member_changed(a_mem[m], b_mem[m])
            if kind == "signature":
                sig_changed.append(m)
            elif kind == "doc":
                doc_changed.append(m)
        obj_doc_changed = a_objs[name].get("doc_sha") != b_objs[name].get("doc_sha")
        if added or removed or sig_changed or doc_changed or obj_doc_changed:
            objects_changed[name] = {
                "members_added": added,
                "members_removed": removed,
                "members_signature_changed": sig_changed,
                "members_doc_changed": doc_changed,
                "object_doc_changed": obj_doc_changed,
                "pages": pages_for(name),
            }

    functions_added = sorted(set(b_fns) - set(a_fns))
    functions_removed = sorted(set(a_fns) - set(b_fns))
    functions_sig_changed = []
    functions_doc_changed = []
    for m in sorted(set(a_fns) & set(b_fns)):
        kind = member_changed(a_fns[m], b_fns[m])
        if kind == "signature":
            functions_sig_changed.append(m)
        elif kind == "doc":
            functions_doc_changed.append(m)

    # #356: dynamic module attributes (current_scene, scenes, ...) are their own
    # manifest section; without this they drift silently.
    a_attrs = a.get("module_attributes", {})
    b_attrs = b.get("module_attributes", {})
    attrs_added = sorted(set(b_attrs) - set(a_attrs))
    attrs_removed = sorted(set(a_attrs) - set(b_attrs))
    attrs_changed = []
    for m in sorted(set(a_attrs) & set(b_attrs)):
        if member_changed(a_attrs[m], b_attrs[m]):
            attrs_changed.append(m)

    return {
        "ref1": None,
        "ref2": None,
        "objects_added": [{"name": n, "pages": pages_for(n)} for n in objects_added],
        "objects_removed": [{"name": n, "pages": pages_for(n)} for n in objects_removed],
        "objects_changed": objects_changed,
        "functions_added": functions_added,
        "functions_removed": functions_removed,
        "functions_signature_changed": functions_sig_changed,
        "functions_doc_changed": functions_doc_changed,
        "module_attributes_added": attrs_added,
        "module_attributes_removed": attrs_removed,
        "module_attributes_changed": attrs_changed,
    }


def delta_is_empty(d):
    return not (d["objects_added"] or d["objects_removed"] or d["objects_changed"]
                or d["functions_added"] or d["functions_removed"]
                or d["functions_signature_changed"] or d["functions_doc_changed"]
                or d["module_attributes_added"] or d["module_attributes_removed"]
                or d["module_attributes_changed"])


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_json(d):
    return json.dumps(d, sort_keys=True, indent=2)


def _pages_suffix(pages):
    return ("  (pages: %s)" % ", ".join(pages)) if pages else ""


def render_md(d):
    out = []
    out.append("# API delta: %s -> %s" % (d["ref1"], d["ref2"]))
    out.append("")
    if delta_is_empty(d):
        out.append("No API changes.")
        out.append("")
        return "\n".join(out)

    if d["objects_added"]:
        out.append("## Objects added")
        out.append("")
        out.append("| object | pages |")
        out.append("| --- | --- |")
        for o in d["objects_added"]:
            out.append("| `%s` | %s |" % (o["name"], ", ".join(o["pages"]) or "-"))
        out.append("")

    if d["objects_removed"]:
        out.append("## Objects removed")
        out.append("")
        out.append("| object | pages |")
        out.append("| --- | --- |")
        for o in d["objects_removed"]:
            out.append("| `%s` | %s |" % (o["name"], ", ".join(o["pages"]) or "-"))
        out.append("")

    if d["objects_changed"]:
        out.append("## Objects changed")
        out.append("")
        for name in sorted(d["objects_changed"]):
            info = d["objects_changed"][name]
            out.append("### %s%s" % (name, _pages_suffix(info["pages"])))
            out.append("")
            if info.get("object_doc_changed"):
                out.append("- class docstring changed")
            out.append("| change | members |")
            out.append("| --- | --- |")
            rows = [
                ("added", info["members_added"]),
                ("removed", info["members_removed"]),
                ("signature changed", info["members_signature_changed"]),
                ("doc changed", info["members_doc_changed"]),
            ]
            for label, members in rows:
                if members:
                    out.append("| %s | %s |"
                               % (label, ", ".join("`%s`" % m for m in members)))
            out.append("")

    fn_rows = [
        ("added", d["functions_added"]),
        ("removed", d["functions_removed"]),
        ("signature changed", d["functions_signature_changed"]),
        ("doc changed", d["functions_doc_changed"]),
    ]
    if any(members for _, members in fn_rows):
        out.append("## Functions")
        out.append("")
        out.append("| change | functions |")
        out.append("| --- | --- |")
        for label, members in fn_rows:
            if members:
                out.append("| %s | %s |"
                           % (label, ", ".join("`%s`" % m for m in members)))
        out.append("")

    attr_rows = [
        ("added", d["module_attributes_added"]),
        ("removed", d["module_attributes_removed"]),
        ("changed", d["module_attributes_changed"]),
    ]
    if any(members for _, members in attr_rows):
        out.append("## Module attributes")
        out.append("")
        out.append("| change | attributes |")
        out.append("| --- | --- |")
        for label, members in attr_rows:
            if members:
                out.append("| %s | %s |"
                           % (label, ", ".join("`%s`" % m for m in members)))
        out.append("")

    return "\n".join(out)


def render_gitea(d):
    out = []
    out.append("## API changes: %s..%s" % (d["ref1"], d["ref2"]))
    out.append("")
    if delta_is_empty(d):
        out.append("No API changes.")
        out.append("")
        return "\n".join(out)

    for o in d["objects_added"]:
        out.append("### %s (new object)%s" % (o["name"], _pages_suffix(o["pages"])))
        out.append("- [ ] document new object `%s`" % o["name"])
        out.append("")
    for o in d["objects_removed"]:
        out.append("### %s (removed object)%s" % (o["name"], _pages_suffix(o["pages"])))
        out.append("- [ ] remove references to `%s`" % o["name"])
        out.append("")

    for name in sorted(d["objects_changed"]):
        info = d["objects_changed"][name]
        out.append("### %s%s" % (name, _pages_suffix(info["pages"])))
        if info.get("object_doc_changed"):
            out.append("- [ ] review class docstring change")
        for m in info["members_added"]:
            out.append("- [ ] member added: `%s`" % m)
        for m in info["members_removed"]:
            out.append("- [ ] member removed: `%s`" % m)
        for m in info["members_signature_changed"]:
            out.append("- [ ] signature changed: `%s`" % m)
        for m in info["members_doc_changed"]:
            out.append("- [ ] doc changed: `%s`" % m)
        out.append("")

    fn_items = (
        [("added", m) for m in d["functions_added"]]
        + [("removed", m) for m in d["functions_removed"]]
        + [("signature changed", m) for m in d["functions_signature_changed"]]
        + [("doc changed", m) for m in d["functions_doc_changed"]]
    )
    if fn_items:
        out.append("### Functions")
        for label, m in fn_items:
            out.append("- [ ] %s: `%s`" % (label, m))
        out.append("")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Diff two McRogueFace API manifests.")
    parser.add_argument("ref1", help="first git ref, or '.' for the working tree")
    parser.add_argument("ref2", help="second git ref, or '.' for the working tree")
    parser.add_argument("--format", choices=["md", "json", "gitea"], default="md")
    parser.add_argument("--site-dir", default=None,
                        help="Jekyll site dir to scan for mcrf.objects frontmatter")
    args = parser.parse_args(argv)

    repo = repo_root()
    a = load_manifest(args.ref1, repo)
    b = load_manifest(args.ref2, repo)

    if a is None:
        print("# API delta: %s -> %s\n" % (args.ref1, args.ref2))
        print("**No baseline.** `%s` predates the API manifest (added in 54624b3), so "
              "there is nothing to diff against -- every object in the current API would "
              "read as \"added\", which is noise rather than a delta.\n"
              % args.ref1)
        print("This release establishes the baseline: the next one can diff against it.")
        return 0

    object_pages = scan_site(args.site_dir) if args.site_dir else None

    delta = compute_delta(a, b, object_pages)
    delta["ref1"] = args.ref1
    delta["ref2"] = args.ref2

    if args.format == "json":
        print(render_json(delta))
    elif args.format == "gitea":
        print(render_gitea(delta))
    else:
        print(render_md(delta))

    return 0


if __name__ == "__main__":
    sys.exit(main())
