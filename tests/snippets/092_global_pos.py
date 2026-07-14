# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
# Global Position - World coordinates
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Nested containers
outer = mcrfpy.Frame(
    pos=(200, 200), size=(500, 400),
    fill_color=mcrfpy.Color(60, 60, 80),
    outline=2.0
)
scene.children.append(outer)

inner = mcrfpy.Frame(
    pos=(100, 100), size=(300, 200),
    fill_color=mcrfpy.Color(80, 80, 100),
    outline=2.0
)
outer.children.append(inner)

deepest = mcrfpy.Frame(
    pos=(50, 50), size=(100, 80),
    fill_color=mcrfpy.Color(150, 100, 100),
    outline=2.0
)
inner.children.append(deepest)

# Show positions
outer.children.append(mcrfpy.Caption(text="Outer: pos=(200,200)", pos=(10, 10)))
inner.children.append(mcrfpy.Caption(text="Inner: pos=(100,100)", pos=(10, 10)))

# Global position
gpos = deepest.global_bounds
deepest.children.append(mcrfpy.Caption(
    text=f"local=(50,50)",
    pos=(5, 5)
))

_caption = mcrfpy.Caption(
    text=f"Deepest global_pos = ({gpos[0].x}, {gpos[0].y})",
    pos=(300, 650))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)
scene.children.append(mcrfpy.Caption(text="(200 + 100 + 50 = 350, 200 + 100 + 50 = 350)", pos=(300, 690)))
