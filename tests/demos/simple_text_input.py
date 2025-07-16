#!/usr/bin/env python3
"""
Simple Text Input Widget for McRogueFace
Minimal implementation focusing on core functionality
"""

import mcrfpy
import sys


class TextInput:
    """Simple text input widget"""
    def __init__(self, x, y, width, label=""):
        self.x = x
        self.y = y
        self.width = width
        self.label = label
        self.text = ""
        self.cursor_pos = 0
        self.focused = False
        
        # Create UI elements
        self.frame = mcrfpy.Frame(self.x, self.y, self.width, 24)
        self.frame.fill_color = (255, 255, 255, 255)
        self.frame.outline_color = (128, 128, 128, 255)
        self.frame.outline = 2
        
        # Label
        if self.label:
            self.label_caption = mcrfpy.Caption(self.label, self.x, self.y - 20)
            self.label_caption.fill_color = (255, 255, 255, 255)
        
        # Text display
        self.text_caption = mcrfpy.Caption("", self.x + 4, self.y + 4)
        self.text_caption.fill_color = (0, 0, 0, 255)
        
        # Cursor (a simple vertical line using a frame)
        self.cursor = mcrfpy.Frame(self.x + 4, self.y + 4, 2, 16)
        self.cursor.fill_color = (0, 0, 0, 255)
        self.cursor.visible = False
        
        # Click handler
        self.frame.click = self._on_click
    
    def _on_click(self, x, y, button):
        """Handle clicks"""
        if button == 1:  # Left click
            # Request focus
            global current_focus
            if current_focus and current_focus != self:
                current_focus.blur()
            current_focus = self
            self.focus()
    
    def focus(self):
        """Give focus to this input"""
        self.focused = True
        self.frame.outline_color = (0, 120, 255, 255)
        self.frame.outline = 3
        self.cursor.visible = True
        self._update_cursor()
    
    def blur(self):
        """Remove focus"""
        self.focused = False
        self.frame.outline_color = (128, 128, 128, 255)
        self.frame.outline = 2
        self.cursor.visible = False
    
    def handle_key(self, key):
        """Process keyboard input"""
        if not self.focused:
            return False
        
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
        elif len(key) == 1 and key.isprintable():
            self.text = self.text[:self.cursor_pos] + key + self.text[self.cursor_pos:]
            self.cursor_pos += 1
        else:
            return False
        
        self._update_display()
        return True
    
    def _update_display(self):
        """Update text display"""
        self.text_caption.text = self.text
        self._update_cursor()
    
    def _update_cursor(self):
        """Update cursor position"""
        if self.focused:
            # Estimate character width (roughly 10 pixels per char)
            self.cursor.x = self.x + 4 + (self.cursor_pos * 10)
    
    def add_to_scene(self, scene):
        """Add all components to scene"""
        scene.append(self.frame)
        if hasattr(self, 'label_caption'):
            scene.append(self.label_caption)
        scene.append(self.text_caption)
        scene.append(self.cursor)


# Global focus tracking
current_focus = None
text_inputs = []


def demo_test(timer_name):
    """Run automated demo after scene loads"""
    print("\n=== Text Input Widget Demo ===")
    
    # Test typing in first field
    print("Testing first input field...")
    text_inputs[0].focus()
    for char in "Hello":
        text_inputs[0].handle_key(char)
    
    print(f"First field contains: '{text_inputs[0].text}'")
    
    # Test second field
    print("\nTesting second input field...")
    text_inputs[1].focus()
    for char in "World":
        text_inputs[1].handle_key(char)
    
    print(f"Second field contains: '{text_inputs[1].text}'")
    
    # Test text operations
    print("\nTesting cursor movement and deletion...")
    text_inputs[1].handle_key("Home")
    text_inputs[1].handle_key("Delete")
    print(f"After delete at start: '{text_inputs[1].text}'")
    
    text_inputs[1].handle_key("End")
    text_inputs[1].handle_key("BackSpace")
    print(f"After backspace at end: '{text_inputs[1].text}'")
    
    print("\n=== Demo Complete! ===")
    print("Text input widget is working successfully!")
    print("Features demonstrated:")
    print("  - Text entry")
    print("  - Focus management (blue outline)")
    print("  - Cursor positioning")
    print("  - Delete/Backspace operations")
    
    sys.exit(0)


def create_scene():
    """Create the demo scene"""
    global text_inputs
    
    mcrfpy.createScene("demo")
    scene = mcrfpy.sceneUI("demo")
    
    # Background
    bg = mcrfpy.Frame(0, 0, 800, 600)
    bg.fill_color = (40, 40, 40, 255)
    scene.append(bg)
    
    # Title
    title = mcrfpy.Caption("Text Input Widget Demo", 10, 10)
    title.fill_color = (255, 255, 255, 255)
    scene.append(title)
    
    # Create input fields
    input1 = TextInput(50, 100, 300, "Name:")
    input1.add_to_scene(scene)
    text_inputs.append(input1)
    
    input2 = TextInput(50, 160, 300, "Email:")
    input2.add_to_scene(scene)
    text_inputs.append(input2)
    
    input3 = TextInput(50, 220, 400, "Comment:")
    input3.add_to_scene(scene)
    text_inputs.append(input3)
    
    # Status text
    status = mcrfpy.Caption("Click to focus, type to enter text", 50, 280)
    status.fill_color = (200, 200, 200, 255)
    scene.append(status)
    
    # Keyboard handler
    def handle_keys(scene_name, key):
        global current_focus, text_inputs
        
        # Tab to switch fields
        if key == "Tab" and current_focus:
            idx = text_inputs.index(current_focus)
            next_idx = (idx + 1) % len(text_inputs)
            text_inputs[next_idx]._on_click(0, 0, 1)
        else:
            # Pass to focused input
            if current_focus:
                current_focus.handle_key(key)
                # Update status
                texts = [inp.text for inp in text_inputs]
                status.text = f"Values: {texts[0]} | {texts[1]} | {texts[2]}"
    
    mcrfpy.keypressScene("demo", handle_keys)
    mcrfpy.setScene("demo")
    
    # Schedule test
    mcrfpy.setTimer("test", demo_test, 500)


if __name__ == "__main__":
    print("Starting simple text input demo...")
    create_scene()