# McRogueFace Cookbook - Modal Widget
"""
Overlay popup that blocks background input.

Example:
    from lib.modal import Modal

    def on_confirm():
        print("Confirmed!")
        modal.hide()

    modal = Modal(
        title="Confirm Action",
        message="Are you sure you want to proceed?",
        buttons=[
            ("Cancel", modal.hide),
            ("Confirm", on_confirm)
        ]
    )
    modal.show(scene)
"""
import mcrfpy


class Modal:
    """Overlay popup that blocks background input.

    Args:
        title: Modal title text
        message: Modal body message (optional)
        content_frame: Custom content frame (overrides message)
        buttons: List of (label, callback) tuples
        width: Modal width (default: 400)
        height: Modal height (default: auto-calculated)
        overlay_color: Semi-transparent overlay color
        bg_color: Modal background color
        title_color: Title text color
        message_color: Message text color
        button_spacing: Space between buttons

    Attributes:
        overlay: The overlay frame (add to scene to show)
        modal_frame: The modal content frame
        visible: Whether modal is currently visible
    """

    DEFAULT_OVERLAY = mcrfpy.Color(0, 0, 0, 180)
    DEFAULT_BG = mcrfpy.Color(40, 40, 50)
    DEFAULT_TITLE_COLOR = mcrfpy.Color(255, 255, 255)
    DEFAULT_MESSAGE_COLOR = mcrfpy.Color(200, 200, 200)
    DEFAULT_BUTTON_BG = mcrfpy.Color(60, 60, 75)
    DEFAULT_BUTTON_HOVER = mcrfpy.Color(80, 80, 100)

    def __init__(self, title, message=None, content_frame=None,
                 buttons=None, width=400, height=None,
                 overlay_color=None, bg_color=None,
                 title_color=None, message_color=None,
                 button_spacing=10):
        self.title = title
        self.message = message
        self.width = width
        self.button_spacing = button_spacing
        self._on_close = None

        # Colors
        self.overlay_color = overlay_color or self.DEFAULT_OVERLAY
        self.bg_color = bg_color or self.DEFAULT_BG
        self.title_color = title_color or self.DEFAULT_TITLE_COLOR
        self.message_color = message_color or self.DEFAULT_MESSAGE_COLOR

        # State
        self.visible = False
        self._scene = None
        self._buttons = buttons or []

        # Calculate height if not specified
        if height is None:
            height = 60  # Title
            if message:
                # Rough estimate of message height
                lines = len(message) // 40 + message.count('\n') + 1
                height += lines * 20 + 20
            if content_frame:
                height += 150  # Default content height
            if buttons:
                height += 50  # Button row
            height = max(150, height)

        self.height = height

        # Create overlay (fullscreen semi-transparent)
        self.overlay = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 768),  # Will be adjusted on show
            fill_color=self.overlay_color,
            outline=0
        )

        # Block clicks on overlay from reaching elements behind
        self.overlay.on_click = self._on_overlay_click

        # Create modal frame (centered)
        modal_x = (1024 - width) // 2
        modal_y = (768 - height) // 2

        self.modal_frame = mcrfpy.Frame(
            pos=(modal_x, modal_y),
            size=(width, height),
            fill_color=self.bg_color,
            outline_color=mcrfpy.Color(100, 100, 120),
            outline=2
        )
        self.overlay.children.append(self.modal_frame)

        # Add title
        self._title_caption = mcrfpy.Caption(
            text=title,
            pos=(width // 2, 15),
            fill_color=self.title_color,
            font_size=18
        )
        self._title_caption.outline = 1
        self._title_caption.outline_color = mcrfpy.Color(0, 0, 0)
        self.modal_frame.children.append(self._title_caption)

        # Add separator
        sep = mcrfpy.Frame(
            pos=(20, 45),
            size=(width - 40, 2),
            fill_color=mcrfpy.Color(80, 80, 100),
            outline=0
        )
        self.modal_frame.children.append(sep)

        # Content area starts at y=55
        content_y = 55

        # Add message if provided
        if message and not content_frame:
            self._message_caption = mcrfpy.Caption(
                text=message,
                pos=(20, content_y),
                fill_color=self.message_color,
                font_size=14
            )
            self.modal_frame.children.append(self._message_caption)
        elif content_frame:
            content_frame.x = 20
            content_frame.y = content_y
            self.modal_frame.children.append(content_frame)

        # Add buttons at bottom
        if buttons:
            self._create_buttons(buttons)

    def _create_buttons(self, buttons):
        """Create button row at bottom of modal."""
        button_width = 100
        button_height = 35
        total_width = len(buttons) * button_width + (len(buttons) - 1) * self.button_spacing
        start_x = (self.width - total_width) // 2
        button_y = self.height - button_height - 15

        self._button_frames = []
        for i, (label, callback) in enumerate(buttons):
            x = start_x + i * (button_width + self.button_spacing)

            btn_frame = mcrfpy.Frame(
                pos=(x, button_y),
                size=(button_width, button_height),
                fill_color=self.DEFAULT_BUTTON_BG,
                outline_color=mcrfpy.Color(120, 120, 140),
                outline=1
            )

            btn_label = mcrfpy.Caption(
                text=label,
                pos=(button_width // 2, (button_height - 14) // 2),
                fill_color=mcrfpy.Color(220, 220, 220),
                font_size=14
            )
            btn_frame.children.append(btn_label)

            # Hover effect
            def make_enter(frame):
                def handler(pos, button, action):
                    frame.fill_color = self.DEFAULT_BUTTON_HOVER
                return handler

            def make_exit(frame):
                def handler(pos, button, action):
                    frame.fill_color = self.DEFAULT_BUTTON_BG
                return handler

            def make_click(cb):
                def handler(pos, button, action):
                    if button == "left" and action == "end" and cb:
                        cb()
                return handler

            btn_frame.on_enter = make_enter(btn_frame)
            btn_frame.on_exit = make_exit(btn_frame)
            btn_frame.on_click = make_click(callback)

            self._button_frames.append(btn_frame)
            self.modal_frame.children.append(btn_frame)

    def _on_overlay_click(self, pos, button, action):
        """Handle clicks on overlay (outside modal)."""
        # Check if click is outside modal
        if button == "left" and action == "end":
            mx, my = self.modal_frame.x, self.modal_frame.y
            mw, mh = self.modal_frame.w, self.modal_frame.h
            px, py = pos.x, pos.y

            if not (mx <= px <= mx + mw and my <= py <= my + mh):
                # Click outside modal - close if allowed
                if self._on_close:
                    self._on_close()

    @property
    def on_close(self):
        """Callback when modal is closed by clicking outside."""
        return self._on_close

    @on_close.setter
    def on_close(self, callback):
        """Set close callback."""
        self._on_close = callback

    def show(self, scene=None):
        """Show the modal.

        Args:
            scene: Scene to add modal to (uses stored scene if not provided)
        """
        if scene:
            self._scene = scene

        if self._scene and not self.visible:
            # Adjust overlay size to match scene
            # Note: Assumes 1024x768 for now
            self._scene.children.append(self.overlay)
            self.visible = True

    def hide(self):
        """Hide the modal."""
        if self._scene and self.visible:
            # Remove overlay from scene
            try:
                # Find and remove overlay
                for i in range(len(self._scene.children)):
                    if self._scene.children[i] is self.overlay:
                        self._scene.children.pop()
                        break
            except Exception:
                pass
            self.visible = False

    def set_message(self, message):
        """Update the modal message."""
        self.message = message
        if hasattr(self, '_message_caption'):
            self._message_caption.text = message

    def set_title(self, title):
        """Update the modal title."""
        self.title = title
        self._title_caption.text = title


class ConfirmModal(Modal):
    """Pre-configured confirmation modal with Yes/No buttons.

    Args:
        title: Modal title
        message: Confirmation message
        on_confirm: Callback when confirmed
        on_cancel: Callback when cancelled (optional)
        confirm_text: Text for confirm button (default: "Confirm")
        cancel_text: Text for cancel button (default: "Cancel")
    """

    def __init__(self, title, message, on_confirm, on_cancel=None,
                 confirm_text="Confirm", cancel_text="Cancel", **kwargs):
        self._confirm_callback = on_confirm
        self._cancel_callback = on_cancel

        buttons = [
            (cancel_text, self._on_cancel),
            (confirm_text, self._on_confirm)
        ]

        super().__init__(title, message=message, buttons=buttons, **kwargs)

    def _on_confirm(self):
        """Handle confirm button."""
        self.hide()
        if self._confirm_callback:
            self._confirm_callback()

    def _on_cancel(self):
        """Handle cancel button."""
        self.hide()
        if self._cancel_callback:
            self._cancel_callback()


class AlertModal(Modal):
    """Pre-configured alert modal with single OK button.

    Args:
        title: Modal title
        message: Alert message
        on_dismiss: Callback when dismissed (optional)
        button_text: Text for button (default: "OK")
    """

    def __init__(self, title, message, on_dismiss=None,
                 button_text="OK", **kwargs):
        self._dismiss_callback = on_dismiss

        buttons = [(button_text, self._on_dismiss)]

        super().__init__(title, message=message, buttons=buttons,
                        width=kwargs.pop('width', 350), **kwargs)

    def _on_dismiss(self):
        """Handle dismiss button."""
        self.hide()
        if self._dismiss_callback:
            self._dismiss_callback()
