# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy

class DialogStyle:
    """Predefined dialog styles."""
    INFO = {
        'bg': mcrfpy.Color(45, 55, 75),
        'border': mcrfpy.Color(80, 120, 180),
        'title': mcrfpy.Color(150, 200, 255),
        'btn_bg': mcrfpy.Color(60, 90, 130),
    }
    WARNING = {
        'bg': mcrfpy.Color(75, 65, 45),
        'border': mcrfpy.Color(180, 150, 80),
        'title': mcrfpy.Color(255, 220, 100),
        'btn_bg': mcrfpy.Color(130, 110, 60),
    }
    ERROR = {
        'bg': mcrfpy.Color(75, 45, 45),
        'border': mcrfpy.Color(180, 80, 80),
        'title': mcrfpy.Color(255, 150, 150),
        'btn_bg': mcrfpy.Color(130, 60, 60),
    }
    SUCCESS = {
        'bg': mcrfpy.Color(45, 75, 55),
        'border': mcrfpy.Color(80, 180, 100),
        'title': mcrfpy.Color(150, 255, 180),
        'btn_bg': mcrfpy.Color(60, 130, 80),
    }


class EnhancedDialog:
    """Modal dialog with styles, keyboard navigation, and animations."""

    def __init__(self, title, message, buttons=None, style=None, on_close=None):
        """
        Create an enhanced dialog.

        Args:
            title: Dialog title
            message: Main message (can include newlines)
            buttons: Button labels (default ["OK"])
            style: DialogStyle dict (default INFO)
            on_close: Callback(button_index, button_label)
        """
        self.title = title
        self.message = message
        self.buttons = buttons or ["OK"]
        self.style = style or DialogStyle.INFO
        self.on_close = on_close
        self.visible = False
        self.selected_button = 0

        self.dialog_width = 450
        self.dialog_height = 200

        # Adjust height for multiline messages
        lines = message.count('\n') + 1
        self.dialog_height = 150 + lines * 20

        self._create_elements()

    def _create_elements(self):
        """Build dialog UI."""
        # Overlay
        self.overlay = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
        self.overlay.fill_color = mcrfpy.Color(0, 0, 0, 180)
        self.overlay.visible = False
        self.overlay.on_click = lambda pos, b, a: None

        # Dialog
        dx = (1024 - self.dialog_width) // 2
        dy = (768 - self.dialog_height) // 2

        self.dialog = mcrfpy.Frame(pos=(dx, dy), size=(self.dialog_width, self.dialog_height))
        self.dialog.fill_color = self.style['bg']
        self.dialog.outline = 3
        self.dialog.outline_color = self.style['border']
        self.dialog.visible = False

        # Title bar
        self.title_bar = mcrfpy.Frame(pos=(dx + 2, dy + 2), size=(self.dialog_width - 4, 35))
        self.title_bar.fill_color = mcrfpy.Color(
            self.style['border'].r,
            self.style['border'].g,
            self.style['border'].b,
            50
        )
        self.title_bar.outline = 0
        self.title_bar.visible = False

        # Title text
        self.title_caption = mcrfpy.Caption(
            text=self.title,
            x=dx + 15,
            y=dy + 10
        )
        self.title_caption.fill_color = self.style['title']
        self.title_caption.visible = False

        # Message
        self.message_caption = mcrfpy.Caption(
            text=self.message,
            x=dx + 20,
            y=dy + 50
        )
        self.message_caption.fill_color = mcrfpy.Color(230, 230, 230)
        self.message_caption.visible = False

        # Buttons
        self.button_frames = []
        self.button_labels = []

        btn_width = 110
        btn_height = 38
        total_width = len(self.buttons) * btn_width + (len(self.buttons) - 1) * 15
        start_x = dx + (self.dialog_width - total_width) // 2
        btn_y = dy + self.dialog_height - btn_height - 20

        for i, label in enumerate(self.buttons):
            bx = start_x + i * (btn_width + 15)

            btn = mcrfpy.Frame(pos=(bx, btn_y), size=(btn_width, btn_height))
            btn.fill_color = self.style['btn_bg']
            btn.outline = 2
            btn.outline_color = mcrfpy.Color(150, 150, 170)
            btn.visible = False

            def make_handler(idx, txt):
                def handler(pos, button, action):
                    if action == mcrfpy.InputState.PRESSED:
                        self._select_button(idx, txt)
                return handler

            btn.on_click = make_handler(i, label)
            self.button_frames.append(btn)

            # Center label
            lx = bx + (btn_width - len(label) * 8) // 2
            ly = btn_y + (btn_height - 16) // 2

            lbl = mcrfpy.Caption(text=label, x=lx, y=ly)
            lbl.fill_color = mcrfpy.Color(255, 255, 255)
            lbl.visible = False
            self.button_labels.append(lbl)

        self._update_button_highlight()

    def _update_button_highlight(self):
        """Update button visual states."""
        for i, btn in enumerate(self.button_frames):
            if i == self.selected_button:
                btn.outline = 2
                btn.outline_color = mcrfpy.Color(255, 255, 100)
                btn.fill_color = mcrfpy.Color(
                    min(255, self.style['btn_bg'].r + 30),
                    min(255, self.style['btn_bg'].g + 30),
                    min(255, self.style['btn_bg'].b + 30)
                )
            else:
                btn.outline = 1
                btn.outline_color = mcrfpy.Color(100, 100, 120)
                btn.fill_color = self.style['btn_bg']

    def _select_button(self, index, label):
        """Handle button selection."""
        self.hide()
        if self.on_close:
            self.on_close(index, label)

    def navigate_left(self):
        """Move selection left."""
        if not self.visible:
            return
        self.selected_button = (self.selected_button - 1) % len(self.buttons)
        self._update_button_highlight()

    def navigate_right(self):
        """Move selection right."""
        if not self.visible:
            return
        self.selected_button = (self.selected_button + 1) % len(self.buttons)
        self._update_button_highlight()

    def confirm(self):
        """Activate selected button."""
        if not self.visible:
            return
        self._select_button(self.selected_button, self.buttons[self.selected_button])

    def show(self):
        """Show the dialog."""
        self.selected_button = 0
        self._update_button_highlight()

        elements = [
            self.overlay, self.dialog, self.title_bar,
            self.title_caption, self.message_caption
        ] + self.button_frames + self.button_labels

        for elem in elements:
            elem.visible = True

        self.visible = True

    def hide(self):
        """Hide the dialog."""
        elements = [
            self.overlay, self.dialog, self.title_bar,
            self.title_caption, self.message_caption
        ] + self.button_frames + self.button_labels

        for elem in elements:
            elem.visible = False

        self.visible = False

    def add_to_scene(self, ui):
        """Add to scene UI."""
        elements = [
            self.overlay, self.dialog, self.title_bar,
            self.title_caption, self.message_caption
        ] + self.button_frames + self.button_labels

        for elem in elements:
            ui.append(elem)

    def handle_key(self, key):
        """Handle keyboard input. Returns True if handled."""
        if not self.visible:
            return False

        if key == mcrfpy.Key.LEFT or key == mcrfpy.Key.A:
            self.navigate_left()
            return True
        elif key == mcrfpy.Key.RIGHT or key == mcrfpy.Key.D:
            self.navigate_right()
            return True
        elif key == mcrfpy.Key.ENTER or key == mcrfpy.Key.SPACE:
            self.confirm()
            return True
        elif key == mcrfpy.Key.ESCAPE:
            # Close with last button (usually Cancel)
            self._select_button(len(self.buttons) - 1, self.buttons[-1])
            return True

        return False


