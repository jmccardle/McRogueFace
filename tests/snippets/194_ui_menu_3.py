# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy
class Menu:
    """A keyboard-navigable menu widget."""

    def __init__(self, x, y, options, on_select, title=None):
        """
        Create a menu.

        Args:
            x, y: Position on screen
            options: List of option strings
            on_select: Callback function(index, option_text)
            title: Optional title string
        """
        self.x = x
        self.y = y
        self.options = options
        self.on_select = on_select
        self.selected_index = 0

        # Style settings
        self.padding = 15
        self.line_height = 30
        self.width = 250

        # Colors
        self.color_normal = mcrfpy.Color(200, 200, 200)
        self.color_selected = mcrfpy.Color(255, 255, 100)
        self.color_bg = mcrfpy.Color(30, 30, 50, 230)

        # Calculate frame height
        title_offset = self.line_height if title else 0
        height = self.padding * 2 + len(options) * self.line_height + title_offset

        # Create container frame
        self.frame = mcrfpy.Frame(pos=(x, y), size=(self.width, height))
        self.frame.fill_color = self.color_bg
        self.frame.outline = 2
        self.frame.outline_color = mcrfpy.Color(100, 100, 150)

        # Create title if provided
        self.title_caption = None
        if title:
            self.title_caption = mcrfpy.Caption(
                text=title,
                x=x + self.padding,
                y=y + self.padding
            )
            self.title_caption.fill_color = mcrfpy.Color(255, 255, 255)

        # Create option captions
        self.option_captions = []
        for i, option in enumerate(options):
            caption_y = y + self.padding + title_offset + i * self.line_height
            caption = mcrfpy.Caption(
                text=option,
                x=x + self.padding,
                y=caption_y
            )
            caption.fill_color = self.color_normal
            self.option_captions.append(caption)

        # Update visual selection
        self._update_selection()

    def _update_selection(self):
        """Update visual highlight for selected option."""
        for i, caption in enumerate(self.option_captions):
            if i == self.selected_index:
                caption.fill_color = self.color_selected
                caption.text = "> " + self.options[i]
            else:
                caption.fill_color = self.color_normal
                caption.text = "  " + self.options[i]

    def move_up(self):
        """Move selection up (with wraparound)."""
        self.selected_index = (self.selected_index - 1) % len(self.options)
        self._update_selection()

    def move_down(self):
        """Move selection down (with wraparound)."""
        self.selected_index = (self.selected_index + 1) % len(self.options)
        self._update_selection()

    def select(self):
        """Trigger the callback for the current selection."""
        if self.on_select:
            self.on_select(self.selected_index, self.options[self.selected_index])

    def add_to_scene(self, ui):
        """Add menu to scene UI."""
        ui.append(self.frame)
        if self.title_caption:
            ui.append(self.title_caption)
        for caption in self.option_captions:
            ui.append(caption)

    def handle_key(self, key):
        """
        Handle keyboard input.

        Args:
            key: Key name string

        Returns:
            True if key was handled, False otherwise
        """
        if key == mcrfpy.Key.UP or key == mcrfpy.Key.W:
            self.move_up()
            return True
        elif key == mcrfpy.Key.DOWN or key == mcrfpy.Key.S:
            self.move_down()
            return True
        elif key == mcrfpy.Key.ENTER or key == mcrfpy.Key.SPACE:
            self.select()
            return True
        return False


# Setup
scene = mcrfpy.Scene("main_menu")

# Background
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
bg.fill_color = mcrfpy.Color(20, 20, 35)
scene.children.append(bg)

# Title
title = mcrfpy.Caption(text="DUNGEON QUEST", x=350, y=100)
title.fill_color = mcrfpy.Color(255, 200, 50)
scene.children.append(title)

# Menu
def start_game():
    print("Starting game...")

def show_options():
    print("Options...")

menu = Menu(
    362, 250,
    ["New Game", "Continue", "Options", "Quit"],
    lambda i, opt: {
        0: start_game,
        1: lambda: print("Continue..."),
        2: show_options,
        3: mcrfpy.exit
    }.get(i, lambda: None)(),
    title="Main Menu"
)
menu.add_to_scene(scene.children)

# Input
def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return
    menu.handle_key(key)

scene.on_key = on_key
scene.activate()
