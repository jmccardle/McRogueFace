# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Frame Opacity - Transparency levels
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Background pattern
for i in range(20):
    stripe = mcrfpy.Frame(
        pos=(i * 52, 0), size=(26, 768),
        fill_color=mcrfpy.Color(50, 50, 80)
    )
    scene.children.append(stripe)

# Frames with varying opacity
opacities = [1.0, 0.75, 0.5, 0.25]
for i, opacity in enumerate(opacities):
    frame = mcrfpy.Frame(
        pos=(112 + i * 220, 234), size=(180, 300),
        fill_color=mcrfpy.Color(255, 150, 50),
        outline=2.0,
        outline_color=mcrfpy.Color(255, 255, 255),
        opacity=opacity
    )
    scene.children.append(frame)

    label = mcrfpy.Caption(
        text=f"opacity={opacity}",
        pos=(112 + i * 220 + 30, 550)
    )
    label.outline = 2
    label.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(label)
