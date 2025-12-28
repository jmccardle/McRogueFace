#!/usr/bin/env python3
"""Focus System Demo for McRogueFace

Demonstrates a Python-level focus management system using engine primitives.
This shows how game developers can implement keyboard navigation without
requiring C++ engine changes.

Features demonstrated:
- Click-to-focus
- Tab/Shift+Tab cycling
- Visual focus indicators
- Keyboard routing to focused widget
- Modal focus stack
- Three widget types: Grid (WASD), TextInput, MenuIcon

Issue: #143
"""

import mcrfpy
import sys

# =============================================================================
# Modifier Key Tracker (workaround until #160 is implemented)
# =============================================================================

class ModifierTracker:
    """Tracks modifier key state since engine doesn't expose this yet."""

    def __init__(self):
        self.shift = False
        self.ctrl = False
        self.alt = False

    def update(self, key: str, action: str):
        """Call this from your key handler to update modifier state."""
        if key in ("LShift", "RShift"):
            self.shift = (action == "start")
        elif key in ("LControl", "RControl"):
            self.ctrl = (action == "start")
        elif key in ("LAlt", "RAlt"):
            self.alt = (action == "start")


# =============================================================================
# Focus Manager
# =============================================================================

class FocusManager:
    """Central focus coordinator for a scene.

    Manages which widget receives keyboard input, handles tab cycling,
    and maintains a modal stack for popup dialogs.
    """

    # Focus indicator colors
    FOCUS_COLOR = mcrfpy.Color(0, 150, 255)      # Blue
    UNFOCUS_COLOR = mcrfpy.Color(80, 80, 80)     # Dark gray
    FOCUS_OUTLINE = 3.0
    UNFOCUS_OUTLINE = 1.0

    def __init__(self):
        self.widgets = []           # List of (widget, focusable: bool)
        self.focus_index = -1       # Currently focused widget index
        self.modal_stack = []       # Stack of (modal_frame, previous_focus_index)
        self.modifiers = ModifierTracker()

    def register(self, widget, focusable: bool = True):
        """Add a widget to the focus order.

        Args:
            widget: Object implementing on_focus(), on_blur(), handle_key()
            focusable: Whether this widget can receive focus via Tab
        """
        self.widgets.append((widget, focusable))
        # Give widget a reference back to us for click-to-focus
        widget._focus_manager = self
        widget._focus_index = len(self.widgets) - 1

    def focus(self, widget_or_index):
        """Set focus to a specific widget."""
        # Resolve to index
        if isinstance(widget_or_index, int):
            new_index = widget_or_index
        else:
            new_index = next(
                (i for i, (w, _) in enumerate(self.widgets) if w is widget_or_index),
                -1
            )

        if new_index < 0 or new_index >= len(self.widgets):
            return

        # Blur old widget
        if 0 <= self.focus_index < len(self.widgets):
            old_widget, _ = self.widgets[self.focus_index]
            if hasattr(old_widget, 'on_blur'):
                old_widget.on_blur()

        # Focus new widget
        self.focus_index = new_index
        new_widget, _ = self.widgets[new_index]
        if hasattr(new_widget, 'on_focus'):
            new_widget.on_focus()

    def cycle(self, direction: int = 1):
        """Cycle focus to next/previous focusable widget.

        Args:
            direction: 1 for next (Tab), -1 for previous (Shift+Tab)
        """
        if not self.widgets:
            return

        start = self.focus_index if self.focus_index >= 0 else 0
        current = start

        for _ in range(len(self.widgets)):
            current = (current + direction) % len(self.widgets)
            widget, focusable = self.widgets[current]
            if focusable:
                self.focus(current)
                return

        # No focusable widget found, stay where we are

    def push_modal(self, modal_frame, first_focus_widget=None):
        """Push a modal onto the focus stack.

        Args:
            modal_frame: The Frame to show as modal
            first_focus_widget: Widget to focus inside modal (optional)
        """
        # Save current focus
        self.modal_stack.append((modal_frame, self.focus_index))

        # Show modal
        modal_frame.visible = True

        # Focus first widget in modal if specified
        if first_focus_widget is not None:
            self.focus(first_focus_widget)

    def pop_modal(self):
        """Pop the top modal and restore previous focus."""
        if not self.modal_stack:
            return False

        modal_frame, previous_focus = self.modal_stack.pop()
        modal_frame.visible = False

        # Restore focus
        if previous_focus >= 0:
            self.focus(previous_focus)

        return True

    def handle_key(self, key: str, action: str) -> bool:
        """Main key handler - route to focused widget or handle global keys.

        Returns True if key was consumed.
        """
        # Always update modifier state
        self.modifiers.update(key, action)

        # Only process on key press, not release (key repeat sends multiple "start")
        if action != "start":
            return False

        # Global: Escape closes modals
        if key == "Escape":
            if self.pop_modal():
                return True

        # Global: Tab cycles focus
        if key == "Tab":
            direction = -1 if self.modifiers.shift else 1
            self.cycle(direction)
            return True

        # Route to focused widget
        if 0 <= self.focus_index < len(self.widgets):
            widget, _ = self.widgets[self.focus_index]
            if hasattr(widget, 'handle_key'):
                if widget.handle_key(key, action):
                    return True

        return False


