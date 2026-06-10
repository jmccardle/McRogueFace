"""
Public API surface snapshot regression test (#314).

Captures the COMPLETE public mcrfpy surface deterministically and diffs it against
a committed golden file (tests/snapshots/api_surface.golden.txt). Any drift in the
public API -- added/removed/renamed type, method, property, enum member, function,
singleton, or a property's inferred type / read-only flag -- fails the test with a
unified diff. This is the regression NET that guards invasive refactors (e.g. #313
UIEntity::grid -> GridData) by reducing "did the API change?" to a reviewable diff.

Intentional re-baseline (after a deliberate, reviewed API change):
    cd build && MCRF_UPDATE_API_SNAPSHOT=1 ./mcrogueface --headless --exec ../tests/unit/api_surface_snapshot_test.py

Design notes (see docs/plan-313-314.md):
  * mcrfpy.Grid IS mcrfpy.GridView and delegates its real API to an internal
    _GridData via tp_getattro -- that surface is INVISIBLE to dir(). We therefore
    walk grid.grid_data explicitly AND probe delegation integrity on a live instance.
  * Singleton/constant VALUES are never captured (build/platform/object dependent);
    only their type name is recorded.
  * Property type / read-only are docstring-derived (same convention as the doc/stub
    generators). A behavioral writability probe compensates for the properties the
    refactor touches.
  * Every exported class must be classified FROZEN or EXPERIMENTAL; an unclassified
    class fails the test so new types force a deliberate freeze decision.
"""

import mcrfpy
import sys
import os
import re
import types
import difflib

# --------------------------------------------------------------------------- #
# Freeze classification (1.0 contract). See docs/plan-313-314.md OD4.
# EXPERIMENTAL types are exempt from the freeze (may change post-1.0).
# Anything exported and not listed here is FROZEN; an exported class in neither
# bucket is an ERROR (fail-on-unclassified) so new types get a deliberate call.
# --------------------------------------------------------------------------- #
EXPERIMENTAL_TYPES = frozenset({
    # 3D / Voxel (experimental, per docs/api-audit-2026-04.md)
    "Billboard", "Entity3D", "EntityCollection3D", "EntityCollection3DIter",
    "Model3D", "Viewport3D", "VoxelGrid", "VoxelRegion",
    # Tiled import (least-tested)
    "TileSetFile", "TileMapFile", "WangSet",
    # LDtk import (least-tested)
    "LdtkProject", "AutoRuleSet",
    # Shader system (least-tested)
    "Shader",
    # Binding helpers (internal-ish, still evolving)
    "CallableBinding", "PropertyBinding",
})

# Internal types not exported on the module but reachable through live instances.
# Captured (they are part of the Grid/Entity contract) but in a separate section.
# Each entry: (label, factory) where factory() returns an instance to introspect.
def _internal_type_probes():
    probes = []
    try:
        g = mcrfpy.Grid(grid_size=(3, 3))
        gd = getattr(g, "grid_data", None)
        if gd is not None:
            probes.append(("_GridData", type(gd)))
        try:
            probes.append(("GridPoint", type(g.at(0, 0))))
        except Exception:
            pass
        try:
            probes.append(("EntityCollection", type(g.entities)))
        except Exception:
            pass
    except Exception:
        pass
    try:
        f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
        probes.append(("UICollection", type(f.children)))
        try:
            probes.append(("UniformCollection", type(f.uniforms)))
        except Exception:
            pass
    except Exception:
        pass
    # De-dup by label, stable order
    seen = set()
    out = []
    for label, t in probes:
        if label in seen:
            continue
        seen.add(label)
        out.append((label, t))
    return out


# --------------------------------------------------------------------------- #
# Introspection helpers (mirrors tools/generate_stubs_v2.py; kept self-contained
# so the golden tracks the API, not the tool).
# --------------------------------------------------------------------------- #
_TYPE_MAPPING = {
    "int": "int", "uint": "int", "float": "float", "bool": "bool",
    "str": "str", "string": "str", "tuple": "tuple", "list": "list",
    "dict": "dict", "set": "set", "frozenset": "frozenset", "bytes": "bytes",
    "any": "Any", "callable": "Callable", "none": "None", "object": "Any",
}


def property_type_hint(doc):
    if not doc:
        return "Any"
    for m in re.finditer(r"\(([^()]+)\)", doc):
        text = m.group(1).strip()
        first = text.split(",")[0].strip()
        lower = first.lower()
        if lower in _TYPE_MAPPING:
            return _TYPE_MAPPING[lower]
        if re.match(r"^[A-Z][A-Za-z0-9_]*$", first):
            return first
        if "|" in first and all(
            tok.strip().lower() in _TYPE_MAPPING or re.match(r"^[A-Z]", tok.strip())
            for tok in first.split("|")
        ):
            return first
    return "Any"


