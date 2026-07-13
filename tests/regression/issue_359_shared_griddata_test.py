"""Regression test for #359 - the shared-data grid path is unwired.

Two concrete defects, both in the `Grid(grid=other)` shared-GridData path
(the whole point of the #252 split -- split-screen, minimap, multiple
cameras over one dataset):

  (a) UIGridView::init_explicit_view never registered the new view with the
      GridData it attaches to, so GridData::markDirty()/markCompositeDirty()
      (which push markContentDirty/markCompositeDirty up a view's OWN
      ancestor chain -- e.g. a Frame(cache_subtree=True) wrapping that view)
      never reached a secondary view's ancestors. Note this is NOT the same
      thing as the #351 render early-out itself: UIGridView::render() polls
      GridData::content_generation directly every time it actually runs, so
      a bare secondary view (no cached ancestor) already re-rasters
      correctly regardless of this bug. The bug only surfaces when a
      secondary view sits under a render-texture-caching ancestor, because
      that ancestor decides whether to invoke the child's render() AT ALL --
      a push notification, not a poll, is required to reach it. Test 3 below
      is the discriminator: it fails (stale cache) on the pre-fix code and
      passes once init_explicit_view registers the view.

  (b) PyUIGridObject::view (the internal `_GridData.view` shim, meant to
      point back at "the" GridView) was placement-new'd but never assigned
      anywhere reachable from Python -- `_GridData.view` was always None.
      Given `_GridData` is internal (never exported to the mcrfpy module
      namespace), the fix deletes the field/getter outright rather than
      wiring it up (a single view back-pointer is structurally wrong once N
      views can share one GridData; see GridData::views / primaryView() for
      the replacement, exercised implicitly by test 2). Test 4 confirms the
      dead property is gone, not silently still None.

Design note carried over from the fix: GridData::views is a *list*, not a
single pointer, specifically because N views can share one GridData.

#361 update: entity.grid no longer returns a view at all -- it returns the
GridData. The "which view is primary?" question that views.front() answered for
identity purposes is gone, because the answer was always arbitrary dressed up as
deterministic. The registry itself remains, and is still load-bearing for
dirty-notification fan-out (test 3).
"""
import sys
import os
import tempfile
import mcrfpy
from mcrfpy import automation

TMPDIR = tempfile.mkdtemp(prefix="mcrf359_")
_counter = 0


def shot():
    """Render the active scene to PNG and return its bytes (headless
    screenshot is synchronous -- see #351's test for the same pattern)."""
    global _counter
    path = os.path.join(TMPDIR, "s%d.png" % _counter)
    _counter += 1
    automation.screenshot(path)
    with open(path, "rb") as f:
        return f.read()


def test_1_two_views_render_shared_mutations():
    """Two Grid views over one GridData, with different camera params, both
    reflect a mutation made through a third path (this is the exact scenario
    the #359 issue's own test description asks for)."""
    print("(1) two views over one GridData both render mutations...")
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

    scene_a = mcrfpy.Scene("issue359_1a")
    grid_a = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160), texture=texture)
    scene_a.children.append(grid_a)

    scene_b = mcrfpy.Scene("issue359_1b")
    grid_b = mcrfpy.Grid(grid=grid_a, pos=(0, 0), size=(160, 160))
    grid_b.zoom = 1.5
    grid_b.center = (64, 64)
    scene_b.children.append(grid_b)

    mcrfpy.current_scene = scene_a
    a1 = shot()
    mcrfpy.current_scene = scene_b
    b1 = shot()

    # Mutate through the shared data (add a visible entity at cell (3,3)).
    e = mcrfpy.Entity((3, 3), grid=grid_a)
    e.sprite_index = 5

    mcrfpy.current_scene = scene_a
    a2 = shot()
    assert a2 != a1, "primary view (grid_a) did not reflect the mutation"

    mcrfpy.current_scene = scene_b
    b2 = shot()
    assert b2 != b1, "secondary view (grid_b) did not reflect the mutation"
    print("    OK")


