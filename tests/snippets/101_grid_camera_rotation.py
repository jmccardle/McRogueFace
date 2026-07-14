# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Key,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Grid Camera Rotation - Rotate the view
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0
)
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        cell.tilesprite = 48 if (x + y) % 2 == 0 else 49

player = mcrfpy.Entity(grid_pos=(8, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

grid.center_camera((8, 6))

angle_label = mcrfpy.Caption(text="Rotation: 0°", pos=(420, 660))
angle_label.outline = 2
angle_label.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(angle_label)

controls = mcrfpy.Caption(text="Q/E to rotate camera", pos=(400, 720))
controls.outline = 2
controls.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(controls)

def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    if key == mcrfpy.Key.Q:
        grid.camera_rotation -= 15
    elif key == mcrfpy.Key.E:
        grid.camera_rotation += 15
    angle_label.text = f"Rotation: {grid.camera_rotation}°"

scene.on_key = on_key
