# mcrf: objects=[Grid,InputState,MouseButton,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("mousebutton_grid_demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(400, 400))
scene.children.append(grid)


def select_at(x, y):
    print(f"select at ({x}, {y})")


def move_to(x, y):
    print(f"move to ({x}, {y})")


def start_pan(x, y):
    print(f"pan from ({x}, {y})")


def go_back():
    print("back")


def go_forward():
    print("forward")


def on_cell_click(cell_pos, button, action):
    if action == mcrfpy.InputState.PRESSED:
        if button == mcrfpy.MouseButton.LEFT:
            select_at(cell_pos.x, cell_pos.y)
        elif button == mcrfpy.MouseButton.RIGHT:
            move_to(cell_pos.x, cell_pos.y)
        elif button == mcrfpy.MouseButton.MIDDLE:
            start_pan(cell_pos.x, cell_pos.y)
        elif button == mcrfpy.MouseButton.X1:
            go_back()
        elif button == mcrfpy.MouseButton.X2:
            go_forward()


grid.on_cell_click = on_cell_click
