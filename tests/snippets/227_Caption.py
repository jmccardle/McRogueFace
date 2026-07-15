# mcrf: objects=[Caption,Color,Font,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("caption_demo")
mcrfpy.current_scene = scene

# Create a caption
title = mcrfpy.Caption(text="Hello, World!", pos=(100, 50), font=mcrfpy.Font("assets/JetbrainsMono.ttf"))

# Style it
title.font_size = 24
title.fill_color = mcrfpy.Color(255, 255, 255)
title.outline_color = mcrfpy.Color(0, 0, 0)
title.outline = 1

# Add to scene
scene.children.append(title)

# Update text dynamically
score = 100
title.text = f"Score: {score}"

# Animate properties
title.animate("opacity", 0.0, 2.0, "easeOut")  # Fade out
