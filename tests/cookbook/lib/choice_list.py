# McRogueFace Cookbook - Choice List Widget
"""
Vertical list of selectable text options with keyboard/mouse navigation.

Example:
    from lib.choice_list import ChoiceList

    def on_select(index, value):
        print(f"Selected {value} at index {index}")

    choices = ChoiceList(
        pos=(100, 100),
        size=(200, 150),
        choices=["New Game", "Load Game", "Options", "Quit"],
        on_select=on_select
    )
    scene.children.append(choices.frame)

    # Navigate with keyboard
    choices.navigate(1)   # Move down
    choices.navigate(-1)  # Move up
    choices.confirm()     # Select current
"""
import mcrfpy


class ChoiceList:
    """Vertical list of selectable text options.

    Args:
        pos: (x, y) position tuple
        size: (width, height) tuple
        choices: List of choice strings
        on_select: Callback(index, value) when selection is confirmed
        item_height: Height of each item (default: 30)
        selected_color: Background color of selected item
        hover_color: Background color when hovered
        normal_color: Background color of unselected items
        text_color: Color of choice text
        selected_text_color: Text color when selected
        font_size: Size of choice text (default: 16)
        outline: Border thickness (default: 1)

    Attributes:
        frame: The outer frame (add this to scene)
        selected_index: Currently selected index
        choices: List of choice strings
    """

    DEFAULT_NORMAL = mcrfpy.Color(40, 40, 45)
    DEFAULT_HOVER = mcrfpy.Color(60, 60, 70)
    DEFAULT_SELECTED = mcrfpy.Color(80, 100, 140)
    DEFAULT_TEXT = mcrfpy.Color(200, 200, 200)
    DEFAULT_SELECTED_TEXT = mcrfpy.Color(255, 255, 255)
    DEFAULT_OUTLINE = mcrfpy.Color(100, 100, 110)

    def __init__(self, pos, size, choices, on_select=None,
                 item_height=30, selected_color=None, hover_color=None,
                 normal_color=None, text_color=None, selected_text_color=None,
                 font_size=16, outline=1):
        self.pos = pos
        self.size = size
        self._choices = list(choices)
        self.on_select = on_select
        self.item_height = item_height
        self.font_size = font_size
        self._selected_index = 0

        # Colors
        self.normal_color = normal_color or self.DEFAULT_NORMAL
        self.hover_color = hover_color or self.DEFAULT_HOVER
        self.selected_color = selected_color or self.DEFAULT_SELECTED
        self.text_color = text_color or self.DEFAULT_TEXT
        self.selected_text_color = selected_text_color or self.DEFAULT_SELECTED_TEXT

        # Hover tracking
        self._hovered_index = -1

        # Create outer frame
        self.frame = mcrfpy.Frame(
            pos=pos,
            size=size,
            fill_color=self.normal_color,
            outline_color=self.DEFAULT_OUTLINE,
            outline=outline
        )

        # Item frames and labels
        self._item_frames = []
        self._item_labels = []

        self._rebuild_items()

    def _rebuild_items(self):
        """Rebuild all item frames and labels."""
        # Clear existing - pop all items from the collection
        while len(self.frame.children) > 0:
            self.frame.children.pop()
        self._item_frames = []
        self._item_labels = []

        # Create item frames
        for i, choice in enumerate(self._choices):
            # Create item frame
            item_frame = mcrfpy.Frame(
                pos=(0, i * self.item_height),
                size=(self.size[0], self.item_height),
                fill_color=self.selected_color if i == self._selected_index else self.normal_color,
                outline=0
            )

            # Create label
            label = mcrfpy.Caption(
                text=choice,
                pos=(10, (self.item_height - self.font_size) / 2),
                fill_color=self.selected_text_color if i == self._selected_index else self.text_color,
                font_size=self.font_size
            )

            item_frame.children.append(label)

            # Set up click handler
            idx = i  # Capture index in closure
            def make_click_handler(index):
                def handler(pos, button, action):
                    if button == "left" and action == "end":
                        self.set_selected(index)
                        if self.on_select:
                            self.on_select(index, self._choices[index])
                return handler

            def make_enter_handler(index):
                def handler(pos, button, action):
                    self._on_item_enter(index)
                return handler

            def make_exit_handler(index):
                def handler(pos, button, action):
                    self._on_item_exit(index)
                return handler

            item_frame.on_click = make_click_handler(idx)
            item_frame.on_enter = make_enter_handler(idx)
            item_frame.on_exit = make_exit_handler(idx)

            self._item_frames.append(item_frame)
            self._item_labels.append(label)
            self.frame.children.append(item_frame)

    def _on_item_enter(self, index):
        """Handle mouse entering an item."""
        self._hovered_index = index
        if index != self._selected_index:
            self._item_frames[index].fill_color = self.hover_color

    def _on_item_exit(self, index):
        """Handle mouse leaving an item."""
        self._hovered_index = -1
        if index != self._selected_index:
            self._item_frames[index].fill_color = self.normal_color

    def _update_display(self):
        """Update visual state of all items."""
        for i, (frame, label) in enumerate(zip(self._item_frames, self._item_labels)):
            if i == self._selected_index:
                frame.fill_color = self.selected_color
                label.fill_color = self.selected_text_color
            elif i == self._hovered_index:
                frame.fill_color = self.hover_color
                label.fill_color = self.text_color
            else:
                frame.fill_color = self.normal_color
                label.fill_color = self.text_color

    @property
    def selected_index(self):
        """Currently selected index."""
        return self._selected_index

    @property
    def selected_value(self):
        """Currently selected value."""
        if 0 <= self._selected_index < len(self._choices):
            return self._choices[self._selected_index]
        return None

    @property
    def choices(self):
        """List of choices."""
        return list(self._choices)

    @choices.setter
    def choices(self, value):
        """Set new choices list."""
        self._choices = list(value)
        self._selected_index = min(self._selected_index, len(self._choices) - 1)
        if self._selected_index < 0:
            self._selected_index = 0
        self._rebuild_items()

    def set_selected(self, index):
        """Set the selected index.

        Args:
            index: Index to select (clamped to valid range)
        """
        if not self._choices:
            return

        old_index = self._selected_index
        self._selected_index = max(0, min(index, len(self._choices) - 1))

        if old_index != self._selected_index:
            self._update_display()

    def navigate(self, direction):
        """Navigate up or down in the list.

        Args:
            direction: +1 for down, -1 for up
        """
        if not self._choices:
            return

        new_index = self._selected_index + direction
        # Wrap around
        if new_index < 0:
            new_index = len(self._choices) - 1
        elif new_index >= len(self._choices):
            new_index = 0

        self.set_selected(new_index)

    def confirm(self):
        """Confirm the current selection (triggers callback)."""
        if self.on_select and 0 <= self._selected_index < len(self._choices):
            self.on_select(self._selected_index, self._choices[self._selected_index])

    def add_choice(self, choice, index=None):
        """Add a choice at the given index (or end if None)."""
        if index is None:
            self._choices.append(choice)
        else:
            self._choices.insert(index, choice)
        self._rebuild_items()

    def remove_choice(self, index):
        """Remove the choice at the given index."""
        if 0 <= index < len(self._choices):
            del self._choices[index]
            if self._selected_index >= len(self._choices):
                self._selected_index = max(0, len(self._choices) - 1)
            self._rebuild_items()

    def set_choice(self, index, value):
        """Change the text of a choice."""
        if 0 <= index < len(self._choices):
            self._choices[index] = value
            self._item_labels[index].text = value