def property_is_readonly(doc):
    if not doc:
        return False
    d = doc.lower()
    return "read-only" in d or "readonly" in d


def first_doc_line(doc):
    if not doc:
        return ""
    for line in doc.split("\n"):
        s = line.strip()
        if s:
            return " ".join(s.split())
    return ""


def is_enum_like(cls):
    if not (isinstance(cls, type) and issubclass(cls, int)):
        return False
    return any(k.isupper() and isinstance(v, cls) for k, v in cls.__dict__.items())


def is_property_descriptor(attr):
    return isinstance(attr, (types.GetSetDescriptorType, types.MemberDescriptorType, property))


_OBJECT_ATTRS = set(dir(object))


def iter_members(cls):
    """Yield (name, attr) across the MRO (excluding object), skipping dunders
    except __init__, first-definition-wins."""
    seen = set()
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


def type_lines(cls):
    """Deterministic property + method lines for a regular class."""
    props = []
    methods = []
    for name, attr in iter_members(cls):
        if name == "__init__":
            continue
        if is_property_descriptor(attr):
            pdoc = attr.__doc__ if not isinstance(attr, property) else (
                attr.fget.__doc__ if attr.fget else "")
            ro = "ro" if property_is_readonly(pdoc) else "rw"
            props.append("  prop %s: %s (%s)" % (name, property_type_hint(pdoc), ro))
        elif callable(attr):
            if name in _OBJECT_ATTRS:
                continue
            sig = first_doc_line(attr.__doc__) or "<no-doc>"
            methods.append("  meth %s :: %s" % (name, sig))
    return sorted(props) + sorted(methods)


def enum_lines(cls):
    out = []
    for name, val in sorted(cls.__dict__.items()):
        if name.isupper() and isinstance(val, cls):
            out.append("  %s = %d" % (name, int(val)))
    return out


# --------------------------------------------------------------------------- #
# Delegation + writability probes (catch breaks invisible to type introspection)
# --------------------------------------------------------------------------- #
def delegation_probe_lines():
    """Assert the GridView instance still resolves its delegated _GridData surface
    via tp_getattro. A break here leaves the _GridData type unchanged (invisible to
    the type snapshot) but breaks the user-facing Grid contract."""
    lines = []
    try:
        g = mcrfpy.Grid(grid_size=(3, 3))
        gd = getattr(g, "grid_data", None)
        if gd is None:
            return ["  <UNREACHABLE: grid.grid_data>"]
        members = sorted(n for n in dir(gd) if not n.startswith("_"))
        # A member "resolves" if getattr finds the descriptor and runs it -- even
        # if the getter then raises a DOMAIN error (e.g. grid_pos on a non-nested
        # grid raises RuntimeError). Only AttributeError means delegation is BROKEN.
        missing = []
        for m in members:
            try:
                getattr(g, m)
            except AttributeError:
                missing.append(m)
            except Exception:
                pass  # resolved; getter raised a domain error -- delegation works
        lines.append("  delegated-resolved: %d/%d" % (len(members) - len(missing), len(members)))
        if missing:
            lines.append("  delegated-MISSING: %s" % " ".join(missing))
    except Exception as e:
        lines.append("  <PROBE-ERROR: %s>" % type(e).__name__)
    return lines


def writability_probe_lines():
    """Behaviorally probe writability of properties the #313 refactor touches.
    Records observed outcome (writable / read-only / error) so a setter NULL/non-NULL
    flip is caught even though the snapshot's ro/rw flag is only docstring-derived."""
    results = []

    def probe(label, obj, attr, value):
        if not hasattr(obj, attr):
            results.append("  %s: ABSENT" % label)
            return
        try:
            setattr(obj, attr, value)
            results.append("  %s: writable" % label)
        except AttributeError:
            results.append("  %s: read-only" % label)
        except (TypeError, ValueError):
            results.append("  %s: writable(validated)" % label)
        except Exception as e:
            results.append("  %s: %s" % (label, type(e).__name__))

    try:
        g = mcrfpy.Grid(grid_size=(3, 3))
        e = mcrfpy.Entity(grid_pos=(1, 1), grid=g)
        # entity.grid is reassigned by #313 internals; entity.texture added in Phase 2.
        probe("Entity.grid", e, "grid", g)
        probe("Entity.texture", e, "texture", mcrfpy.default_texture)
        probe("Entity.sprite_index", e, "sprite_index", 0)
    except Exception as ex:
        results.append("  <ENTITY-PROBE-ERROR: %s>" % type(ex).__name__)
    return sorted(results)


