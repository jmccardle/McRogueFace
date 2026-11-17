"""#528: the TileLayer/ColorLayer class docstrings must not advertise call shapes that
raise. Exec the Example: block of each (it must contain real code), reject the stale
(x, y, ...) shapes, and check the constructor header line is callable as it reads."""
import re, sys, textwrap
import mcrfpy

STALE = ("set(x, y", "fill_rect(x, y, w, h")
# Real constructor keyword order (src/GridLayers.cpp kwlist); the docstring header
# must list exactly these, and positional calls in this order must work.
EXPECTED = {
    "ColorLayer": ["name", "z_index", "grid_size", "grid"],
    "TileLayer": ["name", "z_index", "texture", "grid_size", "grid"],
}
fails = []

def example_lines(doc):
    m = re.search(r"^Example:\n((?:[ \t]+\S.*\n?|[ \t]*\n)+)", doc, re.M)
    if not m:
        return None
    return textwrap.dedent(m.group(1))

def header_params(doc):
    m = re.match(r"(\w+)\((.*)\)\n", doc)
    if not m:
        return None, None
    return m.group(1), [p.split("=")[0].strip() for p in m.group(2).split(",") if p.strip()]

for cls in (mcrfpy.TileLayer, mcrfpy.ColorLayer):
    n = cls.__name__
    doc = cls.__doc__
    for s in STALE:
        if s in doc:
            fails.append(f"{n}: stale call shape {s!r} in docstring")

    code = example_lines(doc)
    if code is None:
        fails.append(f"{n}: no Example: block")
    elif not [l for l in code.splitlines() if l.strip()]:
        fails.append(f"{n}: Example: block has no code lines")
    else:
        try:
            exec(compile(code, f"<{n} Example>", "exec"), {"mcrfpy": mcrfpy})
        except Exception as e:
            fails.append(f"{n}: Example raised {type(e).__name__}: {e}")

    # constructor header: names in the real order...
    hname, params = header_params(doc)
    if hname != n:
        fails.append(f"{n}: docstring does not start with a '{n}(...)' header line")
    elif params != EXPECTED[n]:
        fails.append(f"{n}: header parameters {params} != real order {EXPECTED[n]}")
    # ...and the header, read positionally, constructs what it says
    try:
        if n == "TileLayer":
            lay = cls("t", -2, mcrfpy.default_texture, (4, 3))
        else:
            lay = cls("c", -1, (4, 3))
        if lay.name not in ("t", "c") or lay.z_index not in (-2, -1) or lay.grid_size != (4, 3):
            fails.append(f"{n}: positional construction gave name={lay.name!r} "
                         f"z_index={lay.z_index!r} grid_size={lay.grid_size!r}")
    except Exception as e:
        fails.append(f"{n}: positional construction raised {type(e).__name__}: {e}")
    # every documented Args: name is a real keyword
    for p in EXPECTED[n]:
        if not re.search(rf"^    {p} \(", doc, re.M):
            fails.append(f"{n}: Args section does not document {p!r}")

if fails:
    for f in fails:
        print("FAIL", f)
    sys.exit(1)
print("PASS")
sys.exit(0)
