#!/usr/bin/env python3
"""
Multi-Turn Simulation Demo
==========================

Runs multiple turns of agent interaction with full logging.
This is the Phase 1 implementation from issue #154.

Two agents start in separate rooms and can move, observe,
and (in future versions) communicate to solve puzzles.
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
    create_two_room_scenario, create_button_door_scenario
)
from action_parser import parse_action
from action_executor import ActionExecutor
from turn_orchestrator import TurnOrchestrator, SimulationLog

# Configuration
VLLM_URL = "http://192.168.1.100:8100/v1/chat/completions"
SCREENSHOT_DIR = "/tmp/vllm_multi_turn"
LOG_PATH = "/tmp/vllm_multi_turn/simulation_log.json"
MAX_TURNS = 5

# Sprites
FLOOR_TILE = 0
WALL_TILE = 40
WIZARD_SPRITE = 84
KNIGHT_SPRITE = 96


class Agent:
    """Agent with WorldGraph integration."""

    def __init__(self, name: str, display_name: str, entity, world: WorldGraph):
        self.name = name
        self.display_name = display_name
        self.entity = entity
        self.world = world
        self.message_history = []

    @property
    def pos(self) -> tuple:
        return (int(self.entity.pos[0]), int(self.entity.pos[1]))

    @property
    def current_room(self) -> str:
        room = self.world.room_at(*self.pos)
        return room.name if room else None

    def get_context(self, visible_agents: list) -> dict:
        """Build context for LLM query."""
        room_name = self.current_room
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
            "location": self.world.describe_room(room_name, agent_infos, self.name),
            "available_actions": self.world.get_available_actions(room_name),
            "recent_messages": self.message_history[-5:],
        }


def file_to_base64(path: str) -> str:
    """Convert file to base64 string."""
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def llm_query(agent, screenshot_path: str, context: dict) -> str:
    """
    Query VLLM for agent action.

    This function is passed to TurnOrchestrator as the LLM query callback.
    """
    system_prompt = f"""You are {agent.display_name} exploring a dungeon.
You receive visual and text information about your surroundings.
Your goal is to explore, find items, and interact with the environment.
Always end your response with: Action: <YOUR_ACTION>"""

    actions_str = ", ".join(context["available_actions"])

    user_prompt = f"""{context["location"]}

Available actions: {actions_str}

[Screenshot attached showing your current view - dark areas are outside your vision]