# Usage with different styles
scene = mcrfpy.Scene("styled_dialogs")

bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
bg.fill_color = mcrfpy.Color(35, 35, 45)
scene.children.append(bg)

# Current dialog reference
current_dialog = None

def show_info():
    global current_dialog
    current_dialog = EnhancedDialog(
        "Information",
        "This is an informational message.\nPress OK to continue.",
        ["OK"],
        DialogStyle.INFO
    )
    current_dialog.add_to_scene(scene.children)
    current_dialog.show()

def show_warning():
    global current_dialog
    current_dialog = EnhancedDialog(
        "Warning",
        "You are about to delete this item.\nThis action cannot be undone.",
        ["Delete", "Cancel"],
        DialogStyle.WARNING,
        lambda i, l: print(f"Warning response: {l}")
    )
    current_dialog.add_to_scene(scene.children)
    current_dialog.show()

def show_error():
    global current_dialog
    current_dialog = EnhancedDialog(
        "Error",
        "Failed to save the file.\nPlease check disk space.",
        ["Retry", "Cancel"],
        DialogStyle.ERROR
    )
    current_dialog.add_to_scene(scene.children)
    current_dialog.show()

def show_success():
    global current_dialog
    current_dialog = EnhancedDialog(
        "Success!",
        "Your progress has been saved.",
        ["Continue"],
        DialogStyle.SUCCESS
    )
    current_dialog.add_to_scene(scene.children)
    current_dialog.show()

# Help text
help_text = mcrfpy.Caption(
    text="Press: 1=Info  2=Warning  3=Error  4=Success",
    x=280, y=700
)
help_text.fill_color = mcrfpy.Color(150, 150, 150)
scene.children.append(help_text)

def on_key(key, state):
    global current_dialog
    if state != mcrfpy.InputState.PRESSED:
        return

    # Let dialog handle input first
    if current_dialog and current_dialog.handle_key(key):
        return

    if key == mcrfpy.Key.NUM_1:
        show_info()
    elif key == mcrfpy.Key.NUM_2:
        show_warning()
    elif key == mcrfpy.Key.NUM_3:
        show_error()
    elif key == mcrfpy.Key.NUM_4:
        show_success()

scene.on_key = on_key
scene.activate()
