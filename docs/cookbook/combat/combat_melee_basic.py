"""McRogueFace - Melee Combat System (basic)

Documentation: https://mcrogueface.github.io/cookbook/combat_melee
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_melee_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

class CombatLog:
    """Scrolling combat message log."""

    def __init__(self, x, y, width, height, max_messages=10):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_messages = max_messages
        self.messages = []
        self.captions = []

        ui = mcrfpy.sceneUI(mcrfpy.currentScene())

        # Background
        self.frame = mcrfpy.Frame(x, y, width, height)
        self.frame.fill_color = mcrfpy.Color(0, 0, 0, 180)
        ui.append(self.frame)

    def add_message(self, text, color=None):
        """Add a message to the log."""
        if color is None:
            color = mcrfpy.Color(200, 200, 200)

        self.messages.append((text, color))

        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

        self._refresh_display()

    def _refresh_display(self):
        """Redraw all messages."""
        ui = mcrfpy.sceneUI(mcrfpy.currentScene())

        # Remove old captions
        for caption in self.captions:
            try:
                ui.remove(caption)
            except:
                pass
        self.captions.clear()

        # Create new captions
        line_height = 18
        for i, (text, color) in enumerate(self.messages):
            caption = mcrfpy.Caption(text, self.x + 5, self.y + 5 + i * line_height)
            caption.fill_color = color
            ui.append(caption)
            self.captions.append(caption)

    def log_attack(self, attacker_name, defender_name, damage, killed=False, critical=False):
        """Log an attack event."""
        if critical:
            text = f"{attacker_name} CRITS {defender_name} for {damage}!"
            color = mcrfpy.Color(255, 255, 0)
        else:
            text = f"{attacker_name} hits {defender_name} for {damage}."
            color = mcrfpy.Color(200, 200, 200)

        self.add_message(text, color)

        if killed:
            self.add_message(f"{defender_name} is defeated!", mcrfpy.Color(255, 100, 100))


# Global combat log
combat_log = None

def init_combat_log():
    global combat_log
    combat_log = CombatLog(10, 500, 400, 200)