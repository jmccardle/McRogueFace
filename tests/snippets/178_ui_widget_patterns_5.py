# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene] verified=0.2.8-dev status=ok
# Modal Dialog pattern - a dialog that captures all input until dismissed.
import mcrfpy

scene = mcrfpy.Scene("menu")
ui = scene.children

root = mcrfpy.Frame(pos=(50, 50), size=(300, 400),
                     fill_color=mcrfpy.Color(30, 30, 40))
root.outline_color = mcrfpy.Color(80, 80, 100)
root.outline = 2
ui.append(root)


class ModalDialog:
    def __init__(self, scene, message, on_dismiss=None):
        self.scene = scene
        self.on_dismiss = on_dismiss
        ui = scene.children

        # Semi-transparent backdrop
        self.backdrop = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                                      fill_color=mcrfpy.Color(0, 0, 0, 160))
        self.backdrop.z_index = 900
        self.backdrop.on_click = lambda pos, btn, action: None  # Block clicks
        ui.append(self.backdrop)

        # Dialog box
        self.dialog = mcrfpy.Frame(pos=(312, 284), size=(400, 200),
                                    fill_color=mcrfpy.Color(50, 50, 65))
        self.dialog.outline_color = mcrfpy.Color(120, 120, 150)
        self.dialog.outline = 2
        self.dialog.z_index = 901
        ui.append(self.dialog)

        # Message
        msg = mcrfpy.Caption(text=message, pos=(20, 20))
        msg.fill_color = mcrfpy.Color(220, 220, 220)
        self.dialog.children.append(msg)

        # OK button
        ok_btn = mcrfpy.Frame(pos=(150, 140), size=(100, 36),
                               fill_color=mcrfpy.Color(70, 100, 70))
        ok_btn.outline = 1
        ok_btn.outline_color = mcrfpy.Color(100, 150, 100)
        ok_btn.on_click = lambda pos, btn, action: self.close()
        self.dialog.children.append(ok_btn)

        ok_label = mcrfpy.Caption(text="OK", pos=(35, 8))
        ok_label.fill_color = mcrfpy.Color(220, 255, 220)
        ok_btn.children.append(ok_label)

        # Capture keyboard
        self._prev_handler = scene.on_key

        def modal_keys(key, action):
            if action == mcrfpy.InputState.PRESSED:
                if key == mcrfpy.Key.ENTER or key == mcrfpy.Key.ESCAPE:
                    self.close()
        scene.on_key = modal_keys

    def close(self):
        ui = self.scene.children
        ui.remove(self.backdrop)
        ui.remove(self.dialog)
        if self._prev_handler:
            self.scene.on_key = self._prev_handler
        if self.on_dismiss:
            self.on_dismiss()


# Usage
dialog = ModalDialog(scene, "Game saved successfully!")

mcrfpy.current_scene = scene
