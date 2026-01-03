"""
ui.py - User Interface Components for McRogueFace Roguelike

Contains the health bar and message log UI elements.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import mcrfpy

from constants import (
    HP_BAR_X, HP_BAR_Y, HP_BAR_WIDTH, HP_BAR_HEIGHT,
    MSG_LOG_X, MSG_LOG_Y, MSG_LOG_WIDTH, MSG_LOG_HEIGHT, MSG_LOG_MAX_LINES,
    LEVEL_DISPLAY_X, LEVEL_DISPLAY_Y,
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_TEXT,
    COLOR_HP_BAR_BG, COLOR_HP_BAR_FILL, COLOR_HP_BAR_WARNING, COLOR_HP_BAR_CRITICAL,
    COLOR_MSG_DEFAULT
)


@dataclass
class Message:
    """A message in the message log."""
    text: str
    color: Tuple[int, int, int, int]


class HealthBar:
    """
    Visual health bar displaying player HP.

    Uses nested Frames: an outer background frame and an inner fill frame
    that resizes based on HP percentage.
    """

    def __init__(self, x: int = HP_BAR_X, y: int = HP_BAR_Y,
                 width: int = HP_BAR_WIDTH, height: int = HP_BAR_HEIGHT,
                 font: mcrfpy.Font = None):
        """
        Create a health bar.

        Args:
            x: X position
            y: Y position
            width: Total width of the bar
            height: Height of the bar
            font: Font for the HP text
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font or mcrfpy.default_font

        # Background frame
        self.bg_frame = mcrfpy.Frame(x, y, width, height)
        self.bg_frame.fill_color = mcrfpy.Color(*COLOR_HP_BAR_BG)
        self.bg_frame.outline = 2
        self.bg_frame.outline_color = mcrfpy.Color(*COLOR_UI_BORDER)

        # Fill frame (inside background)
        self.fill_frame = mcrfpy.Frame(x + 2, y + 2, width - 4, height - 4)
        self.fill_frame.fill_color = mcrfpy.Color(*COLOR_HP_BAR_FILL)
        self.fill_frame.outline = 0

        # HP text
        self.hp_text = mcrfpy.Caption("HP: 0 / 0", self.font, x + 8, y + 4)
        self.hp_text.fill_color = mcrfpy.Color(*COLOR_TEXT)

        self._max_fill_width = width - 4

    def add_to_scene(self, ui: mcrfpy.UICollection) -> None:
        """Add all health bar components to a scene."""
        ui.append(self.bg_frame)
        ui.append(self.fill_frame)
        ui.append(self.hp_text)

    def update(self, current_hp: int, max_hp: int) -> None:
        """
        Update the health bar display.

        Args:
            current_hp: Current hit points
            max_hp: Maximum hit points
        """
        # Calculate fill percentage
        if max_hp <= 0:
            percent = 0.0
        else:
            percent = max(0.0, min(1.0, current_hp / max_hp))

        # Update fill bar width
        self.fill_frame.w = int(self._max_fill_width * percent)

        # Update color based on HP percentage
        if percent > 0.6:
            color = COLOR_HP_BAR_FILL
        elif percent > 0.3:
            color = COLOR_HP_BAR_WARNING
        else:
            color = COLOR_HP_BAR_CRITICAL

        self.fill_frame.fill_color = mcrfpy.Color(*color)

        # Update text
        self.hp_text.text = f"HP: {current_hp} / {max_hp}"


