# mcrf: objects=[Caption,Frame,InputState,Key,Scene,Transition] verified=0.2.8-dev status=ok
import mcrfpy

# Create a scene
scene = mcrfpy.Scene("game")

# Add UI elements
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(800, 600)))
scene.children.append(mcrfpy.Caption(text="Hello", pos=(100, 100)))

menu_scene = mcrfpy.Scene("menu")

# Handle input
def on_key(key, action):
    if key == mcrfpy.Key.ESCAPE and action == mcrfpy.InputState.PRESSED:
        menu_scene.activate()

scene.on_key = on_key

# Activate with optional transition
scene.activate()
scene.activate(mcrfpy.Transition.FADE, duration=0.5)

mcrfpy.current_scene = scene

# Subclass for lifecycle callbacks
class GameScene(mcrfpy.Scene):
    def on_enter(self):
        print("Entering game scene")

    def on_exit(self):
        print("Leaving game scene")

    def on_key(self, key, action):
        if key == mcrfpy.Key.Q and action == mcrfpy.InputState.PRESSED:
            self.handle_quit()

    def update(self, dt):
        # Called every frame with delta time
        self.update_entities(dt)

    def on_resize(self, new_size):
        # Window resize handling - new_size is a Vector(width, height)
        self.realign()
