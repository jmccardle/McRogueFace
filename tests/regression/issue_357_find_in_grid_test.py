#!/usr/bin/env python3
"""Regression test for #357 - mcrfpy.find()/find_all() never descend into a
Grid's entities or child drawables.

Root cause (same #252 GridView-split fracture family as #355):
  - McRFPy_API::_find / _findAll gate their grid-entity search on
    `drawable->derived_type() == PyObjectsEnum::UIGRID`, but a real
    mcrfpy.Grid() is a UIGridView (PyObjectsEnum::UIGRIDVIEW) -- that branch
    is structurally unreachable for anything a Python script can build.
  - find_in_collection()'s child-recursion only descends into UIFRAME
    children; it never recurses into a grid's own overlay children
    (grid.children) at all, regardless of the UIGRID/UIGRIDVIEW question.

Both are exercised here as hard assertions.
"""
import sys
import mcrfpy


def test_find_entity_in_grid():
    print("find()/find_all() locate a named Entity inside a Grid...")
    scene = mcrfpy.Scene("issue357_entity")
    ui = scene.children
    mcrfpy.current_scene = scene

    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(0, 0), size=(80, 80))
    ui.append(grid)

    e = mcrfpy.Entity(grid_pos=(2, 2), name="findme_entity")
    grid.entities.append(e)

    found = mcrfpy.find("findme_entity")
    assert found is not None, "mcrfpy.find() failed to locate a named Entity inside a Grid"
    assert found.name == "findme_entity", f"found wrong object: name={getattr(found, 'name', None)!r}"
    assert (found.grid_pos.x, found.grid_pos.y) == (2, 2), (
        f"find() returned an entity with the wrong grid_pos: {found.grid_pos.x},{found.grid_pos.y}"
    )

    all_found = mcrfpy.find_all("findme_entity")
    assert len(all_found) >= 1, "mcrfpy.find_all() failed to locate a named Entity inside a Grid"
    print("    OK")


def test_find_child_drawable_in_grid():
    print("find()/find_all() locate a named child drawable inside a Grid...")
    scene = mcrfpy.Scene("issue357_child")
    ui = scene.children
    mcrfpy.current_scene = scene

    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(0, 0), size=(80, 80))
    ui.append(grid)

    child = mcrfpy.Frame(pos=(10, 10), size=(5, 5), name="findme_child")
    grid.children.append(child)

    found = mcrfpy.find("findme_child")
    assert found is not None, "mcrfpy.find() failed to locate a named child drawable inside a Grid"
    assert found.name == "findme_child", f"found wrong object: name={getattr(found, 'name', None)!r}"

    all_found = mcrfpy.find_all("findme_child")
    assert len(all_found) >= 1, "mcrfpy.find_all() failed to locate a named child drawable inside a Grid"
    print("    OK")


def test_find_preserves_entity_identity():
    """find() must return the SAME Python object the user created (the #266
    identity ref via PythonObjectCache), not a fresh base-class wrapper.

    Two bugs in one, if it doesn't:
      * a Grid entity that is an Entity SUBCLASS comes back as a plain
        mcrfpy.Entity -- attributes on the subclass instance are gone;
      * disposing that duplicate wrapper runs PyUIEntityType's tp_dealloc,
        which clears data->pyobject WITHOUT a Py_DECREF -- permanently leaking
        the entity's strong self-reference, so the subclass instance (and its
        __dict__/closures) is never reclaimed, even after it leaves the grid.
    """
    print("find() returns the entity's real Python object (identity + no leak)...")
    import gc
    import weakref

    scene = mcrfpy.Scene("issue357_identity")
    mcrfpy.current_scene = scene

    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(0, 0), size=(80, 80))
    scene.children.append(grid)

    class Hero(mcrfpy.Entity):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.hp = 10

    hero = Hero(grid_pos=(2, 2), name="hero")
    grid.entities.append(hero)

    assert grid.entities[0] is hero, "collection lookup lost identity (test setup broken)"

    found = mcrfpy.find("hero")
    assert found is hero, (
        f"find() returned a duplicate wrapper ({type(found).__name__}), not the "
        "Hero instance -- PythonObjectCache lookup skipped"
    )
    assert found.hp == 10, "subclass attributes lost -- find() built a base Entity"

    all_found = mcrfpy.find_all("hero")
    assert all_found and all_found[0] is hero, f"find_all() lost identity: {all_found}"

    # Now prove the identity reference was not leaked: dropping every Python
    # handle after the entity leaves the grid must reclaim the Hero object.
    del found
    del all_found
    ref = weakref.ref(hero)
    grid.entities.remove(hero)   # releasePyIdentity() -> DECREF the strong ref
    del hero
    gc.collect()
    assert ref() is None, (
        "Hero object survived removal from the grid -- the entity's strong "
        "identity reference was dropped without a DECREF (leak)"
    )
    print("    OK")


def test_find_dedupes_shared_griddata():
    """N views can share ONE GridData (#359 split-screen/minimap). The grid's
    entities and overlay children must be walked once per GridData, not once
    per view, or find_all() returns N duplicates of every match."""
    print("find_all() does not duplicate entities across views of one GridData...")
    scene = mcrfpy.Scene("issue357_shared")
    mcrfpy.current_scene = scene

    g = mcrfpy.Grid(grid_size=(5, 5), pos=(100, 100), size=(200, 200))
    scene.children.append(g)

    v2 = mcrfpy.GridView(grid=g.grid_data, pos=(400, 100), size=(200, 200))
    scene.children.append(v2)

    enemy = mcrfpy.Entity(grid_pos=(1, 1), name="enemy")
    g.entities.append(enemy)

    child = mcrfpy.Frame(pos=(16, 16), size=(16, 16), name="marker")
    g.children.append(child)

    hits = mcrfpy.find_all("enemy")
    assert len(hits) == 1, (
        f"find_all('enemy') returned {len(hits)} results for one entity -- the "
        "shared GridData was walked once per view (a 'for e in find_all(...)' loop "
        "would apply its effect twice)"
    )
    assert hits[0] is enemy, "find_all() lost entity identity"

    child_hits = mcrfpy.find_all("marker")
    assert len(child_hits) == 1, (
        f"find_all('marker') returned {len(child_hits)} results for one grid child"
    )
    print("    OK")


def main():
    test_find_entity_in_grid()
    test_find_child_drawable_in_grid()
    test_find_preserves_entity_identity()
    test_find_dedupes_shared_griddata()
    print("PASS")


if __name__ == "__main__":
    # See issue_355_grid_input_test.py: --exec does not turn an unhandled
    # exception into a non-zero process exit code, so translate explicitly.
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
