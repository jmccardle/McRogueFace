"""UI widgets for interactive parameter controls.

Provides reusable widget classes for:
- Stepper: +/- buttons with value display for integers/seeds
- Slider: Draggable track for float ranges
- LayerToggle: Checkbox for layer visibility
"""

import mcrfpy
from typing import Callable, Optional
from .parameter import Parameter


class Stepper:
    """Integer/seed stepper with +/- buttons and value display.

    Layout: [-] [ value ] [+]

    Args:
        parameter: Parameter to control
        pos: (x, y) position tuple
        width: Total widget width (default 150)
        height: Widget height (default 30)
        on_change: Optional callback when value changes
    """

    def __init__(self, parameter: Parameter, pos: tuple,
                 width: int = 150, height: int = 30,
                 on_change: Optional[Callable] = None):
        self.parameter = parameter
        self.pos = pos
        self.width = width
        self.height = height
        self.on_change = on_change

        button_width = height  # Square buttons
        value_width = width - 2 * button_width - 4

        # Container frame
        self.frame = mcrfpy.Frame(
            pos=pos,
            size=(width, height),
            fill_color=mcrfpy.Color(40, 40, 45),
            outline=1,
            outline_color=mcrfpy.Color(80, 80, 90)
        )

        # Minus button
        self.btn_minus = mcrfpy.Frame(
            pos=(0, 0),
            size=(button_width, height),
            fill_color=mcrfpy.Color(60, 60, 70),
            outline=1,
            outline_color=mcrfpy.Color(100, 100, 110)
        )
        minus_label = mcrfpy.Caption(
            text="-",
            pos=(button_width // 2 - 4, height // 2 - 10),
            font_size=18,
            fill_color=mcrfpy.Color(200, 200, 210)
        )
        self.btn_minus.children.append(minus_label)
        self.btn_minus.on_click = self._on_minus_click
        self.btn_minus.on_enter = lambda pos: self._on_btn_hover(self.btn_minus, True)
        self.btn_minus.on_exit = lambda pos: self._on_btn_hover(self.btn_minus, False)
        self.frame.children.append(self.btn_minus)

        # Value display
        self.value_caption = mcrfpy.Caption(
            text=parameter.format_value(),
            pos=(button_width + value_width // 2, height // 2 - 8),
            font_size=14,
            fill_color=mcrfpy.Color(220, 220, 230)
        )
        self.frame.children.append(self.value_caption)

        # Plus button
        self.btn_plus = mcrfpy.Frame(
            pos=(width - button_width, 0),
            size=(button_width, height),
            fill_color=mcrfpy.Color(60, 60, 70),
            outline=1,
            outline_color=mcrfpy.Color(100, 100, 110)
        )
        plus_label = mcrfpy.Caption(
            text="+",
            pos=(button_width // 2 - 4, height // 2 - 10),
            font_size=18,
            fill_color=mcrfpy.Color(200, 200, 210)
        )
        self.btn_plus.children.append(plus_label)
        self.btn_plus.on_click = self._on_plus_click
        self.btn_plus.on_enter = lambda pos: self._on_btn_hover(self.btn_plus, True)
        self.btn_plus.on_exit = lambda pos: self._on_btn_hover(self.btn_plus, False)
        self.frame.children.append(self.btn_plus)

        # Wire up parameter change notification
        self.parameter._on_change = self._on_param_change

    def _on_btn_hover(self, btn, entered: bool):
        """Handle button hover state."""
        if entered:
            btn.fill_color = mcrfpy.Color(80, 80, 95)
        else:
            btn.fill_color = mcrfpy.Color(60, 60, 70)

    def _on_minus_click(self, pos, button, action):
        """Handle minus button click."""
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.RELEASED:
            self.parameter.decrement()

    def _on_plus_click(self, pos, button, action):
        """Handle plus button click."""
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.RELEASED:
            self.parameter.increment()

    def _on_param_change(self, param):
        """Handle parameter value change."""
        self.value_caption.text = param.format_value()
        if self.on_change:
            self.on_change(param)

    def update_display(self):
        """Force update of displayed value."""
        self.value_caption.text = self.parameter.format_value()


class Slider:
    """Draggable slider for float parameter ranges.

    Layout: [======o========] value

    Args:
        parameter: Parameter to control
        pos: (x, y) position tuple
        width: Total widget width (default 200)
        height: Widget height (default 25)
        on_change: Optional callback when value changes
    """

    def __init__(self, parameter: Parameter, pos: tuple,
                 width: int = 200, height: int = 25,
                 on_change: Optional[Callable] = None):
        self.parameter = parameter
        self.pos = pos
        self.width = width
        self.height = height
        self.on_change = on_change
        self.dragging = False

        value_display_width = 50
        track_width = width - value_display_width - 5

        # Container frame
        self.frame = mcrfpy.Frame(
            pos=pos,
            size=(width, height),
            fill_color=mcrfpy.Color(40, 40, 45)
        )

        # Track background
        track_height = 8
        track_y = (height - track_height) // 2
        self.track = mcrfpy.Frame(
            pos=(0, track_y),
            size=(track_width, track_height),
            fill_color=mcrfpy.Color(50, 50, 55),
            outline=1,
            outline_color=mcrfpy.Color(80, 80, 90)
        )
        self.track.on_click = self._on_track_click
        self.track.on_move = self._on_track_move
        self.frame.children.append(self.track)

        # Filled portion (left of handle)
        self.fill = mcrfpy.Frame(
            pos=(0, 0),
            size=(int(track_width * parameter.get_normalized()), track_height),
            fill_color=mcrfpy.Color(100, 150, 200)
        )
        self.track.children.append(self.fill)

        # Handle
        handle_width = 12
        handle_pos = int((track_width - handle_width) * parameter.get_normalized())
        self.handle = mcrfpy.Frame(
            pos=(handle_pos, -3),
            size=(handle_width, track_height + 6),
            fill_color=mcrfpy.Color(180, 180, 200),
            outline=1,
            outline_color=mcrfpy.Color(220, 220, 230)
        )
        self.track.children.append(self.handle)

        # Value display
        self.value_caption = mcrfpy.Caption(
            text=parameter.format_value(),
            pos=(track_width + 8, height // 2 - 8),
            font_size=12,
            fill_color=mcrfpy.Color(180, 180, 190)
        )
        self.frame.children.append(self.value_caption)

        # Wire up parameter change notification
        self.parameter._on_change = self._on_param_change
        self.track_width = track_width

    def _on_track_click(self, pos, button, action):
        """Handle click on track for direct positioning and drag start/end."""
        if button == mcrfpy.MouseButton.LEFT:
            if action == mcrfpy.InputState.PRESSED:
                self.dragging = True
                self._update_from_position(pos.x)
            elif action == mcrfpy.InputState.RELEASED:
                self.dragging = False

    def _on_track_move(self, pos):
        """Handle mouse movement for dragging."""
        if self.dragging:
            self._update_from_position(pos.x)

    def _update_from_position(self, x: float):
        """Update parameter value from mouse x position on track."""
        normalized = max(0.0, min(1.0, x / self.track_width))
        self.parameter.set_from_normalized(normalized)

    def _on_param_change(self, param):
        """Handle parameter value change - update visual elements."""
        normalized = param.get_normalized()
        handle_width = 12
        handle_pos = int((self.track_width - handle_width) * normalized)
        self.handle.x = handle_pos
        self.fill.w = int(self.track_width * normalized)
        self.value_caption.text = param.format_value()
        if self.on_change:
            self.on_change(param)

    def update_display(self):
        """Force update of visual elements."""
        self._on_param_change(self.parameter)


class LayerToggle:
    """Checkbox toggle for layer visibility.

    Layout: [x] Layer Name

    Args:
        name: Display name for the layer
        layer: The ColorLayer or TileLayer to toggle
        pos: (x, y) position tuple
        width: Total widget width (default 150)
        height: Widget height (default 25)
        initial: Initial checked state (default True)
        on_change: Optional callback when toggled
    """

    def __init__(self, name: str, layer, pos: tuple,
                 width: int = 150, height: int = 25,
                 initial: bool = True,
                 on_change: Optional[Callable] = None):
        self.name = name
        self.layer = layer
        self.pos = pos
        self.width = width
        self.height = height
        self.checked = initial
        self.on_change = on_change

        checkbox_size = height - 4

        # Container frame
        self.frame = mcrfpy.Frame(
            pos=pos,
            size=(width, height),
            fill_color=mcrfpy.Color(40, 40, 45)
        )
        self.frame.on_click = self._on_click
        self.frame.on_enter = self._on_enter
        self.frame.on_exit = self._on_exit

        # Checkbox box
        self.checkbox = mcrfpy.Frame(
            pos=(2, 2),
            size=(checkbox_size, checkbox_size),
            fill_color=mcrfpy.Color(60, 60, 70) if not initial else mcrfpy.Color(80, 140, 200),
            outline=1,
            outline_color=mcrfpy.Color(120, 120, 130)
        )
        self.frame.children.append(self.checkbox)

        # Check mark (X)
        self.check_mark = mcrfpy.Caption(
            text="x" if initial else "",
            pos=(checkbox_size // 2 - 4, checkbox_size // 2 - 8),
            font_size=14,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        self.checkbox.children.append(self.check_mark)

        # Label
        self.label = mcrfpy.Caption(
            text=name,
            pos=(checkbox_size + 8, height // 2 - 8),
            font_size=14,
            fill_color=mcrfpy.Color(200, 200, 210) if initial else mcrfpy.Color(120, 120, 130)
        )
        self.frame.children.append(self.label)

        # Apply initial visibility
        if layer is not None:
            layer.visible = initial

    def _on_click(self, pos, button, action):
        """Handle click to toggle."""
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.RELEASED:
            self.toggle()

    def _on_enter(self, pos):
        """Handle mouse enter - highlight."""
        self.frame.fill_color = mcrfpy.Color(50, 50, 60)

    def _on_exit(self, pos):
        """Handle mouse exit - unhighlight."""
        self.frame.fill_color = mcrfpy.Color(40, 40, 45)

    def toggle(self):
        """Toggle the checkbox state."""
        self.checked = not self.checked
        self._update_visual()
        if self.layer is not None:
            self.layer.visible = self.checked
        if self.on_change:
            self.on_change(self.name, self.checked)

    def set_checked(self, checked: bool):
        """Set checkbox state directly."""
        if checked != self.checked:
            self.checked = checked
            self._update_visual()
            if self.layer is not None:
                self.layer.visible = checked

    def _update_visual(self):
        """Update visual elements based on checked state."""
        if self.checked:
            self.checkbox.fill_color = mcrfpy.Color(80, 140, 200)
            self.check_mark.text = "x"
            self.label.fill_color = mcrfpy.Color(200, 200, 210)
        else:
            self.checkbox.fill_color = mcrfpy.Color(60, 60, 70)
            self.check_mark.text = ""
            self.label.fill_color = mcrfpy.Color(120, 120, 130)
