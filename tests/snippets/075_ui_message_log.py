# mcrf: objects=[Caption,Color,Frame,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# UI Message Log - Scrolling text messages
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

class MessageLog:
    def __init__(self, x, y, width, height, max_messages=8):
        self.max_messages = max_messages
        self.messages = []

        self.container = mcrfpy.Frame(
            pos=(x, y), size=(width, height),
            fill_color=mcrfpy.Color(20, 20, 30),
            outline=2.0, outline_color=mcrfpy.Color(80, 80, 100),
            clip_children=True
        )

    def add_message(self, text, color):
        self.messages.append((text, color))
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        self._refresh()

    def _refresh(self):
        # Clear existing
        while len(self.container.children) > 0:
            self.container.children.remove(self.container.children[0])

        # Add messages
        for i, (text, color) in enumerate(self.messages):
            cap = mcrfpy.Caption(text=text, pos=(10, 10 + i * 25))
            cap.fill_color = color
            self.container.children.append(cap)

log = MessageLog(262, 200, 500, 250)
scene.children.append(log.container)

messages = [
    ("You enter the dungeon.", mcrfpy.Color(200, 200, 200)),
    ("A goblin appears!", mcrfpy.Color(255, 100, 100)),
    ("You attack the goblin.", mcrfpy.Color(255, 200, 100)),
    ("The goblin is defeated!", mcrfpy.Color(100, 255, 100)),
    ("You found gold!", mcrfpy.Color(255, 255, 100)),
    ("You descend deeper...", mcrfpy.Color(150, 150, 255)),
]

msg_idx = 0
def add_msg(timer, runtime):
    global msg_idx
    if msg_idx < len(messages):
        log.add_message(*messages[msg_idx])
        msg_idx += 1

timer = mcrfpy.Timer("msg", add_msg, 1000)

_caption = mcrfpy.Caption(text="Message Log Demo", pos=(420, 100))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)
