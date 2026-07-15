# mcrf: objects=[Caption,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

caption = mcrfpy.Caption(text="", pos=(20, 20))
scene.children.append(caption)

# Typewriter effect: reveals the target string over 2 seconds
caption.animate("text", "You awaken in a dark cell.", 2.0)
