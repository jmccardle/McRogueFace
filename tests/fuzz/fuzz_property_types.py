"""fuzz_property_types - property getter/setter fuzzing across all UI types.

Targets:
    #267 - PyObject_GetAttrString reference leaks (60+ sites)
    #268 - sfVector2f_to_PyObject NULL deref on bad Vector setters
    #272 - UniformCollection unchecked weak_ptr

Strategy:
    Each iteration creates a mix of Frame/Caption/Sprite/Grid/Entity/
    TileLayer/ColorLayer/Color/Vector instances and hammers their
    properties with both correct-type values (stressing refcount sites)
    and deliberately wrong-type values (stressing setter error paths).

    Hot-loop repeated GetAttrString reads exercise the #267 refcount
    site density. Wrong-type writes exercise #268 and setter NULL
    returns. Nested frame + reparenting stresses parent/children bookkeeping.

Contract: fuzz_one_input(data: bytes) -> None, wrapped in EXPECTED_EXCEPTIONS.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS, safe_reset

MAX_OPS = 40
HOT_LOOP = 60

# Property groups verified against src/UIFrame.cpp, src/UICaption.cpp,
# src/UISprite.cpp, src/UIGridPyProperties.cpp, src/UIEntity.cpp,
# src/GridLayers.cpp, src/PyColor.cpp, src/PyVector.cpp.

FRAME_FLOAT_PROPS = ("x", "y", "w", "h", "outline", "opacity", "rotation")
FRAME_INT_PROPS = ("z_index",)
FRAME_BOOL_PROPS = ("visible", "clip_children", "cache_subtree")
FRAME_COLOR_PROPS = ("fill_color", "outline_color")
FRAME_VECTOR_PROPS = ("pos", "origin")
FRAME_STR_PROPS = ("name",)
FRAME_ALL_READ = (
    FRAME_FLOAT_PROPS + FRAME_INT_PROPS + FRAME_BOOL_PROPS
    + FRAME_COLOR_PROPS + FRAME_VECTOR_PROPS + FRAME_STR_PROPS
    + ("children", "parent", "global_position", "bounds", "global_bounds",
       "hovered", "shader", "uniforms", "align", "margin",
       "horiz_margin", "vert_margin")
)

CAPTION_FLOAT_PROPS = ("x", "y", "outline", "opacity", "rotation", "font_size")
CAPTION_INT_PROPS = ("z_index",)
CAPTION_BOOL_PROPS = ("visible",)
CAPTION_COLOR_PROPS = ("fill_color", "outline_color")
CAPTION_VECTOR_PROPS = ("pos", "origin")
CAPTION_STR_PROPS = ("name", "text")

SPRITE_FLOAT_PROPS = ("x", "y", "scale", "scale_x", "scale_y", "opacity", "rotation")
SPRITE_INT_PROPS = ("z_index", "sprite_index")
SPRITE_BOOL_PROPS = ("visible",)
SPRITE_VECTOR_PROPS = ("pos", "origin")
SPRITE_STR_PROPS = ("name",)

GRID_FLOAT_PROPS = ("x", "y", "w", "h", "center_x", "center_y", "zoom",
                    "camera_rotation", "opacity", "rotation")
GRID_INT_PROPS = ("z_index", "fov_radius")
GRID_BOOL_PROPS = ("visible", "perspective_enabled")
GRID_VECTOR_PROPS = ("pos", "size", "center", "origin")
GRID_COLOR_PROPS = ("fill_color",)
GRID_STR_PROPS = ("name",)

ENTITY_FLOAT_PROPS = ("x", "y", "opacity", "move_speed")
ENTITY_INT_PROPS = ("sprite_index", "cell_x", "cell_y", "grid_x", "grid_y",
                    "tile_width", "tile_height", "default_behavior",
                    "turn_order", "sight_radius")
ENTITY_BOOL_PROPS = ("visible",)
ENTITY_VECTOR_PROPS = ("pos", "cell_pos", "grid_pos", "draw_pos",
                       "sprite_offset", "tile_size")
ENTITY_STR_PROPS = ("name", "target_label")

TILELAYER_INT_PROPS = ("z_index",)
TILELAYER_BOOL_PROPS = ("visible",)

COLORLAYER_INT_PROPS = ("z_index",)
COLORLAYER_BOOL_PROPS = ("visible",)

# Tier C (#312): primitive shapes (Line/Circle/Arc) -- their setters were never
# touched by the property-type fuzzer. Verified against src/UILine.cpp,
# src/UICircle.cpp, src/UIArc.cpp.
LINE_FLOAT_PROPS = ("x", "y", "thickness", "opacity", "rotation")
LINE_INT_PROPS = ("z_index",)
LINE_BOOL_PROPS = ("visible",)
LINE_COLOR_PROPS = ("color",)
LINE_VECTOR_PROPS = ("start", "end", "pos")
LINE_STR_PROPS = ("name",)

CIRCLE_FLOAT_PROPS = ("x", "y", "radius", "outline", "opacity", "rotation")
CIRCLE_INT_PROPS = ("z_index",)
CIRCLE_BOOL_PROPS = ("visible",)
CIRCLE_COLOR_PROPS = ("fill_color", "outline_color")
CIRCLE_VECTOR_PROPS = ("center", "pos")
CIRCLE_STR_PROPS = ("name",)

ARC_FLOAT_PROPS = ("x", "y", "radius", "start_angle", "end_angle", "thickness",
                   "opacity", "rotation")
ARC_INT_PROPS = ("z_index",)
ARC_BOOL_PROPS = ("visible",)
ARC_COLOR_PROPS = ("color",)
ARC_VECTOR_PROPS = ("center", "pos")
ARC_STR_PROPS = ("name",)


def confused_value(stream):
    """Return a deliberately type-confused value for property setters.

    Every branch returns something that is the 'wrong shape' for at
    least one real setter. The fuzz loop catches TypeError/ValueError
    so this flushes out places where setters NULL-deref or leak refs
    on bad input rather than raising cleanly.
    """
    which = stream.u8() % 12
    if which == 0:
        return None
    if which == 1:
        return stream.int_in_range(-1_000_000, 1_000_000)
    if which == 2:
        return stream.float_in_range(-1e9, 1e9)
    if which == 3:
        return stream.ascii_str(12)
    if which == 4:
        return stream.bool()
    if which == 5:
        return ()
    if which == 6:
        return (stream.float_in_range(-100, 100), stream.float_in_range(-100, 100))
    if which == 7:
        return [stream.u8() for _ in range(stream.int_in_range(0, 5))]
    if which == 8:
        return {"x": 1, "y": 2}
    if which == 9:
        # Incomplete color tuple - exercises PyColor::fromPy error paths
        return (stream.int_in_range(-50, 300), stream.int_in_range(-50, 300), stream.int_in_range(-50, 300))
    if which == 10:
        # float specials that can surprise clamping / isnan checks
        variant = stream.u8() % 4
        if variant == 0:
            return float("inf")
        if variant == 1:
            return float("-inf")
        if variant == 2:
            return float("nan")
        return 0.0
    return object()  # bare object with no protocol


def _safe_texture():
    """Return mcrfpy.default_texture or None. Never raises."""
    try:
        return getattr(mcrfpy, "default_texture", None)
    except Exception:
        return None


def _make_frame(stream):
    x = stream.float_in_range(-200, 800)
    y = stream.float_in_range(-200, 800)
    w = stream.float_in_range(1, 400)
    h = stream.float_in_range(1, 400)
    return mcrfpy.Frame(pos=(x, y), size=(w, h))


def _make_caption(stream):
    x = stream.float_in_range(-200, 800)
    y = stream.float_in_range(-200, 800)
    text = stream.ascii_str(20)
    return mcrfpy.Caption(text=text, pos=(x, y))


def _make_sprite(stream):
    x = stream.float_in_range(-200, 800)
    y = stream.float_in_range(-200, 800)
    tex = _safe_texture()
    if tex is not None:
        return mcrfpy.Sprite(pos=(x, y), texture=tex)
    return mcrfpy.Sprite(pos=(x, y))


def _make_grid(stream):
    gw = stream.int_in_range(1, 40)
    gh = stream.int_in_range(1, 40)
    return mcrfpy.Grid(grid_size=(gw, gh))


def _make_entity(stream):
    gx = stream.int_in_range(-5, 40)
    gy = stream.int_in_range(-5, 40)
    return mcrfpy.Entity(grid_pos=(gx, gy))


def _make_tilelayer(stream):
    z = stream.int_in_range(-10, 10)
    tex = _safe_texture()
    name = stream.ascii_str(8) or "tile"
    if tex is not None:
        return mcrfpy.TileLayer(name=name, z_index=z, texture=tex)
    return mcrfpy.TileLayer(name=name, z_index=z)


def _make_colorlayer(stream):
    z = stream.int_in_range(-10, 10)
    name = stream.ascii_str(8) or "color"
    return mcrfpy.ColorLayer(name=name, z_index=z)


def _good_value_for(stream, prop_type):
    """Return a well-typed value for the named property kind."""
    if prop_type == "float":
        return stream.float_in_range(-1000, 1000)
    if prop_type == "int":
        return stream.int_in_range(-100, 100)
    if prop_type == "bool":
        return stream.bool()
    if prop_type == "vector":
        return (stream.float_in_range(-500, 500), stream.float_in_range(-500, 500))
    if prop_type == "color":
        return (
            stream.int_in_range(0, 255),
            stream.int_in_range(0, 255),
            stream.int_in_range(0, 255),
            stream.int_in_range(0, 255),
        )
    if prop_type == "str":
        return stream.ascii_str(16)
    return None


def _read_all(obj, names):
    """Hot-loop getter reads. Exercises PyObject_GetAttrString refcount sites."""
    for name in names:
        try:
            _ = getattr(obj, name)
        except EXPECTED_EXCEPTIONS:
            pass


def _write_correct(stream, obj, groups):
    """Write every property in groups with well-typed values."""
    for prop_type, names in groups:
        for name in names:
            try:
                setattr(obj, name, _good_value_for(stream, prop_type))
            except EXPECTED_EXCEPTIONS:
                pass


def _write_confused(stream, obj, all_names):
    """Pick a property and write a type-confused value."""
    if not all_names:
        return
    name = stream.pick_one(all_names)
    try:
        setattr(obj, name, confused_value(stream))
    except EXPECTED_EXCEPTIONS:
        pass


# ----- Per-type operations -----

def fuzz_frame_correct(stream):
    f = _make_frame(stream)
    groups = (
        ("float", FRAME_FLOAT_PROPS),
        ("int", FRAME_INT_PROPS),
        ("bool", FRAME_BOOL_PROPS),
        ("color", FRAME_COLOR_PROPS),
        ("vector", FRAME_VECTOR_PROPS),
        ("str", FRAME_STR_PROPS),
    )
    _write_correct(stream, f, groups)
    _read_all(f, FRAME_ALL_READ)


def fuzz_frame_confused(stream):
    f = _make_frame(stream)
    all_writable = (
        FRAME_FLOAT_PROPS + FRAME_INT_PROPS + FRAME_BOOL_PROPS
        + FRAME_COLOR_PROPS + FRAME_VECTOR_PROPS + FRAME_STR_PROPS
        + ("parent", "shader", "align")
    )
    n = stream.int_in_range(1, 8)
    for _ in range(n):
        _write_confused(stream, f, all_writable)


def fuzz_caption_correct(stream):
    c = _make_caption(stream)
    groups = (
        ("float", CAPTION_FLOAT_PROPS),
        ("int", CAPTION_INT_PROPS),
        ("bool", CAPTION_BOOL_PROPS),
        ("color", CAPTION_COLOR_PROPS),
        ("vector", CAPTION_VECTOR_PROPS),
        ("str", CAPTION_STR_PROPS),
    )
    _write_correct(stream, c, groups)
    _read_all(c, CAPTION_FLOAT_PROPS + CAPTION_INT_PROPS + CAPTION_BOOL_PROPS
              + CAPTION_COLOR_PROPS + CAPTION_VECTOR_PROPS + CAPTION_STR_PROPS
              + ("size", "w", "h"))


def fuzz_caption_confused(stream):
    c = _make_caption(stream)
    all_writable = (
        CAPTION_FLOAT_PROPS + CAPTION_INT_PROPS + CAPTION_BOOL_PROPS
        + CAPTION_COLOR_PROPS + CAPTION_VECTOR_PROPS + CAPTION_STR_PROPS
    )
    n = stream.int_in_range(1, 8)
    for _ in range(n):
        _write_confused(stream, c, all_writable)


def fuzz_sprite_correct(stream):
    s = _make_sprite(stream)
    groups = (
        ("float", SPRITE_FLOAT_PROPS),
        ("int", SPRITE_INT_PROPS),
        ("bool", SPRITE_BOOL_PROPS),
        ("vector", SPRITE_VECTOR_PROPS),
        ("str", SPRITE_STR_PROPS),
    )
    _write_correct(stream, s, groups)
    _read_all(s, SPRITE_FLOAT_PROPS + SPRITE_INT_PROPS + SPRITE_BOOL_PROPS
              + SPRITE_VECTOR_PROPS + SPRITE_STR_PROPS + ("texture",))


def fuzz_sprite_confused(stream):
    s = _make_sprite(stream)
    all_writable = (
        SPRITE_FLOAT_PROPS + SPRITE_INT_PROPS + SPRITE_BOOL_PROPS
        + SPRITE_VECTOR_PROPS + SPRITE_STR_PROPS + ("texture",)
    )
    n = stream.int_in_range(1, 8)
    for _ in range(n):
        _write_confused(stream, s, all_writable)


def fuzz_grid_correct(stream):
    g = _make_grid(stream)
    groups = (
        ("float", GRID_FLOAT_PROPS),
        ("int", GRID_INT_PROPS),
        ("bool", GRID_BOOL_PROPS),
        ("vector", GRID_VECTOR_PROPS),
        ("color", GRID_COLOR_PROPS),
        ("str", GRID_STR_PROPS),
    )
    _write_correct(stream, g, groups)
    _read_all(g, GRID_FLOAT_PROPS + GRID_INT_PROPS + GRID_BOOL_PROPS
              + GRID_VECTOR_PROPS + GRID_COLOR_PROPS + GRID_STR_PROPS
              + ("grid_size", "grid_w", "grid_h", "entities", "children",
                 "layers", "texture", "view", "hovered_cell"))


def fuzz_grid_confused(stream):
    g = _make_grid(stream)
    all_writable = (
        GRID_FLOAT_PROPS + GRID_INT_PROPS + GRID_BOOL_PROPS
        + GRID_VECTOR_PROPS + GRID_COLOR_PROPS + GRID_STR_PROPS
        + ("perspective", "fov")
    )
    n = stream.int_in_range(1, 8)
    for _ in range(n):
        _write_confused(stream, g, all_writable)


def fuzz_entity_correct(stream):
    e = _make_entity(stream)
    groups = (
        ("float", ENTITY_FLOAT_PROPS),
        ("int", ENTITY_INT_PROPS),
        ("bool", ENTITY_BOOL_PROPS),
        ("vector", ENTITY_VECTOR_PROPS),
        ("str", ENTITY_STR_PROPS),
    )
    _write_correct(stream, e, groups)
    _read_all(e, ENTITY_FLOAT_PROPS + ENTITY_INT_PROPS + ENTITY_BOOL_PROPS
              + ENTITY_VECTOR_PROPS + ENTITY_STR_PROPS
              + ("gridstate", "grid", "shader", "uniforms", "labels",
                 "behavior_type", "sprite_grid"))


def fuzz_entity_confused(stream):
    e = _make_entity(stream)
    all_writable = (
        ENTITY_FLOAT_PROPS + ENTITY_INT_PROPS + ENTITY_BOOL_PROPS
        + ENTITY_VECTOR_PROPS + ENTITY_STR_PROPS
        + ("grid", "shader", "labels", "step", "sprite_grid")
    )
    n = stream.int_in_range(1, 8)
    for _ in range(n):
        _write_confused(stream, e, all_writable)


def fuzz_tilelayer(stream):
    try:
        layer = _make_tilelayer(stream)
    except EXPECTED_EXCEPTIONS:
        return
    # Correct writes
    for _ in range(stream.int_in_range(1, 4)):
        try:
            layer.z_index = stream.int_in_range(-20, 20)
        except EXPECTED_EXCEPTIONS:
            pass
        try:
            layer.visible = stream.bool()
        except EXPECTED_EXCEPTIONS:
            pass
    # Read everything including read-only
    _read_all(layer, ("z_index", "visible", "texture", "grid_size", "name", "grid"))
    # Confused writes
    _write_confused(stream, layer, ("z_index", "visible", "texture", "grid"))


def fuzz_colorlayer(stream):
    try:
        layer = _make_colorlayer(stream)
    except EXPECTED_EXCEPTIONS:
        return
    for _ in range(stream.int_in_range(1, 4)):
        try:
            layer.z_index = stream.int_in_range(-20, 20)
        except EXPECTED_EXCEPTIONS:
            pass
        try:
            layer.visible = stream.bool()
        except EXPECTED_EXCEPTIONS:
            pass
    _read_all(layer, ("z_index", "visible", "grid_size", "name", "grid"))
    _write_confused(stream, layer, ("z_index", "visible", "grid"))


def fuzz_color(stream):
    try:
        c = mcrfpy.Color(
            stream.int_in_range(0, 255),
            stream.int_in_range(0, 255),
            stream.int_in_range(0, 255),
            stream.int_in_range(0, 255),
        )
    except EXPECTED_EXCEPTIONS:
        return
    # Hammer r/g/b/a in and out of 0-255
    for _ in range(stream.int_in_range(4, 16)):
        for prop in ("r", "g", "b", "a"):
            try:
                setattr(c, prop, stream.int_in_range(-500, 1000))
            except EXPECTED_EXCEPTIONS:
                pass
            try:
                _ = getattr(c, prop)
            except EXPECTED_EXCEPTIONS:
                pass
    # Confused writes
    for prop in ("r", "g", "b", "a"):
        try:
            setattr(c, prop, confused_value(stream))
        except EXPECTED_EXCEPTIONS:
            pass


def fuzz_vector(stream):
    try:
        v = mcrfpy.Vector(
            stream.float_in_range(-1000, 1000),
            stream.float_in_range(-1000, 1000),
        )
    except EXPECTED_EXCEPTIONS:
        return
    # Correct writes, including inf/nan specials
    for _ in range(stream.int_in_range(4, 16)):
        sel = stream.u8() % 5
        if sel == 0:
            val = float("inf")
        elif sel == 1:
            val = float("-inf")
        elif sel == 2:
            val = float("nan")
        else:
            val = stream.float_in_range(-1e6, 1e6)
        try:
            v.x = val
        except EXPECTED_EXCEPTIONS:
            pass
        try:
            v.y = val
        except EXPECTED_EXCEPTIONS:
            pass
        try:
            _ = v.x
            _ = v.y
            _ = v.int
        except EXPECTED_EXCEPTIONS:
            pass
    # Confused writes
    for prop in ("x", "y"):
        try:
            setattr(v, prop, confused_value(stream))
        except EXPECTED_EXCEPTIONS:
            pass


def fuzz_nested_reparent(stream):
    """Nest captions/sprites in frames, reparent between two frames.

    Exercises UICollection parent bookkeeping and shared ownership edges.
    """
    f1 = _make_frame(stream)
    f2 = _make_frame(stream)
    try:
        f1.children.append(_make_caption(stream))
        f1.children.append(_make_frame(stream))
    except EXPECTED_EXCEPTIONS:
        pass
    try:
        f2.children.append(_make_caption(stream))
    except EXPECTED_EXCEPTIONS:
        pass
    # Move child from f1 to f2 (if possible) via append/remove
    try:
        if len(f1.children) > 0:
            child = f1.children[stream.int_in_range(0, len(f1.children) - 1)]
            f2.children.append(child)
    except EXPECTED_EXCEPTIONS:
        pass
    # Hammer the nested frames' properties
    for f in (f1, f2):
        try:
            f.x = stream.float_in_range(-100, 100)
            f.y = stream.float_in_range(-100, 100)
        except EXPECTED_EXCEPTIONS:
            pass
    # Read children collection and walk it
    try:
        for child in f1.children:
            _ = getattr(child, "x", None)
            _ = getattr(child, "pos", None)
    except EXPECTED_EXCEPTIONS:
        pass


def fuzz_hot_loop_reads(stream):
    """Dense PyObject_GetAttrString reads to stress #267 sites."""
    f = _make_frame(stream)
    # Also try a Grid (different getter table)
    g = _make_grid(stream)
    e = _make_entity(stream)
    # Tight loop reading many properties
    for _ in range(HOT_LOOP):
        try:
            _ = f.pos
            _ = f.fill_color
            _ = f.outline_color
            _ = f.x
            _ = f.y
            _ = f.w
            _ = f.h
            _ = f.visible
            _ = f.opacity
            _ = f.children
            _ = f.bounds
            _ = f.global_position
        except EXPECTED_EXCEPTIONS:
            pass
        try:
            _ = g.pos
            _ = g.size
            _ = g.center
            _ = g.grid_size
            _ = g.fill_color
            _ = g.entities
            _ = g.layers
        except EXPECTED_EXCEPTIONS:
            pass
        try:
            _ = e.pos
            _ = e.cell_pos
            _ = e.draw_pos
            _ = e.grid_pos
            _ = e.sprite_offset
            _ = e.tile_size
        except EXPECTED_EXCEPTIONS:
            pass


