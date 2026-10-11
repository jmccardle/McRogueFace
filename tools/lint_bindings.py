#!/usr/bin/env python3
"""
lint_bindings.py - AST lint for hand-rolled CPython recipes in the binding layer (#430).

Parses src/**/*.{cpp,h} with tree-sitter-cpp (the same .venv-audit stack as
audit_pymethoddef.py) and flags the recipes that have already produced bugs:

  identity-alloc   tp_alloc (or Foo::pynew / PyObject_New) of an identity-bearing
                   type outside a constructor or a sanctioned converter. Breaks `x is x` and drops subclasses
                   (#369, #373, #429, #430).
  unclassified     tp_alloc whose type isn't in TYPE_CLASS (or can't be resolved).
                   Every allocated type must be classified as identity or value,
                   so a new type can't slip past identity-alloc by being unknown.
  cache-direct     PythonObjectCache:: used outside the cache itself and the
                   sanctioned converters. Each caller re-implements lookup or
                   assignSerial + weakref + registerObject.
  borrowed-leak    A new reference passed inline to a call that does NOT steal it
                   (PyDict_SetItemString(d, k, PyLong_FromLong(x)) leaks x, #413;
                   _click(self, PyTuple_New(0), kw) leaks the tuple).
  from-arg-owner   PyVector::from_arg() (new reference) whose result is neither
                   released nor returned in the same function (#414).
  missing-dealloc  A Python type whose object struct holds C++ members (shared_ptr,
                   weak_ptr, string, containers) but sets no tp_dealloc: tp_free never
                   runs their destructors, so whatever they own leaks (GridPoint leaked
                   its whole grid this way).
  pin-direct       The entity identity pin (UIEntity::pyobject) taken, released or
                   read as "the wrapper" outside its owner (#424, #429, #436).
  traverse-unguarded
                   A tp_traverse / tp_clear that reaches into the wrapped C++ object
                   (obj->data->...) without mcrf::owns_exclusively (or the drawable
                   traverseWrapper / clearWrapper built on it). The wrapper may share
                   that object with a scene or parent, so reporting what it holds let
                   the GC clear a live callback (segfault), and clearing it silently
                   dropped live handlers (#441).
  adopt-unchecked  A function that links a drawable to a parent (setParent(non-null),
                   or the link_child() helper) without first calling
                   UIDrawable::canAdopt (or UICollection's can_link). Appending an
                   ancestor looped the parent chain and segfaulted (#442).
  entity-unlinked  An insert into an entity list (entities->push_back/insert, or an
                   entity collection's own self->data) in a function that does not
                   call removeFromGrid() / removeFromViewport() first. The entity
                   stayed in its old grid too, or twice in this one (#447, #438); use
                   UIEntity::moveToGrid() / Entity3D::moveToViewport().

Findings are matched against tools/lint_bindings_baseline.txt, keyed by
(rule, file, function, call text) with counts and no line numbers, so unrelated
edits don't churn it. The run fails on any finding the baseline doesn't cover,
and on baseline entries that no longer occur (delete them: the list only
shrinks). `--update-baseline` rewrites it but refuses to add entries unless
`--allow-growth` is given.

Usage:
    .venv-audit/bin/python3 tools/lint_bindings.py            # gate (CI / pre-commit)
    .venv-audit/bin/python3 tools/lint_bindings.py --all      # list every finding
    .venv-audit/bin/python3 tools/lint_bindings.py --summary  # counts per rule/file
    .venv-audit/bin/python3 tools/lint_bindings.py --update-baseline
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

try:
    import tree_sitter_cpp
    from tree_sitter import Language, Parser
except ImportError as e:
    sys.stderr.write(
        "ERROR: tree-sitter / tree-sitter-cpp not installed.\n"
        "    python3 -m venv .venv-audit && .venv-audit/bin/pip install -r tools/requirements-audit.txt\n"
        f"(import error: {e})\n")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "tools" / "lint_bindings_baseline.txt"
_PARSER = Parser(Language(tree_sitter_cpp.language()))

# ---------------------------------------------------------------------------
# Policy tables
# ---------------------------------------------------------------------------

# Every type that is ever tp_alloc'd must be listed.
#   identity: wraps a C++ object that outlives the wrapper or is reachable from
#             several places, so Python must see one object (`is`), and a Python
#             subclass must come back as itself. Only constructors and the
#             sanctioned converters may allocate one.
#   value:    a fresh object per call is correct (copies, iterators, results).
TYPE_CLASS = {
    # drawables
    "PyUIFrameType": "identity", "PyUICaptionType": "identity",
    "PyUISpriteType": "identity", "PyUIGridViewType": "identity",
    "PyUILineType": "identity", "PyUICircleType": "identity",
    "PyUIArcType": "identity", "PyViewport3DType": "identity",
    # grid world
    "PyUIEntityType": "identity", "PyGridDataType": "identity",
    "PyColorLayerType": "identity", "PyTileLayerType": "identity",
    "PyUIEntityCollectionType": "identity", "PyUICollectionType": "identity",
    "PyDijkstraMapType": "identity",
    # 3D
    "PyEntity3DType": "identity", "PyEntityCollection3DType": "identity",
    "PyModel3DType": "identity", "PyBillboardType": "identity",
    "PyVoxelGridType": "identity",
    # shared resources
    "PyTextureType": "identity", "PyFontType": "identity",
    "PySoundBufferType": "identity", "PyTileSetFileType": "identity",
    "PySceneType": "identity", "PyWindowType": "identity",
    "PyTimerType": "identity", "PySoundType": "identity", "PyMusicType": "identity",
    # entity.perspective_map is documented as a live reference
    "PyDiscreteMapType": "identity",
    # accessors onto a parent-owned record: fresh per call, no state of their own
    "PyUIGridPointType": "value", "PyVoxelPointType": "value",
    "PyWangSetType": "value", "PyAutoRuleSetType": "value",
    # values: fresh per call is correct
    "PyVectorType": "value", "PyColorType": "value",
    "PyAnimationType": "value", "PyAStarPathType": "value",
    "PyVisibilityMaskType": "value", "PyLayerEditType": "value",
    "PyUniformCollectionType": "value", "PyVoxelRegionType": "value",
    "PyBSPNodeType": "value", "PyBSPAdjacencyType": "value",
    "PyBSPAdjacentTilesType": "value", "PyBSPIterType": "value",
    "PyUICollectionIterType": "value", "PyUIEntityCollectionIterType": "value",
    "PyEntityCollection3DIterType": "value", "PyAStarPathIterType": "value",
}

# Functions allowed to allocate identity types and use PythonObjectCache:: --
# the cache-aware converters. Matched against the qualified function name.
# Empty by design: every converter is built on mcrf::cached_wrapper (src/PyWrap.h),
# which is exempt as the recipe's implementation. Add an entry only with a reason.
SANCTIONED: set = set()

# Files that implement the cache itself.
CACHE_IMPL_FILES = {"PythonObjectCache.cpp", "PythonObjectCache.h", "PyWrap.cpp", "PyWrap.h"}

# A new reference passed inline as an argument leaks unless the callee steals it.
# Callees that steal (or release) the argument at that index; "*" = any index.
STEALING_SINKS = {
    "PyTuple_SetItem": 2, "PyTuple_SET_ITEM": 2, "PyList_SetItem": 2,
    "PyList_SET_ITEM": 2, "PyModule_AddObject": 2,
    "Py_DECREF": "*", "Py_XDECREF": "*", "Py_CLEAR": "*",
    "Py_SETREF": 1, "Py_XSETREF": 1,
    # PyWrap.h helpers
    "mcrf::dict_steal": 2, "dict_steal": 2, "mcrf::PyRef": "*", "PyRef": "*",
}
# Format-string APIs steal an argument only for an "N" code; we accept any call whose
# format literal contains N rather than matching codes to argument positions.
FORMAT_APIS = {"Py_BuildValue", "PyObject_CallFunction", "PyObject_CallMethod"}
# Calls that return a new reference.
NEW_REF_CALL = re.compile(
    r"^(Py(Long|Float|Bool|Unicode|Bytes|Tuple|List|Dict|Set|Complex)_From\w*"
    r"|PyUnicode_FromFormat|Py_BuildValue|PyObject_Call\w*|PyObject_Str|PyObject_Repr"
    r"|PyTuple_New|PyList_New|PyDict_New|PyTuple_Pack|\w+_to_PyObject|PyVector::from_arg"
    r"|(\w+::)?pyobject_for|convert\w+ToPython"
    r"|.*(->|\.|::)(pyObject|pyobject_for)|mcrf::(to_python|live_wrapper))$")

# The identity pin (#436) may only be touched by its owners' choke points.
PIN_OWNERS = {"UIEntity::syncIdentityPin", "Entity3D::syncIdentityPin",
              "UIDrawable::updatePyIdentityPin", "UIDrawable::releasePyIdentity"}

# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def text(src: bytes, n) -> str:
    return src[n.start_byte:n.end_byte].decode("utf-8", "replace")


def walk(n):
    stack = [n]
    while stack:
        n = stack.pop()
        yield n
        stack.extend(reversed(n.children))


def enclosing_scope(n):
    """Nearest function_definition or lambda_expression."""
    while n is not None:
        if n.type in ("function_definition", "lambda_expression"):
            return n
        n = n.parent
    return None


def outer_function(n):
    while n is not None:
        if n.type == "function_definition":
            return n
        n = n.parent
    return None


def function_name(src: bytes, fn) -> str:
    if fn is None:
        return "<file-scope>"
    d = _function_declarator(fn.child_by_field_name("declarator"))
    if d is None:
        return "<unknown>"
    return text(src, d.child_by_field_name("declarator"))


def _function_declarator(d):
    """Descend pointer/reference declarators (`Foo& Foo::operator=(...)`), whose
    inner declarator isn't always a named field."""
    while d is not None and d.type != "function_declarator":
        nxt = d.child_by_field_name("declarator")
        if nxt is None:
            nxt = next((c for c in d.named_children if "declarator" in c.type), None)
        d = nxt
    return d


