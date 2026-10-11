"""
Text Input Widget System for McRogueFace
A reusable module for text input fields with focus management
"""

import mcrfpy


class FocusManager:
    """Manages focus across multiple widgets"""
    def __init__(self):
        self.widgets = []
        self.focused_widget = None
        self.focus_index = -1
    
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
    
    def handle_key(self, key):
        """Send key to focused widget"""
        if self.focused_widget:
            return self.focused_widget.handle_key(key)
        return False


class TextInput:
    """Text input field widget"""
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
        
        # Visual elements
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components"""
        # Background frame
        self.frame = mcrfpy.Frame(pos=(self.x, self.y), size=(self.width, self.height))
        self.frame.fill_color = (255, 255, 255, 255)
        self.frame.outline_color = (128, 128, 128, 255)
        self.frame.outline = 2

        # Label (above input)
        if self.label:
            self.label_text = mcrfpy.Caption(text=self.label, pos=(self.x, self.y - 20))
            self.label_text.fill_color = (255, 255, 255, 255)

        # Text content
        self.text_display = mcrfpy.Caption(text="", pos=(self.x + 4, self.y + 4))
        self.text_display.fill_color = (0, 0, 0, 255)

        # Placeholder text
        if self.placeholder:
            self.placeholder_text = mcrfpy.Caption(text=self.placeholder, pos=(self.x + 4, self.y + 4))
            self.placeholder_text.fill_color = (180, 180, 180, 255)

        # Cursor
        self.cursor = mcrfpy.Frame(pos=(self.x + 4, self.y + 4), size=(2, self.height - 8))
        self.cursor.fill_color = (0, 0, 0, 255)
        self.cursor.visible = False

        # Click handler
        self.frame.on_click = self._on_click

    def _on_click(self, pos, button, action):
        """Handle mouse clicks (#230 signature: pos, button, action)"""
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED \
                and hasattr(self, '_focus_manager'):
            self._focus_manager.focus(self)
    
    def on_focus(self):
        """Called when focused"""
        self.focused = True
        self.frame.outline_color = (0, 120, 255, 255)
        self.frame.outline = 3
        self.cursor.visible = True
        self._update_display()
    
    def on_blur(self):
        """Called when focus lost"""
        self.focused = False
        self.frame.outline_color = (128, 128, 128, 255)
        self.frame.outline = 2
        self.cursor.visible = False
        self._update_display()
    
    def handle_key(self, key):
        """Process keyboard input"""
        if not self.focused:
            return False
        
        old_text = self.text
        handled = True
        
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
        elif key in ("Tab", "Return"):
            handled = False  # Let parent handle
        elif len(key) == 1 and key.isprintable():
            self.text = self.text[:self.cursor_pos] + key + self.text[self.cursor_pos:]
            self.cursor_pos += 1
        else:
            handled = False
        
        # Update if changed
        if old_text != self.text:
            self._update_display()
            if self.on_change:
                self.on_change(self.text)
        elif handled:
            self._update_cursor()
        
        return handled
    
    def _update_display(self):
        """Update visual state"""
        # Show/hide placeholder
        if hasattr(self, 'placeholder_text'):
            self.placeholder_text.visible = (self.text == "" and not self.focused)
        
        # Update text
        self.text_display.text = self.text
        self._update_cursor()
    
    def _update_cursor(self):
        """Update cursor position"""
        if self.focused:
            # Estimate position (10 pixels per character)
            self.cursor.x = self.x + 4 + (self.cursor_pos * 10)
    
    def set_text(self, text):
        """Set text programmatically"""
        self.text = text
        self.cursor_pos = len(text)
        self._update_display()
    
    def get_text(self):
        """Get current text"""
        return self.text
    
    def add_to_scene(self, scene):
        """Add all components to scene"""
        scene.append(self.frame)
        if hasattr(self, 'label_text'):
            scene.append(self.label_text)
        if hasattr(self, 'placeholder_text'):
            scene.append(self.placeholder_text)
        scene.append(self.text_display)
        scene.append(self.cursor)
