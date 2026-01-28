# McRogueFace Cookbook - Grid Container Widget
"""
NxM clickable cells for inventory/slot systems.

Example:
    from lib.grid_container import GridContainer

    def on_cell_click(x, y, item):
        print(f"Clicked cell ({x}, {y}): {item}")

    inventory = GridContainer(
        pos=(100, 100),
        cell_size=(48, 48),
        grid_dims=(5, 4),  # 5 columns, 4 rows
        on_cell_click=on_cell_click
    )
    scene.children.append(inventory.frame)

    # Set cell contents
    inventory.set_cell(0, 0, sprite_index=10, count=5)
"""
import mcrfpy


class GridContainer:
    """NxM clickable cells for inventory/slot systems.

    Args:
        pos: (x, y) position tuple
        cell_size: (width, height) of each cell
        grid_dims: (columns, rows) grid dimensions
        on_cell_click: Callback(x, y, item_data) when cell is clicked
        on_cell_hover: Callback(x, y, item_data) when cell is hovered
        texture: Optional texture for sprites
        empty_color: Background color for empty cells
        filled_color: Background color for cells with items
        selected_color: Background color for selected cell
        hover_color: Background color when hovered
        cell_outline: Cell border thickness
        cell_spacing: Space between cells

    Attributes:
        frame: The outer frame (add this to scene)
        selected: (x, y) of selected cell or None
    """

    DEFAULT_EMPTY = mcrfpy.Color(40, 40, 45)
    DEFAULT_FILLED = mcrfpy.Color(50, 50, 60)
    DEFAULT_SELECTED = mcrfpy.Color(80, 100, 140)
    DEFAULT_HOVER = mcrfpy.Color(60, 60, 75)
    DEFAULT_OUTLINE = mcrfpy.Color(70, 70, 80)

    def __init__(self, pos, cell_size, grid_dims, on_cell_click=None,
                 on_cell_hover=None, texture=None,
                 empty_color=None, filled_color=None,
                 selected_color=None, hover_color=None,
                 cell_outline=1, cell_spacing=2):
        self.pos = pos
        self.cell_size = cell_size
        self.grid_dims = grid_dims  # (cols, rows)
        self.on_cell_click = on_cell_click
        self.on_cell_hover = on_cell_hover
        self.texture = texture
        self.cell_outline = cell_outline
        self.cell_spacing = cell_spacing

        # Colors
        self.empty_color = empty_color or self.DEFAULT_EMPTY
        self.filled_color = filled_color or self.DEFAULT_FILLED
        self.selected_color = selected_color or self.DEFAULT_SELECTED
        self.hover_color = hover_color or self.DEFAULT_HOVER
        self.outline_color = self.DEFAULT_OUTLINE

        # State
        self._selected = None
        self._hovered = None
        self._cells = {}  # (x, y) -> cell data
        self._cell_frames = {}  # (x, y) -> frame

        # Calculate total size
        cols, rows = grid_dims
        total_width = cols * cell_size[0] + (cols - 1) * cell_spacing
        total_height = rows * cell_size[1] + (rows - 1) * cell_spacing

        # Create outer frame
        self.frame = mcrfpy.Frame(
            pos=pos,
            size=(total_width, total_height),
            fill_color=mcrfpy.Color(0, 0, 0, 0),  # Transparent
            outline=0
        )

        # Create cell frames
        self._create_cells()

    def _create_cells(self):
        """Create all cell frames."""
        cols, rows = self.grid_dims
        cw, ch = self.cell_size

        for row in range(rows):
            for col in range(cols):
                x = col * (cw + self.cell_spacing)
                y = row * (ch + self.cell_spacing)

                cell_frame = mcrfpy.Frame(
                    pos=(x, y),
                    size=self.cell_size,
                    fill_color=self.empty_color,
                    outline_color=self.outline_color,
                    outline=self.cell_outline
                )

                # Set up event handlers
                def make_click(cx, cy):
                    def handler(pos, button, action):
                        if button == "left" and action == "end":
                            self._on_cell_clicked(cx, cy)
                    return handler

                def make_enter(cx, cy):
                    def handler(pos, button, action):
                        self._on_cell_enter(cx, cy)
                    return handler

                def make_exit(cx, cy):
                    def handler(pos, button, action):
                        self._on_cell_exit(cx, cy)
                    return handler

                cell_frame.on_click = make_click(col, row)
                cell_frame.on_enter = make_enter(col, row)
                cell_frame.on_exit = make_exit(col, row)

                self._cell_frames[(col, row)] = cell_frame
                self.frame.children.append(cell_frame)

    def _on_cell_clicked(self, x, y):
        """Handle cell click."""
        old_selected = self._selected
        self._selected = (x, y)

        # Update display
        if old_selected:
            self._update_cell_display(*old_selected)
        self._update_cell_display(x, y)

        # Fire callback
        if self.on_cell_click:
            item = self._cells.get((x, y))
            self.on_cell_click(x, y, item)

    def _on_cell_enter(self, x, y):
        """Handle cell hover enter."""
        self._hovered = (x, y)
        self._update_cell_display(x, y)

        if self.on_cell_hover:
            item = self._cells.get((x, y))
            self.on_cell_hover(x, y, item)

    def _on_cell_exit(self, x, y):
        """Handle cell hover exit."""
        if self._hovered == (x, y):
            self._hovered = None
            self._update_cell_display(x, y)

    def _update_cell_display(self, x, y):
        """Update visual state of a cell."""
        if (x, y) not in self._cell_frames:
            return

        frame = self._cell_frames[(x, y)]
        has_item = (x, y) in self._cells

        if (x, y) == self._selected:
            frame.fill_color = self.selected_color
        elif (x, y) == self._hovered:
            frame.fill_color = self.hover_color
        elif has_item:
            frame.fill_color = self.filled_color
        else:
            frame.fill_color = self.empty_color

    @property
    def selected(self):
        """Currently selected cell (x, y) or None."""
        return self._selected

    @selected.setter
    def selected(self, value):
        """Set selected cell."""
        old = self._selected
        self._selected = value
        if old:
            self._update_cell_display(*old)
        if value:
            self._update_cell_display(*value)

    def get_selected_item(self):
        """Get the item in the selected cell."""
        if self._selected:
            return self._cells.get(self._selected)
        return None

    def set_cell(self, x, y, sprite_index=None, count=None, data=None):
        """Set cell contents.

        Args:
            x, y: Cell coordinates
            sprite_index: Index in texture for sprite display
            count: Stack count to display
            data: Arbitrary data to associate with cell
        """
        if (x, y) not in self._cell_frames:
            return

        cell_frame = self._cell_frames[(x, y)]

        # Store cell data
        self._cells[(x, y)] = {
            'sprite_index': sprite_index,
            'count': count,
            'data': data
        }

        # Clear existing children except the frame itself
        while len(cell_frame.children) > 0:
            cell_frame.children.pop()

        # Add sprite if we have texture and sprite_index
        if self.texture and sprite_index is not None:
            sprite = mcrfpy.Sprite(
                pos=(2, 2),
                texture=self.texture,
                sprite_index=sprite_index
            )
            # Scale sprite to fit cell (with padding)
            # Note: sprite scaling depends on texture cell size
            cell_frame.children.append(sprite)

        # Add count label if count > 1
        if count is not None and count > 1:
            count_label = mcrfpy.Caption(
                text=str(count),
                pos=(self.cell_size[0] - 8, self.cell_size[1] - 12),
                fill_color=mcrfpy.Color(255, 255, 255),
                font_size=10
            )
            count_label.outline = 1
            count_label.outline_color = mcrfpy.Color(0, 0, 0)
            cell_frame.children.append(count_label)

        self._update_cell_display(x, y)

    def get_cell(self, x, y):
        """Get cell data.

        Args:
            x, y: Cell coordinates

        Returns:
            Cell data dict or None if empty
        """
        return self._cells.get((x, y))

    def clear_cell(self, x, y):
        """Clear a cell's contents.

        Args:
            x, y: Cell coordinates
        """
        if (x, y) in self._cells:
            del self._cells[(x, y)]

        if (x, y) in self._cell_frames:
            cell_frame = self._cell_frames[(x, y)]
            while len(cell_frame.children) > 0:
                cell_frame.children.pop()

        self._update_cell_display(x, y)

    def clear_all(self):
        """Clear all cells."""
        for key in list(self._cells.keys()):
            self.clear_cell(*key)
        self._selected = None

    def find_empty_cell(self):
        """Find the first empty cell.

        Returns:
            (x, y) of empty cell or None if all full
        """
        cols, rows = self.grid_dims
        for row in range(rows):
            for col in range(cols):
                if (col, row) not in self._cells:
                    return (col, row)
        return None

    def is_full(self):
        """Check if all cells are filled."""
        return len(self._cells) >= self.grid_dims[0] * self.grid_dims[1]

    def swap_cells(self, x1, y1, x2, y2):
        """Swap contents of two cells.

        Args:
            x1, y1: First cell
            x2, y2: Second cell
        """
        cell1 = self._cells.get((x1, y1))
        cell2 = self._cells.get((x2, y2))

        if cell1:
            self.set_cell(x2, y2, **cell1)
        else:
            self.clear_cell(x2, y2)

        if cell2:
            self.set_cell(x1, y1, **cell2)
        else:
            self.clear_cell(x1, y1)

    def move_cell(self, from_x, from_y, to_x, to_y):
        """Move cell contents to another cell.

        Args:
            from_x, from_y: Source cell
            to_x, to_y: Destination cell

        Returns:
            True if successful, False if destination not empty
        """
        if (to_x, to_y) in self._cells:
            return False

        cell = self._cells.get((from_x, from_y))
        if cell:
            self.set_cell(to_x, to_y, **cell)
            self.clear_cell(from_x, from_y)
            return True
        return False