def scope_label(src: bytes, n) -> str:
    """Qualified function name; lambdas are named after their enclosing function or
    the designated initializer they're assigned to (e.g. `.tp_new` in a type)."""
    scope = enclosing_scope(n)
    if scope is not None and scope.type == "lambda_expression":
        p = scope.parent
        while p is not None and p.type not in ("initializer_pair", "function_definition"):
            p = p.parent
        if p is not None and p.type == "initializer_pair":
            return "<lambda " + text(src, p.children[0]).strip() + ">"
        return function_name(src, outer_function(n)) + "/<lambda>"
    return function_name(src, outer_function(n))


def parameter_names(src: bytes, scope) -> set[str]:
    names = set()
    if scope is None:
        return names
    decl = scope.child_by_field_name("declarator")
    if scope.type != "lambda_expression":
        decl = _function_declarator(decl)
    if decl is None:
        return names
    params = decl.child_by_field_name("parameters")
    if params is None:
        return names
    for p in params.named_children:
        d = p.child_by_field_name("declarator")
        while d is not None and d.type not in ("identifier",):
            d = d.child_by_field_name("declarator")
        if d is not None:
            names.add(text(src, d))
    return names


TYPE_TOKEN = re.compile(r"&\s*(?:mcrfpydef::)?(Py\w+Type)\b")