What do you do? Brief reasoning (1-2 sentences), then Action: <action>"""

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {
                    "url": "data:image/png;base64," + file_to_base64(screenshot_path)
                }}
            ]
        }
    ]

    try:
        resp = requests.post(VLLM_URL, json={'messages': messages}, timeout=60)
        data = resp.json()
        if "error" in data:
            return f"[VLLM Error: {data['error']}]"
        return data.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
    except Exception as e:
        return f"[Connection Error: {e}]"


def setup_scene(world: WorldGraph):
    """Create McRogueFace scene from WorldGraph."""
    multi_turn = mcrfpy.Scene("multi_turn")
    multi_turn.activate()
    ui = multi_turn.children

    texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)

    grid = mcrfpy.Grid(
        grid_size=(25, 15),
        texture=texture,
        pos=(5, 5),
        size=(1014, 700)
    )
    grid.fill_color = mcrfpy.Color(20, 20, 30)
    grid.zoom = 2.0
    ui.append(grid)

    # Initialize all as walls
    for x in range(25):
        for y in range(15):
            p = grid.at(x, y)
            p.tilesprite = WALL_TILE
            p.walkable = False
            p.transparent = False

    # Carve rooms from WorldGraph
    for room in world.rooms.values():
        for rx in range(room.x, room.x + room.width):
            for ry in range(room.y, room.y + room.height):
                if 0 <= rx < 25 and 0 <= ry < 15:
                    p = grid.at(rx, ry)
                    p.tilesprite = FLOOR_TILE
                    p.walkable = True
                    p.transparent = True

    # Place doors
    for door in world.doors:
        dx, dy = door.position
        if 0 <= dx < 25 and 0 <= dy < 15:
            p = grid.at(dx, dy)
            p.tilesprite = FLOOR_TILE
            p.walkable = not door.locked
            p.transparent = True

    # FOV layer
    fov_layer = grid.add_layer('color', z_index=10)
    fov_layer.fill(mcrfpy.Color(0, 0, 0, 255))

    return grid, fov_layer, texture


def create_agents(grid, world: WorldGraph, texture) -> list:
    """Create agents in their starting rooms."""
    agents = []

    # Wizard in guard_room (left)
    room_a = world.rooms["guard_room"]
    wizard = mcrfpy.Entity(
        grid_pos=room_a.center,
        texture=texture,
        sprite_index=WIZARD_SPRITE
    )
    grid.entities.append(wizard)
    agents.append(Agent("Wizard", "a wizard", wizard, world))

    # Knight in armory (right)
    room_b = world.rooms["armory"]
    knight = mcrfpy.Entity(
        grid_pos=room_b.center,
        texture=texture,
        sprite_index=KNIGHT_SPRITE
    )
    grid.entities.append(knight)
    agents.append(Agent("Knight", "a knight", knight, world))

    return agents


def run_demo():
    """Run multi-turn simulation."""
    print("=" * 70)
    print("Multi-Turn Simulation Demo")
    print(f"Running up to {MAX_TURNS} turns with 2 agents")
    print("=" * 70)

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # Create world
    print("\nCreating world...")
    world = create_two_room_scenario()
    print(f"  Rooms: {list(world.rooms.keys())}")
    print(f"  Objects: {list(world.objects.keys())}")

    # Setup scene
    print("\nSetting up scene...")
    grid, fov_layer, texture = setup_scene(world)

    # Create agents
    print("\nCreating agents...")
    agents = create_agents(grid, world, texture)
    for agent in agents:
        print(f"  {agent.name} at {agent.pos} in {agent.current_room}")

    # Create orchestrator
    orchestrator = TurnOrchestrator(
        grid=grid,
        fov_layer=fov_layer,
        world=world,
        agents=agents,
        screenshot_dir=SCREENSHOT_DIR,
        llm_query_fn=llm_query
    )

    # Optional: Define a stop condition
    def agents_met(orch):
        """Stop when agents are in the same room."""
        return orch.agents_in_same_room()

    # Run simulation
    log = orchestrator.run_simulation(
        max_turns=MAX_TURNS,
        stop_condition=None  # Or use agents_met for early stopping
    )

    # Save log
    log.save(LOG_PATH)

    # Print summary
    print("\n" + "=" * 70)
    print(log.summary())
    print("=" * 70)

    # Show final positions
    print("\nFinal Agent Positions:")
    for agent in agents:
        print(f"  {agent.name}: {agent.pos} in {agent.current_room}")

    print(f"\nScreenshots saved to: {SCREENSHOT_DIR}/")
    print(f"Simulation log saved to: {LOG_PATH}")

    return True


def replay_log(log_path: str):
    """
    Replay a simulation from a log file.

    This is a utility function for reviewing past simulations.
    """
    print(f"Loading simulation from: {log_path}")
    log = SimulationLog.load(log_path)

    print("\n" + log.summary())

    print("\nTurn-by-Turn Replay:")
    print("-" * 50)

    current_turn = 0
    for step in log.steps:
        if step.turn != current_turn:
            current_turn = step.turn
            print(f"\n=== Turn {current_turn} ===")

        status = "OK" if step.result_success else "FAIL"
        print(f"  {step.agent_id}: {step.parsed_action_type} {step.parsed_action_args}")
        print(f"    {status}: {step.result_message}")
        if step.new_position:
            print(f"    Moved to: {step.new_position}")


if __name__ == "__main__":
    # Check for replay mode
    if len(sys.argv) > 1 and sys.argv[1] == "--replay":
        log_file = sys.argv[2] if len(sys.argv) > 2 else LOG_PATH
        replay_log(log_file)
        sys.exit(0)

    # Normal execution
    try:
        success = run_demo()
        print("\nPASS" if success else "\nFAIL")
        sys.exit(0 if success else 1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