def create_menu(pos, choices, on_select=None, title=None, width=200):
    """Create a simple menu with optional title.

    Args:
        pos: (x, y) position
        choices: List of choice strings
        on_select: Callback(index, value)
        title: Optional menu title
        width: Menu width

    Returns:
        Tuple of (container_frame, choice_list) or just choice_list if no title
    """
    if title:
        # Create container with title
        item_height = 30
        title_height = 40
        total_height = title_height + len(choices) * item_height

        container = mcrfpy.Frame(
            pos=pos,
            size=(width, total_height),
            fill_color=mcrfpy.Color(30, 30, 35),
            outline_color=mcrfpy.Color(100, 100, 110),
            outline=2
        )

        # Title caption
        title_cap = mcrfpy.Caption(
            text=title,
            pos=(width / 2, 10),
            fill_color=mcrfpy.Color(255, 255, 255),
            font_size=18
        )
        container.children.append(title_cap)

        # Choice list below title
        choice_list = ChoiceList(
            pos=(0, title_height),
            size=(width, len(choices) * item_height),
            choices=choices,
            on_select=on_select,
            outline=0
        )

        # Add choice list frame as child
        container.children.append(choice_list.frame)

        return container, choice_list
    else:
        return ChoiceList(
            pos=pos,
            size=(width, len(choices) * 30),
            choices=choices,
            on_select=on_select
        )
