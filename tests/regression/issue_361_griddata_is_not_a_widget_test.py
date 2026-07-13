"""Regression test for #361 - GridData is a map, not a widget.

Before this change `UIGrid` inherited BOTH UIDrawable and GridData, so every map
secretly carried a second camera and RenderTexture that nothing on screen
corresponded to. Three consequences, all tested here:

  1. `scene.children.append(some_grid_data)` DREW THE MAP A SECOND TIME, through
     that ghost camera, frozen at construction values. It must now raise TypeError.

  2. Anything that wrote to the ghost camera was a silent no-op on the widget the
     user was actually looking at. `Grid.center_camera(...)` and `Grid.size = ...`
     both delegated to it and did nothing (case 4) -- that is not a hypothetical:
     it was the behavior on master until this fix.

  3. A GridData could never be independently heap-allocated (`GridData::markDirty`
     did `static_cast<UIGrid*>(this)`), so a map with no view was inexpressible.
     Now `mcrfpy.GridData(...)` is public and standalone: an offscreen level that
     is still steppable, queryable and pathable (case 2).

Also covers the accepted API break: `entity.grid` returns the GridData (the map),
not a view. An entity may be on a map with no view at all, or with several -- "the
grid an entity is in" simply is not a camera.
"""
import mcrfpy
from mcrfpy import automation
import sys, os, tempfile

TMPDIR = tempfile.mkdtemp(prefix="mcrf361_")
_counter = 0
_results = []


def check(label, ok):
    _results.append((label, bool(ok)))
    print("  [%s] %s" % ("PASS" if ok else "FAIL", label))


def shot():
    """Render a frame to PNG and return its bytes. Identical pixels -> identical
    bytes; headless screenshots are synchronous (#153)."""
    global _counter
    path = os.path.join(TMPDIR, "s%d.png" % _counter)
    _counter += 1
    automation.screenshot(path)
    with open(path, "rb") as f:
        return f.read()


def case_griddata_is_not_drawable():
    """A map has no position, no size, no camera, and cannot enter a scene graph."""
    data = mcrfpy.GridData(grid_size=(10, 10))
    scene = mcrfpy.Scene("t361_reject")

    try:
        scene.children.append(data)
        check("1a: appending a GridData to a scene raises TypeError", False)
    except TypeError:
        check("1a: appending a GridData to a scene raises TypeError", True)

    frame = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    try:
        frame.children.append(data)
        check("1b: appending a GridData to a Frame raises TypeError", False)
    except TypeError:
        check("1b: appending a GridData to a Frame raises TypeError", True)

    # The widget properties are gone, not merely unused: keeping them would mean
    # keeping the ghost camera they wrote to.
    for prop in ("x", "y", "w", "h", "pos", "size", "center", "center_x", "zoom",
                 "camera_rotation", "fill_color", "visible", "opacity", "z_index",
                 "on_click", "parent", "children"):
        if hasattr(data, prop):
            check("1c: GridData exposes no widget property (found %r)" % prop, False)
            return
    check("1c: GridData exposes no widget properties", True)

    check("1d: GridData is not a Drawable", not isinstance(data, mcrfpy.Drawable))


def case_map_with_no_view():
    """A GridData with no view at all: mutable, steppable, queryable, pathable.

    This is what the old `static_cast<UIGrid*>(this)` in GridData::markDirty made
    impossible -- a standalone GridData would have been undefined behavior on the
    first cell write.
    """
    data = mcrfpy.GridData(grid_size=(12, 12))
    check("2a: standalone GridData constructs", data.grid_w == 12 and data.grid_h == 12)

    for x in range(12):
        for y in range(12):
            data.at(x, y).walkable = True
            data.at(x, y).transparent = True
    check("2b: cells are writable with no view attached", data.at(5, 5).walkable)

    e = mcrfpy.Entity((1, 1), grid=data)
    check("2c: an entity can live on a viewless map", len(data.entities) == 1)
    check("2d: entity.grid is that map", e.grid is data)

    data.step(1)
    check("2e: a viewless map can be stepped", True)

    data.compute_fov((5, 5), radius=4)
    check("2f: a viewless map computes FOV", data.is_in_fov(5, 6))

    path = data.find_path((0, 0), (11, 11))
    check("2g: a viewless map is pathable", path is not None and len(list(path)) > 0)