class MessageLog:
    """
    Scrolling message log displaying game events.

    Uses a Frame container with Caption children for each line.
    """

    def __init__(self, x: int = MSG_LOG_X, y: int = MSG_LOG_Y,
                 width: int = MSG_LOG_WIDTH, height: int = MSG_LOG_HEIGHT,
                 max_lines: int = MSG_LOG_MAX_LINES,
                 font: mcrfpy.Font = None):
        """
        Create a message log.

        Args:
            x: X position
            y: Y position
            width: Width of the log
            height: Height of the log
            max_lines: Maximum number of visible lines
            font: Font for the messages
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_lines = max_lines
        self.font = font or mcrfpy.default_font

        # Container frame
        self.frame = mcrfpy.Frame(x, y, width, height)
        self.frame.fill_color = mcrfpy.Color(*COLOR_UI_BG)
        self.frame.outline = 1
        self.frame.outline_color = mcrfpy.Color(*COLOR_UI_BORDER)

        # Message storage
        self.messages: List[Message] = []
        self.captions: List[mcrfpy.Caption] = []

        # Line height (approximate based on font)
        self.line_height = 18

        # Create caption objects for each line
        self._init_captions()

    def _init_captions(self) -> None:
        """Initialize caption objects for message display."""
        for i in range(self.max_lines):
            caption = mcrfpy.Caption(
                "",
                self.font,
                self.x + 5,
                self.y + 5 + i * self.line_height
            )
            caption.fill_color = mcrfpy.Color(*COLOR_MSG_DEFAULT)
            self.captions.append(caption)

    def add_to_scene(self, ui: mcrfpy.UICollection) -> None:
        """Add the message log to a scene."""
        ui.append(self.frame)
        for caption in self.captions:
            ui.append(caption)

    def add_message(self, text: str,
                    color: Tuple[int, int, int, int] = COLOR_MSG_DEFAULT) -> None:
        """
        Add a message to the log.

        Args:
            text: Message text
            color: Text color as (R, G, B, A)
        """
        self.messages.append(Message(text, color))

        # Trim old messages
        if len(self.messages) > 100:
            self.messages = self.messages[-100:]

        # Update display
        self._update_display()

    def _update_display(self) -> None:
        """Update the displayed messages."""
        # Get the most recent messages
        recent = self.messages[-self.max_lines:]

        for i, caption in enumerate(self.captions):
            if i < len(recent):
                msg = recent[i]
                caption.text = msg.text
                caption.fill_color = mcrfpy.Color(*msg.color)
            else:
                caption.text = ""

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()
        self._update_display()


class LevelDisplay:
    """Simple display showing current dungeon level."""

    def __init__(self, x: int = LEVEL_DISPLAY_X, y: int = LEVEL_DISPLAY_Y,
                 font: mcrfpy.Font = None):
        """
        Create a level display.

        Args:
            x: X position
            y: Y position
            font: Font for the text
        """
        self.font = font or mcrfpy.default_font

        self.caption = mcrfpy.Caption("Level: 1", self.font, x, y)
        self.caption.fill_color = mcrfpy.Color(*COLOR_TEXT)

    def add_to_scene(self, ui: mcrfpy.UICollection) -> None:
        """Add to a scene."""
        ui.append(self.caption)

    def update(self, level: int) -> None:
        """Update the displayed level."""
        self.caption.text = f"Dungeon Level: {level}"


class GameUI:
    """
    Container for all UI elements.

    Provides a single point of access for updating the entire UI.
    """

    def __init__(self, font: mcrfpy.Font = None):
        """
        Create the game UI.

        Args:
            font: Font for all UI elements
        """
        self.font = font or mcrfpy.default_font

        # Create UI components
        self.health_bar = HealthBar(font=self.font)
        self.message_log = MessageLog(font=self.font)
        self.level_display = LevelDisplay(font=self.font)

    def add_to_scene(self, ui: mcrfpy.UICollection) -> None:
        """Add all UI elements to a scene."""
        self.health_bar.add_to_scene(ui)
        self.message_log.add_to_scene(ui)
        self.level_display.add_to_scene(ui)

    def update_hp(self, current_hp: int, max_hp: int) -> None:
        """Update the health bar."""
        self.health_bar.update(current_hp, max_hp)

    def add_message(self, text: str,
                    color: Tuple[int, int, int, int] = COLOR_MSG_DEFAULT) -> None:
        """Add a message to the log."""
        self.message_log.add_message(text, color)

    def update_level(self, level: int) -> None:
        """Update the dungeon level display."""
        self.level_display.update(level)

    def clear_messages(self) -> None:
        """Clear the message log."""
        self.message_log.clear()


class DeathScreen:
    """Game over screen shown when player dies."""

    def __init__(self, font: mcrfpy.Font = None):
        """
        Create the death screen.

        Args:
            font: Font for text
        """
        self.font = font or mcrfpy.default_font
        self.elements: List = []

        # Semi-transparent overlay
        self.overlay = mcrfpy.Frame(0, 0, 1024, 768)
        self.overlay.fill_color = mcrfpy.Color(0, 0, 0, 180)
        self.elements.append(self.overlay)

        # Death message
        self.death_text = mcrfpy.Caption(
            "YOU HAVE DIED",
            self.font,
            362, 300
        )
        self.death_text.fill_color = mcrfpy.Color(255, 0, 0, 255)
        self.death_text.outline = 2
        self.death_text.outline_color = mcrfpy.Color(0, 0, 0, 255)
        self.elements.append(self.death_text)

        # Restart prompt
        self.restart_text = mcrfpy.Caption(
            "Press R to restart",
            self.font,
            400, 400
        )
        self.restart_text.fill_color = mcrfpy.Color(200, 200, 200, 255)
        self.elements.append(self.restart_text)

    def add_to_scene(self, ui: mcrfpy.UICollection) -> None:
        """Add death screen elements to a scene."""
        for element in self.elements:
            ui.append(element)

    def remove_from_scene(self, ui: mcrfpy.UICollection) -> None:
        """Remove death screen elements from a scene."""
        for element in self.elements:
            try:
                ui.remove(element)
            except (ValueError, RuntimeError):
                pass
