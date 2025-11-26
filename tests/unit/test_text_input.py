#!/usr/bin/env python3
"""
Test the text input widget system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'scripts'))

import mcrfpy
from text_input_widget import FocusManager, TextInput


def create_demo():
    """Create demo scene with text inputs"""
    # Create scene
    mcrfpy.createScene("text_demo")
    scene = mcrfpy.sceneUI("text_demo")
    
    # Background
    bg = mcrfpy.Frame(0, 0, 800, 600)
    bg.fill_color = (40, 40, 40, 255)
    scene.append(bg)
    
    # Title
    title = mcrfpy.Caption("Text Input Widget Demo", 20, 20)
    title.fill_color = (255, 255, 255, 255)
    scene.append(title)
    
    # Focus manager
    focus_mgr = FocusManager()
    
    # Create inputs
    inputs = []
    
    # Name input
    name_input = TextInput(50, 100, 300, label="Name:", placeholder="Enter your name")
    name_input._focus_manager = focus_mgr
    focus_mgr.register(name_input)
    name_input.add_to_scene(scene)
    inputs.append(name_input)
    
    # Email input
    email_input = TextInput(50, 160, 300, label="Email:", placeholder="user@example.com")
    email_input._focus_manager = focus_mgr
    focus_mgr.register(email_input)
    email_input.add_to_scene(scene)
    inputs.append(email_input)
    
    # Tags input
    tags_input = TextInput(50, 220, 400, label="Tags:", placeholder="comma, separated, tags")
    tags_input._focus_manager = focus_mgr
    focus_mgr.register(tags_input)
    tags_input.add_to_scene(scene)
    inputs.append(tags_input)
    
    # Comment input
    comment_input = TextInput(50, 280, 500, height=30, label="Comment:", placeholder="Add a comment...")
    comment_input._focus_manager = focus_mgr
    focus_mgr.register(comment_input)
    comment_input.add_to_scene(scene)
    inputs.append(comment_input)
    
    # Status display
    status = mcrfpy.Caption("Ready for input...", 50, 360)
    status.fill_color = (150, 255, 150, 255)
    scene.append(status)
    
    # Update handler
    def update_status(text=None):
        values = [inp.get_text() for inp in inputs]
        status.text = f"Data: {values[0]} | {values[1]} | {values[2]} | {values[3]}"
    
    # Set change handlers
    for inp in inputs:
        inp.on_change = update_status
    
    # Keyboard handler
    def handle_keys(scene_name, key):
        if not focus_mgr.handle_key(key):
            if key == "Tab":
                focus_mgr.focus_next()
            elif key == "Escape":
                print("\nFinal values:")
                for i, inp in enumerate(inputs):
                    print(f"  Field {i+1}: '{inp.get_text()}'")
                sys.exit(0)
    
    mcrfpy.keypressScene("text_demo", handle_keys)
    mcrfpy.setScene("text_demo")
    
    # Run demo test
    def run_test(timer_name):
        print("\n=== Text Input Widget Test ===")
        print("Features:")
        print("- Click to focus fields")
        print("- Tab to navigate between fields")
        print("- Type to enter text")
        print("- Backspace/Delete to edit")
        print("- Home/End for cursor movement")
        print("- Placeholder text")
        print("- Visual focus indication")
        print("- Press Escape to exit")
        print("\nTry it out!")
    
    mcrfpy.setTimer("info", run_test, 100)


if __name__ == "__main__":
    create_demo()