# mcrf: objects=[Circle,Color,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("circle_button_demo")
mcrfpy.current_scene = scene

# Interactive button circle
button = mcrfpy.Circle(
    radius=25,
    center=(150, 150),
    fill_color=mcrfpy.Color(50, 50, 200),
    outline_color=mcrfpy.Color(100, 100, 255),
    outline=2
)

def on_hover_enter(pos):
    button.fill_color = mcrfpy.Color(80, 80, 230)

def on_hover_exit(pos):
    button.fill_color = mcrfpy.Color(50, 50, 200)

def on_click(pos, btn, action):
    print("Button clicked!")

button.on_enter = on_hover_enter
button.on_exit = on_hover_exit
button.on_click = on_click

scene.children.append(button)
