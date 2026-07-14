#!/usr/bin/env python3
"""Test scene transitions to verify implementation and demonstrate usage.

Headless model (#350): mcrfpy.step(dt) is the only clock -- transitions only
advance when we step. current_scene stays on the OUTGOING scene for the whole
duration of a non-instant transition, and flips to the incoming scene when the
transition finishes.
"""

import mcrfpy
from mcrfpy import automation
import sys

red_scene, blue_scene, green_scene, menu_scene = None, None, None, None # global scoping

failures = []

def check(label, condition):
    if condition:
        print(f"  ok  : {label}")
    else:
        print(f"  FAIL: {label}")
        failures.append(label)

def create_test_scenes():
    """Create several test scenes with different colored backgrounds."""
    global red_scene, blue_scene, green_scene, menu_scene
    # Scene 1: Red background
    red_scene = mcrfpy.Scene("red_scene")
    ui1 = red_scene.children
    bg1 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(255, 0, 0, 255))
    label1 = mcrfpy.Caption(pos=(512, 384), text="RED SCENE", font=mcrfpy.default_font)
    label1.fill_color = mcrfpy.Color(255, 255, 255, 255)
    ui1.append(bg1)
    ui1.append(label1)

    # Scene 2: Blue background
    blue_scene = mcrfpy.Scene("blue_scene")
    ui2 = blue_scene.children
    bg2 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(0, 0, 255, 255))
    label2 = mcrfpy.Caption(pos=(512, 384), text="BLUE SCENE", font=mcrfpy.default_font)
    label2.fill_color = mcrfpy.Color(255, 255, 255, 255)
    ui2.append(bg2)
    ui2.append(label2)

    # Scene 3: Green background
    green_scene = mcrfpy.Scene("green_scene")
    ui3 = green_scene.children
    bg3 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(0, 255, 0, 255))
    label3 = mcrfpy.Caption(pos=(512, 384), text="GREEN SCENE", font=mcrfpy.default_font)
    label3.fill_color = mcrfpy.Color(0, 0, 0, 255)  # Black text on green
    ui3.append(bg3)
    ui3.append(label3)

    # Scene 4: Menu scene with buttons
    menu_scene = mcrfpy.Scene("menu_scene")
    ui4 = menu_scene.children
    bg4 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(50, 50, 50, 255))

    title = mcrfpy.Caption(pos=(512, 100), text="SCENE TRANSITION DEMO", font=mcrfpy.default_font)
    title.fill_color = mcrfpy.Color(255, 255, 255, 255)
    ui4.append(bg4)
    ui4.append(title)

    # Add instruction text
    instructions = mcrfpy.Caption(pos=(512, 200), text="Press keys 1-6 for different transitions", font=mcrfpy.default_font)
    instructions.fill_color = mcrfpy.Color(200, 200, 200, 255)
    ui4.append(instructions)

    controls = mcrfpy.Caption(pos=(512, 250), text="1: Fade | 2: Slide Left | 3: Slide Right | 4: Slide Up | 5: Slide Down | 6: Instant", font=mcrfpy.default_font)
    controls.fill_color = mcrfpy.Color(150, 150, 150, 255)
    ui4.append(controls)

    scene_info = mcrfpy.Caption(pos=(512, 300), text="R: Red Scene | B: Blue Scene | G: Green Scene | M: Menu", font=mcrfpy.default_font)
    scene_info.fill_color = mcrfpy.Color(150, 150, 150, 255)
    ui4.append(scene_info)

    print("Created test scenes: red_scene, blue_scene, green_scene, menu_scene")

# Track current transition type
current_transition = mcrfpy.Transition.FADE
transition_duration = 1.0

def handle_key(key, action):
    """Handle keyboard input for scene transitions."""
    global current_transition, transition_duration

    if action != mcrfpy.InputState.PRESSED:
        return

    # Number keys set transition type
    keyselections = {
            mcrfpy.Key.NUM_1: mcrfpy.Transition.FADE,
            mcrfpy.Key.NUM_2: mcrfpy.Transition.SLIDE_LEFT,
            mcrfpy.Key.NUM_3: mcrfpy.Transition.SLIDE_RIGHT,
            mcrfpy.Key.NUM_4: mcrfpy.Transition.SLIDE_UP,
            mcrfpy.Key.NUM_5: mcrfpy.Transition.SLIDE_DOWN,
            mcrfpy.Key.NUM_6: mcrfpy.Transition.NONE
            }
    if key in keyselections:
        current_transition = keyselections[key]
        print(f"Transition set to: {current_transition}")

    # Letter keys change scene
    keytransitions = {
            mcrfpy.Key.R: red_scene,
            mcrfpy.Key.B: blue_scene,
            mcrfpy.Key.G: green_scene,
            mcrfpy.Key.M: menu_scene
            }
    if key in keytransitions:
        if mcrfpy.current_scene != keytransitions[key]:
            print(f"Transitioning to {keytransitions[key].name} with {current_transition}")
            keytransitions[key].activate(current_transition, transition_duration)