# =============================================================================
# Focusable Widgets
# =============================================================================

class FocusableGrid:
    """A grid where WASD keys move a player entity.

    Demonstrates focus on a game-world element.
    """

    def __init__(self, x: float, y: float, grid_w: int, grid_h: int,
                 tile_size: int = 16, zoom: float = 2.0):
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.tile_size = tile_size
        self.zoom = zoom
        self.base_x = x
        self.base_y = y

        # Calculate pixel dimensions
        self.cell_px = tile_size * zoom  # Pixels per cell
        grid_pixel_w = grid_w * self.cell_px
        grid_pixel_h = grid_h * self.cell_px

        # Create the grid background
        self.grid = mcrfpy.Grid(
            pos=(x, y),
            grid_size=(grid_w, grid_h),
            size=(grid_pixel_w, grid_pixel_h)
        )
        self.grid.zoom = zoom
        self.grid.fill_color = mcrfpy.Color(40, 40, 55)

        # Add outline frame for focus indication
        self.outline_frame = mcrfpy.Frame(
            pos=(x - 2, y - 2),
            size=(grid_pixel_w + 4, grid_pixel_h + 4),
            fill_color=mcrfpy.Color(0, 0, 0, 0),
            outline_color=FocusManager.UNFOCUS_COLOR,
            outline=FocusManager.UNFOCUS_OUTLINE
        )

        # Player marker (a bright square overlay)
        self.player_x = grid_w // 2
        self.player_y = grid_h // 2
        marker_size = self.cell_px - 4  # Slightly smaller than cell
        self.player_marker = mcrfpy.Frame(
            pos=(0, 0),  # Will be positioned by _update_player_display
            size=(marker_size, marker_size),
            fill_color=mcrfpy.Color(255, 200, 50),
            outline_color=mcrfpy.Color(255, 150, 0),
            outline=2
        )
        self._update_player_display()

        # Click handler
        self.grid.on_click = self._on_click

        # Focus manager reference (set by FocusManager.register)
        self._focus_manager = None
        self._focus_index = -1

    def _on_click(self, x, y, button, action):
        """Handle click to focus this grid."""
        if self._focus_manager and action == "start":
            self._focus_manager.focus(self._focus_index)

    def _update_player_display(self):
        """Update the visual representation of player position."""
        # Position the player marker
        px = self.base_x + (self.player_x * self.cell_px) + 2
        py = self.base_y + (self.player_y * self.cell_px) + 2
        self.player_marker.x = px
        self.player_marker.y = py

    def on_focus(self):
        """Called when this widget gains focus."""
        self.outline_frame.outline_color = FocusManager.FOCUS_COLOR
        self.outline_frame.outline = FocusManager.FOCUS_OUTLINE

    def on_blur(self):
        """Called when this widget loses focus."""
        self.outline_frame.outline_color = FocusManager.UNFOCUS_COLOR
        self.outline_frame.outline = FocusManager.UNFOCUS_OUTLINE

    def handle_key(self, key: str, action: str) -> bool:
        """Handle WASD movement."""
        moves = {
            "W": (0, -1), "Up": (0, -1),
            "A": (-1, 0), "Left": (-1, 0),
            "S": (0, 1),  "Down": (0, 1),
            "D": (1, 0),  "Right": (1, 0),
        }

        if key in moves:
            dx, dy = moves[key]
            new_x = self.player_x + dx
            new_y = self.player_y + dy

            # Bounds check
            if 0 <= new_x < self.grid_w and 0 <= new_y < self.grid_h:
                self.player_x = new_x
                self.player_y = new_y
                self._update_player_display()
            return True

        return False

    def add_to_scene(self, ui):
        """Add all components to a scene's UI collection."""
        ui.append(self.outline_frame)
        ui.append(self.grid)
        ui.append(self.player_marker)


