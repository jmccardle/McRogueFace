# mcrf: objects=[Caption,Color,Frame,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy

class TooltipManager:
    """Manages tooltips for multiple UI elements."""

    def __init__(self):
        self.elements = {}  # id(element) -> {text, title} mapping
        self.tooltip_frame = None
        self.tooltip_text = None
        self.current_element = None
        self.hover_delay = 500  # ms before showing tooltip
        self.pending_element = None
        self.pending_x = 0
        self.pending_y = 0

        self._create_tooltip()

    def _create_tooltip(self):
        """Create the tooltip UI elements."""
        self.tooltip_frame = mcrfpy.Frame(pos=(0, 0), size=(200, 60))
        self.tooltip_frame.fill_color = mcrfpy.Color(30, 30, 45, 245)
        self.tooltip_frame.outline = 1
        self.tooltip_frame.outline_color = mcrfpy.Color(80, 80, 100)
        self.tooltip_frame.visible = False

        self.tooltip_text = mcrfpy.Caption(text="", pos=(0, 0))
        self.tooltip_text.fill_color = mcrfpy.Color(255, 255, 230)
        self.tooltip_text.visible = False

    def register(self, element, text, title=None):
        """
        Register an element for tooltips.

        Args:
            element: UI element to track
            text: Tooltip description
            title: Optional title (shown in different color)
        """
        self.elements[id(element)] = {
            'element': element,
            'text': text,
            'title': title
        }

        def on_enter(pos):
            self._on_element_enter(element, pos.x, pos.y)

        def on_exit(pos):
            self._on_element_exit(element)

        element.on_enter = on_enter
        element.on_exit = on_exit

    def _on_element_enter(self, element, x, y):
        """Handle mouse entering a registered element."""
        elem_id = id(element)
        if elem_id not in self.elements:
            return

        self.pending_element = element
        self.pending_x = x
        self.pending_y = y

        def show_after_delay(timer, runtime):
            # Only show if the mouse is still over this element
            if self.pending_element is element:
                self._show_tooltip(element, self.pending_x, self.pending_y)

        timer_name = f"tooltip_delay_{id(self)}"
        mcrfpy.Timer(timer_name, show_after_delay, self.hover_delay)

    def _on_element_exit(self, element):
        """Handle mouse leaving a registered element."""
        if self.pending_element is element:
            self.pending_element = None
        if self.current_element is element:
            self.hide()

    def _show_tooltip(self, element, x, y):
        """Display tooltip for element."""
        elem_id = id(element)
        if elem_id not in self.elements:
            return

        data = self.elements[elem_id]

        # Build tooltip content
        content = ""
        if data.get('title'):
            content = data['title'] + "\n"
        content += data['text']

        # Update tooltip text
        self.tooltip_text.text = content

        # Calculate size based on content
        lines = content.split('\n')
        max_width = max(len(line) for line in lines) * 8 + 20
        height = len(lines) * 18 + 15

        self.tooltip_frame.w = min(300, max(100, max_width))
        self.tooltip_frame.h = height

        # Position tooltip
        self.tooltip_frame.x = x + 20
        self.tooltip_frame.y = y + 20

        # Keep on screen
        if self.tooltip_frame.x + self.tooltip_frame.w > 1000:
            self.tooltip_frame.x = x - self.tooltip_frame.w - 10
        if self.tooltip_frame.y + self.tooltip_frame.h > 750:
            self.tooltip_frame.y = y - self.tooltip_frame.h - 10

        self.tooltip_text.x = self.tooltip_frame.x + 10
        self.tooltip_text.y = self.tooltip_frame.y + 8

        # Show
        self.tooltip_frame.visible = True
        self.tooltip_text.visible = True
        self.current_element = element

    def hide(self):
        """Hide the tooltip."""
        self.tooltip_frame.visible = False
        self.tooltip_text.visible = False
        self.current_element = None
        self.pending_element = None

    def add_to_scene(self, ui):
        """Add tooltip to scene (call last for top layer)."""
        ui.append(self.tooltip_frame)
        ui.append(self.tooltip_text)


# Usage
scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Create tooltip manager
tips = TooltipManager()

# Create some items with tooltips
sword_frame = mcrfpy.Frame(pos=(100, 100), size=(64, 64))
sword_frame.fill_color = mcrfpy.Color(80, 60, 40)
sword_frame.outline = 2
sword_frame.outline_color = mcrfpy.Color(120, 100, 80)
scene.children.append(sword_frame)

tips.register(
    sword_frame,
    "A rusty but reliable blade.\nDamage: 5-10\nSpeed: Fast",
    title="Iron Sword"
)

shield_frame = mcrfpy.Frame(pos=(180, 100), size=(64, 64))
shield_frame.fill_color = mcrfpy.Color(60, 60, 80)
shield_frame.outline = 2
shield_frame.outline_color = mcrfpy.Color(100, 100, 120)
scene.children.append(shield_frame)

tips.register(
    shield_frame,
    "Blocks incoming attacks.\nDefense: +5\nWeight: Medium",
    title="Steel Shield"
)

# Add tooltip last for top layer
tips.add_to_scene(scene.children)
