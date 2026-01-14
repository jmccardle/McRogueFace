"""McRogueFace - Sprite Labeling Tool

A development tool for rapid sprite sheet labeling during game jams.
Creates a dictionary mapping sprite indices to custom labels.

Usage:
    ./mcrogueface docs/cookbook/tools/sprite_labeler.py

Console commands (while running):
    # Save labels to file
    import json; json.dump(labels, open('sprite_labels.json', 'w'), indent=2)

    # Load labels from file
    labels.update(json.load(open('sprite_labels.json')))

    # Print current labels
    for k, v in sorted(labels.items()): print(f"{k}: {v}")
"""

import mcrfpy

# === Global State ===
labels = {}  # sprite_index (int) -> label (str)
selected_label = None  # Currently selected label name
current_sprite_index = 0  # Currently hovered sprite

# Label categories - customize these for your game!
DEFAULT_LABELS = [
    "player",
    "enemy",
    "wall",
    "floor",
    "door",
    "item",
    "trap",
    "decoration",
]

# === Configuration ===
# Change these to match your texture!
TEXTURE_PATH = "assets/kenney_tinydungeon.png"  # Path relative to build dir
TILE_SIZE = 16  # Size of each tile in the texture
GRID_COLS = 12  # Number of sprite columns in texture (texture_width / tile_size)
GRID_ROWS = 11  # Number of sprite rows in texture (texture_height / tile_size)

# UI Layout
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
GRID_X, GRID_Y = 50, 50
GRID_WIDTH, GRID_HEIGHT = 12 * 16 * 2, 11 * 16 * 2
PREVIEW_X, PREVIEW_Y = 480, 50
PREVIEW_SCALE = 4.0
PANEL_X = 480 + 180
PANEL_Y = 50

# Colors
BG_COLOR = mcrfpy.Color(30, 30, 40)
PANEL_COLOR = mcrfpy.Color(40, 45, 55)
BUTTON_COLOR = mcrfpy.Color(60, 65, 80)
BUTTON_HOVER = mcrfpy.Color(80, 85, 100)
BUTTON_SELECTED = mcrfpy.Color(80, 140, 80)
TEXT_COLOR = mcrfpy.Color(220, 220, 230)
LABEL_COLOR = mcrfpy.Color(100, 180, 255)
INPUT_BG = mcrfpy.Color(25, 25, 35)
INPUT_ACTIVE = mcrfpy.Color(35, 35, 50)

# === Scene Setup ===
scene = mcrfpy.Scene("sprite_labeler")
ui = scene.children

# Background
bg = mcrfpy.Frame(pos=(0, 0), size=(WINDOW_WIDTH, WINDOW_HEIGHT))
bg.fill_color = BG_COLOR
ui.append(bg)

# Load texture
texture = mcrfpy.Texture(TEXTURE_PATH, TILE_SIZE, TILE_SIZE)

# === Grid (shows all sprites) ===
grid = mcrfpy.Grid(
    grid_size=(GRID_COLS, GRID_ROWS),
    pos=(GRID_X, GRID_Y),
    size=(GRID_WIDTH, GRID_HEIGHT),
    texture=texture,
    zoom=2.0
)
grid.fill_color = mcrfpy.Color(20, 20, 30)

# Initialize grid with all sprites
for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        sprite_index = row * GRID_COLS + col
        cell = grid.at(col, row)
        if cell:
            cell.tilesprite = sprite_index

ui.append(grid)

# === Preview Section ===
preview_frame = mcrfpy.Frame(pos=(PREVIEW_X, PREVIEW_Y), size=(100, 100))
preview_frame.fill_color = PANEL_COLOR
preview_frame.outline = 1
preview_frame.outline_color = mcrfpy.Color(80, 80, 100)
ui.append(preview_frame)

preview_sprite = mcrfpy.Sprite((18, 18), texture, 0)
preview_sprite.scale = PREVIEW_SCALE
preview_frame.children.append(preview_sprite)

# Index caption
index_caption = mcrfpy.Caption(pos=(PREVIEW_X, PREVIEW_Y + 110), text="Index: 0")
index_caption.font_size = 18
index_caption.fill_color = TEXT_COLOR
ui.append(index_caption)

# Label display (shows current label for hovered sprite)
label_display = mcrfpy.Caption(pos=(PREVIEW_X, PREVIEW_Y + 135), text="Label: (none)")
label_display.font_size = 16
label_display.fill_color = LABEL_COLOR
ui.append(label_display)

