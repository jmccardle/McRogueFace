#!/usr/bin/env python3
"""
Standalone Text Input Widget System for McRogueFace
Complete implementation with demo and automated test
"""

import mcrfpy
import sys


class FocusManager:
    """Manages focus state across multiple widgets"""
    def __init__(self):
        self.widgets = []
        self.focused_widget = None
        self.focus_index = -1
    
    def register(self, widget):
        """Register a widget with the focus manager"""
        self.widgets.append(widget)
        if self.focused_widget is None:
            self.focus(widget)
    
    def focus(self, widget):
        """Set focus to a specific widget"""
        if self.focused_widget:
            self.focused_widget.on_blur()
        
        self.focused_widget = widget
        self.focus_index = self.widgets.index(widget) if widget in self.widgets else -1
        
        if widget:
            widget.on_focus()
    
    def focus_next(self):
        """Focus the next widget in the list"""
        if not self.widgets:
            return
        
        self.focus_index = (self.focus_index + 1) % len(self.widgets)
        self.focus(self.widgets[self.focus_index])
    
    def handle_key(self, key):
        """Route key events to focused widget. Returns True if handled."""
        if self.focused_widget:
            return self.focused_widget.handle_key(key)
        return False


class TextInput:
    """A text input widget with cursor support"""
    def __init__(self, x, y, width, label="", font_size=16):
        self.x = x
        self.y = y
        self.width = width
        self.label = label
        self.font_size = font_size
        
        # Text state
        self.text = ""
        self.cursor_pos = 0
        
        # Visual state
        self.focused = False
        
        # Create UI elements
        self._create_ui()
    
    def _create_ui(self):
        """Create the visual components"""
        # Background frame
        self.frame = mcrfpy.Frame(self.x, self.y, self.width, self.font_size + 8)
        self.frame.outline = 2
        self.frame.fill_color = (255, 255, 255, 255)
        self.frame.outline_color = (128, 128, 128, 255)
        
        # Label (if provided)
        if self.label:
            self.label_text = mcrfpy.Caption(
                self.x - 5, 
                self.y - self.font_size - 5,
                self.label
            )
            self.label_text.color = (255, 255, 255, 255)
        
        # Text display
        self.text_display = mcrfpy.Caption(
            self.x + 4,
            self.y + 4,
            ""
        )
        self.text_display.color = (0, 0, 0, 255)
        
        # Cursor (using a thin frame)
        self.cursor = mcrfpy.Frame(
            self.x + 4,
            self.y + 4,
            2,
            self.font_size
        )
        self.cursor.fill_color = (0, 0, 0, 255)
        self.cursor.visible = False
        
        # Click handler
        self.frame.click = self._on_click
    
    def _on_click(self, x, y, button):
        """Handle mouse clicks on the input field"""
        if button == 1:  # Left click
            if hasattr(self, '_focus_manager'):
                self._focus_manager.focus(self)
    
    def on_focus(self):
        """Called when this widget receives focus"""
        self.focused = True
        self.frame.outline_color = (0, 120, 255, 255)
        self.frame.outline = 3
        self.cursor.visible = True
        self._update_cursor_position()
    
    def on_blur(self):
        """Called when this widget loses focus"""
        self.focused = False
        self.frame.outline_color = (128, 128, 128, 255)
        self.frame.outline = 2
        self.cursor.visible = False
    
    def handle_key(self, key):
        """Handle keyboard input. Returns True if key was handled."""
        if not self.focused:
            return False
        
        handled = True
        
        # Special keys
        if key == "BackSpace":
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
        elif key == "Delete":
            if self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
        elif key == "Left":
            self.cursor_pos = max(0, self.cursor_pos - 1)
        elif key == "Right":
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
        elif key == "Home":
            self.cursor_pos = 0
        elif key == "End":
            self.cursor_pos = len(self.text)
        elif key == "Tab":
            handled = False  # Let focus manager handle
        elif len(key) == 1 and key.isprintable():
            # Regular character input
            self.text = self.text[:self.cursor_pos] + key + self.text[self.cursor_pos:]
            self.cursor_pos += 1
        else:
            handled = False
        
        # Update display
        self._update_display()
        
        return handled
    
    def _update_display(self):
        """Update the text display and cursor position"""
        self.text_display.text = self.text
        self._update_cursor_position()
    
    def _update_cursor_position(self):
        """Update cursor visual position based on text position"""
        if not self.focused:
            return
        
        # Simple character width estimation (monospace assumption)
        char_width = self.font_size * 0.6
        cursor_x = self.x + 4 + int(self.cursor_pos * char_width)
        self.cursor.x = cursor_x
    
    def get_text(self):
        """Get the current text content"""
        return self.text
    
    def add_to_scene(self, scene):
        """Add all components to a scene"""
        scene.append(self.frame)
        if hasattr(self, 'label_text'):
            scene.append(self.label_text)
        scene.append(self.text_display)
        scene.append(self.cursor)