# ----- Tier C (#312): shapes, Scene.children collections, module functions ---

def _make_line(stream):
    return mcrfpy.Line(
        start=(stream.float_in_range(-100, 600), stream.float_in_range(-100, 600)),
        end=(stream.float_in_range(-100, 600), stream.float_in_range(-100, 600)),
        thickness=stream.float_in_range(-2, 12))


def _make_circle(stream):
    return mcrfpy.Circle(
        center=(stream.float_in_range(-100, 600), stream.float_in_range(-100, 600)),
        radius=stream.float_in_range(-5, 120))


def _make_arc(stream):
    return mcrfpy.Arc(
        center=(stream.float_in_range(-100, 600), stream.float_in_range(-100, 600)),
        radius=stream.float_in_range(-5, 120),
        start_angle=stream.float_in_range(-720, 720),
        end_angle=stream.float_in_range(-720, 720))


# maker -> (correct-write groups, all-writable names for confused writes)
_SHAPES = (
    (_make_line,
     (("float", LINE_FLOAT_PROPS), ("int", LINE_INT_PROPS),
      ("bool", LINE_BOOL_PROPS), ("color", LINE_COLOR_PROPS),
      ("vector", LINE_VECTOR_PROPS), ("str", LINE_STR_PROPS)),
     LINE_FLOAT_PROPS + LINE_INT_PROPS + LINE_BOOL_PROPS + LINE_COLOR_PROPS
     + LINE_VECTOR_PROPS + LINE_STR_PROPS),
    (_make_circle,
     (("float", CIRCLE_FLOAT_PROPS), ("int", CIRCLE_INT_PROPS),
      ("bool", CIRCLE_BOOL_PROPS), ("color", CIRCLE_COLOR_PROPS),
      ("vector", CIRCLE_VECTOR_PROPS), ("str", CIRCLE_STR_PROPS)),
     CIRCLE_FLOAT_PROPS + CIRCLE_INT_PROPS + CIRCLE_BOOL_PROPS + CIRCLE_COLOR_PROPS
     + CIRCLE_VECTOR_PROPS + CIRCLE_STR_PROPS),
    (_make_arc,
     (("float", ARC_FLOAT_PROPS), ("int", ARC_INT_PROPS),
      ("bool", ARC_BOOL_PROPS), ("color", ARC_COLOR_PROPS),
      ("vector", ARC_VECTOR_PROPS), ("str", ARC_STR_PROPS)),
     ARC_FLOAT_PROPS + ARC_INT_PROPS + ARC_BOOL_PROPS + ARC_COLOR_PROPS
     + ARC_VECTOR_PROPS + ARC_STR_PROPS),
)


