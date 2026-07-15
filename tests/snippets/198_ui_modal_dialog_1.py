# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy

class ModalDialog:
    """A centered modal dialog with customizable buttons."""

    def __init__(self, title, message, buttons, on_close=None):
        """
        Create a modal dialog.

        Args:
            title: Dialog title
            message: Main message text
            buttons: List of button labels (e.g., ["OK", "Cancel"])
            on_close: Callback function(button_index, button_label)
        """
        self.title = title
        self.message = message
        self.buttons = buttons
        self.on_close = on_close
        self.visible = False
        self.elements = []

        # Calculate dimensions
        self.dialog_width = 400
        self.dialog_height = 180
        self.button_width = 100
        self.button_height = 35

        self._create_elements()

    def _create_elements(self):
        """Create all UI elements for the dialog."""
        # Full-screen overlay
        self.overlay = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
        self.overlay.fill_color = mcrfpy.Color(0, 0, 0, 150)
        self.overlay.visible = False

        # Prevent clicks from passing through overlay
        self.overlay.on_click = lambda pos, b, a: None

        # Center the dialog
        dialog_x = (1024 - self.dialog_width) // 2
        dialog_y = (768 - self.dialog_height) // 2

        # Dialog frame
        self.dialog = mcrfpy.Frame(
            pos=(dialog_x, dialog_y),
            size=(self.dialog_width, self.dialog_height)
        )
        self.dialog.fill_color = mcrfpy.Color(45, 45, 60)
        self.dialog.outline = 2
        self.dialog.outline_color = mcrfpy.Color(100, 100, 130)
        self.dialog.visible = False

        # Title
        self.title_caption = mcrfpy.Caption(
            text=self.title,
            x=dialog_x + 20,
            y=dialog_y + 15
        )
        self.title_caption.fill_color = mcrfpy.Color(255, 220, 100)
        self.title_caption.visible = False

        # Message
        self.message_caption = mcrfpy.Caption(
            text=self.message,
            x=dialog_x + 20,
            y=dialog_y + 50
        )
        self.message_caption.fill_color = mcrfpy.Color(220, 220, 220)
        self.message_caption.visible = False

        # Buttons
        self.button_frames = []
        self.button_labels = []

        total_button_width = len(self.buttons) * self.button_width + (len(self.buttons) - 1) * 15
        start_x = dialog_x + (self.dialog_width - total_button_width) // 2
        button_y = dialog_y + self.dialog_height - self.button_height - 20

        for i, label in enumerate(self.buttons):
            btn_x = start_x + i * (self.button_width + 15)

            btn_frame = mcrfpy.Frame(pos=(btn_x, button_y), size=(self.button_width, self.button_height))
            btn_frame.fill_color = mcrfpy.Color(70, 70, 90)
            btn_frame.outline = 1
            btn_frame.outline_color = mcrfpy.Color(100, 100, 120)
            btn_frame.visible = False

            # Click handler
            def make_handler(index, text):
                def handler(pos, button, action):
                    if action == mcrfpy.InputState.PRESSED:
                        self._on_button_click(index, text)
                return handler

            btn_frame.on_click = make_handler(i, label)
            self.button_frames.append(btn_frame)

            # Button label (centered)
            label_x = btn_x + (self.button_width - len(label) * 8) // 2
            label_y = button_y + (self.button_height - 16) // 2

            btn_label = mcrfpy.Caption(text=label, x=label_x, y=label_y)
            btn_label.fill_color = mcrfpy.Color(255, 255, 255)
            btn_label.visible = False
            self.button_labels.append(btn_label)

        # Track all elements
        self.elements = [
            self.overlay, self.dialog,
            self.title_caption, self.message_caption
        ]
        self.elements.extend(self.button_frames)
        self.elements.extend(self.button_labels)

    def _on_button_click(self, index, label):
        """Handle button click."""
        self.hide()
        if self.on_close:
            self.on_close(index, label)

    def show(self):
        """Show the dialog."""
        for elem in self.elements:
            elem.visible = True
        self.visible = True

    def hide(self):
        """Hide the dialog."""
        for elem in self.elements:
            elem.visible = False
        self.visible = False

    def add_to_scene(self, ui):
        """Add dialog to scene (call once during setup)."""
        for elem in self.elements:
            ui.append(elem)


# Usage Example
scene = mcrfpy.Scene("modal_demo")

# Background content
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
bg.fill_color = mcrfpy.Color(30, 30, 45)
scene.children.append(bg)

label = mcrfpy.Caption(text="Press SPACE to show dialog", x=350, y=350)
label.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(label)

# Create dialog
def on_dialog_close(index, label):
    print(f"Dialog closed with: {label} (index {index})")
    if label == "Yes":
        print("User confirmed!")
    else:
        print("User cancelled.")

dialog = ModalDialog(
    "Confirm Action",
    "Are you sure you want to proceed?",
    ["Yes", "No"],
    on_dialog_close
)
dialog.add_to_scene(scene.children)

# Show dialog on keypress
def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return
    if key == mcrfpy.Key.SPACE and not dialog.visible:
        dialog.show()
    elif key == mcrfpy.Key.ESCAPE and dialog.visible:
        dialog.hide()

scene.on_key = on_key
scene.activate()
