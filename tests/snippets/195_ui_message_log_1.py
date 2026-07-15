# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

class MessageLog:
    """A scrolling message log widget for displaying game events."""

    def __init__(self, x, y, w, h, max_messages=100, line_height=18):
        """
        Create a new message log.

        Args:
            x, y: Position of the log on screen
            w, h: Size of the log area
            max_messages: Maximum messages to keep in history
            line_height: Pixel height of each message line
        """
        self.max_messages = max_messages
        self.line_height = line_height
        self.messages = []  # Store message data

        # Create the container frame
        self.frame = mcrfpy.Frame(pos=(x, y), size=(w, h))
        self.frame.fill_color = mcrfpy.Color(20, 20, 30, 220)
        self.frame.outline = 1
        self.frame.outline_color = mcrfpy.Color(60, 60, 80)

        # Calculate visible lines
        self.visible_lines = int(h / line_height)
        self.scroll_offset = 0

    def add(self, text, color=None):
        """
        Add a message to the log.

        Args:
            text: The message text
            color: Optional Color for the text (defaults to white)
        """
        if color is None:
            color = mcrfpy.Color(220, 220, 220)

        # Add to message buffer
        self.messages.append({'text': text, 'color': color})

        # Trim old messages if over limit
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        # Auto-scroll to bottom
        self.scroll_offset = max(0, len(self.messages) - self.visible_lines)

        # Rebuild the display
        self._rebuild_display()

    def _rebuild_display(self):
        """Rebuild all visible Caption elements."""
        # Clear existing children (remove() takes a child object, not an index)
        while len(self.frame.children) > 0:
            self.frame.children.remove(self.frame.children[0])

        # Calculate which messages to show
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.visible_lines, len(self.messages))

        # Create Caption for each visible message
        # (Frame.children are positioned in frame-local coordinates,
        # not absolute screen coordinates)
        for i, msg_idx in enumerate(range(start_idx, end_idx)):
            msg = self.messages[msg_idx]
            caption = mcrfpy.Caption(
                text=msg['text'],
                pos=(5, 5 + (i * self.line_height))
            )
            caption.fill_color = msg['color']
            self.frame.children.append(caption)

    def scroll_up(self, lines=1):
        """Scroll the log up (show older messages)."""
        self.scroll_offset = max(0, self.scroll_offset - lines)
        self._rebuild_display()

    def scroll_down(self, lines=1):
        """Scroll the log down (show newer messages)."""
        max_offset = max(0, len(self.messages) - self.visible_lines)
        self.scroll_offset = min(max_offset, self.scroll_offset + lines)
        self._rebuild_display()

    def clear(self):
        """Clear all messages from the log."""
        self.messages = []
        self.scroll_offset = 0
        self._rebuild_display()


# Usage Example
scene = mcrfpy.Scene("log_demo")

# Create the message log
log = MessageLog(50, 400, 400, 200)
scene.children.append(log.frame)

scene.activate()

# Add some test messages
log.add("Welcome to the dungeon!")
log.add("You see a dark corridor ahead.", mcrfpy.Color(150, 150, 150))
log.add("A goblin appears!", mcrfpy.Color(255, 100, 100))
log.add("You attack the goblin for 5 damage.", mcrfpy.Color(255, 200, 100))
log.add("The goblin strikes back!", mcrfpy.Color(255, 100, 100))
