"""fuzz_shader_bindings - shader uniform binding lifetime fuzzing (#312, Tier A).

Targets the exact pattern that produced #270 / #271 / #277: uniform bindings and
the UniformCollection are lifetime-coupled to a Drawable via weak_ptr, and the
binding/collection can outlive the Drawable. This hammers create -> bind ->
destroy-target -> evaluate sequences.

Surface (verified against src/PyUniformBinding.cpp, src/PyUniformCollection.cpp,
src/PyShader.cpp, src/UIDrawable.cpp):
    drawable.uniforms                      -> UniformCollection (weak_ptr owner)
    uniforms[name] = float | (x,y[,z[,w]]) | PropertyBinding | CallableBinding
    PropertyBinding(target, property)      -- weak_ptr<UIDrawable> target
    CallableBinding(callable)              -- Python callable, evaluated lazily
    drawable.shader = Shader(frag_src)     -- requires GL; degrades gracefully

If sf::Shader::isAvailable() is false in the windowless fuzz build, Shader()
raises RuntimeError (PyShader.cpp:82) which is swallowed -- but the binding /
UniformCollection bookkeeping (where the bugs lived) runs regardless of whether
a GLSL program actually compiles. Drawables are kept DETACHED (never appended to
a scene) so that `del` drops the last shared_ptr and the weak_ptr safety paths
are actually taken.

Contract: fuzz_one_input(data: bytes) -> None.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS, safe_reset

MAX_OPS = 24

# Animatable float properties shared widely enough to satisfy hasProperty()
# on most drawables; invalid pairings raise ValueError and are swallowed.
PROP_NAMES = ("x", "y", "opacity", "w", "h", "z_index", "radius", "thickness",
              "rotation", "outline", "not_a_real_property")

GOOD_FRAG = (
    "uniform float u; void main(){ gl_FragColor = vec4(u,0.0,0.0,1.0); }"
)
BAD_FRAG = "this is not glsl {{{"


def make_drawable(stream):
    """Construct one DETACHED drawable (not added to any scene)."""
    which = stream.u8() % 7
    try:
        if which == 0:
            return mcrfpy.Frame(pos=(0, 0), size=(10, 10))
        if which == 1:
            return mcrfpy.Caption((0, 0), None, "x")
        if which == 2:
            return mcrfpy.Sprite(pos=(0, 0))
        if which == 3:
            return mcrfpy.Grid(grid_size=(4, 4))
        if which == 4:
            return mcrfpy.Line(start=(0, 0), end=(5, 5))
        if which == 5:
            return mcrfpy.Circle(center=(0, 0), radius=4.0)
        return mcrfpy.Arc(center=(0, 0), radius=4.0, start_angle=0.0, end_angle=90.0)
    except EXPECTED_EXCEPTIONS:
        return None


def uniform_value(stream, target):
    """Return a value to assign into a uniform slot."""
    sel = stream.u8() % 7
    if sel == 0:
        return stream.float_in_range(-1e6, 1e6)
    if sel == 1:
        return (stream.float_in_range(-1, 1), stream.float_in_range(-1, 1))
    if sel == 2:
        return tuple(stream.float_in_range(-1, 1) for _ in range(3))
    if sel == 3:
        return tuple(stream.float_in_range(-1, 1) for _ in range(4))
    if sel == 4 and target is not None:
        # PropertyBinding back to the target drawable (or another one).
        return ("propbind", stream.pick_one(PROP_NAMES))
    if sel == 5:
        return ("callbind", stream.u8() % 3)
    # Deliberately wrong shapes.
    return stream.pick_one((None, "str", (), (1, 2, 3, 4, 5), {"x": 1}))


def _callable_for(kind):
    if kind == 0:
        return lambda: 1.0
    if kind == 1:
        return lambda: (_ for _ in ()).throw(ValueError("boom"))  # raises on call
    return lambda: "not a float"                                   # wrong return type


def set_uniform(stream, drawable, name):
    raw = uniform_value(stream, drawable)
    value = raw
    try:
        if isinstance(raw, tuple) and len(raw) == 2 and raw[0] == "propbind":
            value = mcrfpy.PropertyBinding(drawable, raw[1])
        elif isinstance(raw, tuple) and len(raw) == 2 and raw[0] == "callbind":
            value = mcrfpy.CallableBinding(_callable_for(raw[1]))
    except EXPECTED_EXCEPTIONS:
        return None
    try:
        drawable.uniforms[name] = value
    except EXPECTED_EXCEPTIONS:
        pass
    return value if isinstance(value, (mcrfpy.PropertyBinding, mcrfpy.CallableBinding)) else None


def read_uniforms(drawable, names):
    try:
        coll = drawable.uniforms
    except EXPECTED_EXCEPTIONS:
        return
    try:
        _ = len(coll)
    except (TypeError, ValueError, AttributeError):
        pass
    for name in names:
        try:
            _ = coll[name]
        except EXPECTED_EXCEPTIONS:
            pass
    try:
        for _k in coll:
            pass
    except EXPECTED_EXCEPTIONS:
        pass


def read_binding(binding):
    """Read a binding after its target may have died (the safety check)."""
    if binding is None:
        return
    for name in ("value", "is_valid", "target", "property", "callable"):
        try:
            _ = getattr(binding, name)
        except EXPECTED_EXCEPTIONS:
            pass
    try:
        repr(binding)
    except EXPECTED_EXCEPTIONS:
        pass


def try_assign_shader(stream, drawable):
    src = GOOD_FRAG if stream.bool() else BAD_FRAG
    try:
        sh = mcrfpy.Shader(src, bool(stream.bool()))
    except EXPECTED_EXCEPTIONS:
        return
    try:
        drawable.shader = sh
    except EXPECTED_EXCEPTIONS:
        pass


def fuzz_lifecycle(stream):
    """The core lifetime pattern: bind to a target, drop it, then evaluate."""
    target = make_drawable(stream)
    if target is None:
        return
    if stream.bool():
        try_assign_shader(stream, target)
    bindings = []
    names = []
    for _ in range(stream.int_in_range(1, 5)):
        name = stream.ascii_str(6) or "u"
        names.append(name)
        b = set_uniform(stream, target, name)
        if b is not None:
            bindings.append(b)
    read_uniforms(target, names)
    # Drop the only strong ref to the target while bindings/collection persist.
    if stream.bool():
        try:
            coll = target.uniforms        # keep the collection alive past target
        except EXPECTED_EXCEPTIONS:
            coll = None
        del target
        for b in bindings:
            read_binding(b)
        if coll is not None:
            for name in names:
                try:
                    _ = coll[name]
                except EXPECTED_EXCEPTIONS:
                    pass
    else:
        del target
        for b in bindings:
            read_binding(b)


def fuzz_one_input(data):
    stream = ByteStream(data)
    try:
        n = stream.int_in_range(1, MAX_OPS)
        for _ in range(n):
            if stream.remaining < 1:
                break
            fuzz_lifecycle(stream)
    except EXPECTED_EXCEPTIONS:
        pass
