import mcrfpy

# Create a new scene called "hello"
mcrfpy.createScene("hello")

# Switch to our new scene
mcrfpy.setScene("hello")

# Get the UI container for our scene
ui = mcrfpy.sceneUI("hello")

# Create a text caption
caption = mcrfpy.Caption("Hello Roguelike!", 400, 300)
caption.font_size = 32
caption.fill_color = mcrfpy.Color(255, 255, 255)  # White text

# Add the caption to our scene
ui.append(caption)

# Create a smaller instruction caption
instruction = mcrfpy.Caption("Press ESC to exit", 400, 350)
instruction.font_size = 16
instruction.fill_color = mcrfpy.Color(200, 200, 200)  # Light gray
ui.append(instruction)

# Set up a simple key handler
def handle_keys(key, state):
    if state == "start" and key == "Escape":
        mcrfpy.setScene(None)  # This exits the game

mcrfpy.keypressScene(handle_keys)

print("Hello Roguelike is running!")