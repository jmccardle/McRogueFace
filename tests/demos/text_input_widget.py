#!/usr/bin/env python3
"""
Text Input Widget System for McRogueFace
A pure Python implementation of focusable text input fields
"""

import mcrfpy
import sys
from dataclasses import dataclass
from typing import Optional, List, Callable


class FocusManager:
    """Manages focus state across multiple widgets"""
    def __init__(self):
        self.widgets: List['TextInput'] = []
        self.focused_widget: Optional['TextInput'] = None
        self.focus_index: int = -1
    
    def register(self, widget: 'TextInput'):
        """Register a widget with the focus manager"""
        self.widgets.append(widget)
        if self.focused_widget is None:
            self.focus(widget)
    
    def focus(self, widget: 'TextInput'):
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
    
    def focus_prev(self):
        """Focus the previous widget in the list"""
        if not self.widgets:
            return
        
        self.focus_index = (self.focus_index - 1) % len(self.widgets)
        self.focus(self.widgets[self.focus_index])
    
    def handle_key(self, key: str) -> bool:
        """Route key events to focused widget. Returns True if handled."""
        if self.focused_widget:
            return self.focused_widget.handle_key(key)
        return False


class TextInput:
    """A text input widget with cursor and selection support"""
    def __init__(self, x: int, y: int, width: int = 200, label: str = "", 
                 font_size: int = 16, on_change: Optional[Callable] = None):
        self.x = x
        self.y = y
        self.width = width
        self.label = label
        self.font_size = font_size
        self.on_change = on_change
        
        # Text state
        self.text = ""
        self.cursor_pos = 0
        self.selection_start = -1
        self.selection_end = -1
        
        # Visual state
        self.focused = False
        self.cursor_visible = True
        self.cursor_blink_timer = 0
        
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
    
    def _on_click(self, x: int, y: int, button: int):
        """Handle mouse clicks on the input field"""
        if button == 1:  # Left click
            # Request focus through the focus manager
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
    
    def handle_key(self, key: str) -> bool:
        """Handle keyboard input. Returns True if key was handled."""
        if not self.focused:
            return False
        
        handled = True
        old_text = self.text
        
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
        elif key == "Return":
            handled = False  # Let parent handle submit
        elif key == "Tab":
            handled = False  # Let focus manager handle
        elif len(key) == 1 and key.isprintable():
            # Regular character input
            self.text = self.text[:self.cursor_pos] + key + self.text[self.cursor_pos:]
            self.cursor_pos += 1
        else:
            handled = False
        
        # Update display
        if old_text != self.text:
            self._update_display()
            if self.on_change:
                self.on_change(self.text)
        else:
            self._update_cursor_position()
        
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
    
    def set_text(self, text: str):
        """Set the text content"""
        self.text = text
        self.cursor_pos = len(text)
        self._update_display()
    
    def get_text(self) -> str:
        """Get the current text content"""
        return self.text


# Demo application
def create_demo():
    """Create a demo scene with multiple text input fields"""
    mcrfpy.createScene("text_input_demo")
    scene = mcrfpy.sceneUI("text_input_demo")
    
    # Create background
    bg = mcrfpy.Frame(0, 0, 800, 600)
    bg.fill_color = (40, 40, 40, 255)
    scene.append(bg)
    
    # Title
    title = mcrfpy.Caption(10, 10, "Text Input Widget Demo")
    title.color = (255, 255, 255, 255)
    scene.append(title)
    
    # Instructions
    instructions = mcrfpy.Caption(10, 50, "Click to focus, Tab to switch fields, Type to enter text")
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
    result_text = mcrfpy.Caption(50, 320, "Type in the fields above...")
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
                print("Demo complete!")
                sys.exit(0)
    
    mcrfpy.keypressScene("text_input_demo", handle_keys)
    
    # Set the scene
    mcrfpy.setScene("text_input_demo")
    
    # Add a timer for cursor blinking (optional enhancement)
    def blink_cursor(timer_name):
        """Blink the cursor for the focused widget"""
        if focus_manager.focused_widget and focus_manager.focused_widget.focused:
            cursor = focus_manager.focused_widget.cursor
            cursor.visible = not cursor.visible
    
    mcrfpy.setTimer("cursor_blink", blink_cursor, 500)  # Blink every 500ms


if __name__ == "__main__":
    create_demo()