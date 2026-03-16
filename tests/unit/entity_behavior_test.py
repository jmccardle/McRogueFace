"""Unit test for #300: EntityBehavior struct and behavior primitives."""
import mcrfpy
import sys

def make_grid():
    """Create a simple 20x20 walkable grid."""
    scene = mcrfpy.Scene("test300")
    mcrfpy.current_scene = scene
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)
    for y in range(20):
        for x in range(20):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
    return grid

def test_behavior_properties():
    """Behavior-related properties exist and have correct defaults."""
    e = mcrfpy.Entity()
    assert e.behavior_type == 0, f"Default behavior_type should be 0 (IDLE), got {e.behavior_type}"
    assert e.turn_order == 1, f"Default turn_order should be 1, got {e.turn_order}"
    assert abs(e.move_speed - 0.15) < 0.01, f"Default move_speed should be 0.15, got {e.move_speed}"
    assert e.target_label is None, f"Default target_label should be None, got {e.target_label}"
    assert e.sight_radius == 10, f"Default sight_radius should be 10, got {e.sight_radius}"
    print("PASS: behavior property defaults")

def test_behavior_property_setters():
    """Behavior properties can be set."""
    e = mcrfpy.Entity()
    e.turn_order = 5
    assert e.turn_order == 5

    e.move_speed = 0.3
    assert abs(e.move_speed - 0.3) < 0.01

    e.target_label = "player"
    assert e.target_label == "player"

    e.target_label = None
    assert e.target_label is None

    e.sight_radius = 15
    assert e.sight_radius == 15
    print("PASS: behavior property setters")

def test_set_behavior_noise():
    """set_behavior with NOISE4 type."""
    e = mcrfpy.Entity()
    e.set_behavior(int(mcrfpy.Behavior.NOISE4))
    assert e.behavior_type == int(mcrfpy.Behavior.NOISE4)
    print("PASS: set_behavior NOISE4")

def test_set_behavior_path():
    """set_behavior with PATH type and pre-computed path."""
    e = mcrfpy.Entity()
    path = [(1, 0), (2, 0), (3, 0)]
    e.set_behavior(int(mcrfpy.Behavior.PATH), path=path)
    assert e.behavior_type == int(mcrfpy.Behavior.PATH)
    print("PASS: set_behavior PATH")

def test_set_behavior_patrol():
    """set_behavior with PATROL type and waypoints."""
    e = mcrfpy.Entity()
    waypoints = [(5, 5), (10, 5), (10, 10), (5, 10)]
    e.set_behavior(int(mcrfpy.Behavior.PATROL), waypoints=waypoints)
    assert e.behavior_type == int(mcrfpy.Behavior.PATROL)
    print("PASS: set_behavior PATROL")

def test_set_behavior_sleep():
    """set_behavior with SLEEP type and turns."""
    e = mcrfpy.Entity()
    e.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=5)
    assert e.behavior_type == int(mcrfpy.Behavior.SLEEP)
    print("PASS: set_behavior SLEEP")

def test_set_behavior_reset():
    """set_behavior resets previous behavior state."""
    e = mcrfpy.Entity()
    e.set_behavior(int(mcrfpy.Behavior.PATROL), waypoints=[(1,1), (5,5)])
    assert e.behavior_type == int(mcrfpy.Behavior.PATROL)

    e.set_behavior(int(mcrfpy.Behavior.IDLE))
    assert e.behavior_type == int(mcrfpy.Behavior.IDLE)
    print("PASS: set_behavior reset")

def test_turn_order_zero_skip():
    """turn_order=0 should mean entity is skipped."""
    e = mcrfpy.Entity()
    e.turn_order = 0
    assert e.turn_order == 0
    print("PASS: turn_order=0")

if __name__ == "__main__":
    test_behavior_properties()
    test_behavior_property_setters()
    test_set_behavior_noise()
    test_set_behavior_path()
    test_set_behavior_patrol()
    test_set_behavior_sleep()
    test_set_behavior_reset()
    test_turn_order_zero_skip()
    print("All #300 tests passed")
    sys.exit(0)
