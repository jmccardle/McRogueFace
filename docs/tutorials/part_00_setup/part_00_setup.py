"""McRogueFace - Part 0: Setting Up McRogueFace

Documentation: https://mcrogueface.github.io/tutorial/part_00_setup
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/tutorials/part_00_setup/part_00_setup.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
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