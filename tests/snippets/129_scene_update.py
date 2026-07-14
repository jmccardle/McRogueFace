# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
# Scene Update - Per-frame update method
import mcrfpy
import math

class GameScene(mcrfpy.Scene):
    def __init__(self):
        super().__init__("game")
        self.time = 0

        self.children.append(mcrfpy.Frame(
            pos=(0, 0), size=(1024, 768),
            fill_color=mcrfpy.Color(30, 30, 40)
        ))

        _caption = mcrfpy.Caption(
            text="Scene.update() - Called Every Frame",
            pos=(320, 50))
        _caption.fill_color = mcrfpy.Color(255, 220, 100)
        self.children.append(_caption)

        # Orbiting object
        self.center = mcrfpy.Frame(
            pos=(462, 334), size=(100, 100),
            fill_color=mcrfpy.Color(100, 100, 150)
        )
        self.children.append(self.center)

        self.orbiter = mcrfpy.Frame(
            pos=(612, 334), size=(50, 50),
            fill_color=mcrfpy.Color(255, 150, 100)
        )
        self.children.append(self.orbiter)

        self.fps_label = mcrfpy.Caption(text="", pos=(450, 700))
        self.children.append(self.fps_label)

    def update(self, dt):
        # Called every frame with delta time
        self.time += dt * 2

        # Orbit around center
        radius = 150
        cx, cy = 512, 384
        self.orbiter.x = cx + math.cos(self.time) * radius - 25
        self.orbiter.y = cy + math.sin(self.time) * radius - 25

        self.fps_label.text = f"dt={dt:.4f}s"

scene = GameScene()
mcrfpy.current_scene = scene
