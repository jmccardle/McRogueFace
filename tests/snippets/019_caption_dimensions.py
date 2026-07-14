# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Caption Dimensions - Text width and height
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

texts = [
    "Short",
    "A medium length text",
    "This is a much longer piece of text to display",
]

y = 150
for text in texts:
    # Create caption
    cap = mcrfpy.Caption(text=text, pos=(100, y))
    cap.fill_color = mcrfpy.Color(255, 255, 255)
    scene.children.append(cap)

    # Bounding box showing dimensions
    box = mcrfpy.Frame(
        pos=(100, y - 5),
        size=(cap.w, cap.h + 10),
        fill_color=mcrfpy.Color(0, 0, 0, 0),
        outline=1.0,
        outline_color=mcrfpy.Color(255, 100, 100)
    )
    scene.children.append(box)

    # Show dimensions
    dims = mcrfpy.Caption(text=f"w={cap.w:.0f}, h={cap.h:.0f}", pos=(100, y + 50))
    dims.fill_color = mcrfpy.Color(150, 150, 150)
    scene.children.append(dims)

    y += 150
