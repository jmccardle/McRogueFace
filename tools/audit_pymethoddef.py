#!/usr/bin/env python3
"""
audit_pymethoddef.py - Static-analysis tool for McRogueFace Python bindings.

Walks src/**/*.cpp, parses each file with tree-sitter-cpp, and locates every
`PyMethodDef <name>[] = {...}` and `PyGetSetDef <name>[] = {...}` declaration.
For each entry inside those array initializers, classifies the docstring slot:

    MACRO       - uses MCRF_METHOD(...) or MCRF_PROPERTY(...)
    RAW_STRING  - inline C string literal (or concatenated string literals)
    NULL        - explicit NULL literal
    MISSING     - entry too short to have a doc field (probably malformed)

The `MACRO` classification is the project's compliance target. RAW_STRING and
NULL entries should be migrated to the macro system before the 1.0 API freeze.

Sentinel terminator entries (e.g. `{NULL}`, `{0}`) are skipped.

Usage:
    python3 tools/audit_pymethoddef.py [--strict] [--quiet]
                                       [--paths PATH [PATH ...]]

Flags:
    --strict   Exit nonzero if any non-MACRO entries are found (CI mode).
    --quiet    Suppress per-file output, print only the summary.
    --paths    Restrict scan to the given files/directories. Defaults to src/.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

try:
    import tree_sitter_cpp
    from tree_sitter import Language, Parser
except ImportError as e:
    sys.stderr.write(
        "ERROR: tree-sitter / tree-sitter-cpp not installed.\n"
        "Activate the audit venv first:\n"
        "    source .venv-audit/bin/activate\n"
        f"(import error: {e})\n"
    )
    sys.exit(2)


# ---------------------------------------------------------------------------
# Tree-sitter setup
# ---------------------------------------------------------------------------

_LANG = Language(tree_sitter_cpp.language())
_PARSER = Parser(_LANG)

# Indices of the docstring field in the struct initializer.
# PyMethodDef:  {ml_name, ml_meth, ml_flags, ml_doc}                  -> idx 3
# PyGetSetDef:  {name, get, set, doc, closure}                        -> idx 3
DOC_FIELD_INDEX = 3
EXPECTED_MIN_FIELDS = {
    "PyMethodDef": 4,   # need at least 4 to have ml_doc
    "PyGetSetDef": 4,   # need at least 4 to have doc (closure can be omitted)
}

# Punctuation/structural child node types we ignore when walking entry fields.
_PUNCT_TYPES = {"{", "}", ",", "(", ")", "[", "]", ";"}

# Macros that mark a docstring slot as compliant.
_COMPLIANT_MACROS = {"MCRF_METHOD", "MCRF_PROPERTY"}


# ---------------------------------------------------------------------------
# Data records
# ---------------------------------------------------------------------------

@dataclass
class EntryRecord:
    file_path: Path
    line: int                # 1-based
    array_kind: str          # "PyMethodDef" or "PyGetSetDef"
    array_name: str          # e.g. "PyAnimation::methods"
    entry_name: str          # ml_name / name string, or "<unknown>"
    classification: str      # MACRO / RAW_STRING / NULL / MISSING


# ---------------------------------------------------------------------------
# Tree-sitter helpers
# ---------------------------------------------------------------------------

def _node_text(src: bytes, node) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _meaningful_children(node) -> List:
    """Return children of an initializer_list, skipping punctuation tokens."""
    return [c for c in node.children if c.type not in _PUNCT_TYPES]


def _classify_doc_field(src: bytes, doc_node) -> str:
    """Map a docstring AST node to a classification string."""
    t = doc_node.type
    if t == "null":
        return "NULL"
    if t in ("string_literal", "concatenated_string", "raw_string_literal"):
        return "RAW_STRING"
    if t == "call_expression":
        # The first child of call_expression is the callee identifier.
        callee = doc_node.child_by_field_name("function")
        if callee is None and doc_node.children:
            callee = doc_node.children[0]
        if callee is not None:
            name = _node_text(src, callee).strip()
            if name in _COMPLIANT_MACROS:
                return "MACRO"
        return "RAW_STRING"  # call expression to something non-MACRO
    if t == "identifier":
        # Bare identifier in the doc slot - could be a #define alias. Treat as
        # raw (non-compliant) so the user investigates it.
        text = _node_text(src, doc_node).strip()
        if text == "NULL":
            return "NULL"
        return "RAW_STRING"
    # Anything else (parenthesized_expression, etc.) - inspect text fallback.
    text = _node_text(src, doc_node).strip()
    stripped = text.lstrip("(").lstrip()
    for macro in _COMPLIANT_MACROS:
        if stripped.startswith(macro + "("):
            return "MACRO"
    if stripped == "NULL":
        return "NULL"
    return "RAW_STRING"


def _entry_name(src: bytes, entry_node) -> str:
    """Return the first string literal in an entry initializer (the ml_name)."""
    for c in _meaningful_children(entry_node):
        if c.type == "string_literal":
            # string_literal contains string_content children
            for sub in c.children:
                if sub.type == "string_content":
                    return _node_text(src, sub)
            return _node_text(src, c).strip('"')
        if c.type == "concatenated_string":
            for lit in c.children:
                if lit.type == "string_literal":
                    for sub in lit.children:
                        if sub.type == "string_content":
                            return _node_text(src, sub)
            return _node_text(src, c)
        # Stop at the first non-string field - the name should come first.
        break
    return "<unknown>"


def _is_sentinel(src: bytes, entry_node) -> bool:
    """True if the entry looks like a sentinel terminator (e.g. {NULL} / {0})."""
    fields = _meaningful_children(entry_node)
    if not fields:
        return True
    if len(fields) == 1:
        only = fields[0]
        if only.type == "null":
            return True
        if only.type == "number_literal" and _node_text(src, only).strip() == "0":
            return True
    # Some codebases write {NULL, NULL, NULL, NULL}. Treat all-NULL/0 as sentinel.
    for f in fields:
        if f.type == "null":
            continue
        if f.type == "number_literal" and _node_text(src, f).strip() == "0":
            continue
        return False
    return True


def _array_name_from_init_declarator(src: bytes, init_decl) -> Optional[str]:
    """Extract the array name from an init_declarator containing array_declarator."""
    arr = None
    for c in init_decl.children:
        if c.type == "array_declarator":
            arr = c
            break
    if arr is None:
        return None
    # The first child is the declarator (identifier or qualified_identifier).
    for c in arr.children:
        if c.type in ("identifier", "qualified_identifier", "field_identifier"):
            return _node_text(src, c)
    return None


def _outer_initializer_list(init_decl):
    """Get the top-level initializer_list child of an init_declarator, if any."""
    for c in init_decl.children:
        if c.type == "initializer_list":
            return c
    return None


# ---------------------------------------------------------------------------
# Per-file scan
# ---------------------------------------------------------------------------

def _walk_declarations(node, out: list) -> None:
    """Collect all `declaration` nodes under `node` (recursive)."""
    if node.type == "declaration":
        out.append(node)
    for c in node.children:
        _walk_declarations(c, out)


def scan_file(path: Path) -> List[EntryRecord]:
    try:
        src = path.read_bytes()
    except OSError as e:
        sys.stderr.write(f"WARNING: cannot read {path}: {e}\n")
        return []

    tree = _PARSER.parse(src)
    decls: list = []
    _walk_declarations(tree.root_node, decls)

    records: List[EntryRecord] = []
    for decl in decls:
        # Find the type_identifier child to determine if this is one of ours.
        type_kind = None
        for c in decl.children:
            if c.type == "type_identifier":
                txt = _node_text(src, c).strip()
                if txt in EXPECTED_MIN_FIELDS:
                    type_kind = txt
                break
        if type_kind is None:
            continue

        # Each declaration may have multiple init_declarators (rare for arrays
        # but cheap to handle).
        for c in decl.children:
            if c.type != "init_declarator":
                continue
            outer_init = _outer_initializer_list(c)
            if outer_init is None:
                continue  # forward decl or extern - no initializer
            array_name = _array_name_from_init_declarator(src, c) or "<anon>"

            # Each direct child initializer_list is an entry.
            for entry in outer_init.children:
                if entry.type != "initializer_list":
                    continue
                if _is_sentinel(src, entry):
                    continue

                fields = _meaningful_children(entry)
                line = entry.start_point[0] + 1  # tree-sitter is 0-based
                name = _entry_name(src, entry)

                if len(fields) <= DOC_FIELD_INDEX:
                    records.append(EntryRecord(
                        file_path=path,
                        line=line,
                        array_kind=type_kind,
                        array_name=array_name,
                        entry_name=name,
                        classification="MISSING",
                    ))
                    continue

                doc_node = fields[DOC_FIELD_INDEX]
                classification = _classify_doc_field(src, doc_node)
                records.append(EntryRecord(
                    file_path=path,
                    line=line,
                    array_kind=type_kind,
                    array_name=array_name,
                    entry_name=name,
                    classification=classification,
                ))
    return records


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _iter_cpp_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if root.is_file():
            if root.suffix == ".cpp":
                yield root
            continue
        if not root.exists():
            sys.stderr.write(f"WARNING: path does not exist: {root}\n")
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in filenames:
                if fn.endswith(".cpp"):
                    yield Path(dirpath) / fn


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _print_file_table(records: List[EntryRecord], project_root: Path) -> None:
    by_file: dict[Path, List[EntryRecord]] = defaultdict(list)
    for r in records:
        by_file[r.file_path].append(r)

    for path in sorted(by_file):
        try:
            rel = path.relative_to(project_root)
        except ValueError:
            rel = path
        entries = sorted(by_file[path], key=lambda r: r.line)

        # Compute column widths for this file.
        loc_w = max(len(f"{rel}:{e.line}") for e in entries)
        arr_w = max(len(e.array_name) for e in entries)
        ent_w = max(len(e.entry_name) for e in entries)
        loc_w = max(loc_w, len("file:line"))
        arr_w = max(arr_w, len("array"))
        ent_w = max(ent_w, len("entry"))

        header = (
            f"{'file:line':<{loc_w}}  "
            f"{'array':<{arr_w}}  "
            f"{'entry':<{ent_w}}  "
            f"classification"
        )
        print(header)
        print("-" * len(header))
        for e in entries:
            loc = f"{rel}:{e.line}"
            print(
                f"{loc:<{loc_w}}  "
                f"{e.array_name:<{arr_w}}  "
                f"{e.entry_name:<{ent_w}}  "
                f"{e.classification}"
            )
        print()


def _print_summary(records: List[EntryRecord]) -> None:
    total = len(records)
    counts = Counter(r.classification for r in records)
    macro = counts.get("MACRO", 0)
    raw = counts.get("RAW_STRING", 0)
    null = counts.get("NULL", 0)
    missing = counts.get("MISSING", 0)
    pct = (macro / total * 100.0) if total else 0.0

    print("=" * 60)
    print("PyMethodDef / PyGetSetDef Documentation Audit Summary")
    print("=" * 60)
    print(f"Total entries scanned : {total}")
    print(f"  MACRO compliant     : {macro}")
    print(f"  RAW_STRING          : {raw}")
    print(f"  NULL                : {null}")
    print(f"  MISSING             : {missing}")
    print(f"MACRO compliance      : {pct:.1f}%")

    # Per-kind breakdown.
    by_kind = defaultdict(Counter)
    for r in records:
        by_kind[r.array_kind][r.classification] += 1
    if by_kind:
        print()
        print("Breakdown by kind:")
        for kind in sorted(by_kind):
            kc = by_kind[kind]
            kt = sum(kc.values())
            kp = (kc.get("MACRO", 0) / kt * 100.0) if kt else 0.0
            print(
                f"  {kind:<13} total={kt:<4} "
                f"MACRO={kc.get('MACRO', 0):<4} "
                f"RAW={kc.get('RAW_STRING', 0):<4} "
                f"NULL={kc.get('NULL', 0):<4} "
                f"MISSING={kc.get('MISSING', 0):<4} "
                f"({kp:.1f}% compliant)"
            )

    # Top offenders.
    offenders: dict[Path, int] = defaultdict(int)
    for r in records:
        if r.classification != "MACRO":
            offenders[r.file_path] += 1
    if offenders:
        print()
        print("Top non-compliant files:")
        ranked = sorted(offenders.items(), key=lambda kv: kv[1], reverse=True)
        for path, count in ranked[:10]:
            try:
                rel = path.relative_to(Path.cwd())
            except ValueError:
                rel = path
            print(f"  {count:>4}  {rel}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _default_roots() -> List[Path]:
    cwd = Path.cwd()
    src = cwd / "src"
    return [src] if src.exists() else [cwd]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit PyMethodDef / PyGetSetDef entries in McRogueFace C++ "
            "sources for MCRF_METHOD / MCRF_PROPERTY documentation macro use."
        ),
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit nonzero if any non-MACRO entries are found (CI mode)."
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Print only the summary, omit per-file tables."
    )
    parser.add_argument(
        "--paths", nargs="+", type=Path, default=None,
        help="Files or directories to scan (default: ./src)."
    )
    args = parser.parse_args(argv)

    roots = args.paths if args.paths else _default_roots()
    project_root = Path.cwd()

    files = sorted(set(_iter_cpp_files(roots)))
    if not files:
        sys.stderr.write("WARNING: no .cpp files found.\n")
        return 0

    all_records: List[EntryRecord] = []
    for f in files:
        all_records.extend(scan_file(f))

    if not args.quiet:
        if all_records:
            _print_file_table(all_records, project_root)
        else:
            print("(no PyMethodDef / PyGetSetDef arrays found)")
            print()

    _print_summary(all_records)

    if args.strict:
        non_macro = sum(
            1 for r in all_records if r.classification != "MACRO"
        )
        if non_macro:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
