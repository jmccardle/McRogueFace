# McRogueFace Cookbook - Button Widget
"""
Clickable button with hover/press states and visual feedback.

Example:
    from lib.button import Button

    def on_click():
        print("Button clicked!")

    btn = Button("Start Game", pos=(100, 100), callback=on_click)
    scene.children.append(btn.frame)
"""
import mcrfpy


class Button:
    """Clickable button with hover/press states.

    Args:
        text: Button label text
        pos: (x, y) position tuple
        size: (width, height) tuple, default (120, 40)
        callback: Function to call on click (no arguments)
        fill_color: Background color (default: dark gray)
        hover_color: Color when mouse hovers (default: lighter gray)
        press_color: Color when pressed (default: even lighter)
        text_color: Label color (default: white)
        outline_color: Border color (default: white)
        outline: Border thickness (default: 2)
        font_size: Text size (default: 16)
        enabled: Whether button is clickable (default: True)

    Attributes:
        frame: The underlying mcrfpy.Frame (add this to scene)
        label: The mcrfpy.Caption for the text
        is_hovered: True if mouse is over button
        is_pressed: True if button is being pressed
        enabled: Whether button responds to clicks
    """

    # Default colors
    DEFAULT_FILL = mcrfpy.Color(60, 60, 70)
    DEFAULT_HOVER = mcrfpy.Color(80, 80, 95)
    DEFAULT_PRESS = mcrfpy.Color(100, 100, 120)
    DEFAULT_DISABLED = mcrfpy.Color(40, 40, 45)
    DEFAULT_TEXT = mcrfpy.Color(255, 255, 255)
    DEFAULT_TEXT_DISABLED = mcrfpy.Color(120, 120, 120)
    DEFAULT_OUTLINE = mcrfpy.Color(200, 200, 210)

    def __init__(self, text, pos, size=(120, 40), callback=None,
                 fill_color=None, hover_color=None, press_color=None,
                 text_color=None, outline_color=None, outline=2,
                 font_size=16, enabled=True):
        self.text = text
        self.pos = pos
        self.size = size
        self.callback = callback
        self.font_size = font_size
        self._enabled = enabled

        # Store colors
        self.fill_color = fill_color or self.DEFAULT_FILL
        self.hover_color = hover_color or self.DEFAULT_HOVER
        self.press_color = press_color or self.DEFAULT_PRESS
        self.text_color = text_color or self.DEFAULT_TEXT
        self.outline_color = outline_color or self.DEFAULT_OUTLINE

        # State tracking
        self.is_hovered = False
        self.is_pressed = False

        # Create the frame
        self.frame = mcrfpy.Frame(
            pos=pos,
            size=size,
            fill_color=self.fill_color,
            outline_color=self.outline_color,
            outline=outline
        )

        # Create the label (centered in frame)
        self.label = mcrfpy.Caption(
            text=text,
            pos=(size[0] / 2, size[1] / 2 - font_size / 2),
            fill_color=self.text_color,
            font_size=font_size
        )
        self.frame.children.append(self.label)

        # Set up event handlers
        self.frame.on_click = self._on_click
        self.frame.on_enter = self._on_enter
        self.frame.on_exit = self._on_exit

        # Apply initial state
        if not enabled:
            self._apply_disabled_style()

    def _on_click(self, pos, button, action):
        """Handle click events."""
        if not self._enabled:
            return

        if button == "left":
            if action == "start":
                self.is_pressed = True
                self.frame.fill_color = self.press_color
                # Animate a subtle press effect
                self._animate_press()
            elif action == "end":
                self.is_pressed = False
                # Restore hover or normal state
                if self.is_hovered:
                    self.frame.fill_color = self.hover_color
                else:
                    self.frame.fill_color = self.fill_color
                # Trigger callback on release if still over button
                if self.is_hovered and self.callback:
                    self.callback()

    def _on_enter(self, pos):
        """Handle mouse enter.

        Note: #230 - on_enter now only receives position, not button/action
        """
        if not self._enabled:
            return
        self.is_hovered = True
        if not self.is_pressed:
            self.frame.fill_color = self.hover_color

    def _on_exit(self, pos):
        """Handle mouse exit.

        Note: #230 - on_exit now only receives position, not button/action
        """
        if not self._enabled:
            return
        self.is_hovered = False
        self.is_pressed = False
        self.frame.fill_color = self.fill_color

    def _animate_press(self):
        """Animate a subtle scale bounce on press."""
        # Small scale down then back up
        # Note: If scale animation is not available, this is a no-op
        try:
            # Animate origin for a press effect
            original_x = self.frame.x
            original_y = self.frame.y
            # Quick bounce using position
            self.frame.animate("x", original_x + 2, 0.05, mcrfpy.Easing.EASE_OUT)
            self.frame.animate("y", original_y + 2, 0.05, mcrfpy.Easing.EASE_OUT)
        except Exception:
            pass  # Animation not critical

    def _apply_disabled_style(self):
        """Apply disabled visual style."""
        self.frame.fill_color = self.DEFAULT_DISABLED
        self.label.fill_color = self.DEFAULT_TEXT_DISABLED

    def _apply_enabled_style(self):
        """Restore enabled visual style."""
        self.frame.fill_color = self.fill_color
        self.label.fill_color = self.text_color

    @property
    def enabled(self):
        """Whether the button is clickable."""
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        """Enable or disable the button."""
        self._enabled = value
        if value:
            self._apply_enabled_style()
        else:
            self._apply_disabled_style()
            self.is_hovered = False
            self.is_pressed = False

    def set_text(self, text):
        """Change the button label."""
        self.text = text
        self.label.text = text

    def set_callback(self, callback):
        """Change the click callback."""
        self.callback = callback


def create_button_row(labels, start_pos, spacing=10, size=(120, 40), callbacks=None):
    """Create a horizontal row of buttons.

    Args:
        labels: List of button labels
        start_pos: (x, y) position of first button
        spacing: Pixels between buttons
        size: (width, height) for all buttons
        callbacks: List of callbacks (or None for no callbacks)

    Returns:
        List of Button objects
    """
    buttons = []
    x, y = start_pos
    callbacks = callbacks or [None] * len(labels)

    for label, callback in zip(labels, callbacks):
        btn = Button(label, pos=(x, y), size=size, callback=callback)
        buttons.append(btn)
        x += size[0] + spacing

    return buttons


def create_button_column(labels, start_pos, spacing=10, size=(120, 40), callbacks=None):
    """Create a vertical column of buttons.

    Args:
        labels: List of button labels
        start_pos: (x, y) position of first button
        spacing: Pixels between buttons
        size: (width, height) for all buttons
        callbacks: List of callbacks (or None for no callbacks)

    Returns:
        List of Button objects
    """
    buttons = []
    x, y = start_pos
    callbacks = callbacks or [None] * len(labels)

    for label, callback in zip(labels, callbacks):
        btn = Button(label, pos=(x, y), size=size, callback=callback)
        buttons.append(btn)
        y += size[1] + spacing

    return buttons
