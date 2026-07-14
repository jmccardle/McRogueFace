# mcrf: objects=[Caption,Color,Easing,Frame,InputState,Key,Scene] verified=0.2.8-dev@a7ba486 status=ok
# UI Health Bar - Animated health display
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

class HealthBar:
    def __init__(self, x, y, width, height, max_health):
        self.max_health = max_health
        self.health = max_health
        self.width = width

        # Background
        self.bg = mcrfpy.Frame(
            pos=(x, y), size=(width, height),
            fill_color=mcrfpy.Color(60, 20, 20),
            outline=2.0, outline_color=mcrfpy.Color(100, 100, 100)
        )

        # Fill bar
        self.fill = mcrfpy.Frame(
            pos=(2, 2), size=(width - 4, height - 4),
            fill_color=mcrfpy.Color(200, 50, 50)
        )
        self.bg.children.append(self.fill)

        # Label
        self.label = mcrfpy.Caption(
            text=f"{max_health}/{max_health}",
            pos=(width // 2 - 30, height // 2 - 10)
        )
        self.bg.children.append(self.label)

    def set_health(self, value):
        self.health = max(0, min(value, self.max_health))
        ratio = self.health / self.max_health
        self.fill.animate("w", (self.width - 4) * ratio, 0.3, mcrfpy.Easing.EASE_OUT)
        self.label.text = f"{self.health}/{self.max_health}"

        # Color based on health
        if ratio > 0.5:
            self.fill.fill_color = mcrfpy.Color(100, 200, 100)
        elif ratio > 0.25:
            self.fill.fill_color = mcrfpy.Color(200, 200, 50)
        else:
            self.fill.fill_color = mcrfpy.Color(200, 50, 50)

hp_bar = HealthBar(312, 300, 400, 40, 100)
scene.children.append(hp_bar.bg)

scene.children.append(mcrfpy.Caption(text="Press 1-5 to set health", pos=(380, 400)))

def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED: return
    if key == mcrfpy.Key.NUM_1: hp_bar.set_health(100)
    elif key == mcrfpy.Key.NUM_2: hp_bar.set_health(75)
    elif key == mcrfpy.Key.NUM_3: hp_bar.set_health(50)
    elif key == mcrfpy.Key.NUM_4: hp_bar.set_health(25)
    elif key == mcrfpy.Key.NUM_5: hp_bar.set_health(0)

scene.on_key = on_key
