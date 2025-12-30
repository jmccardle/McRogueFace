#!/usr/bin/env python3
"""Test scene transitions to verify implementation and demonstrate usage."""

import mcrfpy
import sys
import time

def create_test_scenes():
    """Create several test scenes with different colored backgrounds."""
    
    # Scene 1: Red background
    mcrfpy.createScene("red_scene")
    ui1 = mcrfpy.sceneUI("red_scene")
    bg1 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(255, 0, 0, 255))
    label1 = mcrfpy.Caption(pos=(512, 384), text="RED SCENE", font=mcrfpy.Font.font_ui)
    label1.fill_color = mcrfpy.Color(255, 255, 255, 255)
    ui1.append(bg1)
    ui1.append(label1)

    # Scene 2: Blue background
    mcrfpy.createScene("blue_scene")
    ui2 = mcrfpy.sceneUI("blue_scene")
    bg2 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(0, 0, 255, 255))
    label2 = mcrfpy.Caption(pos=(512, 384), text="BLUE SCENE", font=mcrfpy.Font.font_ui)
    label2.fill_color = mcrfpy.Color(255, 255, 255, 255)
    ui2.append(bg2)
    ui2.append(label2)

    # Scene 3: Green background
    mcrfpy.createScene("green_scene")
    ui3 = mcrfpy.sceneUI("green_scene")
    bg3 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(0, 255, 0, 255))
    label3 = mcrfpy.Caption(pos=(512, 384), text="GREEN SCENE", font=mcrfpy.Font.font_ui)
    label3.fill_color = mcrfpy.Color(0, 0, 0, 255)  # Black text on green
    ui3.append(bg3)
    ui3.append(label3)

    # Scene 4: Menu scene with buttons
    mcrfpy.createScene("menu_scene")
    ui4 = mcrfpy.sceneUI("menu_scene")
    bg4 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(50, 50, 50, 255))

    title = mcrfpy.Caption(pos=(512, 100), text="SCENE TRANSITION DEMO", font=mcrfpy.Font.font_ui)
    title.fill_color = mcrfpy.Color(255, 255, 255, 255)
    ui4.append(bg4)
    ui4.append(title)

    # Add instruction text
    instructions = mcrfpy.Caption(pos=(512, 200), text="Press keys 1-6 for different transitions", font=mcrfpy.Font.font_ui)
    instructions.fill_color = mcrfpy.Color(200, 200, 200, 255)
    ui4.append(instructions)

    controls = mcrfpy.Caption(pos=(512, 250), text="1: Fade | 2: Slide Left | 3: Slide Right | 4: Slide Up | 5: Slide Down | 6: Instant", font=mcrfpy.Font.font_ui)
    controls.fill_color = mcrfpy.Color(150, 150, 150, 255)
    ui4.append(controls)

    scene_info = mcrfpy.Caption(pos=(512, 300), text="R: Red Scene | B: Blue Scene | G: Green Scene | M: Menu", font=mcrfpy.Font.font_ui)
    scene_info.fill_color = mcrfpy.Color(150, 150, 150, 255)
    ui4.append(scene_info)
    
    print("Created test scenes: red_scene, blue_scene, green_scene, menu_scene")

# Track current transition type
current_transition = "fade"
transition_duration = 1.0

def handle_key(key, action):
    """Handle keyboard input for scene transitions."""
    global current_transition, transition_duration
    
    if action != "start":
        return
    
    current_scene = mcrfpy.currentScene()
    
    # Number keys set transition type
    if key == "Num1":
        current_transition = "fade"
        print("Transition set to: fade")
    elif key == "Num2":
        current_transition = "slide_left"
        print("Transition set to: slide_left")
    elif key == "Num3":
        current_transition = "slide_right"
        print("Transition set to: slide_right")
    elif key == "Num4":
        current_transition = "slide_up"
        print("Transition set to: slide_up")
    elif key == "Num5":
        current_transition = "slide_down"
        print("Transition set to: slide_down")
    elif key == "Num6":
        current_transition = None  # Instant
        print("Transition set to: instant")
    
    # Letter keys change scene
    elif key == "R":
        if current_scene != "red_scene":
            print(f"Transitioning to red_scene with {current_transition}")
            if current_transition:
                mcrfpy.setScene("red_scene", current_transition, transition_duration)
            else:
                mcrfpy.setScene("red_scene")
    elif key == "B":
        if current_scene != "blue_scene":
            print(f"Transitioning to blue_scene with {current_transition}")
            if current_transition:
                mcrfpy.setScene("blue_scene", current_transition, transition_duration)
            else:
                mcrfpy.setScene("blue_scene")
    elif key == "G":
        if current_scene != "green_scene":
            print(f"Transitioning to green_scene with {current_transition}")
            if current_transition:
                mcrfpy.setScene("green_scene", current_transition, transition_duration)
            else:
                mcrfpy.setScene("green_scene")
    elif key == "M":
        if current_scene != "menu_scene":
            print(f"Transitioning to menu_scene with {current_transition}")
            if current_transition:
                mcrfpy.setScene("menu_scene", current_transition, transition_duration)
            else:
                mcrfpy.setScene("menu_scene")
    elif key == "Escape":
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
            mcrfpy.setScene(scene)
        time.sleep(2)  # Wait for transition to complete plus viewing time
    
    print("Automatic test complete!")
    sys.exit(0)

# Main test setup
print("=== Scene Transition Test ===")
create_test_scenes()

# Start with menu scene
mcrfpy.setScene("menu_scene")

# Set up keyboard handler
mcrfpy.keypressScene(handle_key)

# Option to run automatic test
if len(sys.argv) > 1 and sys.argv[1] == "--auto":
    mcrfpy.setTimer("auto_test", test_automatic_transitions, 1000)
else:
    print("\nManual test mode. Use keyboard controls shown on screen.")
    print("Run with --auto flag for automatic transition demo.")