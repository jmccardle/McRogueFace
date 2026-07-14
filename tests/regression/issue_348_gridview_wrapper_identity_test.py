"""Regression test for #348 - persistent internal-Grid wrapper.

UIGridView.get_grid() used to allocate a throwaway UIGrid wrapper + weakref on
every access (0% cache hit) because it cached only a weakref to a temporary
that died immediately. It now holds a persistent strong ref, so repeated
attribute delegation (grid.at(), grid.entities, ...) reuses one object.

Verifies: identity stability, correctness under hammering, and that set_grid /
None reassignment invalidates the cache correctly (no stale wrapper, no crash).
"""
import mcrfpy
import sys


def main():
    g = mcrfpy.Grid(grid_size=(16, 16), pos=(0, 0), size=(160, 160))

    # Identity: repeated access returns the same wrapper object (the #348 cache)
    a = g.grid_data
    b = g.grid_data
    assert a is b, "grid_data should return a stable wrapper identity"

    # Hammer at()/delegated attribute access -- must not crash or leak
    for i in range(5000):
        c = g.at(i % 16, (i * 3) % 16)
        c.walkable = (i % 2 == 0)
    assert g.at(0, 0).walkable is True

    # entity.grid round-trips to the owning GridData wrapper.
    # (#313/#361: entity.grid returns the shared GridData, NOT the Grid view.
    # The #348 cache guarantee is what matters here: the same wrapper object
    # comes back every time, and it is the *same* wrapper the view hands out.)
    e = mcrfpy.Entity((1, 1), grid=g)
    assert e.grid is g.grid_data, "entity.grid should be the owning GridData"
    assert e.grid is e.grid, "entity.grid must have stable wrapper identity"

    # Reassigning grid_data invalidates the cache: new wrapper for new data
    g2 = mcrfpy.Grid(grid_size=(4, 4), pos=(0, 0), size=(40, 40))
    view = mcrfpy.GridView(grid=g2, pos=(0, 0), size=(40, 40))
    w1 = view.grid_data
    assert w1 is not None
    # Point the view at g's data instead; the cached wrapper must refresh
    view.grid_data = g.grid_data
    w2 = view.grid_data
    assert w2 is not w1, "cache must invalidate when grid_data is reassigned"

    # None reassignment clears cleanly
    view.grid_data = None
    assert view.grid_data is None

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
