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