def resolve_alloc_type(src: bytes, field_expr) -> tuple[str, set[str]]:
    """Type allocated by `T->tp_alloc(...)`: see resolve_type_expr."""
    return resolve_type_expr(src, text(src, field_expr.child_by_field_name("argument")).strip(),
                             field_expr)


def resolve_type_expr(src: bytes, obj: str, field_expr) -> tuple[str, set[str]]:
    """Return ("param", {}) when the expression is a caller-supplied type (a
    constructor or classmethod), else ("types", {PyXType, ...}) from the
    assignments to the variable in scope, or ("unresolved", {expr})."""
    obj = re.sub(r"^\(\s*PyTypeObject\s*\*\s*\)\s*", "", obj)
    m = TYPE_TOKEN.search("&" + obj.lstrip("&(").rstrip(")"))
    if m and obj.lstrip("(&").startswith(("mcrfpydef::", "Py")):
        return "types", {m.group(1)}
    if not re.fullmatch(r"\w+", obj):
        return "unresolved", {obj}
    scope = enclosing_scope(field_expr)
    if obj in parameter_names(src, scope):
        return "param", set()
    if scope is None:
        return "unresolved", {obj}
    # The nearest assignment before the call wins (a switch may reassign `type`
    # once per case).
    body = src[scope.start_byte:field_expr.start_byte].decode("utf-8", "replace")
    assigns = list(re.finditer(r"\b" + re.escape(obj) + r"\s*=\s*([^;]+);", body))
    if not assigns:
        return "unresolved", {obj}
    rhs = assigns[-1].group(1)
    found = set(TYPE_TOKEN.findall(rhs))
    if found:
        return "types", found
    cast = re.fullmatch(r"\s*\(\s*PyTypeObject\s*\*\s*\)\s*(\w+)\s*", rhs)
    if cast and cast.group(1) in parameter_names(src, scope):
        return "param", set()
    return "unresolved", {obj}


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    rule: str
    file: str
    line: int
    function: str
    detail: str

    @property
    def key(self) -> str:
        return f"{self.rule}|{self.file}|{self.function}|{self.detail}"


