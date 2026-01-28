# McRogueFace Cookbook - Stat Bar Widget
"""
Horizontal bar showing current/max value with animation support.

Example:
    from lib.stat_bar import StatBar

    hp_bar = StatBar(
        pos=(100, 50),
        size=(200, 20),
        current=75,
        maximum=100,
        fill_color=mcrfpy.Color(200, 50, 50),  # Red for health
        label="HP"
    )
    scene.children.append(hp_bar.frame)

    # Take damage
    hp_bar.set_value(50, animate=True)

    # Flash on hit
    hp_bar.flash(mcrfpy.Color(255, 255, 255))
"""
import mcrfpy


class StatBar:
    """Horizontal bar showing current/max value.

    Args:
        pos: (x, y) position tuple
        size: (width, height) tuple, default (200, 20)
        current: Current value (default: 100)
        maximum: Maximum value (default: 100)
        fill_color: Bar fill color (default: green)
        bg_color: Background color (default: dark gray)
        outline_color: Border color (default: white)
        outline: Border thickness (default: 1)
        label: Optional label prefix (e.g., "HP")
        show_text: Whether to show value text (default: True)
        text_color: Color of value text (default: white)
        font_size: Size of value text (default: 12)

    Attributes:
        frame: The outer frame (add this to scene)
        bar: The inner fill bar
        current: Current value
        maximum: Maximum value
    """

    # Preset colors for common stat types
    HEALTH_COLOR = mcrfpy.Color(200, 50, 50)      # Red
    MANA_COLOR = mcrfpy.Color(50, 100, 200)       # Blue
    STAMINA_COLOR = mcrfpy.Color(50, 180, 80)     # Green
    XP_COLOR = mcrfpy.Color(200, 180, 50)         # Gold
    SHIELD_COLOR = mcrfpy.Color(100, 150, 200)    # Light blue

    DEFAULT_BG = mcrfpy.Color(30, 30, 35)
    DEFAULT_OUTLINE = mcrfpy.Color(150, 150, 160)
    DEFAULT_TEXT = mcrfpy.Color(255, 255, 255)

    def __init__(self, pos, size=(200, 20), current=100, maximum=100,
                 fill_color=None, bg_color=None, outline_color=None,
                 outline=1, label=None, show_text=True,
                 text_color=None, font_size=12):
        self.pos = pos
        self.size = size
        self._current = current
        self._maximum = maximum
        self.label = label
        self.show_text = show_text
        self.font_size = font_size

        # Colors
        self.fill_color = fill_color or self.STAMINA_COLOR
        self.bg_color = bg_color or self.DEFAULT_BG
        self.text_color = text_color or self.DEFAULT_TEXT
        self.outline_color = outline_color or self.DEFAULT_OUTLINE

        # Create outer frame (background)
        self.frame = mcrfpy.Frame(
            pos=pos,
            size=size,
            fill_color=self.bg_color,
            outline_color=self.outline_color,
            outline=outline
        )

        # Create inner bar (the fill)
        bar_width = self._calculate_bar_width()
        self.bar = mcrfpy.Frame(
            pos=(0, 0),
            size=(bar_width, size[1]),
            fill_color=self.fill_color,
            outline=0
        )
        self.frame.children.append(self.bar)

        # Create text label if needed
        if show_text:
            text = self._format_text()
            # Center text in the bar
            self.text = mcrfpy.Caption(
                text=text,
                pos=(size[0] / 2, (size[1] - font_size) / 2),
                fill_color=self.text_color,
                font_size=font_size
            )
            # Add outline for readability over bar
            self.text.outline = 1
            self.text.outline_color = mcrfpy.Color(0, 0, 0)
            self.frame.children.append(self.text)
        else:
            self.text = None

    def _calculate_bar_width(self):
        """Calculate the fill bar width based on current/max ratio."""
        if self._maximum <= 0:
            return 0
        ratio = max(0, min(1, self._current / self._maximum))
        return ratio * self.size[0]

    def _format_text(self):
        """Format the display text."""
        if self.label:
            return f"{self.label}: {int(self._current)}/{int(self._maximum)}"
        return f"{int(self._current)}/{int(self._maximum)}"

    def _update_display(self, animate=True):
        """Update the bar width and text."""
        target_width = self._calculate_bar_width()

        if animate:
            # Animate bar width change
            self.bar.animate("w", target_width, 0.3, mcrfpy.Easing.EASE_OUT)
        else:
            self.bar.w = target_width

        # Update text
        if self.text:
            self.text.text = self._format_text()

    @property
    def current(self):
        """Current value."""
        return self._current

    @current.setter
    def current(self, value):
        """Set current value (no animation)."""
        self._current = max(0, min(value, self._maximum))
        self._update_display(animate=False)

    @property
    def maximum(self):
        """Maximum value."""
        return self._maximum

    @maximum.setter
    def maximum(self, value):
        """Set maximum value."""
        self._maximum = max(1, value)
        self._current = min(self._current, self._maximum)
        self._update_display(animate=False)

    def set_value(self, current, maximum=None, animate=True):
        """Set the bar value with optional animation.

        Args:
            current: New current value
            maximum: New maximum value (optional)
            animate: Whether to animate the change
        """
        if maximum is not None:
            self._maximum = max(1, maximum)
        self._current = max(0, min(current, self._maximum))
        self._update_display(animate=animate)

    def flash(self, color=None, duration=0.2):
        """Flash the bar a color (e.g., white on damage).

        Args:
            color: Flash color (default: white)
            duration: Flash duration in seconds
        """
        color = color or mcrfpy.Color(255, 255, 255)
        original_color = self.fill_color

        # Flash to color
        self.bar.fill_color = color

        # Create a timer to restore color
        # Using a closure to capture state
        bar_ref = self.bar
        restore_color = original_color

        def restore(runtime):
            bar_ref.fill_color = restore_color

        # Schedule restoration
        timer_name = f"flash_{id(self)}"
        mcrfpy.Timer(timer_name, restore, int(duration * 1000))

    def set_colors(self, fill_color=None, bg_color=None, text_color=None):
        """Update bar colors.

        Args:
            fill_color: New fill color
            bg_color: New background color
            text_color: New text color
        """
        if fill_color:
            self.fill_color = fill_color
            self.bar.fill_color = fill_color
        if bg_color:
            self.bg_color = bg_color
            self.frame.fill_color = bg_color
        if text_color and self.text:
            self.text_color = text_color
            self.text.fill_color = text_color

    @property
    def ratio(self):
        """Get current fill ratio (0.0 to 1.0)."""
        if self._maximum <= 0:
            return 0
        return self._current / self._maximum

    def is_empty(self):
        """Check if bar is empty (current <= 0)."""
        return self._current <= 0

    def is_full(self):
        """Check if bar is full (current >= maximum)."""
        return self._current >= self._maximum


def create_stat_bar_group(stats, start_pos, spacing=30, size=(200, 20)):
    """Create a vertical group of stat bars.

    Args:
        stats: List of dicts with keys: name, current, max, color
        start_pos: (x, y) position of first bar
        spacing: Vertical pixels between bars
        size: (width, height) for all bars

    Returns:
        Dict mapping stat names to StatBar objects

    Example:
        bars = create_stat_bar_group([
            {"name": "HP", "current": 80, "max": 100, "color": StatBar.HEALTH_COLOR},
            {"name": "MP", "current": 50, "max": 80, "color": StatBar.MANA_COLOR},
            {"name": "XP", "current": 250, "max": 1000, "color": StatBar.XP_COLOR},
        ], start_pos=(50, 50))
    """
    bar_dict = {}
    x, y = start_pos

    for stat in stats:
        bar = StatBar(
            pos=(x, y),
            size=size,
            current=stat.get("current", 100),
            maximum=stat.get("max", 100),
            fill_color=stat.get("color"),
            label=stat.get("name")
        )
        bar_dict[stat.get("name", f"stat_{len(bar_dict)}")] = bar
        y += size[1] + spacing

    return bar_dict
