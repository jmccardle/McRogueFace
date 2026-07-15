# mcrf: objects=[Caption,Color,Frame,InputState,MouseButton,Scene] verified=0.2.8-dev status=ok
# Draggable Window pattern - a frame that can be dragged by its title bar.
import mcrfpy

scene = mcrfpy.Scene("menu")
ui = scene.children

root = mcrfpy.Frame(pos=(50, 50), size=(300, 400),
                     fill_color=mcrfpy.Color(30, 30, 40))
root.outline_color = mcrfpy.Color(80, 80, 100)
root.outline = 2
ui.append(root)


class DraggableWindow:
    def __init__(self, parent, pos, size, title):
        self.dragging = False
        self.drag_offset = (0, 0)

        self.frame = mcrfpy.Frame(pos=pos, size=size,
                                   fill_color=mcrfpy.Color(45, 45, 55))
        self.frame.outline = 1
        self.frame.outline_color = mcrfpy.Color(100, 100, 120)
        parent.children.append(self.frame)

        # Title bar
        self.title_bar = mcrfpy.Frame(pos=(0, 0), size=(size[0], 24),
                                       fill_color=mcrfpy.Color(60, 60, 80))
        self.frame.children.append(self.title_bar)

        title_label = mcrfpy.Caption(text=title, pos=(8, 4))
        title_label.fill_color = mcrfpy.Color(200, 200, 220)
        self.title_bar.children.append(title_label)

        self.content_y = 28

        # Drag handling
        # on_click: (pos: Vector, button: MouseButton, action: InputState)
        def start_drag(pos, button, action):
            if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
                self.dragging = True
                self.drag_offset = (pos.x - self.frame.x, pos.y - self.frame.y)

        # on_move: (pos: Vector)
        def on_move(pos):
            if self.dragging:
                self.frame.x = pos.x - self.drag_offset[0]
                self.frame.y = pos.y - self.drag_offset[1]

        # on_exit: (pos: Vector)
        def stop_drag(pos):
            self.dragging = False

        self.title_bar.on_click = start_drag
        self.title_bar.on_move = on_move
        self.title_bar.on_exit = stop_drag


# Usage
window = DraggableWindow(root, (20, 20), (250, 300), "Inventory")

# Add content to window.frame.children at y >= window.content_y
item_list = mcrfpy.Caption(text="Items here...", pos=(10, window.content_y + 10))
window.frame.children.append(item_list)

mcrfpy.current_scene = scene
