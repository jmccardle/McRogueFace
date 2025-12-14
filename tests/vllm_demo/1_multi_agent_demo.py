#!/usr/bin/env python3
"""
Multi-Agent VLLM Demo for McRogueFace
=====================================

Demonstrates cycling through multiple agent perspectives,
each with their own FOV and grounded observations.

Three agents:
- Wizard (left side) - can see the rat but not the other agents
- Blacksmith (right side) - can see the knight, rat, and the wall
- Knight (right side) - can see the blacksmith, rat, and the wall

Each agent gets their own screenshot and VLLM query.
"""

import mcrfpy
from mcrfpy import automation
import sys
import requests
import base64
import os
import random

from action_parser import parse_action
from action_executor import ActionExecutor

# VLLM configuration
VLLM_URL = "http://192.168.1.100:8100/v1/chat/completions"
SCREENSHOT_DIR = "/tmp/vllm_multi_agent"

# Sprite constants
FLOOR_COMMON = 0
FLOOR_SPECKLE1 = 12
FLOOR_SPECKLE2 = 24
WALL_TILE = 40

# Agent sprites
WIZARD_SPRITE = 84
BLACKSMITH_SPRITE = 86
KNIGHT_SPRITE = 96
RAT_SPRITE = 123


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


class Agent:
    """Wrapper for an agent entity with metadata."""
    def __init__(self, name, entity, description):
        self.name = name
        self.entity = entity
        self.description = description  # e.g., "a wizard", "a blacksmith"

    @property
    def pos(self):
        return (int(self.entity.pos[0]), int(self.entity.pos[1]))


def setup_scene():
    """Create a dungeon scene with multiple agents."""
    print("Setting up multi-agent scene...")

    # Create and set scene
    mcrfpy.createScene("multi_agent_demo")
    mcrfpy.setScene("multi_agent_demo")
    ui = mcrfpy.sceneUI("multi_agent_demo")

    # Load the game texture
    texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)

    # Create grid
    grid = mcrfpy.Grid(
        grid_size=(25, 15),
        texture=texture,
        pos=(5, 5),
        size=(1014, 700)
    )
    grid.fill_color = mcrfpy.Color(20, 20, 30)
    grid.zoom = 2.0
    ui.append(grid)

    # Set up floor tiles and walls
    for x in range(25):
        for y in range(15):
            point = grid.at(x, y)
            if x == 0 or x == 24 or y == 0 or y == 14:
                point.tilesprite = WALL_TILE
                point.walkable = False
                point.transparent = False
            else:
                point.tilesprite = get_floor_tile()
                point.walkable = True
                point.transparent = True

    # Add a wall divider in the middle (blocks wizard's view of right side)
    for y in range(3, 12):
        point = grid.at(10, y)
        point.tilesprite = WALL_TILE
        point.walkable = False
        point.transparent = False

    # Door opening in the wall
    door = grid.at(10, 7)
    door.tilesprite = get_floor_tile()
    door.walkable = True
    door.transparent = True

    # Create FOV layer for fog of war
    fov_layer = grid.add_layer('color', z_index=10)
    fov_layer.fill(mcrfpy.Color(0, 0, 0, 255))

    # Create agents
    agents = []

    # Wizard on the left side
    wizard_entity = mcrfpy.Entity(grid_pos=(4, 7), texture=texture, sprite_index=WIZARD_SPRITE)
    grid.entities.append(wizard_entity)
    agents.append(Agent("Wizard", wizard_entity, "a wizard"))

    # Blacksmith on the right side (upper)
    blacksmith_entity = mcrfpy.Entity(grid_pos=(18, 5), texture=texture, sprite_index=BLACKSMITH_SPRITE)
    grid.entities.append(blacksmith_entity)
    agents.append(Agent("Blacksmith", blacksmith_entity, "a blacksmith"))

    # Knight on the right side (lower)
    knight_entity = mcrfpy.Entity(grid_pos=(18, 10), texture=texture, sprite_index=KNIGHT_SPRITE)
    grid.entities.append(knight_entity)
    agents.append(Agent("Knight", knight_entity, "a knight"))

    # Rat in the middle-right area (visible to blacksmith and knight, maybe wizard through door)
    rat_entity = mcrfpy.Entity(grid_pos=(14, 7), texture=texture, sprite_index=RAT_SPRITE)
    grid.entities.append(rat_entity)

    return grid, fov_layer, agents, rat_entity


def switch_perspective(grid, fov_layer, agent):
    """Switch the grid view to an agent's perspective."""
    # Reset fog layer to all unknown (black) before switching
    # This prevents discovered tiles from one agent carrying over to another
    fov_layer.fill(mcrfpy.Color(0, 0, 0, 255))

    # Apply this agent's perspective
    fov_layer.apply_perspective(
        entity=agent.entity,
        visible=mcrfpy.Color(0, 0, 0, 0),
        discovered=mcrfpy.Color(40, 40, 60, 180),
        unknown=mcrfpy.Color(0, 0, 0, 255)
    )

    # Update visibility from agent's position
    agent.entity.update_visibility()

    # Center camera on this agent
    px, py = agent.pos
    grid.center = (px * 16 + 8, py * 16 + 8)


