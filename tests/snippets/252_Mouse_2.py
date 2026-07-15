# mcrf: objects=[Scene,Sprite,Timer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("custom_cursor")
mcrfpy.current_scene = scene

# Create a custom cursor sprite (uses the default texture atlas)
cursor = mcrfpy.Sprite(pos=(0, 0), sprite_index=1)
scene.children.append(cursor)

# Hide the system cursor
mcrfpy.mouse.visible = False

# Update the cursor's position every frame via a Timer
def update(timer, runtime):
    pos = mcrfpy.mouse.pos
    cursor.x, cursor.y = pos.x, pos.y

mcrfpy.Timer("cursor_follow", update, 16)
