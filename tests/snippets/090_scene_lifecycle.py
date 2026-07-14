# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene] verified=0.2.8-dev status=ok
# Scene Lifecycle - on_enter/on_exit callbacks
import mcrfpy

# Create scenes with lifecycle callbacks
class MenuScene(mcrfpy.Scene):
    def __init__(self):
        super().__init__("menu")
        self.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(50, 50, 80)))
        self.status = mcrfpy.Caption(text="Menu Scene", pos=(420, 300))
        self.status.fill_color = mcrfpy.Color(255, 220, 100)
        self.children.append(self.status)
        self.children.append(mcrfpy.Caption(text="Press SPACE for game", pos=(380, 400)))
        self.on_key = self.handle_key

    def on_enter(self):
        self.status.text = "Menu Scene (entered!)"

    def on_exit(self):
        print("Leaving menu scene")

    def handle_key(self, key, action):
        if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
            game_scene.activate()

class GameScene(mcrfpy.Scene):
    def __init__(self):
        super().__init__("game")
        self.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(80, 50, 50)))
        self.status = mcrfpy.Caption(text="Game Scene", pos=(420, 300))
        self.status.fill_color = mcrfpy.Color(100, 255, 100)
        self.children.append(self.status)
        self.children.append(mcrfpy.Caption(text="Press SPACE for menu", pos=(380, 400)))
        self.on_key = self.handle_key

    def on_enter(self):
        self.status.text = "Game Scene (entered!)"

    def handle_key(self, key, action):
        if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
            menu_scene.activate()

menu_scene = MenuScene()
game_scene = GameScene()
mcrfpy.current_scene = menu_scene