class TextInputWidget:
    """A text input field with cursor and editing.

    Demonstrates text entry with focus indication.
    """

    def __init__(self, x: float, y: float, width: float, label: str = "",
                 placeholder: str = ""):
        self.x = x
        self.y = y
        self.width = width
        self.height = 28
        self.label_text = label
        self.placeholder_text = placeholder

        # State
        self.text = ""
        self.cursor_pos = 0
        self.focused = False

        # Create UI elements
        self._create_ui()

        # Focus manager reference
        self._focus_manager = None
        self._focus_index = -1

    def _create_ui(self):
        """Create the visual components."""
        # Label above input
        if self.label_text:
            self.label = mcrfpy.Caption(
                text=self.label_text,
                pos=(self.x, self.y - 20)
            )
            self.label.fill_color = mcrfpy.Color(200, 200, 200)

        # Input background
        self.frame = mcrfpy.Frame(
            pos=(self.x, self.y),
            size=(self.width, self.height),
            fill_color=mcrfpy.Color(40, 40, 50),
            outline_color=FocusManager.UNFOCUS_COLOR,
            outline=FocusManager.UNFOCUS_OUTLINE
        )
        self.frame.on_click = self._on_click

        # Placeholder text
        self.placeholder = mcrfpy.Caption(
            text=self.placeholder_text,
            pos=(self.x + 6, self.y + 5)
        )
        self.placeholder.fill_color = mcrfpy.Color(100, 100, 100)

        # Actual text display
        self.display = mcrfpy.Caption(
            text="",
            pos=(self.x + 6, self.y + 5)
        )
        self.display.fill_color = mcrfpy.Color(255, 255, 255)

        # Cursor (thin frame)
        self.cursor = mcrfpy.Frame(
            pos=(self.x + 6, self.y + 4),
            size=(2, self.height - 8),
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        self.cursor.visible = False

    def _on_click(self, x, y, button, action):
        """Handle click to focus."""
        if self._focus_manager and action == "start":
            self._focus_manager.focus(self._focus_index)

    def _update_display(self):
        """Update visual state."""
        self.display.text = self.text
        self.placeholder.visible = (not self.text and not self.focused)
        self._update_cursor()

    def _update_cursor(self):
        """Update cursor position."""
        # Approximate character width (monospace assumption)
        char_width = 10
        self.cursor.x = self.x + 6 + (self.cursor_pos * char_width)

    def on_focus(self):
        """Called when gaining focus."""
        self.focused = True
        self.frame.outline_color = FocusManager.FOCUS_COLOR
        self.frame.outline = FocusManager.FOCUS_OUTLINE
        self.cursor.visible = True
        self._update_display()

    def on_blur(self):
        """Called when losing focus."""
        self.focused = False
        self.frame.outline_color = FocusManager.UNFOCUS_COLOR
        self.frame.outline = FocusManager.UNFOCUS_OUTLINE
        self.cursor.visible = False
        self._update_display()

    def handle_key(self, key: str, action: str) -> bool:
        """Handle text input and editing keys."""
        if not self.focused:
            return False

        old_text = self.text
        handled = True

        if key == "BackSpace":
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
        elif key == "Delete":
            if self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
        elif key == "Left":
            self.cursor_pos = max(0, self.cursor_pos - 1)
        elif key == "Right":
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
        elif key == "Home":
            self.cursor_pos = 0
        elif key == "End":
            self.cursor_pos = len(self.text)
        elif key in ("Return", "Tab"):
            # Don't consume - let focus manager handle
            handled = False
        elif len(key) == 1 and key.isprintable():
            # Insert character
            self.text = self.text[:self.cursor_pos] + key + self.text[self.cursor_pos:]
            self.cursor_pos += 1
        else:
            handled = False

        self._update_display()
        return handled

    def get_text(self) -> str:
        """Get the current text value."""
        return self.text

    def set_text(self, text: str):
        """Set the text value."""
        self.text = text
        self.cursor_pos = len(text)
        self._update_display()

    def add_to_scene(self, ui):
        """Add all components to the scene."""
        if hasattr(self, 'label'):
            ui.append(self.label)
        ui.append(self.frame)
        ui.append(self.placeholder)
        ui.append(self.display)
        ui.append(self.cursor)


class MenuIcon:
    """An icon that opens a modal dialog when activated.

    Demonstrates activation via Space/Enter and modal focus.
    """

    def __init__(self, x: float, y: float, size: float, icon_char: str,
                 tooltip: str, modal_content_builder=None):
        self.x = x
        self.y = y
        self.size = size
        self.tooltip = tooltip
        self.modal_content_builder = modal_content_builder
        self.modal = None

        # Create icon frame
        self.frame = mcrfpy.Frame(
            pos=(x, y),
            size=(size, size),
            fill_color=mcrfpy.Color(60, 60, 80),
            outline_color=FocusManager.UNFOCUS_COLOR,
            outline=FocusManager.UNFOCUS_OUTLINE
        )
        self.frame.on_click = self._on_click

        # Icon character (centered)
        self.icon = mcrfpy.Caption(
            text=icon_char,
            pos=(x + size//3, y + size//6)
        )
        self.icon.fill_color = mcrfpy.Color(200, 200, 220)

        # Tooltip (shown on hover/focus)
        self.tooltip_caption = mcrfpy.Caption(
            text=tooltip,
            pos=(x, y + size + 4)
        )
        self.tooltip_caption.fill_color = mcrfpy.Color(150, 150, 150)
        self.tooltip_caption.visible = False

        # Focus manager reference
        self._focus_manager = None
        self._focus_index = -1

    def _on_click(self, x, y, button, action):
        """Handle click to focus or activate."""
        if not self._focus_manager:
            return

        if action == "start":
            # If already focused, activate; otherwise just focus
            if self._focus_manager.focus_index == self._focus_index:
                self._activate()
            else:
                self._focus_manager.focus(self._focus_index)

    def _activate(self):
        """Open the modal dialog."""
        if self.modal and self._focus_manager:
            self._focus_manager.push_modal(self.modal)

    def on_focus(self):
        """Called when gaining focus."""
        self.frame.outline_color = FocusManager.FOCUS_COLOR
        self.frame.outline = FocusManager.FOCUS_OUTLINE
        self.frame.fill_color = mcrfpy.Color(80, 80, 110)
        self.tooltip_caption.visible = True

    def on_blur(self):
        """Called when losing focus."""
        self.frame.outline_color = FocusManager.UNFOCUS_COLOR
        self.frame.outline = FocusManager.UNFOCUS_OUTLINE
        self.frame.fill_color = mcrfpy.Color(60, 60, 80)
        self.tooltip_caption.visible = False

    def handle_key(self, key: str, action: str) -> bool:
        """Handle activation keys."""
        if key in ("Space", "Return"):
            self._activate()
            return True
        return False

    def set_modal(self, modal_frame):
        """Set the modal frame this icon opens."""
        self.modal = modal_frame

    def add_to_scene(self, ui):
        """Add all components to the scene."""
        ui.append(self.frame)
        ui.append(self.icon)
        ui.append(self.tooltip_caption)


# =============================================================================
# Modal Dialog Builder
# =============================================================================

def create_modal(x: float, y: float, width: float, height: float,
                 title: str) -> mcrfpy.Frame:
    """Create a modal dialog frame."""
    # Semi-transparent backdrop
    # Note: This is simplified - real implementation might want fullscreen backdrop

    # Modal frame
    modal = mcrfpy.Frame(
        pos=(x, y),
        size=(width, height),
        fill_color=mcrfpy.Color(40, 40, 50),
        outline_color=mcrfpy.Color(100, 100, 120),
        outline=2
    )
    modal.visible = False

    # Title
    title_caption = mcrfpy.Caption(
        text=title,
        pos=(x + 10, y + 8)
    )
    title_caption.fill_color = mcrfpy.Color(220, 220, 240)
    modal.children.append(title_caption)

    # Close hint
    close_hint = mcrfpy.Caption(
        text="[Esc to close]",
        pos=(x + width - 100, y + 8)
    )
    close_hint.fill_color = mcrfpy.Color(120, 120, 140)
    modal.children.append(close_hint)

    return modal


# =============================================================================
# Demo Scene Setup
# =============================================================================

def create_demo_scene():
    """Create and populate the focus system demo scene."""

    # Create scene
    mcrfpy.createScene("focus_demo")
    ui = mcrfpy.sceneUI("focus_demo")

    # Background
    bg = mcrfpy.Frame(
        pos=(0, 0),
        size=(1024, 768),
        fill_color=mcrfpy.Color(25, 25, 35)
    )
    ui.append(bg)

    # Title
    title = mcrfpy.Caption(
        text="Focus System Demo",
        pos=(20, 15)
    )
    title.fill_color = mcrfpy.Color(255, 255, 255)
    ui.append(title)

    # Instructions
    instructions = mcrfpy.Caption(
        text="Tab: cycle focus | Shift+Tab: reverse | WASD: move in grid | Space/Enter: activate | Esc: close modal",
        pos=(20, 45)
    )
    instructions.fill_color = mcrfpy.Color(150, 150, 170)
    ui.append(instructions)

    # Create focus manager
    focus_mgr = FocusManager()

    # --- Grid Section ---
    grid_label = mcrfpy.Caption(text="Game Grid (WASD to move)", pos=(50, 90))
    grid_label.fill_color = mcrfpy.Color(180, 180, 200)
    ui.append(grid_label)

    grid_widget = FocusableGrid(50, 115, 10, 8, tile_size=16, zoom=2.0)
    grid_widget.add_to_scene(ui)
    focus_mgr.register(grid_widget)

    # --- Text Inputs Section ---
    input_label = mcrfpy.Caption(text="Text Inputs", pos=(400, 90))
    input_label.fill_color = mcrfpy.Color(180, 180, 200)
    ui.append(input_label)

    name_input = TextInputWidget(400, 130, 250, label="Name:", placeholder="Enter your name")
    name_input.add_to_scene(ui)
    focus_mgr.register(name_input)

    class_input = TextInputWidget(400, 200, 250, label="Class:", placeholder="e.g. Warrior, Mage")
    class_input.add_to_scene(ui)
    focus_mgr.register(class_input)

    notes_input = TextInputWidget(400, 270, 350, label="Notes:", placeholder="Additional notes...")
    notes_input.add_to_scene(ui)
    focus_mgr.register(notes_input)

    # --- Menu Icons Section ---
    icons_label = mcrfpy.Caption(text="Menu Icons", pos=(50, 390))
    icons_label.fill_color = mcrfpy.Color(180, 180, 200)
    ui.append(icons_label)

    # Help icon
    help_icon = MenuIcon(50, 420, 48, "?", "Help")
    help_icon.add_to_scene(ui)
    focus_mgr.register(help_icon)

    help_modal = create_modal(200, 150, 400, 300, "Help")
    ui.append(help_modal)
    help_text = mcrfpy.Caption(
        text="This demo shows focus management.\n\nUse Tab to move between widgets.\nWASD moves the player in the grid.\nType in text fields.\nPress Space on icons to open dialogs.",
        pos=(210, 190)
    )
    help_text.fill_color = mcrfpy.Color(200, 200, 200)
    help_modal.children.append(help_text)
    help_icon.set_modal(help_modal)

    # Settings icon
    settings_icon = MenuIcon(110, 420, 48, "S", "Settings")
    settings_icon.add_to_scene(ui)
    focus_mgr.register(settings_icon)

    settings_modal = create_modal(200, 150, 400, 250, "Settings")
    ui.append(settings_modal)
    settings_text = mcrfpy.Caption(
        text="Settings would go here.\n\n(This is a placeholder modal)",
        pos=(210, 190)
    )
    settings_text.fill_color = mcrfpy.Color(200, 200, 200)
    settings_modal.children.append(settings_text)
    settings_icon.set_modal(settings_modal)

    # Inventory icon
    inv_icon = MenuIcon(170, 420, 48, "I", "Inventory")
    inv_icon.add_to_scene(ui)
    focus_mgr.register(inv_icon)

    inv_modal = create_modal(200, 150, 400, 300, "Inventory")
    ui.append(inv_modal)
    inv_text = mcrfpy.Caption(
        text="Your inventory:\n\n- Sword\n- Shield\n- 3x Potions",
        pos=(210, 190)
    )
    inv_text.fill_color = mcrfpy.Color(200, 200, 200)
    inv_modal.children.append(inv_text)
    inv_icon.set_modal(inv_modal)

    # --- Status Display ---
    status_frame = mcrfpy.Frame(
        pos=(50, 520),
        size=(700, 80),
        fill_color=mcrfpy.Color(35, 35, 45),
        outline_color=mcrfpy.Color(60, 60, 70),
        outline=1
    )
    ui.append(status_frame)

    status_label = mcrfpy.Caption(text="Status", pos=(60, 530))
    status_label.fill_color = mcrfpy.Color(150, 150, 170)
    ui.append(status_label)

    status_text = mcrfpy.Caption(text="Click or Tab to focus a widget", pos=(60, 555))
    status_text.fill_color = mcrfpy.Color(200, 200, 200)
    ui.append(status_text)

    # Store references for status updates
    demo_state = {
        'focus_mgr': focus_mgr,
        'status_text': status_text,
        'grid': grid_widget,
        'inputs': [name_input, class_input, notes_input],
        'icons': [help_icon, settings_icon, inv_icon],
    }

    # Key handler that routes to focus manager
    def on_key(key: str, action: str):
        focus_mgr.handle_key(key, action)

        # Update status display
        if focus_mgr.focus_index >= 0:
            widget, _ = focus_mgr.widgets[focus_mgr.focus_index]
            if widget is grid_widget:
                status_text.text = f"Grid focused - Player at ({grid_widget.player_x}, {grid_widget.player_y})"
            elif widget in demo_state['inputs']:
                idx = demo_state['inputs'].index(widget)
                labels = ["Name", "Class", "Notes"]
                status_text.text = f"{labels[idx]} input focused - Text: '{widget.get_text()}'"
            elif widget in demo_state['icons']:
                status_text.text = f"Icon focused: {widget.tooltip}"
        else:
            status_text.text = "No widget focused"

    # Register key handler using Scene API
    scene = mcrfpy.sceneUI("focus_demo")
    # Note: We use keypressScene for function-based handler since we're not subclassing Scene
    mcrfpy.keypressScene(on_key)

    # Set initial focus
    focus_mgr.focus(0)

    # Activate scene
    mcrfpy.setScene("focus_demo")

    return demo_state


# =============================================================================
# Entry Point
# =============================================================================

def run_demo():
    """Run the focus system demo."""
    print("=== Focus System Demo ===")
    print("Demonstrating Python-level focus management")
    print()
    print("Controls:")
    print("  Tab / Shift+Tab  - Cycle between widgets")
    print("  WASD / Arrows    - Move player in grid (when focused)")
    print("  Type             - Enter text in inputs (when focused)")
    print("  Space / Enter    - Activate icons (when focused)")
    print("  Escape           - Close modal dialogs")
    print("  Click            - Focus clicked widget")
    print()

    demo_state = create_demo_scene()

    # Set up exit timer for headless testing
    def check_exit(dt):
        # In headless mode, exit after a short delay
        # In interactive mode, this won't trigger
        pass

    # mcrfpy.setTimer("demo_check", check_exit, 100)


# Run if executed directly
if __name__ == "__main__":
    import sys
    from mcrfpy import automation

    run_demo()

    # If --screenshot flag, take a screenshot and exit
    if "--screenshot" in sys.argv or len(sys.argv) > 1:
        def take_screenshot(dt):
            automation.screenshot("focus_demo_screenshot.png")
            print("Screenshot saved: focus_demo_screenshot.png")
            sys.exit(0)
        mcrfpy.setTimer("screenshot", take_screenshot, 200)
