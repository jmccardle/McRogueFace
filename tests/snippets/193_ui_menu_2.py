# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy

class EnhancedMenu:
    """Menu with descriptions, submenus, and visual polish."""

    def __init__(self, x, y, options, title=None):
        """
        Create an enhanced menu.

        Args:
            x, y: Position
            options: List of dicts with keys:
                     'label': Display text
                     'action': Callback function (optional)
                     'description': Help text (optional)
                     'submenu': EnhancedMenu instance (optional)
                     'enabled': Boolean (optional, default True)
        """
        self.x = x
        self.y = y
        self.options = options
        self.title = title
        self.selected_index = 0
        self.active = True
        self.parent_menu = None

        # Layout
        self.padding = 20
        self.line_height = 32
        self.width = 300

        # Colors
        self.colors = {
            'bg': mcrfpy.Color(25, 25, 40, 240),
            'border': mcrfpy.Color(80, 80, 120),
            'title': mcrfpy.Color(255, 220, 100),
            'normal': mcrfpy.Color(180, 180, 180),
            'selected': mcrfpy.Color(255, 255, 255),
            'disabled': mcrfpy.Color(80, 80, 80),
            'description': mcrfpy.Color(150, 150, 180),
            'highlight_bg': mcrfpy.Color(60, 60, 100),
        }

        self._build_ui()

    def _build_ui(self):
        """Construct UI elements."""
        title_offset = self.line_height + 10 if self.title else 0
        desc_height = 50  # Space for description
        height = (
            self.padding * 2 +
            len(self.options) * self.line_height +
            title_offset +
            desc_height
        )

        # Main frame
        self.frame = mcrfpy.Frame(pos=(self.x, self.y), size=(self.width, height))
        self.frame.fill_color = self.colors['bg']
        self.frame.outline = 2
        self.frame.outline_color = self.colors['border']

        # Title
        self.title_caption = None
        if self.title:
            self.title_caption = mcrfpy.Caption(
                text=self.title,
                x=self.x + self.padding,
                y=self.y + self.padding
            )
            self.title_caption.fill_color = self.colors['title']

        # Selection highlight frame
        self.highlight = mcrfpy.Frame(
            pos=(self.x + 5, self.y + self.padding + title_offset),
            size=(self.width - 10, self.line_height)
        )
        self.highlight.fill_color = self.colors['highlight_bg']
        self.highlight.outline = 0

        # Option labels
        self.option_captions = []
        for i, opt in enumerate(self.options):
            caption_y = self.y + self.padding + title_offset + i * self.line_height + 5
            caption = mcrfpy.Caption(
                text=opt.get('label', '???'),
                x=self.x + self.padding + 10,
                y=caption_y
            )
            enabled = opt.get('enabled', True)
            caption.fill_color = self.colors['normal'] if enabled else self.colors['disabled']
            self.option_captions.append(caption)

            # Add arrow for submenus
            if opt.get('submenu'):
                arrow = mcrfpy.Caption(
                    text=">",
                    x=self.x + self.width - self.padding - 15,
                    y=caption_y
                )
                arrow.fill_color = caption.fill_color
                opt['_arrow'] = arrow

        # Description text at bottom
        desc_y = self.y + height - desc_height + 5
        self.description = mcrfpy.Caption(
            text="",
            x=self.x + self.padding,
            y=desc_y
        )
        self.description.fill_color = self.colors['description']

        self._update_selection()

    def _update_selection(self):
        """Update visuals for current selection."""
        title_offset = self.line_height + 10 if self.title else 0

        # Move highlight
        self.highlight.y = self.y + self.padding + title_offset + self.selected_index * self.line_height

        # Update caption colors
        for i, caption in enumerate(self.option_captions):
            opt = self.options[i]
            enabled = opt.get('enabled', True)

            if i == self.selected_index:
                caption.fill_color = self.colors['selected'] if enabled else self.colors['disabled']
            else:
                caption.fill_color = self.colors['normal'] if enabled else self.colors['disabled']

        # Update description
        desc = self.options[self.selected_index].get('description', '')
        self.description.text = desc

    def move_up(self):
        """Move selection up, skipping disabled options."""
        if not self.active:
            return

        start = self.selected_index
        while True:
            self.selected_index = (self.selected_index - 1) % len(self.options)
            if self.options[self.selected_index].get('enabled', True):
                break
            if self.selected_index == start:
                break  # All disabled, stay put
        self._update_selection()

    def move_down(self):
        """Move selection down, skipping disabled options."""
        if not self.active:
            return

        start = self.selected_index
        while True:
            self.selected_index = (self.selected_index + 1) % len(self.options)
            if self.options[self.selected_index].get('enabled', True):
                break
            if self.selected_index == start:
                break
        self._update_selection()

    def select(self):
        """Execute the selected option."""
        if not self.active:
            return None

        opt = self.options[self.selected_index]

        if not opt.get('enabled', True):
            return None

        if opt.get('submenu'):
            return opt['submenu']

        if opt.get('action'):
            opt['action']()

        return None

    def back(self):
        """Return to parent menu."""
        return self.parent_menu

    def add_to_scene(self, ui):
        """Add all elements to scene."""
        ui.append(self.frame)
        ui.append(self.highlight)
        if self.title_caption:
            ui.append(self.title_caption)
        for i, caption in enumerate(self.option_captions):
            ui.append(caption)
            if '_arrow' in self.options[i]:
                ui.append(self.options[i]['_arrow'])
        ui.append(self.description)

    def remove_from_scene(self, ui):
        """Remove all elements from scene."""
        elements = [self.frame, self.highlight, self.description]
        if self.title_caption:
            elements.append(self.title_caption)
        elements.extend(self.option_captions)
        for i, opt in enumerate(self.options):
            if '_arrow' in opt:
                elements.append(opt['_arrow'])

        for elem in elements:
            try:
                ui.remove(elem)
            except:
                pass