def is_sanctioned(fn: str, rel: str) -> bool:
    return fn in SANCTIONED or f"{fn}@{Path(rel).name}" in SANCTIONED


def callee_name(src: bytes, call) -> str:
    f = call.child_by_field_name("function")
    return text(src, f).strip() if f is not None else ""


def lint_file(path: Path) -> list[Finding]:
    src = path.read_bytes()
    rel = path.relative_to(ROOT).as_posix()
    tree = _PARSER.parse(src)
    out: list[Finding] = []

    def add(rule, node, detail):
        out.append(Finding(rule, rel, node.start_point[0] + 1,
                           scope_label(src, node), " ".join(detail.split())))

    for n in walk(tree.root_node):
        # tp_alloc ---------------------------------------------------------
        if n.type == "field_expression":
            field = n.child_by_field_name("field")
            if field is None or text(src, field) != "tp_alloc":
                continue
            kind, types = resolve_alloc_type(src, n)
            fn = scope_label(src, n)
            if kind == "param":
                continue
            if kind == "unresolved":
                add("unclassified", n, f"tp_alloc via {', '.join(sorted(types))}")
                continue
            for t in sorted(types):
                cls = TYPE_CLASS.get(t)
                if cls is None:
                    add("unclassified", n, f"tp_alloc {t}")
                elif cls == "identity" and not is_sanctioned(fn, rel):
                    add("identity-alloc", n, f"tp_alloc {t}")

        # PythonObjectCache:: -------------------------------------------------
        elif n.type == "qualified_identifier" and n.parent is not None \
                and n.parent.type != "qualified_identifier":
            if not text(src, n).startswith("PythonObjectCache::"):
                continue
            if path.name in CACHE_IMPL_FILES or is_sanctioned(scope_label(src, n), rel):
                continue
            stmt = n
            while stmt.parent is not None and stmt.parent.type in (
                    "call_expression", "field_expression", "argument_list"):
                stmt = stmt.parent
            m = re.search(r"getInstance\(\)\s*\.\s*(\w+)", text(src, stmt))
            add("cache-direct", n, f"PythonObjectCache.{m.group(1) if m else '?'}")

        # calls ---------------------------------------------------------------
        elif n.type == "call_expression":
            name = callee_name(src, n)
            args = n.child_by_field_name("arguments")
            if args is not None:
                check_inline_new_refs(src, n, name, args.named_children, add)
                # Other wrapper-construction routes: Foo::pynew(type, ...),
                # PyObject_New(Obj, type), PyObject_GC_New(Obj, type).
                argv = args.named_children
                tnode = None
                if re.fullmatch(r"\w+::pynew", name) and argv:
                    tnode = argv[0]
                elif name in ("PyObject_New", "PyObject_GC_New") and len(argv) >= 2:
                    tnode = argv[1]
                if tnode is not None:
                    kind, types = resolve_type_expr(src, text(src, tnode).strip(), n)
                    fn = scope_label(src, n)
                    via = name.split("::")[-1]
                    if kind == "unresolved":
                        add("unclassified", n, f"{via} via {', '.join(sorted(types))}")
                    elif kind == "types":
                        for t in sorted(types):
                            cls = TYPE_CLASS.get(t)
                            if cls is None:
                                add("unclassified", n, f"{via} {t}")
                            elif cls == "identity" and not is_sanctioned(fn, rel):
                                add("identity-alloc", n, f"{via} {t}")
            if name == "PyVector::from_arg":
                check_from_arg(src, n, add)

    out.extend(check_pin(src, tree, rel))
    out.extend(check_dealloc(src, tree, rel))
    out.extend(check_traverse(src, tree, rel))
    out.extend(check_adopt(src, tree, rel))
    out.extend(check_entity_link(src, tree, rel))
    return out


ENTITY_LIST_INSERT = re.compile(r"\bentities\s*(->|\.)\s*(push_back|emplace_back|insert|emplace)$")
SELF_DATA_INSERT = re.compile(r"\bself->data\s*->\s*(push_back|emplace_back|insert|emplace)$")


