# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene] verified=0.2.8-dev status=ok
# Vertical Menu pattern - a list of selectable options with keyboard navigation.
import mcrfpy

scene = mcrfpy.Scene("menu")
ui = scene.children

root = mcrfpy.Frame(pos=(50, 50), size=(300, 400),
                     fill_color=mcrfpy.Color(30, 30, 40))
root.outline_color = mcrfpy.Color(80, 80, 100)
root.outline = 2
ui.append(root)


class VerticalMenu:
    def __init__(self, parent, pos, options, on_select):
        """
        options: list of (label, value) tuples
        on_select: callback(value) when option chosen
        """
        self.options = options
        self.on_select = on_select
        self.selected = 0

        self.frame = mcrfpy.Frame(pos=pos,
                                   size=(180, len(options) * 28 + 8),
                                   fill_color=mcrfpy.Color(35, 35, 45))
        parent.children.append(self.frame)

        self.items = []
        for i, (label, value) in enumerate(options):
            item = mcrfpy.Caption(text=label, pos=(12, 4 + i * 28))
            item.fill_color = mcrfpy.Color(180, 180, 180)
            self.frame.children.append(item)
            self.items.append(item)

        self._update_highlight()

    def _update_highlight(self):
        for i, item in enumerate(self.items):
            if i == self.selected:
                item.fill_color = mcrfpy.Color(255, 220, 100)
            else:
                item.fill_color = mcrfpy.Color(180, 180, 180)

    def move_up(self):
        self.selected = (self.selected - 1) % len(self.options)
        self._update_highlight()

    def move_down(self):
        self.selected = (self.selected + 1) % len(self.options)
        self._update_highlight()

    def confirm(self):
        _, value = self.options[self.selected]
        self.on_select(value)


def handle_menu_choice(value):
    print(f"chose: {value}")


# Usage
menu = VerticalMenu(root, (20, 20), [
    ("Continue", "continue"),
    ("New Game", "new"),
    ("Options", "options"),
    ("Quit", "quit")
], on_select=handle_menu_choice)


# Keyboard navigation via scene.on_key
def handle_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    if key == mcrfpy.Key.UP:
        menu.move_up()
    elif key == mcrfpy.Key.DOWN:
        menu.move_down()
    elif key == mcrfpy.Key.ENTER:
        menu.confirm()


scene.on_key = handle_key

mcrfpy.current_scene = scene
