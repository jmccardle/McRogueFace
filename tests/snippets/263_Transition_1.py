# mcrf: objects=[Caption,Scene,Transition] verified=0.2.8-dev status=ok
import mcrfpy

# Create scenes
menu = mcrfpy.Scene("menu")
game = mcrfpy.Scene("game")
settings = mcrfpy.Scene("settings")

menu.children.append(mcrfpy.Caption(text="Menu", pos=(10, 10)))
game.children.append(mcrfpy.Caption(text="Game", pos=(10, 10)))
settings.children.append(mcrfpy.Caption(text="Settings", pos=(10, 10)))

# Fade transition (default feel)
game.activate(mcrfpy.Transition.FADE)

# Slide transitions for navigation
settings.activate(mcrfpy.Transition.SLIDE_LEFT)

# Instant switch (no transition)
menu.activate(mcrfpy.Transition.NONE)

# With custom duration (seconds)
game.activate(mcrfpy.Transition.FADE, duration=0.5)
