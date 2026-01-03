#!/usr/bin/env python3
"""
VLLM Integration Demo for McRogueFace
=====================================

Demonstrates using a local Vision-Language Model (Gemma 3) with
McRogueFace headless rendering to create an AI-driven agent.

Requirements:
- Local VLLM running at http://192.168.1.100:8100
- McRogueFace built with headless mode support

This is a research-grade demo for issue #156.
"""

import mcrfpy
from mcrfpy import automation
import sys
import requests
import base64
import os
import random

# VLLM configuration
VLLM_URL = "http://192.168.1.100:8100/v1/chat/completions"
SCREENSHOT_PATH = "/tmp/vllm_demo_screenshot.png"

# Sprite constants from Crypt of Sokoban tileset
FLOOR_COMMON = 0      # 95% of floors
FLOOR_SPECKLE1 = 12   # 4% of floors
FLOOR_SPECKLE2 = 24   # 1% of floors
WALL_TILE = 40        # Wall sprite
PLAYER_SPRITE = 84    # Player character
RAT_SPRITE = 123      # Enemy/rat creature

def file_to_base64(file_path):
    """Convert any image file to base64 string."""
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def llm_chat_completion(messages: list):
    """Chat completion endpoint of local LLM"""
    try:
        response = requests.post(VLLM_URL, json={'messages': messages}, timeout=60)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def message_with_image(text, image_path):
    """Create a message with an embedded image for vision models."""
    image_data = file_to_base64(image_path)
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image_data}}
        ]
    }

def get_floor_tile():
    """Return a floor tile sprite with realistic distribution."""
    roll = random.random()
    if roll < 0.95:
        return FLOOR_COMMON
    elif roll < 0.99:
        return FLOOR_SPECKLE1
    else:
        return FLOOR_SPECKLE2

def setup_scene():
    """Create a dungeon scene with player agent and NPC rat."""
    print("Setting up scene...")

    # Create and set scene
    vllm_demo = mcrfpy.Scene("vllm_demo")
    vllm_demo.activate()
    ui = vllm_demo.children

    # Load the game texture (16x16 tiles from Crypt of Sokoban)
    texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)

    # Create grid: 1014px wide at position (5,5)
    # Using 20x15 grid for a reasonable dungeon size
    grid = mcrfpy.Grid(
        grid_size=(20, 15),
        texture=texture,
        pos=(5, 5),
        size=(1014, 700)
    )
    grid.fill_color = mcrfpy.Color(20, 20, 30)

    # Set zoom factor to 2.0 for better visibility
    grid.zoom = 2.0

    ui.append(grid)

    # Set up floor tiles and walls with proper sprite distribution
    for x in range(20):
        for y in range(15):
            point = grid.at(x, y)
            # Create walls around the edges
            if x == 0 or x == 19 or y == 0 or y == 14:
                point.tilesprite = WALL_TILE
                point.walkable = False
                point.transparent = False  # Walls block FOV
            else:
                # Floor inside with varied sprites
                point.tilesprite = get_floor_tile()
                point.walkable = True
                point.transparent = True  # Floors don't block FOV

    # Add some interior walls for interest - a room divider
    for y in range(5, 10):
        point = grid.at(10, y)
        point.tilesprite = WALL_TILE
        point.walkable = False
        point.transparent = False
    # Door opening
    door = grid.at(10, 7)
    door.tilesprite = get_floor_tile()
    door.walkable = True
    door.transparent = True

    # Create a ColorLayer for fog of war (z_index=10 to render on top)
    fov_layer = grid.add_layer('color', z_index=10)
    fov_layer.fill(mcrfpy.Color(0, 0, 0, 255))  # Start all black (unknown)

    # Create the player entity ("The Agent")
    player = mcrfpy.Entity(grid_pos=(5, 7), texture=texture, sprite_index=PLAYER_SPRITE)
    grid.entities.append(player)

    # Create an NPC rat entity (closer so it's visible in FOV)
    rat = mcrfpy.Entity(grid_pos=(10, 7), texture=texture, sprite_index=RAT_SPRITE)
    grid.entities.append(rat)

    # Bind the fog layer to player's perspective
    # visible = transparent, discovered = dim, unknown = black
    fov_layer.apply_perspective(
        entity=player,
        visible=mcrfpy.Color(0, 0, 0, 0),           # Transparent when visible
        discovered=mcrfpy.Color(40, 40, 60, 180),   # Dark overlay when discovered but not visible
        unknown=mcrfpy.Color(0, 0, 0, 255)          # Black when never seen
    )

    # Update visibility from player's position
    player.update_visibility()

    # Center the camera on the agent entity
    px, py = int(player.pos[0]), int(player.pos[1])
    grid.center = (px * 16 + 8, py * 16 + 8)

    return grid, player, rat

