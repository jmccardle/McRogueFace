import mcrfpy
font = mcrfpy.Font("assets/JetbrainsMono.ttf")
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# build test widgets

mcrfpy.createScene("pytest")
mcrfpy.setScene("pytest")
ui = mcrfpy.sceneUI("pytest")

# Frame
f = mcrfpy.Frame(25, 19, 462, 346, fill_color=(255, 92, 92))
# fill (LinkedColor / Color):    f.fill_color
# outline (LinkedColor / Color): f.outline_color
# pos (LinkedVector / Vector):   f.pos
# size (LinkedVector / Vector):  f.size

# Caption
c = mcrfpy.Caption(512+25, 19, "Hi.", font)
# fill (LinkedColor / Color):    c.fill_color
#color_val = c.fill_color
print(c.fill_color)
print("Set a fill color")
c.fill_color = (255, 255, 255)
print("Lol, did it segfault?")
# outline (LinkedColor / Color): c.outline_color
# font (Font):                   c.font
# pos (LinkedVector / Vector):   c.pos

# Sprite
s = mcrfpy.Sprite(25, 384+19, texture, 86, 9.0)
# pos (LinkedVector / Vector):   s.pos
# texture (Texture):             s.texture

# Grid
g = mcrfpy.Grid(10, 10, texture, 512+25, 384+19, 462, 346)
# texture (Texture):             g.texture
# pos (LinkedVector / Vector):   g.pos
# size (LinkedVector / Vector):  g.size

for _x in range(10):
    for _y in range(10):
        g.at((_x, _y)).color = (255 - _x*25, 255 - _y*25, 255)
g.zoom = 2.0

[ui.append(d) for d in (f, c, s, g)]

print("built!")

# tests

