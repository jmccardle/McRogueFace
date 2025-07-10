"""
Improved Text Input Widget System for McRogueFace
Uses proper parent-child frame structure and handles keyboard input correctly
"""

import mcrfpy


class FocusManager:
    """Manages focus across multiple widgets"""
    def __init__(self):
        self.widgets = []
        self.focused_widget = None
        self.focus_index = -1
        # Global keyboard state
        self.shift_pressed = False
        self.caps_lock = False
    
    def register(self, widget):
        """Register a widget"""
        self.widgets.append(widget)
        if self.focused_widget is None:
            self.focus(widget)
    
    def focus(self, widget):
        """Set focus to widget"""
        if self.focused_widget:
            self.focused_widget.on_blur()
        
        self.focused_widget = widget
        self.focus_index = self.widgets.index(widget) if widget in self.widgets else -1
        
        if widget:
            widget.on_focus()
    
    def focus_next(self):
        """Focus next widget"""
        if not self.widgets:
            return
        self.focus_index = (self.focus_index + 1) % len(self.widgets)
        self.focus(self.widgets[self.focus_index])
    
    def focus_prev(self):
        """Focus previous widget"""
        if not self.widgets:
            return
        self.focus_index = (self.focus_index - 1) % len(self.widgets)
        self.focus(self.widgets[self.focus_index])
    
    def handle_key(self, key, state):
        """Send key to focused widget"""
        # Track shift state
        if key == "LShift" or key == "RShift":
            self.shift_pressed = True
            return True
        elif key == "start":  # Key release for shift
            self.shift_pressed = False
            return True
        elif key == "CapsLock":
            self.caps_lock = not self.caps_lock
            return True
        
        if self.focused_widget:
            return self.focused_widget.handle_key(key, self.shift_pressed, self.caps_lock)
        return False