def press(key_name):
    """Send a real key press/release through the engine to the active scene."""
    automation.keyDown(key_name)
    automation.keyUp(key_name)


def run_transition(target, trans_type, duration=1.0):
    """Activate `target` with `trans_type` and drive the clock until it lands."""
    origin = mcrfpy.current_scene
    target.activate(trans_type, duration)

    if trans_type == mcrfpy.Transition.NONE:
        # Instant: no time needs to pass at all.
        check(f"{trans_type}: instant switch to {target.name}",
              mcrfpy.current_scene == target)
    else:
        # The outgoing scene stays current until the transition finishes.
        check(f"{trans_type}: still on {origin.name} at t=0",
              mcrfpy.current_scene == origin)
        mcrfpy.step(duration / 2.0)
        check(f"{trans_type}: still on {origin.name} mid-transition",
              mcrfpy.current_scene == origin)
        # Step past the end of the transition.
        for _ in range(4):
            mcrfpy.step(duration / 2.0)
            if mcrfpy.current_scene == target:
                break
        check(f"{trans_type}: arrived at {target.name}",
              mcrfpy.current_scene == target)

    check(f"{trans_type}: {target.name}.active", target.active)
    if origin != target:
        check(f"{trans_type}: {origin.name} deactivated", not origin.active)


def test_automatic_transitions():
    """Run through every transition type, asserting each one lands."""
    print("\nRunning automatic transition test...")
    transitions = [
        (mcrfpy.Transition.FADE, red_scene),
        (mcrfpy.Transition.SLIDE_LEFT, blue_scene),
        (mcrfpy.Transition.SLIDE_RIGHT, green_scene),
        (mcrfpy.Transition.SLIDE_UP, red_scene),
        (mcrfpy.Transition.SLIDE_DOWN, menu_scene),
        (mcrfpy.Transition.NONE, blue_scene),  # Instant
    ]
    for trans_type, scene in transitions:
        run_transition(scene, trans_type)
    print("Automatic test complete!")


def test_key_driven_transitions():
    """Exercise the keyboard handler itself: number key picks the transition,
    letter key picks the scene."""
    print("\nRunning key-driven transition test...")

    press("6")  # Transition.NONE
    press("m")  # -> menu_scene, instantly
    mcrfpy.step(0.0)
    check("key '6'+'m': instant to menu_scene", mcrfpy.current_scene == menu_scene)

    press("3")  # Transition.SLIDE_RIGHT
    press("g")  # -> green_scene over transition_duration
    mcrfpy.step(0.0)
    check("key '3'+'g': still on menu_scene while sliding",
          mcrfpy.current_scene == menu_scene)
    for _ in range(6):
        mcrfpy.step(0.25)
        if mcrfpy.current_scene == green_scene:
            break
    check("key '3'+'g': arrived at green_scene",
          mcrfpy.current_scene == green_scene)
    check("green_scene.active after key transition", green_scene.active)

    # Pressing the letter key for the scene we're already on is a no-op.
    press("g")
    mcrfpy.step(0.1)
    check("key 'g' on green_scene is a no-op", mcrfpy.current_scene == green_scene)


# Main test setup
print("=== Scene Transition Test ===")
create_test_scenes()

# Start with menu scene
menu_scene.activate()
check("menu_scene is the starting scene", mcrfpy.current_scene == menu_scene)
check("menu_scene.active", menu_scene.active)
check("menu_scene has 5 children", len(menu_scene.children) == 5)

# Set up keyboard handler
for s in (red_scene, blue_scene, green_scene, menu_scene):
    s.on_key = handle_key

test_automatic_transitions()
test_key_driven_transitions()

if failures:
    print(f"\nFAIL: {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("\nPASS")
sys.exit(0)
