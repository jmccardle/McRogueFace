# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene,Timer] verified=0.3.6 status=ok
# region: enhanced
import mcrfpy
import time

class EnhancedMessageLog:
    """Message log with categories, timestamps, and filtering."""

    # Predefined message categories with colors
    CATEGORIES = {
        'system': mcrfpy.Color(150, 150, 255),
        'combat': mcrfpy.Color(255, 100, 100),
        'loot': mcrfpy.Color(255, 215, 0),
        'dialog': mcrfpy.Color(100, 255, 100),
        'info': mcrfpy.Color(200, 200, 200),
    }

    def __init__(self, x, y, w, h, max_messages=200, line_height=18):
        self.max_messages = max_messages
        self.line_height = line_height
        self.messages = []
        self.filter_category = None  # None = show all

        self.frame = mcrfpy.Frame(pos=(x, y), size=(w, h))
        self.frame.fill_color = mcrfpy.Color(15, 15, 25, 240)
        self.frame.outline = 2
        self.frame.outline_color = mcrfpy.Color(80, 80, 120)

        self.visible_lines = int(h / line_height)
        self.scroll_offset = 0

    def add(self, text, category='info', show_time=False):
        """
        Add a categorized message.

        Args:
            text: Message text
            category: Category key (system, combat, loot, dialog, info)
            show_time: Whether to prepend timestamp
        """
        color = self.CATEGORIES.get(category, self.CATEGORIES['info'])

        if show_time:
            # Game time or real time - customize as needed
            timestamp = time.strftime("%H:%M")
            text = f"[{timestamp}] {text}"

        self.messages.append({
            'text': text,
            'color': color,
            'category': category,
            'timestamp': time.time()
        })

        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        # Auto-scroll only if already at bottom
        visible_msgs = self._get_filtered_messages()
        if self.scroll_offset >= len(visible_msgs) - self.visible_lines - 1:
            self.scroll_offset = max(0, len(visible_msgs) - self.visible_lines)

        self._rebuild_display()

    def _get_filtered_messages(self):
        """Get messages matching current filter."""
        if self.filter_category is None:
            return self.messages
        return [m for m in self.messages if m['category'] == self.filter_category]

    def set_filter(self, category):
        """
        Set category filter.

        Args:
            category: Category to show, or None for all
        """
        self.filter_category = category
        self.scroll_offset = 0
        self._rebuild_display()

    def _rebuild_display(self):
        """Rebuild visible messages."""
        self.frame.children.clear()

        filtered = self._get_filtered_messages()
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.visible_lines, len(filtered))

        # Positions are frame-local (relative to the frame's top-left corner)
        for i, msg_idx in enumerate(range(start_idx, end_idx)):
            msg = filtered[msg_idx]
            caption = mcrfpy.Caption(
                text=msg['text'],
                pos=(8, 4 + (i * self.line_height))
            )
            caption.fill_color = msg['color']
            self.frame.children.append(caption)

    def scroll_up(self, lines=1):
        self.scroll_offset = max(0, self.scroll_offset - lines)
        self._rebuild_display()

    def scroll_down(self, lines=1):
        filtered = self._get_filtered_messages()
        max_offset = max(0, len(filtered) - self.visible_lines)
        self.scroll_offset = min(max_offset, self.scroll_offset + lines)
        self._rebuild_display()

    # Convenience methods for common message types
    def system(self, text):
        self.add(text, 'system')

    def combat(self, text):
        self.add(text, 'combat')

    def loot(self, text):
        self.add(text, 'loot')

    def dialog(self, text):
        self.add(text, 'dialog')


# Usage
scene = mcrfpy.Scene("enhanced_log_demo")
log = EnhancedMessageLog(50, 400, 500, 250)
scene.children.append(log.frame)
scene.activate()

log.system("Game loaded successfully.")
log.combat("You attack the skeleton!")
log.combat("The skeleton crumbles to dust.")
log.loot("You found 50 gold!")
log.dialog("The merchant says: 'Welcome, traveler!'")

# Filter to only combat messages
log.set_filter('combat')

# Show all again
log.set_filter(None)
# endregion


# region: usage
import mcrfpy

# Initialize
scene = mcrfpy.Scene("game")

# Create log at bottom of screen
log = EnhancedMessageLog(10, 500, 700, 250, line_height=20)
scene.children.append(log.frame)

# Simulate game events
def simulate_combat(timer, runtime):
    import random
    events = [
        ("You swing your sword!", "combat"),
        ("The orc dodges!", "combat"),
        ("Critical hit!", "combat"),
        ("You found a potion!", "loot"),
    ]
    event = random.choice(events)
    log.add(event[0], event[1])

# Add messages every 2 seconds for demo
mcrfpy.Timer("combat_sim", simulate_combat, 2000)

# Keyboard controls
def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return
    if key == mcrfpy.Key.PAGE_UP:
        log.scroll_up(3)
    elif key == mcrfpy.Key.PAGE_DOWN:
        log.scroll_down(3)
    elif key == mcrfpy.Key.C:
        log.set_filter('combat')
    elif key == mcrfpy.Key.L:
        log.set_filter('loot')
    elif key == mcrfpy.Key.A:
        log.set_filter(None)  # All

scene.on_key = on_key

log.system("Press PageUp/PageDown to scroll")
log.system("Press C for combat, L for loot, A for all")

scene.activate()
# endregion
