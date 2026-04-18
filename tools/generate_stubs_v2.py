#!/usr/bin/env python3
"""Generate .pyi type stub files for McRogueFace Python API.

Uses runtime introspection of the compiled mcrfpy module. Signatures are
extracted from the first line of each docstring when present, with a
fallback to (*args, **kwargs) when a class or callable has no signature
declared.

Run via McRogueFace itself so the mcrfpy module is importable:

    ./build/mcrogueface --headless --exec tools/generate_stubs_v2.py
"""

import os
import re
import sys
import types
import inspect
from pathlib import Path

try:
    import mcrfpy
except ImportError:
    print("Error: this script must be run under McRogueFace (needs mcrfpy)")
    sys.exit(1)


# ---------- signature extraction ----------

_SIG_NAME_RE = re.compile(r"^\s*(\w+)\s*\(")
_RET_RE = re.compile(r"^\s*->\s*(.+?)\s*$")


def _parse_balanced_signature(line):
    """Parse 'name(...) -> ret' with proper paren/bracket depth tracking.

    Returns (name, params_text, return_text) or None if not a signature.
    Rejects multi-form signatures like 'foo(x) or foo(y)' by requiring the
    content after the matched closing paren to be empty or '-> X'.
    """
    m = _SIG_NAME_RE.match(line)
    if not m:
        return None
    name = m.group(1)
    i = m.end()  # position right after the opening '('
    depth = 1
    params_start = i
    while i < len(line) and depth:
        c = line[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    if depth != 0:
        return None
    params = line[params_start:i]
    tail = line[i + 1:].strip()
    if not tail:
        return name, params, None
    rm = _RET_RE.match(tail)
    if not rm:
        return None  # trailing 'or foo(...)' or similar, bail out
    return name, params, rm.group(1).strip()


def first_line(doc):
    if not doc:
        return ""
    return doc.strip().split("\n", 1)[0].strip()


def extract_signature(name, doc):
    """Parse 'name(args) -> ret' from the first docstring line.

    Returns (params_str, return_str) or (None, None) if no signature present
    or if the signature is multi-form (e.g. 'foo(x) or foo(y)').
    """
    line = first_line(doc)
    if not line:
        return None, None
    parsed = _parse_balanced_signature(line)
    if parsed is None:
        return None, None
    sig_name, params, ret = parsed
    if sig_name != name:
        return None, None
    return params.strip(), ret


def first_description_paragraph(doc):
    """Return the first non-empty line after a signature line, if any."""
    if not doc:
        return ""
    lines = doc.strip().split("\n")
    start = 1 if lines and _parse_balanced_signature(lines[0].strip()) else 0
    for line in lines[start:]:
        s = line.strip()
        if s:
            return s
    return ""


# ---------- classification ----------

def is_enum_like(cls):
    """True if this class looks like an IntEnum: int subclass with uppercase members."""
    if not issubclass(cls, int):
        return False
    for name, value in cls.__dict__.items():
        if name.isupper() and isinstance(value, cls):
            return True
    return False


def enum_members(cls):
    """Yield (name, int_value) pairs for enum-like classes."""
    for name, value in sorted(cls.__dict__.items()):
        if name.isupper() and isinstance(value, cls):
            yield name, int(value)


def is_method_like(attr):
    return isinstance(attr, (types.BuiltinFunctionType,
                             types.BuiltinMethodType,
                             types.MethodType,
                             types.FunctionType,
                             types.MethodDescriptorType,
                             types.WrapperDescriptorType,
                             types.ClassMethodDescriptorType)) or callable(attr) and not inspect.isclass(attr)


def is_property_descriptor(attr):
    return isinstance(attr, (types.GetSetDescriptorType, types.MemberDescriptorType, property))


# ---------- emitters ----------

def indent(text, n=4):
    pad = " " * n
    return "\n".join(pad + ln if ln else ln for ln in text.split("\n"))


def _sanitize_params(params):
    """Rewrite param forms that are not valid Python syntax.

    - Bare `...` (used in docs to mean "and more kwargs") becomes `**kwargs`.
    - `**kwargs` already present is kept.
    """
    if not params:
        return params
    # Replace a trailing ", ..." or lone "..." with **kwargs
    if params.strip() == "...":
        return "**kwargs"
    # If "..." appears as a token, replace with **kwargs
    tokens = [t.strip() for t in params.split(",")]
    fixed = []
    saw_kwargs = False
    for tok in tokens:
        if tok == "...":
            if not saw_kwargs:
                fixed.append("**kwargs")
                saw_kwargs = True
        else:
            if tok.startswith("**"):
                saw_kwargs = True
            fixed.append(tok)
    return ", ".join(fixed)


def emit_function(name, doc, is_method=False, is_static=False):
    """Emit a def line for a free function or method. Always returns a str
    ending with `: ...` plus an optional one-line docstring."""
    params, ret = extract_signature(name, doc)
    if params is None:
        if is_method:
            params = "self, *args, **kwargs"
        else:
            params = "*args, **kwargs"
    else:
        params = _sanitize_params(params)
        if is_method and not is_static:
            params = "self" + (", " + params if params else "")
    ret = ret or "Any"

    decorator = ("@staticmethod\n" if is_static and is_method else "")
    summary = first_description_paragraph(doc) or first_line(doc)
    # If the signature itself is the only line, there's nothing useful to
    # restate. Strip a summary that exactly matches the signature.
    sig_line = f"{name}({params.replace('self, ', '').replace('self', '')})"
    body = f'"""{escape_docstring(summary)}"""' if summary else "..."
    # Never add duplicate bodies
    if body == "...":
        return f'{decorator}def {name}({params}) -> {ret}: ...'
    return f'{decorator}def {name}({params}) -> {ret}:\n    {body}\n    ...'


def escape_docstring(text):
    # Collapse whitespace and escape triple quotes
    t = " ".join(text.split())
    t = t.replace('"""', "'''")
    if len(t) > 160:
        t = t[:157] + "..."
    return t


# Recognized type words the property parser will accept.
# Lowercase maps directly to a Python typing name. Anything else must
# look like a class name (CapitalCase).
_TYPE_MAPPING = {
    "int": "int",
    "uint": "int",
    "float": "float",
    "bool": "bool",
    "str": "str",
    "string": "str",
    "tuple": "tuple",
    "list": "list",
    "dict": "dict",
    "set": "set",
    "frozenset": "frozenset",
    "bytes": "bytes",
    "any": "Any",
    "callable": "Callable",
    "none": "None",
    "object": "Any",
}


def property_type_hint(doc):
    """Best-effort type inference from a property docstring.

    Accepts the FIRST parenthesized group whose first word is either a
    recognized primitive type or a CapitalCase class name. Skips groups
    like "(width, height)" or "(trigger, data)" that are argument lists
    rather than type declarations.
    """
    if not doc:
        return "Any"
    for m in re.finditer(r"\(([^()]+)\)", doc):
        text = m.group(1).strip()
        first = text.split(",")[0].strip()
        lower = first.lower()
        if lower in _TYPE_MAPPING:
            return _TYPE_MAPPING[lower]
        # Class-like name (starts with capital): accept
        if re.match(r"^[A-Z][A-Za-z0-9_]*$", first):
            return first
        # Union-like text "int | None" etc.
        if "|" in first and all(
            tok.strip().lower() in _TYPE_MAPPING or re.match(r"^[A-Z]", tok.strip())
            for tok in first.split("|")
        ):
            return first
    return "Any"


def property_is_readonly(doc):
    if not doc:
        return False
    return "read-only" in doc.lower() or "readonly" in doc.lower()


def emit_property(name, doc):
    t = property_type_hint(doc)
    summary = first_description_paragraph(doc) or first_line(doc)
    if summary:
        return f'{name}: {t}  # {escape_docstring(summary)}'
    return f'{name}: {t}'


# ---------- class emitter ----------

# Methods inherited from object that we should never emit
_OBJECT_ATTRS = set(dir(object))


def iter_class_members(cls):
    """Yield (name, attr) from cls __dict__ plus inherited members, skipping dunders
    except __init__, and skipping plain object inheritance."""
    seen = set()
    # Walk mro excluding object
    for klass in cls.__mro__:
        if klass is object:
            break
        for name, attr in klass.__dict__.items():
            if name in seen:
                continue
            if name.startswith("__") and name != "__init__":
                continue
            seen.add(name)
            yield name, attr


def emit_class(name, cls):
    """Emit a `class Name:` block for a regular class or IntEnum."""
    bases = []
    if is_enum_like(cls):
        bases.append("IntEnum")

    header = f'class {name}({", ".join(bases)}):' if bases else f'class {name}:'
    doc = cls.__doc__ or ""
    summary = first_description_paragraph(doc) or first_line(doc) or f"{name} type."
    body_lines = [f'"""{escape_docstring(summary)}"""']

    if is_enum_like(cls):
        for m_name, m_val in enum_members(cls):
            body_lines.append(f"{m_name}: int")
        # Enums rarely have other members we need to expose in stubs
        return header + "\n" + indent("\n".join(body_lines))

    # Regular class: emit __init__, methods, properties
    methods = []
    properties = []
    seen_names = set()

    def add_from(klass):
        for attr_name, attr in iter_class_members(klass):
            if attr_name == "__init__" or attr_name in seen_names:
                continue
            if is_property_descriptor(attr):
                pdoc = attr.__doc__ if not isinstance(attr, property) else (attr.fget.__doc__ if attr.fget else "")
                properties.append((attr_name, pdoc or ""))
                seen_names.add(attr_name)
            elif callable(attr):
                if attr_name in _OBJECT_ATTRS:
                    continue
                mdoc = attr.__doc__ or ""
                is_static = isinstance(attr, (types.BuiltinFunctionType,
                                              types.BuiltinMethodType)) and not hasattr(attr, "__self__")
                methods.append((attr_name, mdoc, is_static))
                seen_names.add(attr_name)

    add_from(cls)

    # Merge delegated methods/properties from any inner data class
    delegate = discover_delegate(name, cls)
    if delegate is not None:
        add_from(delegate)

    # __init__: take signature from class doc when possible
    init_params, _ = extract_signature(name, doc)
    if init_params is None:
        init_body = "def __init__(self, *args, **kwargs) -> None: ..."
    else:
        init_body = f"def __init__(self, {init_params}) -> None: ..." if init_params else \
                    "def __init__(self) -> None: ..."
    body_lines.append(init_body)

    for pname, pdoc in sorted(properties):
        body_lines.append(emit_property(pname, pdoc))

    for mname, mdoc, is_static in sorted(methods):
        # Skip dunders we don't have a good signature for
        if mname.startswith("__") and mname != "__init__":
            continue
        body_lines.append(emit_function(mname, mdoc, is_method=True, is_static=is_static))

    if len(body_lines) == 1:
        body_lines.append("...")
    return header + "\n" + indent("\n".join(body_lines))


# ---------- delegation discovery ----------

# Some C types expose methods on an inner "_Data" helper that dir(cls) does
# not see because __getattr__ forwards at the instance level. We probe known
# method names on a live instance to discover the delegate type and merge its
# surface into the stub.
_DELEGATION_PROBES = (
    "center_camera",  # Grid/GridView -> _GridData
    "camera_rotation",
    "add_collision_label",
    "entities",
    "compute_fov",
    "add_layer",
    "apply_threshold",
)

_DELEGATE_CLASS_FACTORIES = {
    # class_name: callable returning a live instance, or None to skip
    "Grid": lambda: mcrfpy.Grid(grid_size=(2, 2)),
    "GridView": lambda: mcrfpy.GridView(grid=mcrfpy.Grid(grid_size=(2, 2))),
}


def discover_delegate(cls_name, cls):
    """Return a delegate type if `cls` forwards known method names to it, else None."""
    factory = _DELEGATE_CLASS_FACTORIES.get(cls_name)
    if factory is None:
        return None
    try:
        inst = factory()
    except Exception:
        return None
    for probe in _DELEGATION_PROBES:
        try:
            m = getattr(inst, probe, None)
        except Exception:
            continue
        if callable(m) and hasattr(m, "__self__"):
            s_type = type(m.__self__)
            if s_type is not cls:
                return s_type
    return None


# ---------- submodule (automation) ----------

def emit_submodule(mod_name, mod):
    lines = [f"class _{mod_name}_module:"]
    body = [f'"""Stub for mcrfpy.{mod_name} submodule."""']
    for name in sorted(dir(mod)):
        if name.startswith("_"):
            continue
        attr = getattr(mod, name)
        if callable(attr):
            body.append(emit_function(name, attr.__doc__ or "", is_method=True, is_static=True))
    if len(body) == 1:
        body.append("...")
    lines.append(indent("\n".join(body)))
    lines.append(f"{mod_name}: _{mod_name}_module")
    return "\n".join(lines)


# ---------- main entry ----------

HEADER = '''"""Type stubs for McRogueFace Python API.

Auto-generated by tools/generate_stubs_v2.py via runtime introspection.
Do not edit by hand -- regenerate after API changes:

    make && ./tools/generate_all_docs.sh
"""

from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, overload
'''


def classify_module():
    classes = {}
    functions = {}
    constants = {}
    submodules = {}
    for name in sorted(dir(mcrfpy)):
        if name.startswith("_"):
            continue
        attr = getattr(mcrfpy, name)
        if isinstance(attr, types.ModuleType):
            submodules[name] = attr
        elif inspect.isclass(attr):
            classes[name] = attr
        elif callable(attr):
            functions[name] = attr
        else:
            constants[name] = attr
    return classes, functions, constants, submodules


def main():
    classes, functions, constants, submodules = classify_module()

    out_lines = [HEADER]

    # Emit classes (enums first so forward-reference order is sensible)
    enum_names = [n for n, c in classes.items() if is_enum_like(c)]
    other_names = [n for n in classes if n not in enum_names]

    out_lines.append("# --- Enums --------------------------------------------------------------")
    for n in sorted(enum_names):
        out_lines.append(emit_class(n, classes[n]))
        out_lines.append("")

    out_lines.append("# --- Classes ------------------------------------------------------------")
    for n in sorted(other_names):
        out_lines.append(emit_class(n, classes[n]))
        out_lines.append("")

    out_lines.append("# --- Submodules ---------------------------------------------------------")
    for n in sorted(submodules):
        out_lines.append(emit_submodule(n, submodules[n]))
        out_lines.append("")

    out_lines.append("# --- Module-level functions ---------------------------------------------")
    for n in sorted(functions):
        fn = functions[n]
        out_lines.append(emit_function(n, fn.__doc__ or ""))

    out_lines.append("")
    out_lines.append("# --- Module-level constants ---------------------------------------------")
    for n in sorted(constants):
        v = constants[n]
        t = type(v).__name__
        out_lines.append(f"{n}: {t}")

    out_text = "\n".join(out_lines).rstrip() + "\n"

    stubs_dir = Path("stubs")
    stubs_dir.mkdir(exist_ok=True)
    (stubs_dir / "mcrfpy.pyi").write_text(out_text)
    (stubs_dir / "py.typed").write_text("")

    print(f"Wrote stubs/mcrfpy.pyi ({len(out_text)} bytes, "
          f"{len(classes)} classes, {len(functions)} functions, "
          f"{len(constants)} constants, {len(submodules)} submodules)")


if __name__ == "__main__":
    main()
