# mcrf: objects=[Caption,Color,Scene] verified=0.2.8-dev status=ok
"""McRogueFace Tutorial - Part 0: Hello Roguelike

This script demonstrates the basic structure of a McRogueFace program.
"""
import mcrfpy

# Create a Scene object - this is the preferred approach
scene = mcrfpy.Scene("hello")

# Create a caption to display text
title = mcrfpy.Caption(
    pos=(512, 300),
    text="Hello, Roguelike!"
)
title.fill_color = mcrfpy.Color(255, 255, 255)
title.font_size = 32

# Add the caption to the scene's UI collection
scene.children.append(title)

# Activate the scene to display it
scene.activate()

# Note: There is no run() function!
# The engine is already running - your script is imported by it.
