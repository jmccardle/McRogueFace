# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.3.6-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("hud_patterns")

# region: hud
def create_hud(scene):
    ui = scene.children

    hud = mcrfpy.Frame(pos=(0, 0), size=(800, 60),
                        fill_color=mcrfpy.Color(30, 30, 30, 200))
    hud.z_index = 100
    ui.append(hud)

    health_label = mcrfpy.Caption(text="HP: 100/100", pos=(10, 10))
    health_label.font_size = 18
    health_label.fill_color = mcrfpy.Color(255, 255, 255)
    hud.children.append(health_label)

    return health_label

def update_hud(health_label, current_hp, max_hp):
    health_label.text = f"HP: {current_hp}/{max_hp}"

    if current_hp < max_hp * 0.3:
        health_label.fill_color = mcrfpy.Color(255, 0, 0)    # Red
    elif current_hp < max_hp * 0.6:
        health_label.fill_color = mcrfpy.Color(255, 255, 0)  # Yellow
    else:
        health_label.fill_color = mcrfpy.Color(0, 255, 0)    # Green
# endregion

health_label = create_hud(scene)
update_hud(health_label, 25, 100)

def create_explosion(scene, x, y):
    """Create explosion effect using animated frames."""
    import random
    ui = scene.children
    particles = []

    for i in range(10):
        p = mcrfpy.Frame(pos=(x, y), size=(4, 4),
                          fill_color=mcrfpy.Color(255, 200, 50))
        p.z_index = 50

        target_x = x + random.randint(-50, 50)
        target_y = y + random.randint(-50, 50)

        p.animate("x", float(target_x), 0.5, mcrfpy.Easing.EASE_OUT_QUAD)
        p.animate("y", float(target_y), 0.5, mcrfpy.Easing.EASE_OUT_QUAD)
        p.animate("opacity", 0.0, 0.5, mcrfpy.Easing.LINEAR)

        particles.append(p)
        ui.append(p)

    # Cleanup after animation
    # Timer callbacks receive (timer, runtime_ms), not just runtime
    def cleanup(timer, runtime):
        for p in particles:
            ui.remove(p)
    timer = mcrfpy.Timer("explosion_cleanup", cleanup, 600)

create_explosion(scene, 400, 300)

# region: health-bar
class HealthBar:
    def __init__(self, parent, pos, width, height, max_hp):
        self.max_hp = max_hp
        self.width = width

        # Background (red)
        self.bg = mcrfpy.Frame(pos=pos, size=(width, height),
                                fill_color=mcrfpy.Color(255, 0, 0))
        self.bg.z_index = 90
        parent.children.append(self.bg)

        # Foreground (green)
        self.fg = mcrfpy.Frame(pos=pos, size=(width, height),
                                fill_color=mcrfpy.Color(0, 255, 0))
        self.fg.z_index = 91
        parent.children.append(self.fg)

    def set_hp(self, current):
        current = max(0, min(current, self.max_hp))
        ratio = current / self.max_hp
        target_width = int(self.width * ratio)

        self.fg.animate("w", float(target_width), 0.2,
                         mcrfpy.Easing.EASE_OUT_QUAD)

        if ratio < 0.3:
            self.fg.fill_color = mcrfpy.Color(255, 0, 0)
        elif ratio < 0.6:
            self.fg.fill_color = mcrfpy.Color(255, 255, 0)
# endregion

bar = HealthBar(scene, (300, 150), 200, 20, 100)
bar.set_hp(40)

mcrfpy.current_scene = scene