# Usage with submenus
scene = mcrfpy.Scene("menu")

# Create options submenu
options_menu = EnhancedMenu(350, 220, [
    {'label': 'Sound Volume', 'description': 'Adjust sound effects volume'},
    {'label': 'Music Volume', 'description': 'Adjust background music volume'},
    {'label': 'Fullscreen', 'description': 'Toggle fullscreen mode'},
    {'label': 'Back', 'action': lambda: switch_menu(main_menu)},
])
options_menu.title = "Options"

# Create main menu
main_menu = EnhancedMenu(300, 200, [
    {
        'label': 'New Game',
        'description': 'Start a new adventure',
        'action': lambda: print("Starting new game...")
    },
    {
        'label': 'Continue',
        'description': 'Load your saved game',
        'enabled': False,  # Disabled if no save exists
    },
    {
        'label': 'Options',
        'description': 'Configure game settings',
        'submenu': options_menu
    },
    {
        'label': 'Quit',
        'description': 'Exit the game',
        'action': lambda: mcrfpy.exit()
    },
])
main_menu.title = "My Game"

options_menu.parent_menu = main_menu
current_menu = main_menu
main_menu.add_to_scene(scene.children)

def switch_menu(new_menu):
    global current_menu
    current_menu.remove_from_scene(scene.children)
    current_menu = new_menu
    current_menu.add_to_scene(scene.children)

def handle_keys(key, state):
    global current_menu
    if state != mcrfpy.InputState.PRESSED:
        return

    if key == mcrfpy.Key.UP or key == mcrfpy.Key.W:
        current_menu.move_up()
    elif key == mcrfpy.Key.DOWN or key == mcrfpy.Key.S:
        current_menu.move_down()
    elif key == mcrfpy.Key.ENTER or key == mcrfpy.Key.SPACE:
        result = current_menu.select()
        if result:  # Submenu returned
            switch_menu(result)
    elif key == mcrfpy.Key.ESCAPE:
        parent = current_menu.back()
        if parent:
            switch_menu(parent)

scene.on_key = handle_keys
scene.activate()
