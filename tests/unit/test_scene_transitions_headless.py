#!/usr/bin/env python3
"""Test scene transitions in headless mode."""

import mcrfpy
import sys

failures = []

def check(cond, msg):
    if cond:
        print(f"  ok: {msg}")
    else:
        print(f"  FAIL: {msg}")
        failures.append(msg)

def test_scene_transitions():
    """Test all scene transition types."""

    # Create two simple scenes
    print("Creating test scenes...")

    # Scene 1
    scene1 = mcrfpy.Scene("scene1")
    ui1 = scene1.children
    frame1 = mcrfpy.Frame(pos=(0, 0), size=(100, 100), fill_color=mcrfpy.Color(255, 0, 0))
    ui1.append(frame1)

    # Scene 2
    scene2 = mcrfpy.Scene("scene2")
    ui2 = scene2.children
    frame2 = mcrfpy.Frame(pos=(0, 0), size=(100, 100), fill_color=mcrfpy.Color(0, 0, 255))
    ui2.append(frame2)

    scenes = {"scene1": scene1, "scene2": scene2}

    # Test each transition type. mcrfpy.setScene(name, str, duration) is gone;
    # transitions are now scene.activate(mcrfpy.Transition.X, duration).
    transitions = [
        (mcrfpy.Transition.FADE, 0.5),
        (mcrfpy.Transition.SLIDE_LEFT, 0.5),
        (mcrfpy.Transition.SLIDE_RIGHT, 0.5),
        (mcrfpy.Transition.SLIDE_UP, 0.5),
        (mcrfpy.Transition.SLIDE_DOWN, 0.5),
        (None, 0.0),  # Instant
    ]

    print("\nTesting scene transitions:")

    # Start with scene1
    scene1.activate()
    check(mcrfpy.current_scene.name == "scene1",
          f"initial scene is scene1 (got {mcrfpy.current_scene.name})")

    for trans_type, duration in transitions:
        source = mcrfpy.current_scene.name
        target = "scene2" if source == "scene1" else "scene1"
        target_scene = scenes[target]

        if trans_type is not None:
            print(f"\nTransitioning to {target} with {trans_type!r} (duration: {duration}s)")
            target_scene.activate(trans_type, duration)

            # A transition is in flight: the outgoing scene stays current until it
            # completes, and headless only advances when we call mcrfpy.step().
            check(mcrfpy.current_scene.name == source,
                  f"mid-transition current_scene is still {source}")

            # Half the duration elapsed -> still not switched.
            steps = int(duration / 0.05)
            for _ in range(steps // 2):
                mcrfpy.step(0.05)
            check(mcrfpy.current_scene.name == source,
                  f"halfway through {trans_type!r}, current_scene is still {source}")

            # Run past the end of the transition.
            for _ in range(steps):
                mcrfpy.step(0.05)
        else:
            print(f"\nTransitioning to {target} instantly")
            mcrfpy.current_scene = target_scene

        check(mcrfpy.current_scene.name == target,
              f"after transition, current_scene is {target}")
        check(target_scene.active is True, f"{target}.active is True")
        check(scenes[source].active is False, f"{source}.active is False")

    print("\nAll scene transition types tested.")

if __name__ == "__main__":
    test_scene_transitions()
    if failures:
        print(f"\nFAIL: {len(failures)} check(s) failed")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nPASS")
    sys.exit(0)
