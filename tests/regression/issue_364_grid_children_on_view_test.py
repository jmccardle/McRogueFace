"""Regression test for #364 - grid children belong to the GridView, not the GridData.

Children (speech bubbles, markers, range indicators) are OVERLAYS painted on top of
a grid through one camera. They are not world contents -- entities are. So they live
on the view, not on the shared data:

  * a child's parent is the Grid (i.e. the UIGridView), a real scene-graph drawable,
    so its dirty push reaches the view and every caching ancestor above it (#364);
  * two views over one GridData have independent children, and shared entities;
  * the GridData is not a drawable container at all, so it cannot be a parent.

The load-bearing case is the last one: a grid inside a Frame(cache_subtree=True).
Before this change a child's parent was the internal _GridData, which is in no scene,
so markCompositeDirty() dead-ended there and the Frame re-blitted a STALE composite.
That is invisible in a bare scene (the view re-renders itself) and only shows up under
a caching ancestor -- which is exactly what case 5 builds.
"""
import mcrfpy
from mcrfpy import automation
import sys, os, tempfile

TMPDIR = tempfile.mkdtemp(prefix="mcrf364_")
_counter = 0
_results = []


def check(label, ok):
    _results.append((label, bool(ok)))
    print("  [%s] %s" % ("PASS" if ok else "FAIL", label))


def shot():
    """Render a frame to PNG and return its bytes (identical pixels -> identical
    bytes with the deterministic PNG encoder). Headless screenshots are synchronous
    (#153): render-then-capture, so no Timer dance is required."""
    global _counter
    path = os.path.join(TMPDIR, "s%d.png" % _counter)
    _counter += 1
    automation.screenshot(path)
    with open(path, "rb") as f:
        return f.read()


def case_child_parent_is_the_view():
    """The child's parent is the Grid (UIGridView), not the internal _GridData.

    Identity (`child.parent is grid`) is NOT asserted: `.parent` allocates a fresh
    wrapper on every read, so `is` fails for Frames too -- even `kid.parent is
    kid.parent` is False. That is a pre-existing engine-wide gap, not this bug, and
    it is filed separately. Here we assert the parent's TYPE and identify the view by
    name, which is what #364 actually turns on.
    """
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(200, 200), name="the_view")
    bubble = mcrfpy.Frame(pos=(32, 32), size=(20, 20))
    grid.children.append(bubble)

    check("1a: child.parent is the grid view", bubble.parent.name == "the_view")
    # #361: mcrfpy.Grid IS mcrfpy.GridView (one type object, two names), and the
    # canonical tp_name is GridView.
    check("1b: child.parent is a Grid, not a GridData",
          isinstance(bubble.parent, mcrfpy.Grid))


def case_children_are_per_view_entities_are_shared():
    """Two views over one GridData: children are per-view, entities are shared."""
    v1 = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(200, 200), name="v1")
    v2 = mcrfpy.Grid(grid=v1.grid_data, pos=(220, 0), size=(200, 200), name="v2")

    check("2a: both views share one GridData", v1.grid_data is v2.grid_data)

    marker = mcrfpy.Frame(pos=(32, 32), size=(20, 20))
    v1.children.append(marker)
    check("2b: child appended to v1 is in v1.children", len(v1.children) == 1)
    check("2c: child appended to v1 is NOT in v2.children", len(v2.children) == 0)
    check("2d: the child's parent is v1, not v2", marker.parent.name == "v1")

    v2.children.append(mcrfpy.Frame(pos=(64, 64), size=(20, 20)))
    check("2e: v2 keeps its own children", len(v2.children) == 1 and len(v1.children) == 1)

    # Entities are world contents: both cameras must see the same ones.
    mcrfpy.Entity((3, 3), grid=v1)
    check("2f: entity added through v1 is visible through v2",
          len(v1.entities) == 1 and len(v2.entities) == 1)


def case_griddata_is_not_a_parent():
    """GridData holds no drawables, so it cannot be assigned as a parent."""
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(200, 200))
    orphan = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    try:
        orphan.parent = grid.grid_data
        check("3a: assigning a GridData as parent raises TypeError", False)
    except TypeError:
        check("3a: assigning a GridData as parent raises TypeError", True)

    check("3b: GridData exposes no children collection",
          not hasattr(grid.grid_data, "children"))


def case_parent_none_removes_from_the_view():
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(200, 200))
    child = mcrfpy.Frame(pos=(32, 32), size=(20, 20))
    grid.children.append(child)
    check("4a: appended", len(grid.children) == 1)

    child.parent = None
    check("4b: parent=None removes the child from the view", len(grid.children) == 0)
    check("4c: the detached child has no parent", child.parent is None)


def case_child_mutation_invalidates_a_caching_ancestor():
    """#364 proper: a grid child's dirty push must reach a Frame(cache_subtree=True).

    Pre-fix the child's parent was the internal _GridData -- in no scene, with no
    parent of its own -- so markCompositeDirty() stopped there, the Frame stayed
    clean, and it re-blitted its cached (stale) composite. The screenshots below
    would come back byte-identical even though the child had moved.
    """
    scene = mcrfpy.Scene("t364")
    scene.activate()

    cache = mcrfpy.Frame(pos=(10, 10), size=(300, 300),
                         fill_color=mcrfpy.Color(20, 20, 20),
                         cache_subtree=True)
    scene.children.append(cache)

    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(280, 280))
    cache.children.append(grid)

    bubble = mcrfpy.Frame(pos=(32, 32), size=(48, 48),
                          fill_color=mcrfpy.Color(255, 0, 0))
    grid.children.append(bubble)

    a = shot()

    bubble.x = 128.0
    b = shot()
    check("5a: moving a grid child re-composites the caching ancestor", a != b)

    bubble.fill_color = mcrfpy.Color(0, 255, 0)
    c = shot()
    check("5b: recoloring a grid child re-composites the caching ancestor", b != c)

    grid.children.remove(bubble)
    d = shot()
    check("5c: removing a grid child re-composites the caching ancestor", c != d)

    # And the skip path itself stays honest: no mutation -> byte-identical frames.
    e = shot()
    check("5d: idle frames are stable", d == e)


def run_tests():
    case_child_parent_is_the_view()
    case_children_are_per_view_entities_are_shared()
    case_griddata_is_not_a_parent()
    case_parent_none_removes_from_the_view()
    case_child_mutation_invalidates_a_caching_ancestor()
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
