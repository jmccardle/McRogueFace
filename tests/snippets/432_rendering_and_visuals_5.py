# mcrf: objects=[Color,Easing,Frame,Scene,Sprite] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("effects")
ui = scene.children

frame = mcrfpy.Frame(pos=(100, 100), size=(200, 150),
                      fill_color=mcrfpy.Color(50, 50, 50))
frame.opacity = 0.0
ui.append(frame)

sprite = mcrfpy.Sprite(x=350, y=120, sprite_index=0)
ui.append(sprite)

# region: animations
# Fade in
frame.animate("opacity", 1.0, 1.0, mcrfpy.Easing.EASE_IN_QUAD)

# Color transition
frame.animate("fill_color", (255, 0, 0, 255), 0.5, mcrfpy.Easing.LINEAR)

# Movement
frame.animate("x", 500.0, 0.3, mcrfpy.Easing.EASE_OUT_CUBIC)
frame.animate("y", 300.0, 0.3, mcrfpy.Easing.EASE_OUT_CUBIC)

# With completion callback
def on_done(target, prop, value):
    print(f"{prop} reached {value}")
frame.animate("x", 500.0, 0.3, mcrfpy.Easing.EASE_OUT_CUBIC, callback=on_done)
# endregion

# region: visibility
# Show/hide elements
sprite.visible = False  # Hidden
sprite.visible = True   # Visible

# Opacity
sprite.opacity = 0.0   # Invisible
sprite.opacity = 0.5   # Semi-transparent
sprite.opacity = 1.0   # Opaque
# endregion

mcrfpy.current_scene = scene
