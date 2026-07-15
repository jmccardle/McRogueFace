# mcrf: objects=[Caption,Color,Frame,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("game")
mcrfpy.current_scene = scene

# Background
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768))
bg.fill_color = mcrfpy.Color(25, 25, 35)
scene.children.append(bg)

class TooltipManager:
    """Manages tooltips for multiple UI elements."""

    def __init__(self):
        self.elements = {}
        self.tooltip_frame = None
        self.tooltip_text = None
        self.current_element = None
        self.hover_delay = 300
        self.pending_element = None
        self.pending_x = 0
        self.pending_y = 0
        self._create_tooltip()

    def _create_tooltip(self):
        self.tooltip_frame = mcrfpy.Frame(pos=(0, 0), size=(200, 60))
        self.tooltip_frame.fill_color = mcrfpy.Color(30, 30, 45, 245)
        self.tooltip_frame.outline = 1
        self.tooltip_frame.outline_color = mcrfpy.Color(80, 80, 100)
        self.tooltip_frame.visible = False

        self.tooltip_text = mcrfpy.Caption(text="", pos=(0, 0))
        self.tooltip_text.fill_color = mcrfpy.Color(255, 255, 230)
        self.tooltip_text.visible = False

    def register(self, element, text, title=None):
        self.elements[id(element)] = {'element': element, 'text': text, 'title': title}

        def on_enter(pos):
            self.pending_element = element
            self.pending_x, self.pending_y = pos.x, pos.y

            def show_after_delay(timer, runtime):
                if self.pending_element is element:
                    self._show_tooltip(element, self.pending_x, self.pending_y)

            mcrfpy.Timer(f"tooltip_delay_{id(self)}", show_after_delay, self.hover_delay)

        def on_exit(pos):
            if self.pending_element is element:
                self.pending_element = None
            if self.current_element is element:
                self.hide()

        element.on_enter = on_enter
        element.on_exit = on_exit

    def _show_tooltip(self, element, x, y):
        elem_id = id(element)
        if elem_id not in self.elements:
            return
        data = self.elements[elem_id]

        content = (data['title'] + "\n" if data.get('title') else "") + data['text']
        self.tooltip_text.text = content

        lines = content.split('\n')
        max_width = max(len(line) for line in lines) * 8 + 20
        height = len(lines) * 18 + 15
        self.tooltip_frame.w = min(300, max(100, max_width))
        self.tooltip_frame.h = height

        self.tooltip_frame.x = x + 20
        self.tooltip_frame.y = y + 20
        if self.tooltip_frame.x + self.tooltip_frame.w > 1000:
            self.tooltip_frame.x = x - self.tooltip_frame.w - 10
        if self.tooltip_frame.y + self.tooltip_frame.h > 750:
            self.tooltip_frame.y = y - self.tooltip_frame.h - 10

        self.tooltip_text.x = self.tooltip_frame.x + 10
        self.tooltip_text.y = self.tooltip_frame.y + 8

        self.tooltip_frame.visible = True
        self.tooltip_text.visible = True
        self.current_element = element

    def hide(self):
        self.tooltip_frame.visible = False
        self.tooltip_text.visible = False
        self.current_element = None
        self.pending_element = None

    def add_to_scene(self, ui):
        ui.append(self.tooltip_frame)
        ui.append(self.tooltip_text)


# Create inventory slots with tooltips
class InventorySlot:
    def __init__(self, x, y, item_name, item_desc, tooltip_mgr):
        self.frame = mcrfpy.Frame(pos=(x, y), size=(50, 50))
        self.frame.fill_color = mcrfpy.Color(50, 50, 60)
        self.frame.outline = 1
        self.frame.outline_color = mcrfpy.Color(80, 80, 90)

        self.label = mcrfpy.Caption(text=item_name[:3], pos=(x + 10, y + 15))
        self.label.fill_color = mcrfpy.Color(200, 200, 200)

        tooltip_mgr.register(self.frame, item_desc, title=item_name)

    def add_to_scene(self, ui):
        ui.append(self.frame)
        ui.append(self.label)

# Setup tooltip manager
tips = TooltipManager()

# Create inventory
items = [
    ("Health Potion", "Restores 50 HP\nConsumable"),
    ("Mana Crystal", "Restores 30 MP\nConsumable"),
    ("Iron Key", "Opens iron doors\nQuest Item"),
    ("Gold Ring", "Worth 100 gold\nSell to merchant"),
]

slots = []
for i, (name, desc) in enumerate(items):
    slot = InventorySlot(100 + i * 60, 100, name, desc, tips)
    slot.add_to_scene(scene.children)
    slots.append(slot)

# Add tooltip last
tips.add_to_scene(scene.children)
