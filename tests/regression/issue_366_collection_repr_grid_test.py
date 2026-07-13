#!/usr/bin/env python3
"""Regression test for #366: UICollection.repr counted grids as "UIDrawable".

UICollection::repr tallies collection contents by derived_type() and routed
PyObjectsEnum::UIGRIDVIEW into other_count, while the "Grid" bucket was fed only
by UIGRID -- the internal _GridData type, which no scene graph ever contains
since #252. So repr(scene.children) on a scene holding grids reported
"<UICollection (3 objects: 1 Frame, 2 UIDrawables)>" and never named the grids.

Last surviving instance of the bug class #355 eliminated (a caller switching on
derived_type() to detect grid-ness, silently dead since the type it names stopped
appearing in scene graphs). Now dispatched on the asGridData() virtual instead.
"""
import sys
import mcrfpy

FAILURES = []


def check(cond, msg):
    if not cond:
        print(f"FAIL: {msg}", file=sys.stderr)
        FAILURES.append(msg)


def main():
    scene = mcrfpy.Scene("repr_grid")
    ui = scene.children

    ui.append(mcrfpy.Frame(pos=(0, 0), size=(10, 10)))
    ui.append(mcrfpy.Grid(grid_size=(4, 4), pos=(20, 20), size=(64, 64)))
    ui.append(mcrfpy.Grid(grid_size=(4, 4), pos=(100, 20), size=(64, 64)))

    r = repr(ui)
    print(f"repr: {r}")

    check("2 Grids" in r,
          f"repr should name the 2 Grids (grids counted as 'other'?); got {r}")
    check("1 Frame" in r, f"repr should still name the Frame; got {r}")
    check("UIDrawable" not in r,
          f"no element here is an unclassified UIDrawable; got {r}")

    # A single grid uses the singular form.
    scene2 = mcrfpy.Scene("repr_grid_one")
    scene2.children.append(mcrfpy.Grid(grid_size=(4, 4), pos=(0, 0), size=(64, 64)))
    r2 = repr(scene2.children)
    print(f"repr: {r2}")
    check("1 Grid" in r2 and "Grids" not in r2,
          f"a single grid should read '1 Grid'; got {r2}")


if __name__ == "__main__":
    try:
        main()
        if FAILURES:
            print(f"\n{len(FAILURES)} FAILURE(S)", file=sys.stderr)
            sys.exit(1)
        print("PASS")
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        print(f"\nTEST CRASHED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
