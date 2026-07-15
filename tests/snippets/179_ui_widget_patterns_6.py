# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene] verified=0.2.8-dev status=ok
# Hotbar / Quick Slots pattern - number keys (1-9) mapped to inventory slots.
import mcrfpy

scene = mcrfpy.Scene("menu")
ui = scene.children

root = mcrfpy.Frame(pos=(50, 50), size=(300, 400),
                     fill_color=mcrfpy.Color(30, 30, 40))
root.outline_color = mcrfpy.Color(80, 80, 100)
root.outline = 2
ui.append(root)


class Hotbar:
    def __init__(self, parent, pos, slot_count=9):
        self.slots = []
        self.items = [None] * slot_count
        self.selected = 0

        self.frame = mcrfpy.Frame(pos=pos,
                                   size=(slot_count * 36 + 8, 44),
                                   fill_color=mcrfpy.Color(30, 30, 40, 200))
        parent.children.append(self.frame)

        for i in range(slot_count):
            slot = mcrfpy.Frame(pos=(4 + i * 36, 4), size=(32, 32),
                                 fill_color=mcrfpy.Color(50, 50, 60))
            slot.outline = 1
            slot.outline_color = mcrfpy.Color(80, 80, 100)
            self.frame.children.append(slot)
            self.slots.append(slot)

            num = mcrfpy.Caption(text=str((i + 1) % 10), pos=(2, 2))
            num.fill_color = mcrfpy.Color(100, 100, 120)
            slot.children.append(num)

        self._update_selection()

    def _update_selection(self):
        for i, slot in enumerate(self.slots):
            if i == self.selected:
                slot.outline_color = mcrfpy.Color(200, 180, 80)
                slot.outline = 2
            else:
                slot.outline_color = mcrfpy.Color(80, 80, 100)
                slot.outline = 1

    def select(self, index):
        if 0 <= index < len(self.slots):
            self.selected = index
            self._update_selection()


# Usage
hotbar = Hotbar(root, (20, 340))

# Key mapping for number keys
num_keys = {
    mcrfpy.Key.NUM_1: 0, mcrfpy.Key.NUM_2: 1, mcrfpy.Key.NUM_3: 2,
    mcrfpy.Key.NUM_4: 3, mcrfpy.Key.NUM_5: 4, mcrfpy.Key.NUM_6: 5,
    mcrfpy.Key.NUM_7: 6, mcrfpy.Key.NUM_8: 7, mcrfpy.Key.NUM_9: 8,
}


def handle_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    if key in num_keys:
        hotbar.select(num_keys[key])


scene.on_key = handle_key

mcrfpy.current_scene = scene
