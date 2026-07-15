# mcrf: objects=[Circle,Color,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("circle_demo")
mcrfpy.current_scene = scene

# Create a filled circle
circle = mcrfpy.Circle(radius=30, center=(100, 100))
circle.fill_color = mcrfpy.Color(0, 255, 0)

# Add to scene
scene.children.append(circle)

# Circle with outline only
ring = mcrfpy.Circle(
    radius=50,
    center=(200, 200),
    fill_color=mcrfpy.Color(0, 0, 0, 0),  # Transparent fill
    outline_color=mcrfpy.Color(255, 255, 255),
    outline=3
)
scene.children.append(ring)