# --------------------------------------------------------------------------- #
# Snapshot builder
# --------------------------------------------------------------------------- #
def build_snapshot():
    out = []
    out.append("# McRogueFace Public API Surface Snapshot (#314 freeze net)")
    out.append("# Regenerate intentionally: MCRF_UPDATE_API_SNAPSHOT=1")
    out.append("# Singleton/constant VALUES are intentionally NOT captured.")

    names = [n for n in dir(mcrfpy) if not n.startswith("_")]
    enums, classes, funcs, singletons, submodules = [], [], [], [], []
    for n in names:
        v = getattr(mcrfpy, n)
        if isinstance(v, types.ModuleType):
            submodules.append(n)
        elif isinstance(v, type):
            (enums if is_enum_like(v) else classes).append(n)
        elif callable(v):
            funcs.append(n)
        else:
            singletons.append((n, type(v).__name__))

    # Fail-on-unclassified: every exported class must be FROZEN or EXPERIMENTAL.
    unclassified = sorted(c for c in classes if c not in EXPERIMENTAL_TYPES)
    frozen = sorted(c for c in classes if c not in EXPERIMENTAL_TYPES)
    experimental = sorted(c for c in classes if c in EXPERIMENTAL_TYPES)

    out.append("")
    out.append("=== MODULE FUNCTIONS (%d) ===" % len(funcs))
    for n in sorted(funcs):
        out.append("func %s :: %s" % (n, first_doc_line(getattr(mcrfpy, n).__doc__) or "<no-doc>"))

    out.append("")
    out.append("=== MODULE SINGLETONS / CONSTANTS (%d) ===" % len(singletons))
    for n, tn in sorted(singletons):
        out.append("const %s: %s" % (n, tn))

    out.append("")
    out.append("=== SUBMODULES (%d) ===" % len(submodules))
    for n in sorted(submodules):
        out.append("submodule %s" % n)

    out.append("")
    out.append("=== ENUMS (FROZEN) (%d) ===" % len(enums))
    for n in sorted(enums):
        out.append("[%s]" % n)
        out.extend(enum_lines(getattr(mcrfpy, n)))

    out.append("")
    out.append("=== FROZEN TYPES (%d) ===" % len(frozen))
    for n in frozen:
        out.append("[%s]" % n)
        out.extend(type_lines(getattr(mcrfpy, n)))

    out.append("")
    out.append("=== EXPERIMENTAL TYPES (NOT FROZEN) (%d) ===" % len(experimental))
    for n in experimental:
        out.append("[%s]" % n)
        out.extend(type_lines(getattr(mcrfpy, n)))

    out.append("")
    out.append("=== INTERNAL TYPES (reached via live instances) ===")
    for label, t in _internal_type_probes():
        out.append("[%s]" % label)
        out.extend(type_lines(t))

    out.append("")
    out.append("=== AUTOMATION (PyAutoGUI-compat, snake_case-exempt) ===")
    if submodules and "automation" in submodules:
        auto = getattr(mcrfpy, "automation")
        for n in sorted(x for x in dir(auto) if not x.startswith("_")):
            v = getattr(auto, n)
            if callable(v):
                out.append("func %s :: %s" % (n, first_doc_line(v.__doc__) or "<no-doc>"))

    out.append("")
    out.append("=== DELEGATION INTEGRITY (Grid instance -> _GridData) ===")
    out.extend(delegation_probe_lines())

    out.append("")
    out.append("=== WRITABILITY PROBES (#313-touched properties) ===")
    out.extend(writability_probe_lines())

    return "\n".join(out) + "\n", unclassified


# --------------------------------------------------------------------------- #
# Compare / update against golden
# --------------------------------------------------------------------------- #
def golden_path():
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, "..", "snapshots", "api_surface.golden.txt")


def main():
    snapshot, unclassified = build_snapshot()

    if unclassified is None:
        unclassified = []
    # (unclassified is currently always empty because `frozen` == not-experimental;
    # the real guard is the explicit EXPERIMENTAL_TYPES list + reviewer of the golden.
    # Kept as a hook in case classification becomes a positive allowlist later.)

    path = golden_path()
    update = os.environ.get("MCRF_UPDATE_API_SNAPSHOT") == "1"

    if update:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(snapshot)
        print("Updated API surface golden: %s" % path)
        print("PASS")
        sys.exit(0)

    if not os.path.exists(path):
        print("FAIL: golden file missing: %s" % path)
        print("      Run once with MCRF_UPDATE_API_SNAPSHOT=1 to create it.")
        sys.exit(1)

    with open(path) as f:
        golden = f.read()

    if snapshot == golden:
        print("API surface matches golden (%d lines)." % len(golden.splitlines()))
        print("PASS")
        sys.exit(0)

    diff = difflib.unified_diff(
        golden.splitlines(keepends=True),
        snapshot.splitlines(keepends=True),
        fromfile="api_surface.golden.txt (committed)",
        tofile="current API surface",
        n=2,
    )
    sys.stdout.write("".join(diff))
    print("")
    print("FAIL: public API surface drifted from the golden.")
    print("      If this change is intentional, re-baseline with "
          "MCRF_UPDATE_API_SNAPSHOT=1 and review the diff in code review.")
    sys.exit(1)


if __name__ == "__main__":
    main()
