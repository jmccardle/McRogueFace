# McRogueFace Cookbook - Scrollable List Widget
"""
Scrolling list with arbitrary item rendering.

Example:
    from lib.scrollable_list import ScrollableList

    def render_item(item, frame, index, selected):
        # Add item content to frame
        label = mcrfpy.Caption(text=item['name'], pos=(10, 5))
        frame.children.append(label)

    items = [{'name': f'Item {i}'} for i in range(50)]

    scroll_list = ScrollableList(
        pos=(100, 100),
        size=(300, 400),
        items=items,
        render_item=render_item,
        item_height=40
    )
    scene.children.append(scroll_list.frame)
"""
import mcrfpy


class ScrollableList:
    """Scrolling list with arbitrary item rendering.

    Args:
        pos: (x, y) position tuple
        size: (width, height) tuple
        items: List of items to display
        item_height: Height of each item row (default: 30)
        render_item: Callback(item, frame, index, selected) to render item content
        on_select: Callback(index, item) when item is selected
        bg_color: Background color (default: dark)
        item_bg_color: Normal item background
        selected_bg_color: Selected item background
        hover_bg_color: Hovered item background
        outline_color: Border color
        outline: Border thickness

    Attributes:
        frame: The outer frame (add this to scene)
        items: List of items
        selected_index: Currently selected index
        scroll_offset: Current scroll position
    """

    DEFAULT_BG = mcrfpy.Color(30, 30, 35)
    DEFAULT_ITEM_BG = mcrfpy.Color(35, 35, 40)
    DEFAULT_SELECTED_BG = mcrfpy.Color(60, 80, 120)
    DEFAULT_HOVER_BG = mcrfpy.Color(50, 50, 60)
    DEFAULT_OUTLINE = mcrfpy.Color(80, 80, 90)

    def __init__(self, pos, size, items=None, item_height=30,
                 render_item=None, on_select=None,
                 bg_color=None, item_bg_color=None,
                 selected_bg_color=None, hover_bg_color=None,
                 outline_color=None, outline=1):
        self.pos = pos
        self.size = size
        self._items = list(items) if items else []
        self.item_height = item_height
        self.render_item = render_item or self._default_render
        self.on_select = on_select

        # Colors
        self.bg_color = bg_color or self.DEFAULT_BG
        self.item_bg_color = item_bg_color or self.DEFAULT_ITEM_BG
        self.selected_bg_color = selected_bg_color or self.DEFAULT_SELECTED_BG
        self.hover_bg_color = hover_bg_color or self.DEFAULT_HOVER_BG
        self.outline_color = outline_color or self.DEFAULT_OUTLINE

        # State
        self._selected_index = -1
        self._scroll_offset = 0
        self._hovered_index = -1
        self._visible_count = int(size[1] / item_height)

        # Create outer frame with clipping
        self.frame = mcrfpy.Frame(
            pos=pos,
            size=size,
            fill_color=self.bg_color,
            outline_color=self.outline_color,
            outline=outline
        )
        self.frame.clip_children = True

        # Content container (scrolls within frame)
        self._content = mcrfpy.Frame(
            pos=(0, 0),
            size=(size[0], max(size[1], len(self._items) * item_height)),
            fill_color=mcrfpy.Color(0, 0, 0, 0),  # Transparent
            outline=0
        )
        self.frame.children.append(self._content)

        # Set up scroll handler
        self.frame.on_move = self._on_mouse_move

        # Build initial items
        self._rebuild_items()

    def _default_render(self, item, frame, index, selected):
        """Default item renderer - just shows string representation."""
        text = str(item) if not isinstance(item, dict) else item.get('name', str(item))
        label = mcrfpy.Caption(
            text=text,
            pos=(10, (self.item_height - 14) / 2),
            fill_color=mcrfpy.Color(200, 200, 200),
            font_size=14
        )
        frame.children.append(label)

    def _rebuild_items(self):
        """Rebuild all item frames."""
        # Clear content
        while len(self._content.children) > 0:
            self._content.children.pop()

        # Update content size
        total_height = len(self._items) * self.item_height
        self._content.h = max(self.size[1], total_height)

        # Create item frames
        self._item_frames = []
        for i, item in enumerate(self._items):
            item_frame = mcrfpy.Frame(
                pos=(0, i * self.item_height),
                size=(self.size[0], self.item_height),
                fill_color=self.item_bg_color,
                outline=0
            )

            # Set up click handler
            def make_click_handler(index):
                def handler(pos, button, action):
                    if button == "left" and action == "end":
                        self.select(index)
                return handler

            def make_enter_handler(index):
                def handler(pos, button, action):
                    self._on_item_enter(index)
                return handler

            def make_exit_handler(index):
                def handler(pos, button, action):
                    self._on_item_exit(index)
                return handler

            item_frame.on_click = make_click_handler(i)
            item_frame.on_enter = make_enter_handler(i)
            item_frame.on_exit = make_exit_handler(i)

            # Render item content
            is_selected = i == self._selected_index
            self.render_item(item, item_frame, i, is_selected)

            self._item_frames.append(item_frame)
            self._content.children.append(item_frame)

    def _on_item_enter(self, index):
        """Handle mouse entering an item."""
        self._hovered_index = index
        if index != self._selected_index:
            self._item_frames[index].fill_color = self.hover_bg_color

    def _on_item_exit(self, index):
        """Handle mouse leaving an item."""
        if self._hovered_index == index:
            self._hovered_index = -1
        if index != self._selected_index:
            self._item_frames[index].fill_color = self.item_bg_color

    def _on_mouse_move(self, pos, button, action):
        """Handle mouse movement for scroll wheel detection."""
        # Note: This is a placeholder - actual scroll wheel handling
        # depends on the engine's input system
        pass

    def _update_item_display(self):
        """Update visual state of items."""
        for i, frame in enumerate(self._item_frames):
            if i == self._selected_index:
                frame.fill_color = self.selected_bg_color
            elif i == self._hovered_index:
                frame.fill_color = self.hover_bg_color
            else:
                frame.fill_color = self.item_bg_color

    @property
    def items(self):
        """List of items."""
        return list(self._items)

    @items.setter
    def items(self, value):
        """Set new items list."""
        self._items = list(value)
        self._selected_index = -1
        self._scroll_offset = 0
        self._rebuild_items()

    @property
    def selected_index(self):
        """Currently selected index (-1 if none)."""
        return self._selected_index

    @property
    def selected_item(self):
        """Currently selected item (None if none)."""
        if 0 <= self._selected_index < len(self._items):
            return self._items[self._selected_index]
        return None

    @property
    def scroll_offset(self):
        """Current scroll position in pixels."""
        return self._scroll_offset

    def select(self, index):
        """Select an item by index.

        Args:
            index: Item index to select
        """
        if not self._items:
            return

        old_index = self._selected_index
        self._selected_index = max(-1, min(index, len(self._items) - 1))

        if old_index != self._selected_index:
            self._update_item_display()
            if self.on_select and self._selected_index >= 0:
                self.on_select(self._selected_index, self._items[self._selected_index])

    def scroll(self, delta):
        """Scroll the list by a number of items.

        Args:
            delta: Number of items to scroll (positive = down)
        """
        max_scroll = max(0, len(self._items) * self.item_height - self.size[1])
        new_offset = self._scroll_offset + delta * self.item_height
        new_offset = max(0, min(new_offset, max_scroll))

        if new_offset != self._scroll_offset:
            self._scroll_offset = new_offset
            self._content.y = -self._scroll_offset

    def scroll_to(self, index):
        """Scroll to make an item visible.

        Args:
            index: Item index to scroll to
        """
        if not 0 <= index < len(self._items):
            return

        item_top = index * self.item_height
        item_bottom = item_top + self.item_height

        if item_top < self._scroll_offset:
            self._scroll_offset = item_top
        elif item_bottom > self._scroll_offset + self.size[1]:
            self._scroll_offset = item_bottom - self.size[1]

        self._content.y = -self._scroll_offset

    def navigate(self, direction):
        """Navigate selection up or down.

        Args:
            direction: +1 for down, -1 for up
        """
        if not self._items:
            return

        if self._selected_index < 0:
            new_index = 0 if direction > 0 else len(self._items) - 1
        else:
            new_index = self._selected_index + direction
            # Wrap around
            if new_index < 0:
                new_index = len(self._items) - 1
            elif new_index >= len(self._items):
                new_index = 0

        self.select(new_index)
        self.scroll_to(new_index)

    def add_item(self, item, index=None):
        """Add an item to the list.

        Args:
            item: Item to add
            index: Position to insert (None = end)
        """
        if index is None:
            self._items.append(item)
        else:
            self._items.insert(index, item)
        self._rebuild_items()

    def remove_item(self, index):
        """Remove an item by index.

        Args:
            index: Index of item to remove
        """
        if 0 <= index < len(self._items):
            del self._items[index]
            if self._selected_index >= len(self._items):
                self._selected_index = len(self._items) - 1
            self._rebuild_items()

    def clear(self):
        """Remove all items."""
        self._items.clear()
        self._selected_index = -1
        self._scroll_offset = 0
        self._rebuild_items()

    def filter(self, predicate):
        """Filter displayed items.

        Args:
            predicate: Function(item) -> bool to filter items

        Note: This creates a new filtered view, not modifying original items.
        """
        # Store original items if not already stored
        if not hasattr(self, '_original_items'):
            self._original_items = list(self._items)

        self._items = [item for item in self._original_items if predicate(item)]
        self._selected_index = -1
        self._rebuild_items()

    def reset_filter(self):
        """Reset to show all items (undo filter)."""
        if hasattr(self, '_original_items'):
            self._items = list(self._original_items)
            del self._original_items
            self._selected_index = -1
            self._rebuild_items()