def check_entity_link(src: bytes, tree, rel: str) -> list:
    """#447: an entity joins a grid's list only after leaving the one it was in."""
    out = []
    collection = Path(rel).name in ("UIEntityCollection.cpp", "EntityCollection3D.cpp")
    for n in walk(tree.root_node):
        if n.type != "call_expression":
            continue
        name = callee_name(src, n)
        if not (ENTITY_LIST_INSERT.search(name) or (collection and SELF_DATA_INSERT.search(name))):
            continue
        fn = outer_function(n)
        if fn is None:
            continue
        before = src[fn.start_byte:n.start_byte].decode("utf8", "replace")
        if "removeFromGrid(" not in before and "removeFromViewport(" not in before:
            out.append(Finding("entity-unlinked", rel, n.start_point[0] + 1,
                               scope_label(src, n), f"{name}() without removeFromGrid/removeFromViewport"))
    return out


ADOPT_CHECK = re.compile(r"\b(canAdopt|can_link)\s*\(")
# link_child() is the helper the checked mutators call; it does not re-check.
ADOPT_HELPERS = {"link_child"}


def check_adopt(src: bytes, tree, rel: str) -> list:
    """#442: every link of a drawable to a parent is preceded, in the same function,
    by the cycle check -- so a new mutator can't forget it."""
    out = []
    for n in walk(tree.root_node):
        if n.type != "call_expression":
            continue
        name = callee_name(src, n)
        args = n.child_by_field_name("arguments")
        argv = [text(src, a).strip() for a in args.named_children] if args is not None else []
        if name == "link_child":
            pass
        elif name.endswith("setParent") and ("->" in name or "." in name):
            if not argv or argv[0] in ("nullptr", "NULL"):
                continue
        else:
            continue
        fn = outer_function(n)
        if fn is None or function_name(src, fn).split("::")[-1] in ADOPT_HELPERS:
            continue
        before = src[fn.start_byte:n.start_byte].decode("utf8", "replace")
        if not ADOPT_CHECK.search(before):
            out.append(Finding("adopt-unchecked", rel, n.start_point[0] + 1,
                               scope_label(src, n), f"{name}() without canAdopt"))
    return out


# A body that reaches THROUGH a wrapper member into the C++ object it points at.
REACHES_IN = re.compile(r"->\s*\w+\s*(->|\.\s*(get|borrow)\b)")
GC_GUARD = re.compile(r"\b(owns_exclusively|traverseWrapper|clearWrapper)\b")


def function_bodies() -> dict:
    """Qualified function name -> body text, across src/ (for tp_traverse = Foo::bar)."""
    global _BODIES
    if _BODIES is not None:
        return _BODIES
    _BODIES = {}
    for p in list((ROOT / "src").rglob("*.cpp")) + list((ROOT / "src").rglob("*.h")):
        src = p.read_bytes()
        for n in walk(_PARSER.parse(src).root_node):
            if n.type == "function_definition":
                _BODIES[function_name(src, n)] = text(src, n)
    return _BODIES


_BODIES = None


def check_traverse(src: bytes, tree, rel: str) -> list:
    """#441: tp_traverse / tp_clear may only touch the wrapped C++ object behind the
    exclusive-ownership guard."""
    out = []
    for n in walk(tree.root_node):
        if n.type != "initializer_pair":
            continue
        slot = text(src, n.children[0]).strip()
        if slot not in (".tp_traverse", ".tp_clear"):
            continue
        value = n.child_by_field_name("value") or n.children[-1]
        if value.type == "lambda_expression":
            body = text(src, value)
        else:
            name = re.sub(r"^\(\s*\w+\s*\)\s*", "", text(src, value).strip())
            body = function_bodies().get(name, "")
        if REACHES_IN.search(body) and not GC_GUARD.search(body):
            decl = n.parent
            while decl is not None and decl.type != "init_declarator":
                decl = decl.parent
            owner = text(src, decl.child_by_field_name("declarator")).strip() if decl else "<type>"
            out.append(Finding("traverse-unguarded", rel, n.start_point[0] + 1, owner,
                               f"{slot} reaches into the C++ object without owns_exclusively"))
    return out


