# mcrf: objects=[Color,Easing,Line,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("line_example")
mcrfpy.current_scene = scene

# Draw a triangle using three lines
points = [(100, 50), (50, 150), (150, 150)]
color = mcrfpy.Color(255, 100, 100)

for i in range(3):
    line = mcrfpy.Line(
        start=points[i],
        end=points[(i + 1) % 3],
        thickness=2,
        color=color
    )
    scene.children.append(line)

# Animated growing line
growing_line = mcrfpy.Line(
    start=(200, 100),
    end=(200, 100),  # Start with zero length
    thickness=3,
    color=mcrfpy.Color(0, 255, 255)
)
scene.children.append(growing_line)

# Animate the end point to create a growing effect
growing_line.animate("end", (350, 200), 1.5, mcrfpy.Easing.EASE_OUT)
