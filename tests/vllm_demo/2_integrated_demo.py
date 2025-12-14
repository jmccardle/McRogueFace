#!/usr/bin/env python3
"""
Integrated VLLM Demo
====================

Combines:
- WorldGraph for structured room descriptions (#155)
- Action parsing and execution (#156)
- Per-agent perspective rendering

This is the foundation for multi-turn simulation.
"""

import sys
import os
# Add the vllm_demo directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mcrfpy
from mcrfpy import automation
import requests
import base64

from world_graph import (
    WorldGraph, Room, Door, WorldObject, Direction, AgentInfo,
    create_two_room_scenario
)
from action_parser import parse_action, ActionType
from action_executor import ActionExecutor

# Configuration
VLLM_URL = "http://192.168.1.100:8100/v1/chat/completions"
SCREENSHOT_DIR = "/tmp/vllm_integrated"

# Sprite constants
FLOOR_TILE = 0
WALL_TILE = 40
WIZARD_SPRITE = 84
KNIGHT_SPRITE = 96


class Agent:
    """Agent wrapper with WorldGraph integration."""

    def __init__(self, name: str, display_name: str, entity, world: WorldGraph):
        self.name = name
        self.display_name = display_name
        self.entity = entity
        self.world = world
        self.message_history = []  # For speech system (future)

    @property
    def pos(self) -> tuple:
        return (int(self.entity.pos[0]), int(self.entity.pos[1]))

    @property
    def current_room(self) -> str:
        """Get the name of the room this agent is in."""
        room = self.world.room_at(*self.pos)
        return room.name if room else None

    def get_context(self, visible_agents: list) -> dict:
        """
        Build complete context for LLM query.

        Args:
            visible_agents: List of Agent objects visible to this agent

        Returns:
            Dict with location description, available actions, messages
        """
        room_name = self.current_room

        # Convert Agent objects to AgentInfo for WorldGraph
        agent_infos = [
            AgentInfo(
                name=a.name,
                display_name=a.display_name,
                position=a.pos,
                is_player=(a.name == self.name)
            )
            for a in visible_agents
        ]

        return {
            "location": self.world.describe_room(
                room_name,
                visible_agents=agent_infos,
                observer_name=self.name
            ),
            "available_actions": self.world.get_available_actions(room_name),
            "recent_messages": self.message_history[-5:],
        }


def file_to_base64(file_path):
    """Convert image file to base64 string."""
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def llm_chat_completion(messages: list):
    """Send chat completion request to local LLM."""
    try:
        response = requests.post(VLLM_URL, json={'messages': messages}, timeout=60)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def message_with_image(text, image_path):
    """Create a message with embedded image for vision models."""
    image_data = file_to_base64(image_path)
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image_data}}
        ]
    }


def setup_scene_from_world(world: WorldGraph):
    """
    Create McRogueFace scene from WorldGraph.

    Carves out rooms and places doors based on WorldGraph data.
    """
    mcrfpy.createScene("integrated_demo")
    mcrfpy.setScene("integrated_demo")
    ui = mcrfpy.sceneUI("integrated_demo")

    texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)

    # Create grid sized for the world (with margin)
    grid = mcrfpy.Grid(
        grid_size=(25, 15),
        texture=texture,
        pos=(5, 5),
        size=(1014, 700)
    )
    grid.fill_color = mcrfpy.Color(20, 20, 30)
    grid.zoom = 2.0
    ui.append(grid)

    # Initialize all tiles as walls
    for x in range(25):
        for y in range(15):
            point = grid.at(x, y)
            point.tilesprite = WALL_TILE
            point.walkable = False
            point.transparent = False

    # Carve out rooms from WorldGraph
    for room in world.rooms.values():
        for rx in range(room.x, room.x + room.width):
            for ry in range(room.y, room.y + room.height):
                if 0 <= rx < 25 and 0 <= ry < 15:
                    point = grid.at(rx, ry)
                    point.tilesprite = FLOOR_TILE
                    point.walkable = True
                    point.transparent = True

    # Place doors (carve corridor between rooms)
    for door in world.doors:
        dx, dy = door.position
        if 0 <= dx < 25 and 0 <= dy < 15:
            point = grid.at(dx, dy)
            point.tilesprite = FLOOR_TILE
            point.walkable = not door.locked
            point.transparent = True

    # Create FOV layer for fog of war
    fov_layer = grid.add_layer('color', z_index=10)
    fov_layer.fill(mcrfpy.Color(0, 0, 0, 255))

    return grid, fov_layer, texture


def create_agents(grid, world: WorldGraph, texture) -> list:
    """Create agent entities in their starting rooms."""
    agents = []

    # Agent A: Wizard in guard_room
    guard_room = world.rooms["guard_room"]
    wizard_entity = mcrfpy.Entity(
        grid_pos=guard_room.center,
        texture=texture,
        sprite_index=WIZARD_SPRITE
    )
    grid.entities.append(wizard_entity)
    agents.append(Agent("Wizard", "a wizard", wizard_entity, world))

    # Agent B: Knight in armory
    armory = world.rooms["armory"]
    knight_entity = mcrfpy.Entity(
        grid_pos=armory.center,
        texture=texture,
        sprite_index=KNIGHT_SPRITE
    )
    grid.entities.append(knight_entity)
    agents.append(Agent("Knight", "a knight", knight_entity, world))

    return agents