# === Input Section (for adding new labels) ===
input_panel = mcrfpy.Frame(pos=(PANEL_X, PANEL_Y), size=(300, 80))
input_panel.fill_color = PANEL_COLOR
input_panel.outline = 1
input_panel.outline_color = mcrfpy.Color(80, 80, 100)
ui.append(input_panel)

input_title = mcrfpy.Caption(pos=(10, 8), text="Add New Label:")
input_title.font_size = 14
input_title.fill_color = TEXT_COLOR
input_panel.children.append(input_title)

# Text input field (frame + caption)
input_field = mcrfpy.Frame(pos=(10, 35), size=(200, 30))
input_field.fill_color = INPUT_BG
input_field.outline = 1
input_field.outline_color = mcrfpy.Color(60, 60, 80)
input_panel.children.append(input_field)

input_text = mcrfpy.Caption(pos=(8, 6), text="")
input_text.font_size = 14
input_text.fill_color = TEXT_COLOR
input_field.children.append(input_text)

# Text input state
input_buffer = ""
input_active = False

# Submit button
submit_btn = mcrfpy.Frame(pos=(220, 35), size=(70, 30))
submit_btn.fill_color = BUTTON_COLOR
submit_btn.outline = 1
submit_btn.outline_color = mcrfpy.Color(100, 100, 120)
input_panel.children.append(submit_btn)

submit_text = mcrfpy.Caption(pos=(12, 6), text="Add")
submit_text.font_size = 14
submit_text.fill_color = TEXT_COLOR
submit_btn.children.append(submit_text)

# === Label Selection Panel ===
labels_panel = mcrfpy.Frame(pos=(PANEL_X, PANEL_Y + 100), size=(300, 350))
labels_panel.fill_color = PANEL_COLOR
labels_panel.outline = 1
labels_panel.outline_color = mcrfpy.Color(80, 80, 100)
ui.append(labels_panel)

labels_title = mcrfpy.Caption(pos=(10, 8), text="Select Label (click to choose):")
labels_title.font_size = 14
labels_title.fill_color = TEXT_COLOR
labels_panel.children.append(labels_title)

# Store label button references for updating selection highlight
label_buttons = []  # list of (frame, caption, label_name)

def create_label_button(label_name, index):
    """Create a clickable label button"""
    row = index // 2
    col = index % 2
    btn_x = 10 + col * 145
    btn_y = 35 + row * 40

    btn = mcrfpy.Frame(pos=(btn_x, btn_y), size=(135, 32))
    btn.fill_color = BUTTON_COLOR
    btn.outline = 1
    btn.outline_color = mcrfpy.Color(80, 80, 100)

    btn_caption = mcrfpy.Caption(pos=(8, 7), text=label_name[:14])
    btn_caption.font_size = 12
    btn_caption.fill_color = TEXT_COLOR
    btn.children.append(btn_caption)

    labels_panel.children.append(btn)
    label_buttons.append((btn, btn_caption, label_name))

    # Set click handler
    def on_label_click(x, y, button):
        select_label(label_name)
        #return True
    btn.on_click = on_label_click

    return btn

def select_label(label_name):
    """Select a label for applying to sprites"""
    global selected_label
    selected_label = label_name

    # Update button colors
    for btn, caption, name in label_buttons:
        if name == selected_label:
            btn.fill_color = BUTTON_SELECTED
        else:
            btn.fill_color = BUTTON_COLOR

def add_new_label(label_name):
    """Add a new label to the selection list"""
    global input_buffer

    # Don't add duplicates or empty labels
    label_name = label_name.strip()
    if not label_name:
        return

    for _, _, existing in label_buttons:
        if existing == label_name:
            return

    # Create button for new label
    create_label_button(label_name, len(label_buttons))

    # Clear input
    input_buffer = ""
    input_text.text = ""

    # Select the new label
    select_label(label_name)

# Initialize default labels
for i, label in enumerate(DEFAULT_LABELS):
    create_label_button(label, i)

# Select first label by default
if DEFAULT_LABELS:
    select_label(DEFAULT_LABELS[0])

# === Event Handlers ===

