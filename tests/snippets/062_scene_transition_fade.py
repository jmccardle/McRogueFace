# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene,Transition] verified=0.2.8-dev@a7ba486 status=ok
# Scene Transition Fade - Smooth scene transitions
import mcrfpy

scene1 = mcrfpy.Scene("scene1")
scene2 = mcrfpy.Scene("scene2")

scene1.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(100, 50, 50)))
_caption = mcrfpy.Caption(text="Scene 1 - Red", pos=(420, 350))
_caption.fill_color = mcrfpy.Color(255, 255, 255)
scene1.children.append(_caption)

scene2.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(50, 50, 100)))
_caption = mcrfpy.Caption(text="Scene 2 - Blue", pos=(420, 350))
_caption.fill_color = mcrfpy.Color(255, 255, 255)
scene2.children.append(_caption)

# Set default transition
mcrfpy.default_transition = mcrfpy.Transition.FADE
mcrfpy.default_transition_duration = 1.0

scene1.children.append(mcrfpy.Caption(text="Press SPACE - Fade transition", pos=(340, 450)))
scene2.children.append(mcrfpy.Caption(text="Press SPACE - Fade transition", pos=(340, 450)))

def key1(key, action):
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        scene2.activate()

def key2(key, action):
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        scene1.activate()

scene1.on_key = key1
scene2.on_key = key2

mcrfpy.current_scene = scene1
