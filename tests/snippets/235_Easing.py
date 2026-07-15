# mcrf: objects=[Easing,Scene,Sprite] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("easing_demo")
mcrfpy.current_scene = scene

sprite = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite)

# Use with animate() method
sprite.animate("x", 500, 1.0, mcrfpy.Easing.EASE_OUT_QUAD)
sprite.animate("opacity", 0, 0.5, mcrfpy.Easing.EASE_IN_OUT)

# Bouncy effect
sprite.animate("scale", 1.2, 0.3, mcrfpy.Easing.EASE_OUT_ELASTIC)

# Anticipation (pullback before action)
sprite.animate("x", 100, 0.5, mcrfpy.Easing.EASE_IN_BACK)
