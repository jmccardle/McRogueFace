# McRogueFace Cookbook - Toast Notification Widget
"""
Auto-dismissing notification popups.

Example:
    from lib.toast import ToastManager

    # Create manager (once per scene)
    toasts = ToastManager(scene)

    # Show notifications
    toasts.show("Game saved!")
    toasts.show("Level up!", duration=5000, color=mcrfpy.Color(100, 200, 100))
"""
import mcrfpy


class Toast:
    """Single toast notification.

    Internal class - use ToastManager to create toasts.
    """

    DEFAULT_BG = mcrfpy.Color(50, 50, 60, 240)
    DEFAULT_TEXT = mcrfpy.Color(255, 255, 255)

    def __init__(self, message, y_position, width=300,
                 bg_color=None, text_color=None, duration=3000):
        self.message = message
        self.duration = duration
        self.y_position = y_position
        self.width = width
        self._dismissed = False

        # Colors
        self.bg_color = bg_color or self.DEFAULT_BG
        self.text_color = text_color or self.DEFAULT_TEXT

        # Create toast frame (starts off-screen to the right)
        self.frame = mcrfpy.Frame(
            pos=(1024 + 10, y_position),  # Start off-screen
            size=(width, 40),
            fill_color=self.bg_color,
            outline_color=mcrfpy.Color(100, 100, 120),
            outline=1
        )

        # Create message caption
        self.caption = mcrfpy.Caption(
            text=message,
            pos=(15, 10),
            fill_color=self.text_color,
            font_size=14
        )
        self.frame.children.append(self.caption)

    def slide_in(self, target_x):
        """Animate sliding in from the right."""
        self.frame.animate("x", target_x, 0.3, mcrfpy.Easing.EASE_OUT)

    def slide_out(self, callback=None):
        """Animate sliding out to the right."""
        self._dismissed = True
        self.frame.animate("x", 1024 + 10, 0.3, mcrfpy.Easing.EASE_IN)
        if callback:
            mcrfpy.Timer(f"toast_dismiss_{id(self)}", lambda rt: callback(), 350)

    def move_up(self, new_y):
        """Animate moving to a new Y position."""
        self.y_position = new_y
        self.frame.animate("y", new_y, 0.2, mcrfpy.Easing.EASE_OUT)

    @property
    def is_dismissed(self):
        """Whether this toast has been dismissed."""
        return self._dismissed


class ToastManager:
    """Manages auto-dismissing notification popups.

    Args:
        scene: Scene to add toasts to
        position: Anchor position ("top-right", "bottom-right", "top-left", "bottom-left")
        max_toasts: Maximum visible toasts (default: 5)
        toast_width: Width of toast notifications
        toast_spacing: Vertical spacing between toasts
        margin: Margin from screen edge

    Attributes:
        scene: The scene toasts are added to
        toasts: List of active toast objects
    """

    def __init__(self, scene, position="top-right", max_toasts=5,
                 toast_width=300, toast_spacing=10, margin=20):
        self.scene = scene
        self.position = position
        self.max_toasts = max_toasts
        self.toast_width = toast_width
        self.toast_spacing = toast_spacing
        self.margin = margin
        self.toasts = []

        # Calculate anchor position
        self._calculate_anchor()

    def _calculate_anchor(self):
        """Calculate the anchor point based on position setting."""
        # Assuming 1024x768 screen
        if "right" in self.position:
            self._anchor_x = 1024 - self.toast_width - self.margin
        else:
            self._anchor_x = self.margin

        if "top" in self.position:
            self._anchor_y = self.margin
            self._direction = 1  # Stack downward
        else:
            self._anchor_y = 768 - 40 - self.margin  # 40 = toast height
            self._direction = -1  # Stack upward

    def _get_toast_y(self, index):
        """Get Y position for toast at given index."""
        return self._anchor_y + index * (40 + self.toast_spacing) * self._direction

    def show(self, message, duration=3000, color=None):
        """Show a toast notification.

        Args:
            message: Text to display
            duration: Time in ms before auto-dismiss (0 = never)
            color: Optional background color

        Returns:
            Toast object
        """
        # Create new toast
        y_pos = self._get_toast_y(len(self.toasts))
        toast = Toast(
            message=message,
            y_position=y_pos,
            width=self.toast_width,
            bg_color=color,
            duration=duration
        )

        # Add to scene
        self.scene.children.append(toast.frame)
        self.toasts.append(toast)

        # Animate in
        toast.slide_in(self._anchor_x)

        # Schedule auto-dismiss
        if duration > 0:
            timer_name = f"toast_auto_{id(toast)}"
            mcrfpy.Timer(timer_name, lambda rt: self.dismiss(toast), duration)

        # Remove oldest if over limit
        while len(self.toasts) > self.max_toasts:
            self.dismiss(self.toasts[0])

        return toast

    def dismiss(self, toast):
        """Dismiss a specific toast.

        Args:
            toast: Toast object to dismiss
        """
        if toast not in self.toasts or toast.is_dismissed:
            return

        index = self.toasts.index(toast)

        def on_dismissed():
            # Remove from scene and list
            if toast in self.toasts:
                self.toasts.remove(toast)
                # Try to remove from scene
                try:
                    for i in range(len(self.scene.children)):
                        if self.scene.children[i] is toast.frame:
                            self.scene.children.pop()
                            break
                except Exception:
                    pass

            # Move remaining toasts up
            self._reposition_toasts()

        toast.slide_out(callback=on_dismissed)

    def _reposition_toasts(self):
        """Reposition all remaining toasts after one is removed."""
        for i, toast in enumerate(self.toasts):
            if not toast.is_dismissed:
                new_y = self._get_toast_y(i)
                toast.move_up(new_y)

    def dismiss_all(self):
        """Dismiss all active toasts."""
        for toast in list(self.toasts):
            self.dismiss(toast)

    def show_success(self, message, duration=3000):
        """Show a success toast (green)."""
        return self.show(message, duration, mcrfpy.Color(40, 120, 60, 240))

    def show_error(self, message, duration=5000):
        """Show an error toast (red)."""
        return self.show(message, duration, mcrfpy.Color(150, 50, 50, 240))

    def show_warning(self, message, duration=4000):
        """Show a warning toast (yellow)."""
        return self.show(message, duration, mcrfpy.Color(180, 150, 40, 240))

    def show_info(self, message, duration=3000):
        """Show an info toast (blue)."""
        return self.show(message, duration, mcrfpy.Color(50, 100, 150, 240))
