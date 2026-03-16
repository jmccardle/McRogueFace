"""Unit test for #299: Entity step() callback and default_behavior."""
import mcrfpy
import sys

def test_step_callback_assignment():
    """step callback can be assigned and retrieved."""
    e = mcrfpy.Entity()
    assert e.step is None, "Initial step should be None"

    def my_step(trigger, data):
        pass

    e.step = my_step
    assert e.step is my_step, "step should be the assigned callable"
    print("PASS: step callback assignment")

def test_step_callback_clear():
    """Setting step to None clears the callback."""
    e = mcrfpy.Entity()
    e.step = lambda t, d: None
    assert e.step is not None

    e.step = None
    assert e.step is None, "step should be None after clearing"
    print("PASS: step callback clear")

def test_step_callback_type_check():
    """step rejects non-callable values."""
    e = mcrfpy.Entity()
    try:
        e.step = 42
        assert False, "Should have raised TypeError"
    except TypeError:
        pass
    print("PASS: step type check")

def test_default_behavior_roundtrip():
    """default_behavior property round-trips correctly."""
    e = mcrfpy.Entity()
    assert e.default_behavior == 0, "Initial default_behavior should be 0 (IDLE)"

    e.default_behavior = int(mcrfpy.Behavior.SEEK)
    assert e.default_behavior == 9

    e.default_behavior = int(mcrfpy.Behavior.IDLE)
    assert e.default_behavior == 0
    print("PASS: default_behavior round-trip")

def test_step_callback_subclass():
    """Subclass def step() overrides the C getter - this is expected behavior.
    Phase 3 grid.step() will check for subclass method override via PyObject_GetAttrString."""
    class Guard(mcrfpy.Entity):
        def on_step(self, trigger, data):
            self.stepped = True

    g = Guard()
    # The step property should be None (no callback assigned)
    assert g.step is None, "step callback should be None initially"

    # Subclass methods with different names are accessible
    assert hasattr(g, 'on_step'), "subclass should have on_step method"
    assert callable(g.on_step)
    print("PASS: subclass step method coexistence")

if __name__ == "__main__":
    test_step_callback_assignment()
    test_step_callback_clear()
    test_step_callback_type_check()
    test_default_behavior_roundtrip()
    test_step_callback_subclass()
    print("All #299 tests passed")
    sys.exit(0)
