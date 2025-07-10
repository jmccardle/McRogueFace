# Part 0 - Setting Up McRogueFace

Welcome to the McRogueFace Roguelike Tutorial! This tutorial will teach you how to create a complete roguelike game using the McRogueFace game engine. Unlike traditional Python libraries, McRogueFace is a complete, portable game engine that includes everything you need to make and distribute games.

## What is McRogueFace?

McRogueFace is a high-performance game engine with Python scripting support. Think of it like Unity or Godot, but specifically designed for roguelikes and 2D games. It includes:

- A complete Python 3.12 runtime (no installation needed!)
- High-performance C++ rendering and entity management
- Built-in UI components and scene management
- Integrated audio system
- Professional sprite-based graphics
- Easy distribution - your players don't need Python installed!

## Prerequisites

Before starting this tutorial, you should:

- Have basic Python knowledge (variables, functions, classes)
- Be comfortable editing text files
- Have a text editor (VS Code, Sublime Text, Notepad++, etc.)

That's it! Unlike other roguelike tutorials, you don't need Python installed - McRogueFace includes everything.

## Getting McRogueFace

### Step 1: Download the Engine

1. Visit the McRogueFace releases page
2. Download the version for your operating system:
   - `McRogueFace-Windows.zip` for Windows
   - `McRogueFace-MacOS.zip` for macOS
   - `McRogueFace-Linux.zip` for Linux

### Step 2: Extract the Archive

Extract the downloaded archive to a folder where you want to develop your game. You should see this structure:

```
McRogueFace/
├── mcrogueface (or mcrogueface.exe on Windows)
├── scripts/
│   └── game.py
├── assets/
│   ├── sprites/
│   ├── fonts/
│   └── audio/
└── lib/
```

### Step 3: Run the Engine

Run the McRogueFace executable:

- **Windows**: Double-click `mcrogueface.exe`
- **Mac/Linux**: Open a terminal in the folder and run `./mcrogueface`

You should see a window open with the default McRogueFace demo. This shows the engine is working correctly!

## Your First McRogueFace Script

Let's modify the engine to display "Hello Roguelike!" instead of the default demo.

### Step 1: Open game.py

Open `scripts/game.py` in your text editor. You'll see the default demo code. Replace it entirely with:

```python
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
```

### Step 2: Save and Run

1. Save the file
2. If McRogueFace is still running, it will automatically reload!
3. If not, run the engine again

You should now see "Hello Roguelike!" displayed in the window.

### Step 3: Understanding the Code

Let's break down what we just wrote:

1. **Import mcrfpy**: This is McRogueFace's Python API
2. **Create a scene**: Scenes are like game states (menu, gameplay, inventory, etc.)
3. **UI elements**: We create Caption objects for text display
4. **Colors**: McRogueFace uses RGB colors (0-255 for each component)
5. **Input handling**: We set up a callback for keyboard input
6. **Scene switching**: Setting the scene to None exits the game

## Key Differences from Pure Python Development

### The Game Loop

Unlike typical Python scripts, McRogueFace runs your code inside its game loop:

1. The engine starts and loads `scripts/game.py`
2. Your script sets up scenes, UI elements, and callbacks
3. The engine runs at 60 FPS, handling rendering and input
4. Your callbacks are triggered by game events

### Hot Reloading

McRogueFace can reload your scripts while running! Just save your changes and the engine will reload automatically. This makes development incredibly fast.

### Asset Pipeline

McRogueFace includes a complete asset system:

- **Sprites**: Place images in `assets/sprites/`
- **Fonts**: TrueType fonts in `assets/fonts/`
- **Audio**: Sound effects and music in `assets/audio/`

We'll explore these in later lessons.

## Testing Your Setup

Let's create a more interactive test to ensure everything is working properly:

```python
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
```

## Troubleshooting

### Engine Won't Start

- **Windows**: Make sure you extracted all files, not just the .exe
- **Mac**: You may need to right-click and select "Open" the first time
- **Linux**: Make sure the file is executable: `chmod +x mcrogueface`

### Scripts Not Loading

- Ensure your script is named exactly `game.py` in the `scripts/` folder
- Check the console output for Python errors
- Make sure you're using Python 3 syntax

### Performance Issues

- McRogueFace should run smoothly at 60 FPS
- If not, check if your graphics drivers are updated
- The engine shows FPS in the window title

## What's Next?

Congratulations! You now have McRogueFace set up and running. You've learned:

- How to download and run the McRogueFace engine
- The basic structure of a McRogueFace project
- How to create scenes and UI elements
- How to handle keyboard input
- The development workflow with hot reloading

In Part 1, we'll create our player character and implement movement. We'll explore McRogueFace's entity system and learn how to create a game world.

## Why McRogueFace?

Before we continue, let's highlight why McRogueFace is excellent for roguelike development:

1. **No Installation Hassles**: Your players just download and run - no Python needed!
2. **Professional Performance**: C++ engine core means smooth gameplay even with hundreds of entities
3. **Built-in Features**: UI, audio, scenes, and animations are already there
4. **Easy Distribution**: Just zip your game folder and share it
5. **Rapid Development**: Hot reloading and Python scripting for quick iteration

Ready to make a roguelike? Let's continue to Part 1!