def fuzz_shapes(stream):
    """Build a Line/Circle/Arc and hammer its setters (correct + confused)."""
    maker, groups, all_writable = _SHAPES[stream.u8() % len(_SHAPES)]
    try:
        shape = maker(stream)
    except EXPECTED_EXCEPTIONS:
        return
    _write_correct(stream, shape, groups)
    read_names = tuple(name for _t, names in groups for name in names)
    _read_all(shape, read_names + ("bounds", "global_position", "shader", "uniforms"))
    for _ in range(stream.int_in_range(1, 6)):
        _write_confused(stream, shape, all_writable)


def fuzz_scene_children(stream):
    """Tier C (#312): Scene.children collection ops -- append/insert/index/
    count/pop/remove/slice/iterate, exercised outside the grid-entity scope."""
    scene = mcrfpy.Scene(stream.ascii_str(6) or "fz")
    col = scene.children
    for _ in range(stream.int_in_range(0, 6)):
        kind = stream.u8() % 5
        try:
            if kind == 0:
                col.append(_make_frame(stream))
            elif kind == 1:
                col.append(_make_caption(stream))
            elif kind == 2:
                col.append(_make_sprite(stream))
            elif kind == 3:
                col.append(_make_circle(stream))
            else:
                idx = stream.int_in_range(0, max(0, len(col)))
                col.insert(idx, _make_line(stream))
        except EXPECTED_EXCEPTIONS:
            pass
    try:
        _ = len(col)
    except EXPECTED_EXCEPTIONS:
        pass
    n = 0
    try:
        n = len(col)
    except EXPECTED_EXCEPTIONS:
        pass
    if n > 0:
        first = None
        try:
            first = col[stream.int_in_range(0, n - 1)]
        except EXPECTED_EXCEPTIONS:
            pass
        for meth in ("index", "count"):
            try:
                getattr(col, meth)(first)
            except EXPECTED_EXCEPTIONS:
                pass
        try:
            col.find(stream.ascii_str(6))
        except EXPECTED_EXCEPTIONS:
            pass
        try:
            col.remove(first)
        except EXPECTED_EXCEPTIONS:
            pass
    try:
        a = stream.int_in_range(0, max(0, n))
        b = stream.int_in_range(a, max(a, n))
        _ = col[a:b]
    except EXPECTED_EXCEPTIONS:
        pass
    try:
        for item in col:
            _ = getattr(item, "x", None)
    except EXPECTED_EXCEPTIONS:
        pass
    try:
        col.pop()
    except EXPECTED_EXCEPTIONS:
        pass