NONTRIVIAL = re.compile(r"\bstd::(shared_ptr|weak_ptr|unique_ptr|string|vector|map|"
                        r"unordered_map|set|unordered_set|list|deque|function|optional)\b")


def struct_fields_by_name() -> dict:
    """typedef struct {...} Name; across src/, mapped to whether it holds C++ members."""
    global _STRUCTS
    if _STRUCTS is not None:
        return _STRUCTS
    _STRUCTS = {}
    for p in (ROOT / "src").rglob("*.h"):
        src = p.read_bytes()
        for n in walk(_PARSER.parse(src).root_node):
            if n.type == "type_definition":
                body = n.child_by_field_name("type")
                if body is None or body.type != "struct_specifier":
                    continue
                for d in n.children_by_field_name("declarator"):
                    _STRUCTS[text(src, d).strip()] = bool(NONTRIVIAL.search(text(src, body)))
    return _STRUCTS


_STRUCTS = None


def check_dealloc(src: bytes, tree, rel: str) -> list:
    """Every PyTypeObject initializer whose tp_basicsize struct has C++ members must set
    tp_dealloc."""
    out = []
    structs = None
    for n in walk(tree.root_node):
        if n.type != "init_declarator":
            continue
        decl = text(src, n)
        if ".tp_basicsize" not in decl or "PyTypeObject" not in text(src, n.parent):
            continue
        m = re.search(r"\.tp_basicsize\s*=\s*sizeof\s*\(\s*(?:\w+::)*(\w+)\s*\)", decl)
        if not m or ".tp_dealloc" in decl:
            continue
        structs = structs if structs is not None else struct_fields_by_name()
        if structs.get(m.group(1)):
            name = text(src, n.child_by_field_name("declarator")).strip()
            out.append(Finding("missing-dealloc", rel, n.start_point[0] + 1, name,
                               f"{m.group(1)} has C++ members but no tp_dealloc"))
    return out


def check_inline_new_refs(src: bytes, call, name: str, argv, add) -> None:
    steals = STEALING_SINKS.get(name)
    if steals == "*":
        return
    if name in FORMAT_APIS and any(
            a.type == "string_literal" and "N" in text(src, a) for a in argv):
        return
    for i, a in enumerate(argv):
        if a.type != "call_expression" or i == steals:
            continue
        inner = callee_name(src, a)
        if NEW_REF_CALL.match(inner):
            add("borrowed-leak", call, f"{name}(..., {inner}(...))")


def check_from_arg(src: bytes, call, add) -> None:
    """The result must be bound to a name that is DECREF'd, returned, or handed to
    an owning holder in the same scope."""
    parent = call.parent
    var = None
    if parent.type == "init_declarator":
        var = text(src, parent.child_by_field_name("declarator")).lstrip("*& ")
    elif parent.type == "assignment_expression":
        var = text(src, parent.child_by_field_name("left")).strip()
    elif parent.type == "return_statement":
        return
    if var is None:
        add("from-arg-owner", call, "PyVector::from_arg(...) result not bound")
        return
    scope = enclosing_scope(call)
    body = text(src, scope) if scope is not None else ""
    owned = re.search(
        r"(Py_X?DECREF|Py_CLEAR)\s*\(\s*(\([^)]*\)\s*)?" + re.escape(var) + r"\s*\)"
        r"|return\s+(\(\s*\w+\s*\*?\s*\)\s*)?" + re.escape(var) + r"\s*;"
        r"|PyRef\w*\s*[({]?\s*\w*\s*[({]\s*" + re.escape(var) + r"\b", body)
    if not owned:
        add("from-arg-owner", call, f"{var} = PyVector::from_arg(...) never released")


PIN_FIELD = re.compile(r"(->|\.)(pyobject|identity_pin|py_identity)$")