def on_cell_enter(cell):
    """Handle mouse hovering over grid cells"""
    global current_sprite_index

    x, y = int(cell[0]), int(cell[1])
    sprite_index = y * GRID_COLS + x
    current_sprite_index = sprite_index

    # Update preview
    preview_sprite.sprite_index = sprite_index
    index_caption.text = f"Index: {sprite_index}"

    # Update label display
    if sprite_index in labels:
        label_display.text = f"Label: {labels[sprite_index]}"
        label_display.fill_color = BUTTON_SELECTED
    else:
        label_display.text = "Label: (none)"
        label_display.fill_color = LABEL_COLOR

def on_cell_click(cell):
    """Handle clicking on grid cells to apply labels"""
    global labels

    x, y = int(cell[0]), int(cell[1])
    sprite_index = y * GRID_COLS + x

    if selected_label:
        labels[sprite_index] = selected_label
        print(f"Labeled sprite {sprite_index} as '{selected_label}'")

        # Update display if this is the current sprite
        if sprite_index == current_sprite_index:
            label_display.text = f"Label: {selected_label}"
            label_display.fill_color = BUTTON_SELECTED

grid.on_cell_enter = on_cell_enter
grid.on_cell_click = on_cell_click

# Submit button click handler
def on_submit_click(x, y, button):
    """Handle submit button click"""
    add_new_label(input_buffer)
    #return True

submit_btn.on_click = on_submit_click

# Input field click handler (activate text input)
def on_input_click(x, y, button):
    """Handle input field click to activate typing"""
    global input_active
    input_active = True
    input_field.fill_color = INPUT_ACTIVE
    #return True

input_field.on_click = on_input_click

# === Keyboard Handler ===

def on_keypress(key, state):
    """Handle keyboard input for text entry"""
    global input_buffer, input_active

    if state != "start":
        return

    # Escape clears input focus
    if key == "Escape":
        input_active = False
        input_field.fill_color = INPUT_BG
        return

    # Enter submits the label
    if key == "Return":
        if input_active and input_buffer:
            add_new_label(input_buffer)
        input_active = False
        input_field.fill_color = INPUT_BG
        return

    # Only process text input when field is active
    if not input_active:
        return

    # Backspace
    if key == "BackSpace":
        if input_buffer:
            input_buffer = input_buffer[:-1]
            input_text.text = input_buffer
        return

    # Handle alphanumeric and common characters
    # Map key names to characters
    if len(key) == 1 and key.isalpha():
        input_buffer += key.lower()
        input_text.text = input_buffer
    elif key.startswith("Num") and len(key) == 4:
        # Numpad numbers
        input_buffer += key[3]
        input_text.text = input_buffer
    elif key == "Space":
        input_buffer += " "
        input_text.text = input_buffer
    elif key == "Minus":
        input_buffer += "-"
        input_text.text = input_buffer
    elif key == "Period":
        input_buffer += "."
        input_text.text = input_buffer

scene.on_key = on_keypress

# === Instructions Caption ===
#instructions = mcrfpy.Caption(
#    pos=(GRID_X, GRID_Y + GRID_HEIGHT + 20),
#    text="Hover: preview sprite | Click grid: apply selected label | Type: add new labels"
#)
#instructions.font_size = 12
#instructions.fill_color = mcrfpy.Color(150, 150, 160)
#ui.append(instructions)
#
#instructions2 = mcrfpy.Caption(
#    pos=(GRID_X, GRID_Y + GRID_HEIGHT + 40),
#    text="Console: labels (dict), json.dump(labels, open('labels.json','w'))"
#)
#instructions2.font_size = 12
#instructions2.fill_color = mcrfpy.Color(150, 150, 160)
#ui.append(instructions2)

# Activate the scene
scene.activate()

#print("=== Sprite Labeler Tool ===")
#print(f"Texture: {TEXTURE_PATH}")
#print(f"Grid: {GRID_COLS}x{GRID_ROWS} = {GRID_COLS * GRID_ROWS} sprites")
#print("")
#print("Usage:")
#print("  - Hover over grid to preview sprites")
#print("  - Click a label button to select it")
#print("  - Click on grid cells to apply the selected label")
#print("  - Type in the text field to add new labels")
#print("")
#print("Console commands:")
#print("  labels                    # View all labels")
#print("  labels[42] = 'custom'     # Manual labeling")
#print("  import json")
#print("  json.dump(labels, open('sprite_labels.json', 'w'), indent=2)  # Save")
#print("  labels.update(json.load(open('sprite_labels.json')))         # Load")
