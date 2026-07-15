# mcrf: objects=[Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

# Create scenes, then switch between them with activate()
menu_scene = mcrfpy.Scene("menu")
game_scene = mcrfpy.Scene("game")

# Instant switch (default) -- also settable via mcrfpy.current_scene = scene
menu_scene.activate()
game_scene.activate()

game_scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768)))
