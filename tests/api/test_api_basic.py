#!/usr/bin/env python3
"""Basic test for the McRogueFace Game API.

Run with: cd build && ./mcrogueface --headless --exec ../tests/api/test_api_basic.py
"""

import sys
import time
import threading
import urllib.request
import json

import mcrfpy

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
    if str(action) == "PRESSED" or action == mcrfpy.InputState.PRESSED:
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

# Activate scene
mcrfpy.current_scene = test_scene


def run_api_tests(timer, runtime):
    """Run the API tests after scene is set up."""
    print("\n=== Starting API Tests ===\n")

    base_url = "http://localhost:8765"

    # Test 1: Health check
    print("Test 1: Health check...")
    try:
        req = urllib.request.Request(f"{base_url}/health")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read())
            assert data["status"] == "ok", f"Expected 'ok', got '{data['status']}'"
            print(f"  PASS: Server healthy, version {data.get('version')}")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # Test 2: Scene introspection
    print("\nTest 2: Scene introspection...")
    try:
        req = urllib.request.Request(f"{base_url}/scene")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read())
            assert data["scene_name"] == "api_test", f"Expected 'api_test', got '{data['scene_name']}'"
            assert data["element_count"] == 3, f"Expected 3 elements, got {data['element_count']}"
            print(f"  PASS: Scene '{data['scene_name']}' with {data['element_count']} elements")
            print(f"        Viewport: {data['viewport']}")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # Test 3: Affordances
    print("\nTest 3: Affordance extraction...")
    try:
        req = urllib.request.Request(f"{base_url}/affordances")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read())
            affordances = data["affordances"]
            assert len(affordances) >= 2, f"Expected at least 2 affordances, got {len(affordances)}"

            # Check for our named buttons
            labels = [a.get("label") for a in affordances]
            print(f"  Found affordances with labels: {labels}")

            # Find play_button by name hint
            play_affordance = None
            for a in affordances:
                if a.get("hint") and "play_button" in a.get("hint", ""):
                    play_affordance = a
                    break
                if a.get("label") and "Play" in a.get("label", ""):
                    play_affordance = a
                    break

            if play_affordance:
                print(f"  PASS: Found play button affordance, ID={play_affordance['id']}")
            else:
                print(f"  WARN: Could not find play button by name or label")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # Test 4: Metadata
    print("\nTest 4: Metadata...")
    try:
        req = urllib.request.Request(f"{base_url}/metadata")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read())
            assert "current_scene" in data, "Missing current_scene"
            print(f"  PASS: Got metadata, current_scene={data['current_scene']}")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # Test 5: Input - click
    print("\nTest 5: Input click...")
    try:
        # Click the play button
        req = urllib.request.Request(
            f"{base_url}/input",
            data=json.dumps({
                "action": "click",
                "x": 150,  # Center of play button
                "y": 80
            }).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read())
            assert data["success"], "Click failed"
            print(f"  PASS: Click executed at ({data['x']}, {data['y']})")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # Test 6: Input - key
    print("\nTest 6: Input key press...")
    try:
        req = urllib.request.Request(
            f"{base_url}/input",
            data=json.dumps({
                "action": "key",
                "key": "ESCAPE"
            }).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read())
            assert data["success"], "Key press failed"
            print(f"  PASS: Key '{data['key']}' pressed")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # Test 7: Wait endpoint (quick check)
    print("\nTest 7: Wait endpoint...")
    try:
        req = urllib.request.Request(f"{base_url}/wait?timeout=1")
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read())
            assert "hash" in data, "Missing hash"
            print(f"  PASS: Got scene hash: {data['hash']}")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    print("\n=== All API Tests Passed ===\n")
    sys.exit(0)


# Start the API server
print("Starting API server...")
import sys
sys.path.insert(0, '../src/scripts')
from api import start_server
server = start_server(8765)

# Give server time to start
time.sleep(0.5)

# Run tests after a short delay
test_timer = mcrfpy.Timer("api_test", run_api_tests, 500)
