"""Regression test for #344 - cached Key/InputState enum members.

Per-keypress dispatch was changed from constructing enum members via
EnumMeta.__call__ (PyObject_CallFunction) to returning memoized members. This
test verifies the handler still receives correct, identity-stable enum members
with intact equality.
"""
import mcrfpy
from mcrfpy import automation
import sys


def main():
    scene = mcrfpy.Scene("t344")
    mcrfpy.current_scene = scene

    seen = []

    def on_key(key, state):
        seen.append((key, state))

    scene.on_key = on_key

    # Fire the same key several times; cached members must be reused correctly.
    for _ in range(3):
        automation.keyDown('a')
        automation.keyUp('a')

    assert len(seen) == 6, f"expected 6 events, got {len(seen)}"

    # Correct enum types and values
    for key, state in seen:
        assert isinstance(key, mcrfpy.Key), f"key not a Key: {type(key)}"
        assert isinstance(state, mcrfpy.InputState), f"state not InputState: {type(state)}"
        assert key == mcrfpy.Key.A, f"expected Key.A, got {key}"

    # Memoization => identity stability across repeated events
    first_key = seen[0][0]
    assert all(k is first_key for k, _ in seen), "cached Key members should be identical objects"

    down_states = [s for _, s in seen[0::2]]
    up_states = [s for _, s in seen[1::2]]
    assert all(s == mcrfpy.InputState.PRESSED for s in down_states), down_states
    assert all(s == mcrfpy.InputState.RELEASED for s in up_states), up_states
    assert down_states[0] is down_states[1], "cached InputState.PRESSED should be identical"

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
