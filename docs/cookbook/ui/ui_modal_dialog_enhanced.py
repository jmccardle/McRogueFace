"""McRogueFace - Modal Dialog Widget (enhanced)

Documentation: https://mcrogueface.github.io/cookbook/ui_modal_dialog
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/ui/ui_modal_dialog_enhanced.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

class DialogManager:
    """Manages a queue of dialogs."""

    def __init__(self, ui):
        self.ui = ui
        self.queue = []
        self.current = None

    def show(self, title, message, buttons=None, style=None, callback=None):
        """
        Queue a dialog to show.

        If no dialog is active, shows immediately.
        Otherwise, queues for later.
        """
        dialog_data = {
            'title': title,
            'message': message,
            'buttons': buttons or ["OK"],
            'style': style or DialogStyle.INFO,
            'callback': callback
        }

        if self.current is None:
            self._show_dialog(dialog_data)
        else:
            self.queue.append(dialog_data)

    def _show_dialog(self, data):
        """Actually display a dialog."""
        def on_close(index, label):
            if data['callback']:
                data['callback'](index, label)
            self._on_dialog_closed()

        self.current = EnhancedDialog(
            data['title'],
            data['message'],
            data['buttons'],
            data['style'],
            on_close
        )
        self.current.add_to_scene(self.ui)
        self.current.show()

    def _on_dialog_closed(self):
        """Handle dialog close, show next if queued."""
        self.current = None

        if self.queue:
            next_dialog = self.queue.pop(0)
            self._show_dialog(next_dialog)

    def handle_key(self, key):
        """Forward key events to current dialog."""
        if self.current:
            return self.current.handle_key(key)
        return False


# Usage
manager = DialogManager(ui)

# Queue multiple dialogs
manager.show("First", "This is the first message")
manager.show("Second", "This appears after closing the first")
manager.show("Third", "And this is last", ["Done"])