def test_2_entity_grid_identity():
    """entity.grid is the shared GridData -- one stable object, the same one both
    views are looking at, and NOT either view (#361)."""
    print("(2) entity.grid identity with a secondary view registered...")
    grid_a = mcrfpy.Grid(grid_size=(5, 5))
    grid_b = mcrfpy.Grid(grid=grid_a, pos=(0, 0), size=(80, 80))

    e = mcrfpy.Entity((1, 1), grid=grid_a)

    data = grid_a.grid_data
    assert grid_b.grid_data is data, "the two views do not share one GridData"
    assert e.grid is data, f"entity.grid identity broken: {e.grid!r} is not {data!r}"
    assert e.grid is e.grid, "entity.grid is not stable across reads"
    assert e.grid is not grid_a and e.grid is not grid_b, \
        "entity.grid returned a view; it must return the map (#361)"
    print("    OK")


def test_3_ancestor_cache_invalidation_through_secondary_view():
    """The discriminating regression: a SECONDARY view nested inside a
    Frame(cache_subtree=True) must have its ancestor's cached subtree
    invalidated when the shared GridData mutates, even though the mutation
    happens through a DIFFERENT (primary) view/handle. This requires
    init_explicit_view to register the secondary view with GridData -- pure
    content_generation polling (#351) is not enough, because the caching
    Frame decides whether to call the child's render() at all."""
    print("(3) ancestor render-texture cache invalidated via secondary view...")
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

    scene = mcrfpy.Scene("issue359_3")
    grid_a = mcrfpy.Grid(grid_size=(6, 6), pos=(200, 200), size=(96, 96), texture=texture)
    # grid_a deliberately NOT added to this scene -- it exists only to own
    # the data and be the mutation path; only the secondary view is visible.

    grid_b = mcrfpy.Grid(grid=grid_a, pos=(0, 0), size=(96, 96))

    frame = mcrfpy.Frame(pos=(0, 0), size=(96, 96))
    frame.cache_subtree = True
    frame.children.append(grid_b)
    scene.children.append(frame)
    mcrfpy.current_scene = scene

    # First render bakes the Frame's cached subtree (render_dirty starts True).
    shot1 = shot()
    # Idle render: cache should be stable (sanity check the test methodology).
    shot2 = shot()
    assert shot1 == shot2, "cache_subtree Frame was not stable across an idle frame (test setup problem)"

    # Mutate the shared GridData through the PRIMARY handle grid_a, NOT the
    # secondary view. If grid_b is registered on the GridData, this reaches
    # grid_b's own ancestor chain (the cache_subtree Frame) and invalidates it.
    e = mcrfpy.Entity((3, 3), grid=grid_a)
    e.sprite_index = 5

    shot3 = shot()
    assert shot3 != shot2, (
        "Frame(cache_subtree=True) wrapping the SECONDARY view did not invalidate "
        "when the shared GridData mutated through the primary handle -- "
        "init_explicit_view is not registering the view with GridData (#359 defect a)"
    )
    print("    OK")


def test_4_griddata_view_property_removed():
    """_GridData.view (PyUIGridObject::view) is dead: nothing in the
    codebase ever assigned it, and _GridData is internal/not exported. The
    fix deletes the field and getter outright rather than wiring a
    structurally-wrong single back-pointer; confirm it's actually gone, not
    silently still None."""
    print("(4) _GridData.view property deleted (not left dangling)...")
    grid_a = mcrfpy.Grid(grid_size=(3, 3))
    gd = grid_a.grid_data
    assert not hasattr(gd, "view"), (
        "_GridData.view still exists -- #359 defect (b) says delete it "
        "(internal type, never wired, N-view sharing makes a single "
        "back-pointer wrong) rather than leave it dangling"
    )
    print("    OK")


def main():
    test_1_two_views_render_shared_mutations()
    test_2_entity_grid_identity()
    test_3_ancestor_cache_invalidation_through_secondary_view()
    test_4_griddata_view_property_removed()
    print("PASS")


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
