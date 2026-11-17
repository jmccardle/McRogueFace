# mcrf: objects=[Caption,Scene] verified=0.3.6-dev status=ok
import mcrfpy



# region: builtin
import mcrfpy

# Create scenes, then switch between them with activate()
menu_scene = mcrfpy.Scene("menu")
game_scene = mcrfpy.Scene("game")

# Instant switch (default) -- also settable via mcrfpy.current_scene = scene
menu_scene.activate()
game_scene.activate()
# endregion

game_scene.children.append(mcrfpy.Caption(text="Game scene", pos=(100, 100)))
