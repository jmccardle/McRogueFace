from text_input_widget_improved import FocusManager, TextInput       
                                                            
# Create focus manager                                      
focus_mgr = FocusManager()                                  
                                                            
# Create input field
name_input = TextInput(
    x=50, y=100,
    width=300,
    label="Name:",
    placeholder="Enter your name",
    on_change=lambda text: print(f"Name changed to: {text}")
)

tags_input = TextInput(
    x=50, y=160,
    width=300,
    label="Tags:",
    placeholder="door,chest,floor,wall",
    on_change=lambda text: print(f"Text: {text}")
)

# Register with focus manager
name_input._focus_manager = focus_mgr
focus_mgr.register(name_input)


# Create demo scene
import mcrfpy

mcrfpy.createScene("text_example")
mcrfpy.setScene("text_example")

ui = mcrfpy.sceneUI("text_example")
# Add to scene
#ui.append(name_input) # don't do this, only the internal Frame class can go into the UI; have to manage derived objects "carefully" (McRogueFace alpha anti-feature)
name_input.add_to_scene(ui)
tags_input.add_to_scene(ui)

# Handle keyboard events
def handle_keys(key, state):
    if not focus_mgr.handle_key(key, state):
        if key == "Tab" and state == "start":
            focus_mgr.focus_next()

# McRogueFace alpha anti-feature: only the active scene can be given a keypress callback
mcrfpy.keypressScene(handle_keys)

