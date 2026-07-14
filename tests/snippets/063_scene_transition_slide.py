# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene,Transition] verified=0.2.8-dev status=ok
# Scene Transition Slide - Sliding transitions
import mcrfpy

scene1 = mcrfpy.Scene("left")
scene2 = mcrfpy.Scene("right")

scene1.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(50, 100, 50)))
_caption = mcrfpy.Caption(text="LEFT Scene", pos=(420, 350))
_caption.fill_color = mcrfpy.Color(255, 255, 255)
scene1.children.append(_caption)

scene2.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(100, 50, 100)))
_caption = mcrfpy.Caption(text="RIGHT Scene", pos=(420, 350))
_caption.fill_color = mcrfpy.Color(255, 255, 255)
scene2.children.append(_caption)

mcrfpy.default_transition = mcrfpy.Transition.SLIDE_LEFT
mcrfpy.default_transition_duration = 0.5

scene1.children.append(mcrfpy.Caption(text="Press SPACE - Slide left", pos=(360, 450)))
scene2.children.append(mcrfpy.Caption(text="Press SPACE - Slide left", pos=(360, 450)))

def key1(key, action):
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        scene2.activate()

def key2(key, action):
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        scene1.activate()

scene1.on_key = key1
scene2.on_key = key2

mcrfpy.current_scene = scene1
