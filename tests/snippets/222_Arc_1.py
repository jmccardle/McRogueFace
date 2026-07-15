# mcrf: objects=[Arc,Color,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("arc_demo")
mcrfpy.current_scene = scene

# Create a simple arc
arc = mcrfpy.Arc(center=(200, 200), radius=50, start_angle=0, end_angle=180)

# Style it
arc.color = mcrfpy.Color(255, 0, 0)
arc.thickness = 3

# Add to scene
scene.children.append(arc)

# Create a progress indicator (quarter circle)
progress = mcrfpy.Arc(
    center=(100, 100),
    radius=40,
    start_angle=270,
    end_angle=360,
    color=mcrfpy.Color(0, 255, 0),
    thickness=5
)
scene.children.append(progress)
