# McRogueFace Cookbook - Text Box Widget
"""
Word-wrapped text display with typewriter effect.

Example:
    from lib.text_box import TextBox

    text_box = TextBox(
        pos=(100, 100),
        size=(400, 200),
        text="This is a long text that will be word-wrapped...",
        chars_per_second=30
    )
    scene.children.append(text_box.frame)

    # Skip animation
    text_box.skip_animation()
"""
import mcrfpy


class TextBox:
    """Word-wrapped text with optional typewriter effect.

    Args:
        pos: (x, y) position tuple
        size: (width, height) tuple
        text: Initial text to display
        chars_per_second: Typewriter speed (0 = instant)
        font_size: Text size (default: 14)
        text_color: Color of text (default: white)
        bg_color: Background color (default: dark)
        outline_color: Border color (default: gray)
        outline: Border thickness (default: 1)
        padding: Internal padding (default: 10)

    Attributes:
        frame: The outer frame (add this to scene)
        text: Current text content
        is_complete: Whether typewriter animation finished
    """

    DEFAULT_TEXT_COLOR = mcrfpy.Color(220, 220, 220)
    DEFAULT_BG_COLOR = mcrfpy.Color(25, 25, 30)
    DEFAULT_OUTLINE = mcrfpy.Color(80, 80, 90)

    def __init__(self, pos, size, text="", chars_per_second=30,
                 font_size=14, text_color=None, bg_color=None,
                 outline_color=None, outline=1, padding=10):
        self.pos = pos
        self.size = size
        self._full_text = text
        self.chars_per_second = chars_per_second
        self.font_size = font_size
        self.padding = padding

        # Colors
        self.text_color = text_color or self.DEFAULT_TEXT_COLOR
        self.bg_color = bg_color or self.DEFAULT_BG_COLOR
        self.outline_color = outline_color or self.DEFAULT_OUTLINE

        # State
        self._displayed_chars = 0
        self._is_complete = chars_per_second == 0
        self._on_complete = None
        self._timer_name = None

        # Create outer frame
        self.frame = mcrfpy.Frame(
            pos=pos,
            size=size,
            fill_color=self.bg_color,
            outline_color=self.outline_color,
            outline=outline
        )

        # Calculate text area
        self._text_width = size[0] - padding * 2
        self._text_height = size[1] - padding * 2

        # Create text caption
        self._caption = mcrfpy.Caption(
            text="",
            pos=(padding, padding),
            fill_color=self.text_color,
            font_size=font_size
        )
        self.frame.children.append(self._caption)

        # Start typewriter if there's text
        if text and chars_per_second > 0:
            self._start_typewriter()
        elif text:
            self._caption.text = self._word_wrap(text)
            self._displayed_chars = len(text)
            self._is_complete = True

    def _word_wrap(self, text):
        """Word-wrap text to fit within the text box width.

        Simple implementation that breaks on spaces.
        """
        # Estimate chars per line based on font size
        # This is approximate - real implementation would measure text
        avg_char_width = self.font_size * 0.6
        chars_per_line = int(self._text_width / avg_char_width)

        if chars_per_line <= 0:
            return text

        words = text.split(' ')
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            # Check if word fits on current line
            word_len = len(word)
            if current_length + word_len + (1 if current_line else 0) <= chars_per_line:
                current_line.append(word)
                current_length += word_len + (1 if len(current_line) > 1 else 0)
            else:
                # Start new line
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_len

        # Add last line
        if current_line:
            lines.append(' '.join(current_line))

        return '\n'.join(lines)

    def _start_typewriter(self):
        """Start the typewriter animation."""
        if self.chars_per_second <= 0:
            return

        self._displayed_chars = 0
        self._is_complete = False

        # Calculate interval in milliseconds
        interval_ms = max(1, int(1000 / self.chars_per_second))

        self._timer_name = f"textbox_{id(self)}"
        mcrfpy.Timer(self._timer_name, self._typewriter_tick, interval_ms)

    def _typewriter_tick(self, runtime):
        """Add one character to the display."""
        if self._displayed_chars >= len(self._full_text):
            # Animation complete
            self._is_complete = True
            # Stop timer by deleting it - there's no direct stop method
            # The timer will continue but we'll just not update
            if self._on_complete:
                self._on_complete()
            return

        self._displayed_chars += 1
        visible_text = self._full_text[:self._displayed_chars]
        self._caption.text = self._word_wrap(visible_text)

    @property
    def text(self):
        """Get the full text content."""
        return self._full_text

    @property
    def is_complete(self):
        """Whether the typewriter animation has finished."""
        return self._is_complete

    @property
    def on_complete(self):
        """Callback when animation completes."""
        return self._on_complete

    @on_complete.setter
    def on_complete(self, callback):
        """Set callback for animation completion."""
        self._on_complete = callback

    def set_text(self, text, animate=True):
        """Change the text content.

        Args:
            text: New text to display
            animate: Whether to use typewriter effect
        """
        self._full_text = text

        if animate and self.chars_per_second > 0:
            self._start_typewriter()
        else:
            self._caption.text = self._word_wrap(text)
            self._displayed_chars = len(text)
            self._is_complete = True

    def skip_animation(self):
        """Skip to the end of the typewriter animation."""
        self._displayed_chars = len(self._full_text)
        self._caption.text = self._word_wrap(self._full_text)
        self._is_complete = True
        if self._on_complete:
            self._on_complete()

    def clear(self):
        """Clear the text box."""
        self._full_text = ""
        self._displayed_chars = 0
        self._caption.text = ""
        self._is_complete = True

    def append_text(self, text, animate=True):
        """Append text to the current content.

        Args:
            text: Text to append
            animate: Whether to animate the new text
        """
        new_text = self._full_text + text
        self.set_text(new_text, animate=animate)


class DialogueBox(TextBox):
    """Specialized text box for dialogue with speaker name.

    Args:
        pos: (x, y) position tuple
        size: (width, height) tuple
        speaker: Name of the speaker
        text: Dialogue text
        speaker_color: Color for speaker name (default: yellow)
        **kwargs: Additional TextBox arguments
    """

    DEFAULT_SPEAKER_COLOR = mcrfpy.Color(255, 220, 100)

    def __init__(self, pos, size, speaker="", text="",
                 speaker_color=None, **kwargs):
        # Initialize parent with empty text
        super().__init__(pos, size, text="", **kwargs)

        self._speaker = speaker
        self.speaker_color = speaker_color or self.DEFAULT_SPEAKER_COLOR

        # Create speaker name caption
        self._speaker_caption = mcrfpy.Caption(
            text=speaker,
            pos=(self.padding, self.padding - 5),
            fill_color=self.speaker_color,
            font_size=self.font_size + 2
        )
        self._speaker_caption.outline = 1
        self._speaker_caption.outline_color = mcrfpy.Color(0, 0, 0)
        self.frame.children.append(self._speaker_caption)

        # Adjust main text position
        self._caption.y = self.padding + self.font_size + 10

        # Now set the actual text
        if text:
            self.set_text(text, animate=kwargs.get('chars_per_second', 30) > 0)

    @property
    def speaker(self):
        """Get the speaker name."""
        return self._speaker

    @speaker.setter
    def speaker(self, value):
        """Set the speaker name."""
        self._speaker = value
        self._speaker_caption.text = value

    def set_dialogue(self, speaker, text, animate=True):
        """Set both speaker and text.

        Args:
            speaker: Speaker name
            text: Dialogue text
            animate: Whether to animate the text
        """
        self.speaker = speaker
        self.set_text(text, animate=animate)
