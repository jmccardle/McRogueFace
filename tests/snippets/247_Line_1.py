# mcrf: objects=[Color,Line,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("line_quickref")
mcrfpy.current_scene = scene

# Create a simple line
line = mcrfpy.Line(start=(50, 50), end=(200, 150))
line.color = mcrfpy.Color(255, 255, 0)
line.thickness = 2

# Add to scene
scene.children.append(line)

# Create a divider
divider = mcrfpy.Line(
    start=(0, 100),
    end=(400, 100),
    thickness=1,
    color=mcrfpy.Color(100, 100, 100)
)
scene.children.append(divider)