def get_visible_entities(grid, observer, all_agents, rat):
    """Get list of entities visible to the observer."""
    visible = []
    ox, oy = observer.pos

    # Check rat visibility
    rx, ry = int(rat.pos[0]), int(rat.pos[1])
    if grid.is_in_fov(rx, ry):
        # Determine direction
        direction = get_direction(ox, oy, rx, ry)
        visible.append(f"a rat to the {direction}")

    # Check other agents
    for agent in all_agents:
        if agent.name == observer.name:
            continue
        ax, ay = agent.pos
        if grid.is_in_fov(ax, ay):
            direction = get_direction(ox, oy, ax, ay)
            visible.append(f"{agent.description} to the {direction}")

    return visible


def get_direction(from_x, from_y, to_x, to_y):
    """Get cardinal direction from one point to another."""
    dx = to_x - from_x
    dy = to_y - from_y

    # Primary direction
    if abs(dx) > abs(dy):
        return "east" if dx > 0 else "west"
    elif abs(dy) > abs(dx):
        return "south" if dy > 0 else "north"
    else:
        # Diagonal - pick one
        ns = "south" if dy > 0 else "north"
        ew = "east" if dx > 0 else "west"
        return f"{ns}{ew}"


def build_grounded_prompt(visible_entities):
    """Build grounded text from visible entities."""
    if not visible_entities:
        return "The area appears clear."

    if len(visible_entities) == 1:
        return f"You see {visible_entities[0]}."
    else:
        items = ", ".join(visible_entities[:-1]) + f" and {visible_entities[-1]}"
        return f"You see {items}."


def query_agent(agent, screenshot_path, grounded_text):
    """Query VLLM for a single agent's perspective."""
    system_prompt = f"""You are {agent.description} in a roguelike dungeon game. You can see the game world through screenshots.
The view shows a top-down grid-based dungeon. Your character is centered in the view.
The dark areas are outside your field of vision. Other figures may be allies, enemies, or NPCs.
Describe what you observe concisely and decide on an action."""

    user_prompt = f"""Look at this game screenshot from your perspective as {agent.description}. {grounded_text}

Describe what you see briefly, then choose an action:
- GO NORTH / SOUTH / EAST / WEST
- WAIT
- LOOK

State your reasoning in 1-2 sentences, then declare: "Action: <YOUR_ACTION>" """

    messages = [
        {"role": "system", "content": system_prompt},
        message_with_image(user_prompt, screenshot_path)
    ]

    resp = llm_chat_completion(messages)

    if "error" in resp:
        return f"VLLM Error: {resp['error']}"
    else:
        return resp.get('choices', [{}])[0].get('message', {}).get('content', 'No response')


def run_demo():
    """Main demo function."""
    print("=" * 70)
    print("Multi-Agent VLLM Demo")
    print("=" * 70)
    print()

    # Create screenshot directory
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # Setup scene
    grid, fov_layer, agents, rat = setup_scene()

    # Create action executor
    executor = ActionExecutor(grid)

    # Cycle through each agent's perspective
    for i, agent in enumerate(agents):
        print(f"\n{'='*70}")
        print(f"Agent {i+1}/3: {agent.name} ({agent.description})")
        print(f"Position: {agent.pos}")
        print("=" * 70)

        # Switch to this agent's perspective
        switch_perspective(grid, fov_layer, agent)

        # Advance simulation
        mcrfpy.step(0.016)

        # Take screenshot
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"{i}_{agent.name.lower()}_view.png")
        result = automation.screenshot(screenshot_path)
        if not result:
            print(f"ERROR: Failed to take screenshot for {agent.name}")
            continue

        file_size = os.path.getsize(screenshot_path)
        print(f"Screenshot: {screenshot_path} ({file_size} bytes)")

        # Get visible entities for this agent
        visible = get_visible_entities(grid, agent, agents, rat)
        grounded_text = build_grounded_prompt(visible)
        print(f"Grounded observations: {grounded_text}")

        # Query VLLM
        print(f"\nQuerying VLLM for {agent.name}...")
        print("-" * 50)
        response = query_agent(agent, screenshot_path, grounded_text)
        print(f"\n{agent.name}'s Response:\n{response}")
        print()

        # Parse and execute action
        print(f"--- Action Execution ---")
        action = parse_action(response)
        print(f"Parsed action: {action.type.value} {action.args}")

        result = executor.execute(agent, action)
        if result.success:
            print(f"SUCCESS: {result.message}")
            if result.new_position:
                # Update perspective after movement
                switch_perspective(grid, fov_layer, agent)
                mcrfpy.step(0.016)
        else:
            print(f"FAILED: {result.message}")

    print("\n" + "=" * 70)
    print("Multi-Agent Demo Complete")
    print("=" * 70)
    print(f"\nScreenshots saved to: {SCREENSHOT_DIR}/")
    for i, agent in enumerate(agents):
        print(f"  - {i}_{agent.name.lower()}_view.png")

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
