# mcrf: objects=[Scene,Sprite] verified=0.2.8-dev status=ok
# Sprite Quick Reference - create, scale, animate a sprite
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Load a texture atlas
texture = mcrfpy.default_texture

# Create a sprite from the texture
sprite = mcrfpy.Sprite(pos=(100, 100), texture=texture, sprite_index=42)

# Scale it
sprite.scale = 2.0  # Uniform scaling

# Or scale independently
sprite.scale_x = 2.0
sprite.scale_y = 1.5

# Add to scene
scene.children.append(sprite)

# Animate through sprite frames
sprite.animate("sprite_index", 45, 0.5)  # Animate to frame 45