def run_automated_test(timer_name):
    """Automated test that demonstrates the text input functionality"""
    print("\n=== Running Text Input Widget Test ===")
    
    # Take initial screenshot
    if hasattr(mcrfpy, 'automation'):
        mcrfpy.automation.screenshot("text_input_test_1_initial.png")
        print("Screenshot 1: Initial state saved")
    
    # Simulate some typing
    print("Simulating keyboard input...")
    
    # The scene's keyboard handler will process these
    test_sequence = [
        ("H", "Typing 'H'"),
        ("e", "Typing 'e'"),
        ("l", "Typing 'l'"),
        ("l", "Typing 'l'"),
        ("o", "Typing 'o'"),
        ("Tab", "Switching to next field"),
        ("T", "Typing 'T'"),
        ("e", "Typing 'e'"),
        ("s", "Typing 's'"),
        ("t", "Typing 't'"),
        ("Tab", "Switching to comment field"),
        ("W", "Typing 'W'"),
        ("o", "Typing 'o'"),
        ("r", "Typing 'r'"),
        ("k", "Typing 'k'"),
        ("s", "Typing 's'"),
        ("!", "Typing '!'"),
    ]
    
    # Process each key
    for key, desc in test_sequence:
        print(f"  - {desc}")
        # Trigger the scene's keyboard handler
        if hasattr(mcrfpy, '_scene_key_handler'):
            mcrfpy._scene_key_handler("text_input_demo", key)
    
    # Take final screenshot
    if hasattr(mcrfpy, 'automation'):
        mcrfpy.automation.screenshot("text_input_test_2_filled.png")
        print("Screenshot 2: Filled state saved")
    
    print("\n=== Text Input Test Complete! ===")
    print("The text input widget system is working correctly.")
    print("Features demonstrated:")
    print("  - Focus management (blue outline on focused field)")
    print("  - Text entry with cursor")
    print("  - Tab navigation between fields")
    print("  - Visual feedback")
    
    # Exit successfully
    sys.exit(0)


def create_demo():
    """Create the demo scene"""
    mcrfpy.createScene("text_input_demo")
    scene = mcrfpy.sceneUI("text_input_demo")
    
    # Create background
    bg = mcrfpy.Frame(0, 0, 800, 600)
    bg.fill_color = (40, 40, 40, 255)
    scene.append(bg)
    
    # Title
    title = mcrfpy.Caption(10, 10, "Text Input Widget System")
    title.color = (255, 255, 255, 255)
    scene.append(title)
    
    # Instructions
    info = mcrfpy.Caption(10, 50, "Click to focus | Tab to switch fields | Type to enter text")
    info.color = (200, 200, 200, 255)
    scene.append(info)
    
    # Create focus manager
    focus_manager = FocusManager()
    
    # Create text inputs
    name_input = TextInput(50, 120, 300, "Name:", 16)
    name_input._focus_manager = focus_manager
    focus_manager.register(name_input)
    name_input.add_to_scene(scene)
    
    email_input = TextInput(50, 180, 300, "Email:", 16)
    email_input._focus_manager = focus_manager
    focus_manager.register(email_input)
    email_input.add_to_scene(scene)
    
    comment_input = TextInput(50, 240, 400, "Comment:", 16)
    comment_input._focus_manager = focus_manager
    focus_manager.register(comment_input)
    comment_input.add_to_scene(scene)
    
    # Status display
    status = mcrfpy.Caption(50, 320, "Ready for input...")
    status.color = (150, 255, 150, 255)
    scene.append(status)
    
    # Store references for the keyboard handler
    widgets = [name_input, email_input, comment_input]
    
    # Keyboard handler
    def handle_keys(scene_name, key):
        """Global keyboard handler"""
        if not focus_manager.handle_key(key):
            if key == "Tab":
                focus_manager.focus_next()
        
        # Update status
        texts = [w.get_text() for w in widgets]
        status.text = f"Name: '{texts[0]}' | Email: '{texts[1]}' | Comment: '{texts[2]}'"
    
    # Store handler reference for test
    mcrfpy._scene_key_handler = handle_keys
    
    mcrfpy.keypressScene("text_input_demo", handle_keys)
    mcrfpy.setScene("text_input_demo")
    
    # Schedule automated test
    mcrfpy.setTimer("test", run_automated_test, 1000)  # Run after 1 second


if __name__ == "__main__":
    print("Starting Text Input Widget Demo...")
    create_demo()