#!/usr/bin/env python3
"""
Issue #379: a transition into the FIRST scene must not leave current_scene as None.

While a transition runs, mcrfpy.current_scene reports the OUTGOING scene -- "current"
means "what is on screen". That is a sane convention for scene->scene. But at startup
there is no outgoing scene, so configuring default_transition before the first
activation made the engine fade from nothing, and current_scene read None for the
transition's entire duration:

    mcrfpy.default_transition = mcrfpy.Transition.FADE
    mcrfpy.default_transition_duration = 1.0
    mcrfpy.current_scene = s
    print(mcrfpy.current_scene)   # None -- assigned one line ago

A transition with nothing to transition from is not a transition. changeScene() now
takes the immediate path when there is no outgoing scene.

Found by the tests/snippets/ gate: 062_scene_transition_fade.py and
063_scene_transition_slide.py both configure a transition and then activate their first
scene, which is the natural way to write that sample.
"""

import sys

import mcrfpy

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"FAIL: {msg}")
    else:
        print(f"  ok: {msg}")


def frame():
    return mcrfpy.Frame(pos=(0, 0), size=(10, 10))


def test_first_scene_with_transition_is_immediate():
    """The bug: no outgoing scene means nothing to fade from."""
    s = mcrfpy.Scene("first")
    s.children.append(frame())

    mcrfpy.default_transition = mcrfpy.Transition.FADE
    mcrfpy.default_transition_duration = 1.0
    mcrfpy.current_scene = s

    got = mcrfpy.current_scene
    check(got is not None, "current_scene is not None right after the first activation")
    check(got is not None and got.name == "first",
          f"current_scene is the scene we activated (got {got!r})")

    mcrfpy.step(0.016)
    got = mcrfpy.current_scene
    check(got is not None and got.name == "first",
          "it is still the activated scene after a step")


def test_scene_to_scene_transition_still_defers():
    """The existing convention must not regress: mid-transition, current_scene is the
    OUTGOING scene, and only becomes the incoming one on completion."""
    a = mcrfpy.Scene("from_a")
    a.children.append(frame())
    b = mcrfpy.Scene("to_b")
    b.children.append(frame())

    mcrfpy.default_transition = mcrfpy.Transition.NONE
    mcrfpy.default_transition_duration = 0.0
    mcrfpy.current_scene = a
    check(mcrfpy.current_scene.name == "from_a", "scene a is active with no transition")

    mcrfpy.default_transition = mcrfpy.Transition.FADE
    mcrfpy.default_transition_duration = 1.0
    mcrfpy.current_scene = b

    mcrfpy.step(0.1)
    check(mcrfpy.current_scene.name == "from_a",
          "mid-transition, current_scene is still the outgoing scene")

    for _ in range(20):
        mcrfpy.step(0.1)
    check(mcrfpy.current_scene.name == "to_b",
          "after the transition completes, current_scene is the incoming scene")


def main():
    test_first_scene_with_transition_is_immediate()
    test_scene_to_scene_transition_still_defers()

    if failures:
        print(f"\nFAILED ({len(failures)} checks)")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nPASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
