#!/usr/bin/env python3
"""
Enhanced Action Demo
====================

Demonstrates the enhanced action economy system:
- Free actions (LOOK, SPEAK/ANNOUNCE) vs turn-ending (MOVE, WAIT)
- Points of interest targeting for LOOK/MOVE
- Speech system with room-wide ANNOUNCE and proximity SPEAK
- Multi-tile path continuation with FOV interrupts
- Enhanced logging for offline viewer replay

This implements the turn-based LLM agent orchestration from issue #156.
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
from enhanced_executor import EnhancedExecutor
from enhanced_orchestrator import EnhancedOrchestrator, EnhancedSimulationLog

# Configuration
VLLM_URL = "http://192.168.1.100:8100/v1/chat/completions"
SCREENSHOT_DIR = "/tmp/vllm_enhanced_demo"
LOG_PATH = "/tmp/vllm_enhanced_demo/simulation_log.json"
MAX_TURNS = 3

# Sprites
FLOOR_TILE = 0
WALL_TILE = 40
WIZARD_SPRITE = 84
KNIGHT_SPRITE = 96
RAT_SPRITE = 123


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
    Query VLLM for agent action with enhanced context.

    Includes points of interest, action economy hints, error feedback,
    and conversation history.
    """
    system_prompt = f"""You are {agent.display_name} exploring a dungeon.
You receive visual and text information about your surroundings.

ACTION ECONOMY:
- LOOK <target>: Free action. Examine something, then choose another action.
- SPEAK "<message>" or ANNOUNCE "<message>": Free action (once per turn). Then choose another action.
- GO <direction>: Ends your turn. Move one tile in that direction (NORTH/SOUTH/EAST/WEST).
- TAKE <item>: Ends your turn. Pick up an item you are standing next to.
- WAIT: Ends your turn without moving.

IMPORTANT: You can only TAKE items that are adjacent to you (1 tile away). If something is far away, GO towards it first.

You can LOOK or SPEAK, then still MOVE in the same turn.
Always end your final response with: Action: <YOUR_ACTION>"""

    # Build enhanced prompt
    parts = [context["location"]]

    # Add received messages
    if context.get("messages"):
        parts.append("\nMessages received this turn:")
        for msg in context["messages"]:
            sender = msg.get("sender", "someone")
            content = msg.get("content", "")
            parts.append(f'  {sender} says: "{content}"')

    # Add points of interest
    if context.get("poi_prompt"):
        parts.append(f"\n{context['poi_prompt']}")

    # Add available actions
    actions_str = ", ".join(context.get("available_actions", []))
    parts.append(f"\nAvailable actions: {actions_str}")

    # Add action economy hint
    if context.get("has_spoken"):
        parts.append("\n[You have already spoken this turn - you can still MOVE or WAIT]")

    # Add error feedback from last failed action
    if context.get("last_error"):
        parts.append(f"\n[ERROR: {context['last_error']}]")
        parts.append("[Your last action failed. Please try a different action.]")

    # Add conversation history from this turn
    if context.get("conversation_history"):
        parts.append("\n[Previous attempts this turn:")
        for exch in context["conversation_history"]:
            action_str = f"{exch.get('action_type', '?')} {exch.get('action_args', '')}"
            if exch.get("error"):
                parts.append(f"  - You tried: {action_str} -> FAILED: {exch['error']}")
            else:
                parts.append(f"  - You did: {action_str}")
        parts.append("]")

    parts.append("\n[Screenshot attached showing your current view]")
    parts.append("\nWhat do you do? Brief reasoning (1-2 sentences), then Action: <action>")

    user_prompt = "\n".join(parts)

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
    enhanced_demo = mcrfpy.Scene("enhanced_demo")
    enhanced_demo.activate()
    ui = enhanced_demo.children

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
    wizard.name = "wizard"
    grid.entities.append(wizard)
    agents.append(Agent("Wizard", "a wizard", wizard, world))

    # Knight in armory (right)
    room_b = world.rooms["armory"]
    knight = mcrfpy.Entity(
        grid_pos=room_b.center,
        texture=texture,
        sprite_index=KNIGHT_SPRITE
    )
    knight.name = "knight"
    grid.entities.append(knight)
    agents.append(Agent("Knight", "a knight", knight, world))

    return agents


def add_rat(grid, world: WorldGraph, texture, position: tuple):
    """Add a rat entity at the specified position."""
    rat = mcrfpy.Entity(
        grid_pos=position,
        texture=texture,
        sprite_index=RAT_SPRITE
    )
    rat.name = "rat"
    grid.entities.append(rat)
    return rat