def switch_perspective(grid, fov_layer, agent):
    """Switch grid view to an agent's perspective."""
    # Reset fog layer to all unknown (black)
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


def get_visible_agents(grid, observer, all_agents) -> list:
    """Get agents visible to the observer based on FOV."""
    visible = []
    for agent in all_agents:
        if agent.name == observer.name:
            continue
        ax, ay = agent.pos
        if grid.is_in_fov(ax, ay):
            visible.append(agent)
    return visible


def query_agent_llm(agent, screenshot_path, context) -> str:
    """
    Query VLLM for agent's action using WorldGraph context.

    This uses the structured context from WorldGraph instead of
    ad-hoc grounded prompts.
    """
    system_prompt = f"""You are {agent.display_name} in a roguelike dungeon game.
You see the world through screenshots and receive text descriptions.
Your goal is to explore and interact with your environment.
Always end your response with a clear action declaration: "Action: <ACTION>"
"""

    # Build the user prompt with WorldGraph context
    actions_str = ", ".join(context["available_actions"])

    user_prompt = f"""{context["location"]}

Available actions: {actions_str}

Look at the screenshot showing your current view. The dark areas are outside your field of vision.

What would you like to do? State your reasoning briefly (1-2 sentences), then declare your action.
Example: "I see a key on the ground that might be useful. Action: TAKE brass_key"
"""

    messages = [
        {"role": "system", "content": system_prompt},
        message_with_image(user_prompt, screenshot_path)
    ]

    resp = llm_chat_completion(messages)

    if "error" in resp:
        return f"[VLLM Error: {resp['error']}]"
    return resp.get('choices', [{}])[0].get('message', {}).get('content', 'No response')


def run_single_turn(grid, fov_layer, agents, executor, turn_num):
    """
    Execute one turn for all agents.

    Each agent:
    1. Gets their perspective rendered
    2. Receives WorldGraph context
    3. Queries LLM for action
    4. Executes the action
    """
    print(f"\n{'='*70}")
    print(f"TURN {turn_num}")
    print("=" * 70)

    results = []

    for agent in agents:
        print(f"\n--- {agent.name}'s Turn ---")
        print(f"Position: {agent.pos} | Room: {agent.current_room}")

        # Switch perspective to this agent
        switch_perspective(grid, fov_layer, agent)
        mcrfpy.step(0.016)

        # Take screenshot
        screenshot_path = os.path.join(
            SCREENSHOT_DIR,
            f"turn{turn_num}_{agent.name.lower()}.png"
        )
        automation.screenshot(screenshot_path)
        print(f"Screenshot: {screenshot_path}")

        # Get context using WorldGraph
        visible = get_visible_agents(grid, agent, agents)
        context = agent.get_context(visible + [agent])  # Include self for filtering

        print(f"\nContext from WorldGraph:")
        print(f"  Location: {context['location']}")
        print(f"  Actions: {context['available_actions']}")

        # Query LLM
        print(f"\nQuerying VLLM...")
        response = query_agent_llm(agent, screenshot_path, context)
        print(f"Response: {response[:300]}{'...' if len(response) > 300 else ''}")

        # Parse and execute action
        action = parse_action(response)
        print(f"\nParsed: {action.type.value} {action.args}")

        result = executor.execute(agent, action)
        status = "SUCCESS" if result.success else "FAILED"
        print(f"Result: {status} - {result.message}")

        results.append({
            "agent": agent.name,
            "room": agent.current_room,
            "context": context,
            "response": response,
            "action": action,
            "result": result
        })

    return results


def run_demo():
    """Main demo: single integrated turn with WorldGraph context."""
    print("=" * 70)
    print("Integrated WorldGraph + Action Demo")
    print("=" * 70)

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # Create world from WorldGraph factory
    print("\nCreating world from WorldGraph...")
    world = create_two_room_scenario()
    print(f"  Rooms: {list(world.rooms.keys())}")
    print(f"  Doors: {len(world.doors)}")
    print(f"  Objects: {list(world.objects.keys())}")

    # Setup scene from WorldGraph
    print("\nSetting up scene...")
    grid, fov_layer, texture = setup_scene_from_world(world)

    # Create agents
    print("\nCreating agents...")
    agents = create_agents(grid, world, texture)
    for agent in agents:
        print(f"  {agent.name} at {agent.pos} in {agent.current_room}")

    # Create executor
    executor = ActionExecutor(grid)

    # Run one turn
    results = run_single_turn(grid, fov_layer, agents, executor, turn_num=1)

    # Summary
    print("\n" + "=" * 70)
    print("TURN SUMMARY")
    print("=" * 70)
    for r in results:
        status = "OK" if r["result"].success else "FAIL"
        print(f"  {r['agent']}: {r['action'].type.value} -> {status}")
        if r["result"].new_position:
            print(f"    New position: {r['result'].new_position}")

    print("\n" + "=" * 70)
    print("Demo Complete")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = run_demo()
        print("\nPASS" if success else "\nFAIL")
        sys.exit(0 if success else 1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
