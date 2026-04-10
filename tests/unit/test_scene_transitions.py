#!/usr/bin/env python3
"""Test scene transitions to verify implementation and demonstrate usage."""

import mcrfpy
import sys
import time

red_scene, blue_scene, green_scene, menu_scene = None, None, None, None # global scoping

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
    
    current_scene = (mcrfpy.current_scene.name if mcrfpy.current_scene else None)
    
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
    #if key == mcrfpy.Key.NUM_1:
    #    current_transition = "fade"
    #    print("Transition set to: fade")
    #elif key == mcrfpy.Key.NUM_2:
    #    current_transition = "slide_left"
    #    print("Transition set to: slide_left")
    #elif key == mcrfpy.Key.NUM_3:
    #    current_transition = "slide_right"
    #    print("Transition set to: slide_right")
    #elif key == mcrfpy.Key.NUM_4:
    #    current_transition = "slide_up"
    #    print("Transition set to: slide_up")
    #elif key == mcrfpy.Key.NUM_5:
    #    current_transition = "slide_down"
    #    print("Transition set to: slide_down")
    #elif key == mcrfpy.Key.NUM_6:
    #    current_transition = None  # Instant
    #    print("Transition set to: instant")
    
    # Letter keys change scene
    keytransitions = {
            mcrfpy.Key.R: red_scene,
            mcrfpy.Key.B: blue_scene,
            mcrfpy.Key.G: green_scene,
            mcrfpy.Key.M: menu_scene
            }
    if key in keytransitions:
        if mcrfpy.current_scene != keytransitions[key]:
            keytransitions[key].activate(current_transition, transition_duration)
    #elif key == mcrfpy.Key.R:
    #    if current_scene != "red_scene":
    #        print(f"Transitioning to red_scene with {current_transition}")
    #        if current_transition:
    #            mcrfpy.setScene("red_scene", current_transition, transition_duration)
    #        else:
    #            red_scene.activate()
    #elif key == mcrfpy.Key.B:
    #    if current_scene != "blue_scene":
    #        print(f"Transitioning to blue_scene with {current_transition}")
    #        if current_transition:
    #            mcrfpy.setScene("blue_scene", current_transition, transition_duration)
    #        else:
    #            blue_scene.activate()
    #elif key == mcrfpy.Key.G:
    #    if current_scene != "green_scene":
    #        print(f"Transitioning to green_scene with {current_transition}")
    #        if current_transition:
    #            mcrfpy.setScene("green_scene", current_transition, transition_duration)
    #        else:
    #            green_scene.activate()
    #elif key == mcrfpy.Key.M:
    #    if current_scene != "menu_scene":
    #        print(f"Transitioning to menu_scene with {current_transition}")
    #        if current_transition:
    #            mcrfpy.setScene("menu_scene", current_transition, transition_duration)
    #        else:
    #            menu_scene.activate()
    elif key == mcrfpy.Key.ESCAPE:
        print("Exiting...")
        sys.exit(0)

def test_automatic_transitions(delay):
    """Run through all transitions automatically after a delay."""
    transitions = [
        ("fade", "red_scene"),
        ("slide_left", "blue_scene"),
        ("slide_right", "green_scene"),
        ("slide_up", "red_scene"),
        ("slide_down", "menu_scene"),
        (None, "blue_scene"),  # Instant
    ]
    
    print("\nRunning automatic transition test...")
    for i, (trans_type, scene) in enumerate(transitions):
        if trans_type:
            print(f"Transition {i+1}: {trans_type} to {scene}")
            mcrfpy.setScene(scene, trans_type, 1.0)
        else:
            print(f"Transition {i+1}: instant to {scene}")
            mcrfpy.current_scene = scene
        time.sleep(2)  # Wait for transition to complete plus viewing time
    
    print("Automatic test complete!")
    sys.exit(0)

# Main test setup
print("=== Scene Transition Test ===")
create_test_scenes()

# Start with menu scene
menu_scene.activate()

# Set up keyboard handler
for s in (red_scene, blue_scene, green_scene, menu_scene):
    s.on_key = handle_key
#menu_scene.on_key = handle_key

# Option to run automatic test
if len(sys.argv) > 1 and sys.argv[1] == "--auto":
    mcrfpy.Timer("auto_test", lambda t, r: test_automatic_transitions(r), 1000, once=True)
else:
    print("\nManual test mode. Use keyboard controls shown on screen.")
    print("Run with --auto flag for automatic transition demo.")
