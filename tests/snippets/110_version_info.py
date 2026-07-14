# mcrf: objects=[Caption,Color,Frame,Scene,Sprite] verified=0.2.8-dev status=ok
# Version Info - Engine version and info
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="McRogueFace Engine Info",
    pos=(360, 100))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

# Large logo/sprite
sprite = mcrfpy.Sprite(
    texture=mcrfpy.default_texture,
    sprite_index=84,
    pos=(412, 200),
    scale=12.0
)
scene.children.append(sprite)

# Version info
info_frame = mcrfpy.Frame(
    pos=(262, 420), size=(500, 200),
    fill_color=mcrfpy.Color(40, 40, 60),
    outline=2.0
)
scene.children.append(info_frame)

version = mcrfpy.__version__
info_frame.children.append(mcrfpy.Caption(text=f"Version: {version}", pos=(150, 30)))
info_frame.children.append(mcrfpy.Caption(text="A Python-powered roguelike engine", pos=(80, 80)))
info_frame.children.append(mcrfpy.Caption(text="Built with SFML, libtcod, and Python", pos=(70, 120)))

link = mcrfpy.Caption(
    text="https://github.com/jmcb/McRogueFace",
    pos=(330, 650))
link.fill_color = mcrfpy.Color(100, 150, 255)
link.outline = 2
link.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(link)