def check_pin(src: bytes, tree, rel: str) -> list[Finding]:
    """UIEntity::pyobject (and Entity3D's twin) may only be touched by its owner.
    Everyone else must go through the converter or a collection-membership hook."""
    out = []
    for n in walk(tree.root_node):
        if n.type == "call_expression":
            name = callee_name(src, n)
            if name.endswith("releasePyIdentity") and ("->" in name or "." in name):
                fn = scope_label(src, n)
                # Drawables release through updatePyIdentityPin/releaseChildPins.
                if fn.startswith("UIDrawable::"):
                    continue
                out.append(Finding("pin-direct", rel, n.start_point[0] + 1, fn,
                                   "releasePyIdentity() call"))
        elif n.type == "field_expression" and n.parent.type != "field_expression":
            if not PIN_FIELD.search(text(src, n)):
                continue
            fn = scope_label(src, n)
            if fn in PIN_OWNERS or "dealloc" in fn:
                continue
            # `x->pyobject = <ptr>` is a take, `= nullptr` a release; anything else
            # reads the pin as if it were "the wrapper" (it is null once released).
            p = n.parent
            role = "read"
            if p.type == "assignment_expression" and p.child_by_field_name("left") == n:
                rhs = text(src, p.child_by_field_name("right")).strip()
                role = "release" if rhs in ("nullptr", "NULL") else "take"
            out.append(Finding("pin-direct", rel, n.start_point[0] + 1, fn,
                               f"{role} {text(src, n.child_by_field_name('field'))}"))
    return out


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------


def load_baseline() -> Counter:
    c = Counter()
    if BASELINE.exists():
        for line in BASELINE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            count, _, key = line.partition(" ")
            c[key] += int(count)
    return c


def write_baseline(c: Counter) -> None:
    header = ("# lint_bindings.py allowlist (#430). Each line: <count> rule|file|function|detail.\n"
              "# This list only shrinks: fix a site, then run --update-baseline to drop it.\n"
              "# New code must not add entries (CI fails on any finding not covered here).\n")
    body = "".join(f"{n} {k}\n" for k, n in sorted(c.items()))
    BASELINE.write_text(header + body)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--all", action="store_true", help="list every finding, baselined or not")
    ap.add_argument("--summary", action="store_true", help="counts per rule and per file")
    ap.add_argument("--rule", help="restrict output to one rule")
    ap.add_argument("--json", action="store_true", help="every finding as JSON (with its baseline key)")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--allow-growth", action="store_true",
                    help="with --update-baseline: permit new entries (needs a reason)")
    ap.add_argument("paths", nargs="*", help="files/dirs (default: src/)")
    a = ap.parse_args()

    targets = [Path(p).resolve() for p in a.paths] or [ROOT / "src"]
    files = []
    for t in targets:
        files += [t] if t.is_file() else sorted(
            p for p in t.rglob("*") if p.suffix in (".cpp", ".h", ".hpp"))
    findings = [f for p in files for f in lint_file(p)]
    if a.rule:
        findings = [f for f in findings if f.rule == a.rule]

    current = Counter(f.key for f in findings)
    baseline = load_baseline()

    if a.summary:
        by_rule = Counter(f.rule for f in findings)
        for r, n in by_rule.most_common():
            files_n = len({f.file for f in findings if f.rule == r})
            print(f"{n:5d}  {r}  ({files_n} files)")
        print()
        for fl, n in Counter(f.file for f in findings).most_common(15):
            print(f"{n:5d}  {fl}")
        return 0
    if a.json:
        import json
        print(json.dumps([dict(rule=f.rule, file=f.file, line=f.line, function=f.function,
                               detail=f.detail, key=f.key) for f in findings], indent=1))
        return 0
    if a.all:
        for f in sorted(findings, key=lambda f: (f.rule, f.file, f.line)):
            print(f"{f.file}:{f.line}: [{f.rule}] {f.function}: {f.detail}")
        return 0
    if a.update_baseline:
        grown = current - baseline
        if grown and not a.allow_growth:
            for k, n in grown.items():
                print(f"would ADD {n} {k}", file=sys.stderr)
            print("refusing to grow the baseline (pass --allow-growth if this is deliberate)",
                  file=sys.stderr)
            return 1
        write_baseline(current)
        print(f"baseline: {sum(baseline.values())} -> {sum(current.values())} entries")
        return 0

    new = current - baseline
    stale = baseline - current
    rc = 0
    if new:
        rc = 1
        print("BINDING LINT: new findings (use the cache-aware helpers; see tools/lint_bindings.py):")
        for f in findings:
            if new[f.key] > 0:
                new[f.key] -= 1
                print(f"  {f.file}:{f.line}: [{f.rule}] {f.function}: {f.detail}")
    if stale:
        rc = 1
        print("BINDING LINT: fixed sites still in the baseline -- run "
              "`tools/lint_bindings.py --update-baseline` to drop them:")
        for k, n in sorted(stale.items()):
            print(f"  {n} {k}")
    if rc == 0:
        print(f"BINDING LINT: PASS ({sum(current.values())} baselined sites remain)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
