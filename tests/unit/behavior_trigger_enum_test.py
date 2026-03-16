"""Unit test for #297/#298: Behavior and Trigger enums."""
import mcrfpy
import sys

def test_behavior_values():
    """All Behavior enum values are accessible and have correct int values."""
    expected = {
        "IDLE": 0, "CUSTOM": 1, "NOISE4": 2, "NOISE8": 3,
        "PATH": 4, "WAYPOINT": 5, "PATROL": 6, "LOOP": 7,
        "SLEEP": 8, "SEEK": 9, "FLEE": 10,
    }
    for name, value in expected.items():
        b = getattr(mcrfpy.Behavior, name)
        assert int(b) == value, f"Behavior.{name} should be {value}, got {int(b)}"
    print("PASS: All Behavior values correct")

def test_trigger_values():
    """All Trigger enum values are accessible and have correct int values."""
    expected = {"DONE": 0, "BLOCKED": 1, "TARGET": 2}
    for name, value in expected.items():
        t = getattr(mcrfpy.Trigger, name)
        assert int(t) == value, f"Trigger.{name} should be {value}, got {int(t)}"
    print("PASS: All Trigger values correct")

def test_string_comparison():
    """Enums compare equal to their name strings."""
    assert mcrfpy.Behavior.IDLE == "IDLE"
    assert mcrfpy.Behavior.SEEK == "SEEK"
    assert mcrfpy.Trigger.DONE == "DONE"
    assert not (mcrfpy.Behavior.IDLE == "SEEK")
    print("PASS: String comparison works")

def test_inequality():
    """__ne__ works correctly for both string and int."""
    assert mcrfpy.Behavior.IDLE != "SEEK"
    assert not (mcrfpy.Behavior.IDLE != "IDLE")
    assert mcrfpy.Trigger.DONE != 1
    assert not (mcrfpy.Trigger.DONE != 0)
    print("PASS: Inequality works")

def test_int_comparison():
    """Enums compare equal to their integer values."""
    assert mcrfpy.Behavior.FLEE == 10
    assert mcrfpy.Trigger.BLOCKED == 1
    print("PASS: Int comparison works")

def test_repr():
    """Repr format is ClassName.MEMBER."""
    assert repr(mcrfpy.Behavior.IDLE) == "Behavior.IDLE"
    assert repr(mcrfpy.Trigger.TARGET) == "Trigger.TARGET"
    print("PASS: Repr format correct")

def test_hashable():
    """Enum values are hashable (can be used in sets/dicts)."""
    s = {mcrfpy.Behavior.IDLE, mcrfpy.Behavior.SEEK}
    assert len(s) == 2
    d = {mcrfpy.Trigger.DONE: "done", mcrfpy.Trigger.TARGET: "target"}
    assert d[mcrfpy.Trigger.DONE] == "done"
    print("PASS: Hashable")

if __name__ == "__main__":
    test_behavior_values()
    test_trigger_values()
    test_string_comparison()
    test_inequality()
    test_int_comparison()
    test_repr()
    test_hashable()
    print("All #297/#298 tests passed")
    sys.exit(0)
