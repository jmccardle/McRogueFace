# mcrf: objects=[Caption,Color,Frame,Scene,Vector] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("vector-arithmetic")
mcrfpy.current_scene = scene
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

a = mcrfpy.Vector(10, 20)
b = mcrfpy.Vector(5, 10)

# Addition and subtraction
c = a + b  # Vector(15, 30)
d = a - b  # Vector(5, 10)

# Scalar multiplication and division
e = a * 2  # Vector(20, 40)
f = a / 2  # Vector(5, 10)

# In-place operations
a += b
a -= b
a *= 2
a /= 2

# Comparison
lines = []
if a == b:
    lines.append("Same position")
if a != b:
    lines.append("Different positions")

cap = mcrfpy.Caption(text=", ".join(lines) or "no comparisons matched", pos=(20, 20))
scene.children.append(cap)
