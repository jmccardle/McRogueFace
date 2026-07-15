# mcrf: objects=[Caption,Scene,Window] verified=0.2.8-dev status=ok
import mcrfpy

# Get window instance
window = mcrfpy.Window.get()

# Configure window (headless-safe subset; resolution/fullscreen/vsync/center()
# require a real window and raise RuntimeError in --headless mode)
window.title = "My Roguelike"
window.framerate_limit = 60

# Scaling modes for different resolutions
window.game_resolution = (320, 240)  # Internal game resolution
window.scaling_mode = "fit"          # Scale to fit window

# Take a screenshot (returns raw RGBA bytes when no filename is given)
data = window.screenshot()

scene = mcrfpy.Scene("window_demo")
mcrfpy.current_scene = scene
scene.children.append(mcrfpy.Caption(text=f"Window: {window.title}", pos=(50, 50)))