def run_demo():
    """Run enhanced action demo."""
    print("=" * 70)
    print("Enhanced Action Demo")
    print("=" * 70)
    print("""
Features demonstrated:
- LOOK as free action (doesn't end turn)
- SPEAK/ANNOUNCE as free action (once per turn)
- Points of interest targeting
- Enhanced logging for offline viewer
""")

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # Create world
    print("Creating world...")
    world = create_two_room_scenario()
    print(f"  Rooms: {list(world.rooms.keys())}")
    print(f"  Objects: {list(world.objects.keys())}")

    # Setup scene
    print("\nSetting up scene...")
    grid, fov_layer, texture = setup_scene(world)

    # Create agents
    print("\nCreating agents...")
    agents = create_agents(grid, world, texture)

    # Add a rat near the door for interest
    rat = add_rat(grid, world, texture, (9, 4))
    print(f"  Added rat at (9, 4)")

    for agent in agents:
        print(f"  {agent.name} at {agent.pos} in {agent.current_room}")

    # Create enhanced orchestrator
    print("\nInitializing enhanced orchestrator...")
    orchestrator = EnhancedOrchestrator(
        grid=grid,
        fov_layer=fov_layer,
        world=world,
        agents=agents,
        screenshot_dir=SCREENSHOT_DIR,
        llm_query_fn=llm_query
    )

    # Run simulation
    print(f"\nRunning simulation ({MAX_TURNS} turns)...")
    log = orchestrator.run_simulation(max_turns=MAX_TURNS)

    # Save enhanced log
    log.save(LOG_PATH)

    # Print summary
    print("\n" + "=" * 70)
    print("SIMULATION SUMMARY")
    print("=" * 70)

    for turn in range(1, orchestrator.turn_number + 1):
        print(log.get_turn_summary(turn))

    # Print speech log
    if log.speech_log:
        print("\n" + "-" * 40)
        print("SPEECH LOG")
        print("-" * 40)
        for entry in log.speech_log:
            print(f"  Turn {entry['turn']}: {entry['speaker']} {entry['type']}s: \"{entry['content'][:50]}...\"")
            if entry['recipients']:
                print(f"    -> Heard by: {', '.join(entry['recipients'])}")

    print("\n" + "=" * 70)
    print("Demo Complete")
    print("=" * 70)
    print(f"\nScreenshots saved to: {SCREENSHOT_DIR}/")
    print(f"Simulation log saved to: {LOG_PATH}")
    print("\nLog structure (for offline viewer):")
    print("  - metadata: simulation info")
    print("  - steps[]: per-agent-turn records with:")
    print("    - screenshot_path, position, room")
    print("    - llm_prompt_user, llm_response")
    print("    - free_actions[] (LOOK, SPEAK)")
    print("    - final_action (MOVE, WAIT)")
    print("  - speech_log[]: all speech events")

    return True


def replay_log(log_path: str):
    """
    Replay a simulation from log file.

    This is a text-based preview of what the offline viewer would show.
    """
    print(f"Loading simulation from: {log_path}")

    try:
        log = EnhancedSimulationLog.load(log_path)
    except FileNotFoundError:
        print(f"Log file not found: {log_path}")
        return

    print("\n" + "=" * 70)
    print("SIMULATION REPLAY")
    print("=" * 70)
    print(f"Turns: {log.metadata.get('total_turns', '?')}")
    print(f"Agents: {', '.join(log.metadata.get('agent_names', []))}")
    print(f"Rooms: {', '.join(log.metadata.get('world_rooms', []))}")

    for step in log.steps:
        print(f"\n{'='*40}")
        print(f"Turn {step.turn}: {step.agent_id}")
        print(f"{'='*40}")
        print(f"Position: {step.position_start} -> {step.position_end}")
        print(f"Room: {step.room}")

        if step.pending_messages:
            print(f"\nMessages received:")
            for msg in step.pending_messages:
                print(f"  {msg.get('sender')}: \"{msg.get('content', '')[:40]}...\"")

        if step.llm_was_queried:
            print(f"\nLLM Response (truncated):")
            print(f"  {step.llm_response[:200]}...")
        else:
            print(f"\n[Path continuation - no LLM query]")

        if step.free_actions:
            print(f"\nFree actions:")
            for fa in step.free_actions:
                print(f"  - {fa['action_type']}: {fa.get('args', ())}")

        status = "OK" if step.final_action_success else "FAIL"
        print(f"\nFinal: {step.final_action_type} {step.final_action_args} [{status}]")
        print(f"  {step.final_action_message}")

    # Speech summary
    if log.speech_log:
        print("\n" + "=" * 40)
        print("ALL SPEECH")
        print("=" * 40)
        for entry in log.speech_log:
            print(f"Turn {entry['turn']}: {entry['speaker']} -> {entry['recipients']}")
            print(f"  \"{entry['content']}\"")


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
