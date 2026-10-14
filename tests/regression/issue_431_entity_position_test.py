"""Regression test for #431: one meaning for an entity's position.

1. Setting the cell (grid_pos / grid_x / grid_y and the cell_* aliases) is a
   teleport: draw_pos snaps to the new cell, exactly as grid.step() does.
   Smooth movement is animating draw_pos.
2. The spatial hash is keyed on the logical cell everywhere: entities_in_radius
   and GridPoint.entities measure from the cell, never from draw_pos.
3. The integer cell setters accept integral floats (5.0, a Vector component);
   a non-integral float raises ValueError; a non-number raises TypeError.
"""
import mcrfpy
import sys


def make_grid():
    return mcrfpy.Grid(grid_size=(100, 100), pos=(0, 0), size=(400, 400),
                       texture=mcrfpy.default_texture)


# --- 1. teleport semantics -------------------------------------------------

def test_cell_setters_snap_draw_pos():
    grid = make_grid()
    e = mcrfpy.Entity(grid_pos=(2, 3), grid=grid)

    e.grid_pos = (5, 6)
    assert (e.draw_pos.x, e.draw_pos.y) == (5.0, 6.0), e.draw_pos
    e.cell_pos = (7, 8)
    assert (e.draw_pos.x, e.draw_pos.y) == (7.0, 8.0), e.draw_pos
    e.grid_x = 10
    assert (e.draw_pos.x, e.draw_pos.y) == (10.0, 8.0), e.draw_pos
    e.grid_y = 11
    assert (e.draw_pos.x, e.draw_pos.y) == (10.0, 11.0), e.draw_pos
    e.cell_x = 12
    e.cell_y = 13
    assert (e.draw_pos.x, e.draw_pos.y) == (12.0, 13.0), e.draw_pos
    # pixel position follows (16 px cells)
    assert (e.x, e.y) == (12 * 16.0, 13 * 16.0), (e.x, e.y)


def test_cell_setter_snaps_on_detached_entity():
    e = mcrfpy.Entity(grid_pos=(1, 1))
    e.grid_pos = (4, 9)
    assert (e.draw_pos.x, e.draw_pos.y) == (4.0, 9.0), e.draw_pos


def test_draw_pos_does_not_move_cell():
    grid = make_grid()
    e = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
    e.draw_pos = (5.5, 9.25)
    assert (e.grid_x, e.grid_y) == (5, 5)


# --- 2. spatial hash keyed on the cell ------------------------------------

def test_radius_measures_from_cell_not_draw_pos():
    grid = make_grid()
    e = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)

    # Sprite drawn far away (different hash bucket), cell unchanged.
    e.draw_pos = (80.0, 80.0)
    assert grid.entities_in_radius((5, 5), 1.0) == [e]
    assert grid.entities_in_radius((80, 80), 2.0) == []
    assert e in grid.at(5, 5).entities


def test_radius_follows_cell_setters():
    grid = make_grid()
    e = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)

    e.grid_pos = (70, 70)                    # crosses a bucket boundary
    assert grid.entities_in_radius((70, 70), 1.0) == [e]
    assert grid.entities_in_radius((5, 5), 1.0) == []

    e.grid_x = 3                              # per-axis setter, back across
    assert grid.entities_in_radius((3, 70), 1.0) == [e]
    assert grid.entities_in_radius((70, 70), 1.0) == []
    assert e in grid.at(3, 70).entities


def test_animation_mid_flight_found_at_cell():
    grid = make_grid()
    e = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
    e.animate("draw_pos", (90.0, 90.0), 10.0, mcrfpy.Easing.LINEAR)
    for _ in range(5):
        mcrfpy.step(1.0)                      # about halfway
    assert e.draw_pos.x > 20.0, e.draw_pos
    assert grid.entities_in_radius((5, 5), 1.0) == [e]
    assert e in grid.at(5, 5).entities


def test_removal_after_draw_pos_change():
    """remove() must find the entity in the bucket it was inserted into."""
    grid = make_grid()
    e = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
    e.draw_pos = (80.0, 80.0)
    grid.entities.remove(e)
    assert grid.entities_in_radius((5, 5), 1.0) == []
    assert grid.entities_in_radius((80, 80), 1.0) == []


# --- 3. integral floats ----------------------------------------------------

def test_integral_floats_accepted():
    grid = make_grid()
    e = mcrfpy.Entity(grid_pos=(0, 0), grid=grid)
    v = mcrfpy.Vector(5, 6)
    e.grid_x = v.x
    e.grid_y = v.y
    assert (e.grid_x, e.grid_y) == (5, 6)
    assert type(e.grid_x) is int
    e.cell_x = 7.0
    e.cell_y = 8.0
    assert (e.cell_x, e.cell_y) == (7, 8)
    e.grid_pos = (9.0, 10.0)
    assert (e.grid_x, e.grid_y) == (9, 10)
    e.cell_pos = mcrfpy.Vector(11, 12)
    assert (e.grid_x, e.grid_y) == (11, 12)


def test_non_integral_floats_raise_value_error():
    grid = make_grid()
    e = mcrfpy.Entity(grid_pos=(3, 4), grid=grid)
    for name in ("grid_x", "grid_y", "cell_x", "cell_y"):
        try:
            setattr(e, name, 5.5)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{name} = 5.5 should raise ValueError")
    for name in ("grid_pos", "cell_pos"):
        for value in ((5.5, 1), (1, 2.25), mcrfpy.Vector(0.5, 1)):
            try:
                setattr(e, name, value)
            except ValueError:
                pass
            else:
                raise AssertionError(f"{name} = {value!r} should raise ValueError")
    for name in ("grid_x", "grid_pos"):
        bad = float("nan") if name == "grid_x" else (float("inf"), 0)
        try:
            setattr(e, name, bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{name} = {bad!r} should raise ValueError")
    # Nothing moved.
    assert (e.grid_x, e.grid_y) == (3, 4)
    assert (e.draw_pos.x, e.draw_pos.y) == (3.0, 4.0)


def test_non_numbers_raise_type_error():
    e = mcrfpy.Entity(grid_pos=(3, 4))
    for name, value in (("grid_x", "5"), ("cell_y", None), ("grid_pos", "ab"),
                        ("grid_pos", (1, "2")), ("cell_pos", 5)):
        try:
            setattr(e, name, value)
        except TypeError:
            pass
        else:
            raise AssertionError(f"{name} = {value!r} should raise TypeError")


tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
failed = 0
for t in tests:
    try:
        t()
        print(f"  PASS: {t.__name__}")
    except Exception as exc:
        failed += 1
        print(f"  FAIL: {t.__name__}: {type(exc).__name__}: {exc}")
if failed:
    print(f"FAIL: {failed} of {len(tests)}")
    sys.exit(1)
print("PASS")
sys.exit(0)