class TextInput:
    """Text input field widget with proper parent-child structure"""
    def __init__(self, x, y, width, height=24, label="", placeholder="", on_change=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.placeholder = placeholder
        self.on_change = on_change
        
        # Text state
        self.text = ""
        self.cursor_pos = 0
        self.focused = False
        
        # Create the widget structure
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components with proper parent-child structure"""
        # Parent frame that contains everything
        self.parent_frame = mcrfpy.Frame(self.x, self.y - (20 if self.label else 0), 
                                         self.width, self.height + (20 if self.label else 0))
        self.parent_frame.fill_color = (0, 0, 0, 0)  # Transparent parent
        
        # Input frame (relative to parent)
        self.frame = mcrfpy.Frame(0, 20 if self.label else 0, self.width, self.height)
        self.frame.fill_color = (255, 255, 255, 255)
        self.frame.outline_color = (128, 128, 128, 255)
        self.frame.outline = 2
        
        # Label (relative to parent)
        if self.label:
            self.label_text = mcrfpy.Caption(self.label, 0, 0)
            self.label_text.fill_color = (255, 255, 255, 255)
            self.parent_frame.children.append(self.label_text)
        
        # Text content (relative to input frame)
        self.text_display = mcrfpy.Caption("", 4, 4)
        self.text_display.fill_color = (0, 0, 0, 255)
        
        # Placeholder text (relative to input frame)
        if self.placeholder:
            self.placeholder_text = mcrfpy.Caption(self.placeholder, 4, 4)
            self.placeholder_text.fill_color = (180, 180, 180, 255)
            self.frame.children.append(self.placeholder_text)
        
        # Cursor (relative to input frame)
        # Experiment: replacing cursor frame with an inline text character
        #self.cursor = mcrfpy.Frame(4, 4, 2, self.height - 8)
        #self.cursor.fill_color = (0, 0, 0, 255)
        #self.cursor.visible = False
        
        # Add children to input frame
        self.frame.children.append(self.text_display)
        #self.frame.children.append(self.cursor)
        
        # Add input frame to parent
        self.parent_frame.children.append(self.frame)
        
        # Click handler on the input frame
        self.frame.click = self._on_click
    
    def _on_click(self, x, y, button, state):
        """Handle mouse clicks"""
        print(f"{x=} {y=} {button=} {state=}")
        if button == "left" and hasattr(self, '_focus_manager'):
            self._focus_manager.focus(self)
    
    def on_focus(self):
        """Called when focused"""
        self.focused = True
        self.frame.outline_color = (0, 120, 255, 255)
        self.frame.outline = 3
        #self.cursor.visible = True
        self._update_display()
    
    def on_blur(self):
        """Called when focus lost"""
        self.focused = False
        self.frame.outline_color = (128, 128, 128, 255)
        self.frame.outline = 2
        #self.cursor.visible = False
        self._update_display()
    
    def handle_key(self, key, shift_pressed, caps_lock):
        """Process keyboard input with shift state"""
        if not self.focused:
            return False
        
        old_text = self.text
        handled = True
        
        # Special key mappings for shifted characters
        shift_map = {
            "1": "!", "2": "@", "3": "#", "4": "$", "5": "%",
            "6": "^", "7": "&", "8": "*", "9": "(", "0": ")",
            "-": "_", "=": "+", "[": "{", "]": "}", "\\": "|",
            ";": ":", "'": '"', ",": "<", ".": ">", "/": "?",
            "`": "~"
        }
        
        # Navigation and editing keys
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
        elif key == "Space":
            self._insert_at_cursor(" ")
        elif key in ("Tab", "Return"):
            handled = False  # Let parent handle
        # Handle number keys with "Num" prefix
        elif key.startswith("Num") and len(key) == 4:
            num = key[3]  # Get the digit after "Num"
            if shift_pressed and num in shift_map:
                self._insert_at_cursor(shift_map[num])
            else:
                self._insert_at_cursor(num)
        # Handle single character keys
        elif len(key) == 1:
            char = key
            # Apply shift transformations
            if shift_pressed:
                if char in shift_map:
                    char = shift_map[char]
                elif char.isalpha():
                    char = char.upper()
            else:
                # Apply caps lock for letters
                if char.isalpha():
                    if caps_lock:
                        char = char.upper()
                    else:
                        char = char.lower()
            self._insert_at_cursor(char)
        else:
            # Unhandled key - print for debugging
            print(f"[TextInput] Unhandled key: '{key}' (shift={shift_pressed}, caps={caps_lock})")
            handled = False
        
        # Update if changed
        if old_text != self.text:
            self._update_display()
            if self.on_change:
                self.on_change(self.text)
        elif handled:
            self._update_cursor()
        
        return handled
    
    def _insert_at_cursor(self, char):
        """Insert a character at the cursor position"""
        self.text = self.text[:self.cursor_pos] + char + self.text[self.cursor_pos:]
        self.cursor_pos += 1
    
    def _update_display(self):
        """Update visual state"""
        # Show/hide placeholder
        if hasattr(self, 'placeholder_text'):
            self.placeholder_text.visible = (self.text == "" and not self.focused)
        
        # Update text
        self.text_display.text = self.text[:self.cursor_pos] + "|" + self.text[self.cursor_pos:]
        self._update_cursor()
    
    def _update_cursor(self):
        """Update cursor position"""
        if self.focused:
            # Estimate position (10 pixels per character)
            #self.cursor.x = 4 + (self.cursor_pos * 10)
            self.text_display.text = self.text[:self.cursor_pos] + "|" + self.text[self.cursor_pos:]
            pass
    
    def set_text(self, text):
        """Set text programmatically"""
        self.text = text
        self.cursor_pos = len(text)
        self._update_display()
    
    def get_text(self):
        """Get current text"""
        return self.text
    
    def add_to_scene(self, scene):
        """Add only the parent frame to scene"""
        scene.append(self.parent_frame)
