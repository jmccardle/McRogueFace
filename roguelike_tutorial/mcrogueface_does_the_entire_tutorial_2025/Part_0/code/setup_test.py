import mcrfpy

# Create our test scene
mcrfpy.createScene("test")
mcrfpy.setScene("test")
ui = mcrfpy.sceneUI("test")

# Create a background frame
background = mcrfpy.Frame(0, 0, 1024, 768)
background.fill_color = mcrfpy.Color(20, 20, 30)  # Dark blue-gray
ui.append(background)

# Title text
title = mcrfpy.Caption("McRogueFace Setup Test", 512, 100)
title.font_size = 36
title.fill_color = mcrfpy.Color(255, 255, 100)  # Yellow
ui.append(title)

# Status text that will update
status_text = mcrfpy.Caption("Press any key to test input...", 512, 300)
status_text.font_size = 20
status_text.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(status_text)

# Instructions
instructions = [
    "Arrow Keys: Test movement input",
    "Space: Test action input", 
    "Mouse Click: Test mouse input",
    "ESC: Exit"
]

y_offset = 400
for instruction in instructions:
    inst_caption = mcrfpy.Caption(instruction, 512, y_offset)
    inst_caption.font_size = 16
    inst_caption.fill_color = mcrfpy.Color(150, 150, 150)
    ui.append(inst_caption)
    y_offset += 30

# Input handler
def handle_input(key, state):
    if state != "start":
        return
        
    if key == "Escape":
        mcrfpy.setScene(None)
    else:
        status_text.text = f"You pressed: {key}"
        status_text.fill_color = mcrfpy.Color(100, 255, 100)  # Green

# Set up input handling
mcrfpy.keypressScene(handle_input)

print("Setup test is running! Try pressing different keys.")