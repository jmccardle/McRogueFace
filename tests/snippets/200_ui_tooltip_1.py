# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

class Tooltip:
    """A simple tooltip that follows the mouse."""

    def __init__(self, text, width=200):
        """
        Create a tooltip (initially hidden).

        Args:
            text: Tooltip text
            width: Maximum width
        """
        self.text = text
        self.visible = False

        # Tooltip frame
        self.frame = mcrfpy.Frame(pos=(0, 0), size=(width, 30))
        self.frame.fill_color = mcrfpy.Color(40, 40, 50, 240)
        self.frame.outline = 1
        self.frame.outline_color = mcrfpy.Color(100, 100, 120)
        self.frame.visible = False

        # Tooltip text
        self.caption = mcrfpy.Caption(text=text, pos=(5, 5))
        self.caption.fill_color = mcrfpy.Color(255, 255, 220)
        self.caption.visible = False

    def show(self, x, y):
        """Show tooltip at position."""
        # Offset from cursor
        self.frame.x = x + 15
        self.frame.y = y + 15
        self.caption.x = self.frame.x + 8
        self.caption.y = self.frame.y + 6

        # Keep on screen
        if self.frame.x + self.frame.w > 1024:
            self.frame.x = x - self.frame.w - 5
            self.caption.x = self.frame.x + 8
        if self.frame.y + self.frame.h > 768:
            self.frame.y = y - self.frame.h - 5
            self.caption.y = self.frame.y + 6

        self.frame.visible = True
        self.caption.visible = True
        self.visible = True

    def hide(self):
        """Hide the tooltip."""
        self.frame.visible = False
        self.caption.visible = False
        self.visible = False

    def set_text(self, text):
        """Update tooltip text."""
        self.text = text
        self.caption.text = text

    def add_to_scene(self, ui):
        """Add tooltip to scene (add last for top layer)."""
        ui.append(self.frame)
        ui.append(self.caption)


def make_hoverable(element, tooltip, tooltip_text=None):
    """
    Make a UI element show a tooltip on hover.

    Args:
        element: Frame, Caption, or Sprite to make hoverable
        tooltip: Tooltip instance
        tooltip_text: Text to show (optional, uses tooltip's default)
    """
    def on_enter(pos):
        if tooltip_text:
            tooltip.set_text(tooltip_text)
        tooltip.show(pos.x, pos.y)

    def on_move(pos):
        tooltip.show(pos.x, pos.y)

    def on_exit(pos):
        tooltip.hide()

    element.on_enter = on_enter
    element.on_move = on_move
    element.on_exit = on_exit


# Usage Example
scene = mcrfpy.Scene("tooltip_demo")
mcrfpy.current_scene = scene

# Create some buttons
button1 = mcrfpy.Frame(pos=(100, 100), size=(120, 40))
button1.fill_color = mcrfpy.Color(60, 60, 100)
button1.outline = 2
button1.outline_color = mcrfpy.Color(100, 100, 150)
scene.children.append(button1)

btn1_label = mcrfpy.Caption(text="Attack", pos=(125, 112))
btn1_label.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(btn1_label)

button2 = mcrfpy.Frame(pos=(100, 160), size=(120, 40))
button2.fill_color = mcrfpy.Color(60, 100, 60)
button2.outline = 2
button2.outline_color = mcrfpy.Color(100, 150, 100)
scene.children.append(button2)

btn2_label = mcrfpy.Caption(text="Defend", pos=(125, 172))
btn2_label.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(btn2_label)

# Create shared tooltip (add last for top layer)
tooltip = Tooltip("", width=250)
tooltip.add_to_scene(scene.children)

# Make buttons hoverable
make_hoverable(button1, tooltip, "Deal damage to the enemy")
make_hoverable(button2, tooltip, "Reduce incoming damage by 50%")
