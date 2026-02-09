import mcrfpy

scene = mcrfpy.Scene("gui")
mcrfpy.current_scene = scene

tick_id = 0

class Draggable(mcrfpy.Frame):
    """a frame GUI that can be dragged around the screen"""
    def __init__(self, pos=(0, 0), size=(400, 150)):
        global tick_id
        super().__init__(pos, size, fill_color = (64, 64, 255), outline=2, opacity=0.9)

        # close button
        close_btn = mcrfpy.Frame((size[0]-32-5, 5), (32, 32), children=[mcrfpy.Caption((8, 0), text="X", font=mcrfpy.default_font, font_size=24)])
        self.children.append(close_btn)
        close_btn.on_click = self.close

        # minimize button
        self.minimize_btn = mcrfpy.Frame((size[0]-74, 5), (32, 32), children=[mcrfpy.Caption((8, 0), text="-", font=mcrfpy.default_font, font_size=24)])
        self.children.append(self.minimize_btn)
        self.minimize_btn.on_click = self.minmax
        self.minimized = False

        # grab / title bar
        grab_bar = mcrfpy.Frame((5,5), (size[0]-84, 32), fill_color=(32, 32, 128))
        grab_bar.on_click = self.toggle_move
        self.dragging = False
        self.drag_start_pos = None
        self.children.append(grab_bar)

        # stopwatch
        self.tick = mcrfpy.Timer(f"tick{tick_id}", self.tick, 1000, start=True)
        tick_id += 1
        self.clock = mcrfpy.Caption((50, 42), font=mcrfpy.default_font, text="00:00", font_size=48)
        self.time = 0
        self.children.append(self.clock)

    def close(self, *args):
        self.parent = None
        self.tick.stop()

    def minmax(self, pos, btn, event):
        if event != "start": return
        self.minimized = not self.minimized
        self.minimize_btn.children[0].text = "+" if self.minimized else "-"
        self.clock.visible = not self.minimized
        self.h = 40 if self.minimized else 150

    def toggle_move(self, *args):
        if not self.dragging and args[-1] == "start":
            self.dragging = True
            self.drag_start_pos = args[0]
            self.on_move = self.update_pos
        else:
            self.dragging = False
            self.on_move = None

    def update_pos(self, *args):
        cursor_pos = args[0]
        self.pos += (cursor_pos - self.drag_start_pos)
        self.drag_start_pos = cursor_pos

    def tick(self, *args):
        self.time += 1
        self.clock.text = f"{str(self.time//60).zfill(2)}:{str(self.time%60).zfill(2)}"

def spawn(*args):
    if args[-1] != "start": return
    scene.children.append(Draggable((50, 100)))

add_btn = mcrfpy.Frame((5, 5), (32, 32), fill_color = (64, 12, 12), children=[mcrfpy.Caption((8, 0), text="+", font=mcrfpy.default_font, font_size=24)])
add_btn.on_click = spawn
add_btn.parent = scene