def case_two_views_one_map():
    """N cameras, one map: independent cameras, shared entities and cells."""
    data = mcrfpy.GridData(grid_size=(20, 20))
    main = mcrfpy.Grid(grid=data, pos=(0, 0), size=(200, 200))
    mini = mcrfpy.Grid(grid=data, pos=(220, 0), size=(100, 100))

    check("3a: both views share one GridData",
          main.grid_data is data and mini.grid_data is data)

    main.center_camera((5, 5))
    mini.center_camera((15, 15))
    check("3b: the two cameras pan independently",
          main.center_x != mini.center_x and main.center_y != mini.center_y)

    main.zoom = 2.0
    check("3c: the two cameras zoom independently", mini.zoom == 1.0)

    mcrfpy.Entity((3, 3), grid=main)
    check("3d: an entity added through one view is on the shared map",
          len(main.entities) == 1 and len(mini.entities) == 1 and len(data.entities) == 1)

    data.at(4, 4).walkable = True
    check("3e: a cell written on the map is seen through both views",
          main.at(4, 4).walkable and mini.at(4, 4).walkable)


def case_grid_is_gridview():
    """mcrfpy.Grid IS mcrfpy.GridView -- one type object, two names, no subclassing."""
    check("4a: Grid is GridView (the same type object)", mcrfpy.Grid is mcrfpy.GridView)

    g = mcrfpy.Grid(grid_size=(8, 8), pos=(0, 0), size=(80, 80))
    check("4b: isinstance(Grid(...), GridView)", isinstance(g, mcrfpy.GridView))
    check("4c: Grid() creates its own GridData",
          isinstance(g.grid_data, mcrfpy.GridData) and g.grid_data.grid_w == 8)

    # grid= names an existing map; grid_size= describes a new one. Asking for both
    # is a contradiction, and silently ignoring one would hand back a view of a
    # different map than the caller asked for.
    try:
        mcrfpy.Grid(grid=g.grid_data, grid_size=(4, 4))
        check("4d: Grid(grid=..., grid_size=...) raises TypeError", False)
    except TypeError:
        check("4d: Grid(grid=..., grid_size=...) raises TypeError", True)


def case_camera_writes_are_not_no_ops():
    """#361's smoking gun: center_camera() and size= used to write to the ghost.

    On master both of these silently did nothing to the rendered widget -- they
    resolved, through attribute delegation, to the internal UIGrid's copy of the
    camera, which no view reads. The assertions below fail on master.
    """
    g = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(100, 100))

    before = g.center_x
    g.center_camera((5.0, 5.0))
    check("5a: center_camera() moves THIS view's camera", g.center_x != before)

    g.size = (300, 300)
    check("5b: size= resizes THIS view's widget",
          g.w == 300.0 and g.h == 300.0 and g.size.x == 300.0)


def case_no_ghost_render():
    """The ghost path is gone: only the view draws, and only where the view is.

    Constructing a second view of the same map must change the frame; destroying
    the reference to a map must not (the view holds it alive).
    """
    scene = mcrfpy.Scene("t361_render")
    scene.activate()

    data = mcrfpy.GridData(grid_size=(6, 6))
    for x in range(6):
        for y in range(6):
            data.at(x, y).walkable = True

    view = mcrfpy.Grid(grid=data, pos=(10, 10), size=(96, 96),
                       fill_color=mcrfpy.Color(200, 30, 30))
    scene.children.append(view)
    a = shot()

    # A second camera on the same map paints a second region of the screen.
    view2 = mcrfpy.Grid(grid=data, pos=(120, 10), size=(96, 96),
                        fill_color=mcrfpy.Color(30, 200, 30))
    scene.children.append(view2)
    b = shot()
    check("6a: adding a second view of the same map changes the frame", a != b)

    # Mutating the shared map repaints BOTH views.
    mcrfpy.Entity((2, 2), grid=data)
    c = shot()
    check("6b: mutating the shared map repaints the views", b != c)

    # Idle frames are stable -- the #351 early-out still holds.
    d = shot()
    check("6c: idle frames are byte-identical", c == d)


def run_tests():
    case_griddata_is_not_drawable()
    case_map_with_no_view()
    case_two_views_one_map()
    case_grid_is_gridview()
    case_camera_writes_are_not_no_ops()
    case_no_ghost_render()
    return all(ok for _, ok in _results)


if __name__ == "__main__":
    try:
        ok = run_tests()
        print("PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    except Exception:
        import traceback
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