def fuzz_module_functions(stream):
    """Tier C (#312): mcrfpy.find / find_all / bresenham / lock.

    NOTE: the benchmark triplet (start_benchmark/log_benchmark/end_benchmark) is
    intentionally NOT fuzzed here -- end_benchmark() writes a log file to disk on
    every call (g_benchmarkLogger.end()), which over a fuzz campaign would spam
    the filesystem and throttle iteration without exercising any memory-safety
    path. It is harness instrumentation, not API surface worth fuzzing.
    """
    try:
        mcrfpy.find(stream.ascii_str(8))
    except EXPECTED_EXCEPTIONS:
        pass
    try:
        mcrfpy.find(stream.ascii_str(8), stream.ascii_str(6))
    except EXPECTED_EXCEPTIONS:
        pass
    try:
        mcrfpy.find_all(stream.ascii_str(8))
    except EXPECTED_EXCEPTIONS:
        pass
    a = (stream.int_in_range(-80, 80), stream.int_in_range(-80, 80))
    b = (stream.int_in_range(-80, 80), stream.int_in_range(-80, 80))
    try:
        mcrfpy.bresenham(a, b, stream.bool(), stream.bool())
    except EXPECTED_EXCEPTIONS:
        pass
    try:
        with mcrfpy.lock():
            pass
    except EXPECTED_EXCEPTIONS:
        pass


# ----- Dispatch -----

OPS = (
    fuzz_frame_correct,
    fuzz_frame_confused,
    fuzz_caption_correct,
    fuzz_caption_confused,
    fuzz_sprite_correct,
    fuzz_sprite_confused,
    fuzz_grid_correct,
    fuzz_grid_confused,
    fuzz_entity_correct,
    fuzz_entity_confused,
    fuzz_tilelayer,
    fuzz_colorlayer,
    fuzz_color,
    fuzz_vector,
    fuzz_nested_reparent,
    fuzz_hot_loop_reads,
    fuzz_shapes,            # Tier C (#312)
    fuzz_scene_children,    # Tier C (#312)
    fuzz_module_functions,  # Tier C (#312)
)


def fuzz_one_input(data):
    stream = ByteStream(data)
    try:
        n = stream.int_in_range(1, MAX_OPS)
        for _ in range(n):
            if stream.remaining < 1:
                break
            op = OPS[stream.u8() % len(OPS)]
            try:
                op(stream)
            except EXPECTED_EXCEPTIONS:
                pass
    except EXPECTED_EXCEPTIONS:
        pass