def check_entity_visible(grid, entity):
    """Check if an entity is within the current FOV."""
    ex, ey = int(entity.pos[0]), int(entity.pos[1])
    return grid.is_in_fov(ex, ey)

def build_grounded_prompt(grid, player, rat):
    """Build a text prompt with visually grounded information."""
    observations = []

    # Check what the agent can see
    if check_entity_visible(grid, rat):
        observations.append("You see a rat to the east.")

    # Could add more observations here:
    # - walls blocking path
    # - items on ground
    # - doors/exits

    if not observations:
        observations.append("The area appears clear.")

    return " ".join(observations)

def run_demo():
    """Main demo function."""
    print("=" * 60)
    print("VLLM Integration Demo (Research Mode)")
    print("=" * 60)
    print()

    # Setup the scene
    grid, player, rat = setup_scene()

    # Advance simulation to ensure scene is ready
    mcrfpy.step(0.016)

    # Take screenshot
    print(f"Taking screenshot: {SCREENSHOT_PATH}")
    result = automation.screenshot(SCREENSHOT_PATH)
    if not result:
        print("ERROR: Failed to take screenshot")
        return False

    file_size = os.path.getsize(SCREENSHOT_PATH)
    print(f"Screenshot saved: {file_size} bytes")
    print()

    # Build grounded observations
    grounded_text = build_grounded_prompt(grid, player, rat)
    print(f"Grounded observations: {grounded_text}")
    print()

    # Query 1: Ask VLLM to describe what it sees
    print("-" * 40)
    print("Query 1: Describe what you see")
    print("-" * 40)

    system_prompt = """You are an AI agent in a roguelike dungeon game. You can see the game world through screenshots.
The view shows a top-down grid-based dungeon with tiles, walls, and creatures.
Your character is the humanoid figure. The dark areas are outside your field of vision.
Other creatures may be enemies or NPCs. Describe what you observe concisely."""

    user_prompt = f"""Look at this game screenshot. {grounded_text}

Describe what you see in the dungeon from your character's perspective.
Be specific about:
- Your position in the room
- Any creatures you can see
- The layout of walls and passages
- Areas obscured by fog of war (darkness)"""

    messages = [
        {"role": "system", "content": system_prompt},
        message_with_image(user_prompt, SCREENSHOT_PATH)
    ]

    resp = llm_chat_completion(messages)

    if "error" in resp:
        print(f"VLLM Error: {resp['error']}")
        print("\nNote: The VLLM server may not be running or accessible.")
        print("Screenshot is saved for manual inspection.")
        description = "I can see a dungeon scene."
    else:
        description = resp.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
        print(f"\nVLLM Response:\n{description}")
    print()

    # Query 2: Ask what action the agent would like to take
    print("-" * 40)
    print("Query 2: What would you like to do?")
    print("-" * 40)

    messages.append({"role": "assistant", "content": description})
    messages.append({
        "role": "user",
        "content": f"""Based on what you see, what action would you like to take?

Available actions:
- GO NORTH / SOUTH / EAST / WEST - move in that direction
- WAIT - stay in place and observe
- LOOK - examine your surroundings more carefully

{grounded_text}

State your reasoning briefly, then declare your action clearly (e.g., "Action: GO EAST")."""
    })

    resp = llm_chat_completion(messages)

    if "error" in resp:
        print(f"VLLM Error: {resp['error']}")
    else:
        action = resp.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
        print(f"\nVLLM Response:\n{action}")
    print()

    print("=" * 60)
    print("Demo Complete")
    print("=" * 60)
    print(f"\nScreenshot preserved at: {SCREENSHOT_PATH}")
    print("Grid settings: zoom=2.0, FOV radius=8, perspective rendering enabled")

    return True

# Main execution
if __name__ == "__main__":
    try:
        success = run_demo()
        if success:
            print("\nPASS")
            sys.exit(0)
        else:
            print("\nFAIL")
            sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
