# mcrf: objects=[Caption,Color,Frame,Scene,Vector] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("vector-demo")
mcrfpy.current_scene = scene
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Create vectors
pos = mcrfpy.Vector(100, 200)
direction = mcrfpy.Vector(1, 0)  # Unit vector pointing right

# Arithmetic operations
new_pos = pos + direction * 50
offset = mcrfpy.Vector(10, 10)
pos += offset

# Distance and magnitude
other_pos = mcrfpy.Vector(150, 220)
dist = pos.distance_to(other_pos)
length = direction.magnitude()
unit = direction.normalize()

# Use as dict key
positions = {}
positions[pos.int] = "player"

cap = mcrfpy.Caption(
    text=f"pos={pos.x:.1f},{pos.y:.1f} dist={dist:.2f} len={length:.2f} unit=({unit.x:.1f},{unit.y:.1f})",
    pos=(20, 20),
)
scene.children.append(cap)
