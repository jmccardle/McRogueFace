# mcrf: objects=[Arc,Color,Easing,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("arc_spinner")
mcrfpy.current_scene = scene

# Animated loading spinner
arc = mcrfpy.Arc(
    center=(150, 150),
    radius=30,
    start_angle=0,
    end_angle=270,
    color=mcrfpy.Color(100, 150, 255),
    thickness=4
)
scene.children.append(arc)

# Animate the arc rotating
arc.animate("start_angle", 360, 1.0, mcrfpy.Easing.LINEAR)
arc.animate("end_angle", 630, 1.0, mcrfpy.Easing.LINEAR)
