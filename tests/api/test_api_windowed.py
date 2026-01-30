#!/usr/bin/env python3
"""Test for the McRogueFace Game API in windowed mode.

Run with: cd build && ./mcrogueface --exec ../tests/api/test_api_windowed.py

Tests all API endpoints and verifies proper functionality.
"""

import sys
import time
import urllib.request
import json

import mcrfpy

# Force flush on print
import functools
print = functools.partial(print, flush=True)

def log(msg):
    print(msg)

# Create a test scene with some UI elements
test_scene = mcrfpy.Scene("api_test")
ui = test_scene.children

# Add various interactive elements
font = mcrfpy.Font("assets/JetbrainsMono.ttf")

# A button-like frame with click handler
button_frame = mcrfpy.Frame(pos=(50, 50), size=(200, 60), fill_color=(64, 64, 128))
button_frame.name = "play_button"

button_label = mcrfpy.Caption(text="Play Game", pos=(20, 15), font=font, fill_color=(255, 255, 255))
button_frame.children.append(button_label)

click_count = [0]

def on_button_click(pos, button, action):
    if action == mcrfpy.InputState.PRESSED:
        click_count[0] += 1
        print(f"Button clicked! Count: {click_count[0]}")

button_frame.on_click = on_button_click
ui.append(button_frame)

# A second button
settings_frame = mcrfpy.Frame(pos=(50, 130), size=(200, 60), fill_color=(64, 128, 64))
settings_frame.name = "settings_button"
settings_label = mcrfpy.Caption(text="Settings", pos=(20, 15), font=font, fill_color=(255, 255, 255))
settings_frame.children.append(settings_label)
settings_frame.on_click = lambda pos, btn, action: print("Settings clicked")
ui.append(settings_frame)

# A caption without click (for display)
title = mcrfpy.Caption(text="API Test Scene", pos=(50, 10), font=font, fill_color=(255, 255, 0))
title.font_size = 24
ui.append(title)

# Status caption to show test progress
status = mcrfpy.Caption(text="Starting API tests...", pos=(50, 220), font=font, fill_color=(255, 255, 255))
ui.append(status)

# Activate scene
mcrfpy.current_scene = test_scene

# Start the API server
log("Starting API server...")
sys.path.insert(0, '../src/scripts')
from api import start_server
server = start_server(8765)
print("API server started on http://localhost:8765")


def run_api_tests(timer, runtime):
    """Run the API tests after scene is set up."""
    print("\n=== Starting API Tests ===\n")
    status.text = "Running tests..."

    base_url = "http://localhost:8765"
    all_passed = True

    # Test 1: Health check
    print("Test 1: Health check...")
    try:
        req = urllib.request.Request(f"{base_url}/health")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            assert data["status"] == "ok", f"Expected 'ok', got '{data['status']}'"
            print(f"  PASS: Server healthy, version {data.get('version')}")
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

    # Test 2: Scene introspection
    print("\nTest 2: Scene introspection...")
    try:
        req = urllib.request.Request(f"{base_url}/scene")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            assert data["scene_name"] == "api_test", f"Expected 'api_test', got '{data['scene_name']}'"
            print(f"  PASS: Scene '{data['scene_name']}' with {data['element_count']} elements")
            print(f"        Viewport: {data['viewport']}")
            for elem in data.get('elements', []):
                print(f"        - {elem['type']}: name='{elem.get('name', '')}' interactive={elem.get('interactive')}")
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

    # Test 3: Affordances
    print("\nTest 3: Affordance extraction...")
    try:
        req = urllib.request.Request(f"{base_url}/affordances")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            affordances = data["affordances"]
            print(f"  Found {len(affordances)} affordances:")
            for aff in affordances:
                print(f"    ID={aff['id']} type={aff['type']} label='{aff.get('label')}' actions={aff.get('actions')}")
            if len(affordances) >= 2:
                print(f"  PASS")
            else:
                print(f"  WARN: Expected at least 2 affordances")
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

    # Test 4: Metadata
    print("\nTest 4: Metadata...")
    try:
        req = urllib.request.Request(f"{base_url}/metadata")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            print(f"  Game: {data.get('game_name')}")
            print(f"  Current scene: {data.get('current_scene')}")
            print(f"  PASS")
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

    # Test 5: Input - click affordance by label
    print("\nTest 5: Click affordance by label...")
    try:
        req = urllib.request.Request(
            f"{base_url}/input",
            data=json.dumps({
                "action": "click_affordance",
                "label": "Play Game"  # Matches the button text
            }).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            if data.get("success"):
                print(f"  PASS: Clicked affordance '{data.get('affordance_label')}' at ({data.get('x'):.0f}, {data.get('y'):.0f})")
            else:
                print(f"  FAIL: {data}")
                all_passed = False
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

    # Test 6: Screenshot (base64)
    print("\nTest 6: Screenshot...")
    try:
        req = urllib.request.Request(f"{base_url}/screenshot?format=base64")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            if "image" in data and data["image"].startswith("data:image/png;base64,"):
                img_size = len(data["image"])
                print(f"  PASS: Got base64 image ({img_size} chars)")
            else:
                print(f"  FAIL: Invalid image data")
                all_passed = False
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

    # Test 7: Wait endpoint (quick check)
    print("\nTest 7: Wait endpoint...")
    try:
        req = urllib.request.Request(f"{base_url}/wait?timeout=1")
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read())
            print(f"  PASS: Scene hash: {data.get('hash')}")
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

    if all_passed:
        print("\n=== All API Tests Passed ===\n")
        status.text = "All tests PASSED!"
        status.fill_color = (0, 255, 0)
    else:
        print("\n=== Some Tests Failed ===\n")
        status.text = "Some tests FAILED"
        status.fill_color = (255, 0, 0)

    print("Press ESC to exit, or interact with the scene...")
    print(f"API still running at {base_url}")


# Add key handler to exit
def on_key(key, action):
    if key == mcrfpy.Key.ESCAPE and action == mcrfpy.InputState.PRESSED:
        mcrfpy.exit()

test_scene.on_key = on_key

# Run tests after a short delay to let rendering settle
test_timer = mcrfpy.Timer("api_test", run_api_tests, 1000)
