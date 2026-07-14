# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Scene Switching - Multiple scenes
import mcrfpy

# Create two scenes
scene1 = mcrfpy.Scene("menu")
scene2 = mcrfpy.Scene("game")

# Menu scene
scene1.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(50, 50, 80)))
_caption = mcrfpy.Caption(text="MENU SCENE", pos=(420, 300))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene1.children.append(_caption)
scene1.children.append(mcrfpy.Caption(text="Press SPACE to go to game", pos=(360, 400)))

# Game scene
scene2.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(80, 50, 50)))
_caption = mcrfpy.Caption(text="GAME SCENE", pos=(420, 300))
_caption.fill_color = mcrfpy.Color(100, 255, 100)
scene2.children.append(_caption)
scene2.children.append(mcrfpy.Caption(text="Press SPACE to go to menu", pos=(360, 400)))

def menu_key(key, action):
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        scene2.activate()

def game_key(key, action):
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        scene1.activate()

scene1.on_key = menu_key
scene2.on_key = game_key

mcrfpy.current_scene = scene1
