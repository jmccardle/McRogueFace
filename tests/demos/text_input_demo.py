#!/usr/bin/env python3
"""
Text Input Demo with Auto-Test
Demonstrates the text input widget system with automated testing
"""

import mcrfpy
from mcrfpy import automation
import sys
from text_input_widget import FocusManager, TextInput


def test_text_input(timer_name):
    """Automated test that runs after scene is loaded"""
    print("Testing text input widget system...")
    
    # Take a screenshot of the initial state
    automation.screenshot("text_input_initial.png")
    
    # Simulate typing in the first field
    print("Clicking on first field...")
    automation.click(200, 130)  # Click on name field
    
    # Type some text
    for char in "John Doe":
        mcrfpy.keypressScene("text_input_demo", char)
    
    # Tab to next field
    mcrfpy.keypressScene("text_input_demo", "Tab")
    
    # Type email
    for char in "john@example.com":
        mcrfpy.keypressScene("text_input_demo", char)
    
    # Tab to comment field
    mcrfpy.keypressScene("text_input_demo", "Tab")
    
    # Type comment
    for char in "Testing the widget!":
        mcrfpy.keypressScene("text_input_demo", char)
    
    # Take final screenshot
    automation.screenshot("text_input_filled.png")
    
    print("Text input test complete!")
    print("Screenshots saved: text_input_initial.png, text_input_filled.png")
    
    # Exit after test
    sys.exit(0)


def create_demo():
    """Create a demo scene with multiple text input fields"""
    mcrfpy.createScene("text_input_demo")
    scene = mcrfpy.sceneUI("text_input_demo")
    
    # Create background
    bg = mcrfpy.Frame(0, 0, 800, 600)
    bg.fill_color = (40, 40, 40, 255)
    scene.append(bg)
    
    # Title
    title = mcrfpy.Caption(10, 10, "Text Input Widget Demo - Auto Test")
    title.color = (255, 255, 255, 255)
    scene.append(title)
    
    # Instructions
    instructions = mcrfpy.Caption(10, 50, "This will automatically test the text input system")
    instructions.color = (200, 200, 200, 255)
    scene.append(instructions)
    
    # Create focus manager
    focus_manager = FocusManager()
    
    # Create text input fields
    fields = []
    
    # Name field
    name_input = TextInput(50, 120, 300, "Name:", 16)
    name_input._focus_manager = focus_manager
    focus_manager.register(name_input)
    scene.append(name_input.frame)
    if hasattr(name_input, 'label_text'):
        scene.append(name_input.label_text)
    scene.append(name_input.text_display)
    scene.append(name_input.cursor)
    fields.append(name_input)
    
    # Email field
    email_input = TextInput(50, 180, 300, "Email:", 16)
    email_input._focus_manager = focus_manager
    focus_manager.register(email_input)
    scene.append(email_input.frame)
    if hasattr(email_input, 'label_text'):
        scene.append(email_input.label_text)
    scene.append(email_input.text_display)
    scene.append(email_input.cursor)
    fields.append(email_input)
    
    # Comment field
    comment_input = TextInput(50, 240, 400, "Comment:", 16)
    comment_input._focus_manager = focus_manager
    focus_manager.register(comment_input)
    scene.append(comment_input.frame)
    if hasattr(comment_input, 'label_text'):
        scene.append(comment_input.label_text)
    scene.append(comment_input.text_display)
    scene.append(comment_input.cursor)
    fields.append(comment_input)
    
    # Result display
    result_text = mcrfpy.Caption(50, 320, "Values will appear here as you type...")
    result_text.color = (150, 255, 150, 255)
    scene.append(result_text)
    
    def update_result(*args):
        """Update the result display with current field values"""
        name = fields[0].get_text()
        email = fields[1].get_text()
        comment = fields[2].get_text()
        result_text.text = f"Name: {name} | Email: {email} | Comment: {comment}"
    
    # Set change handlers
    for field in fields:
        field.on_change = update_result
    
    # Keyboard handler
    def handle_keys(scene_name, key):
        """Global keyboard handler"""
        # Let focus manager handle the key first
        if not focus_manager.handle_key(key):
            # Handle focus switching
            if key == "Tab":
                focus_manager.focus_next()
            elif key == "Escape":
                print("Demo terminated by user")
                sys.exit(0)
    
    mcrfpy.keypressScene("text_input_demo", handle_keys)
    
    # Set the scene
    mcrfpy.setScene("text_input_demo")
    
    # Schedule the automated test
    mcrfpy.setTimer("test", test_text_input, 500)  # Run test after 500ms


if __name__ == "__main__":
    create_demo()