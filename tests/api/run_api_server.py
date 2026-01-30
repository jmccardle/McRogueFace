#!/usr/bin/env python3
"""Simple script to start the McRogueFace Game API server.

Run with: cd build && ./mcrogueface --exec ../tests/api/run_api_server.py

Then test with:
    curl http://localhost:8765/health
    curl http://localhost:8765/scene
    curl http://localhost:8765/affordances
"""

import sys
sys.path.insert(0, '../src/scripts')

import mcrfpy

print("Creating test scene...", flush=True)

# Create a simple test scene
scene = mcrfpy.Scene("test")
ui = scene.children

font = mcrfpy.Font("assets/JetbrainsMono.ttf")

# Title
title = mcrfpy.Caption(text="API Test Scene", pos=(50, 20), font=font, fill_color=(255, 255, 0))
title.font_size = 24
ui.append(title)

# A clickable button
button = mcrfpy.Frame(pos=(50, 80), size=(200, 50), fill_color=(64, 64, 128))
button.name = "test_button"
button.on_click = lambda pos, btn, action: print(f"Button clicked: {action}", flush=True)
button_text = mcrfpy.Caption(text="Click Me", pos=(50, 10), font=font, fill_color=(255, 255, 255))
button.children.append(button_text)
ui.append(button)

# A second button
button2 = mcrfpy.Frame(pos=(50, 150), size=(200, 50), fill_color=(64, 128, 64))
button2.name = "settings_button"
button2.on_click = lambda pos, btn, action: print(f"Settings clicked: {action}", flush=True)
button2_text = mcrfpy.Caption(text="Settings", pos=(50, 10), font=font, fill_color=(255, 255, 255))
button2.children.append(button2_text)
ui.append(button2)

# Status text
status = mcrfpy.Caption(text="API Server running on http://localhost:8765", pos=(50, 230), font=font, fill_color=(128, 255, 128))
ui.append(status)

status2 = mcrfpy.Caption(text="Press ESC to exit", pos=(50, 260), font=font, fill_color=(200, 200, 200))
ui.append(status2)

mcrfpy.current_scene = scene

print("Starting API server...", flush=True)

# Start the API server
from api import start_server
server = start_server(8765)

print("", flush=True)
print("=" * 50, flush=True)
print("API Server is ready!", flush=True)
print("", flush=True)
print("Test endpoints:", flush=True)
print("  curl http://localhost:8765/health", flush=True)
print("  curl http://localhost:8765/scene", flush=True)
print("  curl http://localhost:8765/affordances", flush=True)
print("  curl http://localhost:8765/metadata", flush=True)
print("  curl http://localhost:8765/screenshot?format=base64 | jq -r .image", flush=True)
print("", flush=True)
print("Input examples:", flush=True)
print('  curl -X POST -H "Content-Type: application/json" -d \'{"action":"key","key":"W"}\' http://localhost:8765/input', flush=True)
print('  curl -X POST -H "Content-Type: application/json" -d \'{"action":"click","x":150,"y":100}\' http://localhost:8765/input', flush=True)
print("=" * 50, flush=True)
print("", flush=True)

# Key handler
def on_key(key, action):
    if key == mcrfpy.Key.ESCAPE and action == mcrfpy.InputState.PRESSED:
        print("Exiting...", flush=True)
        mcrfpy.exit()

scene.on_key = on_key
