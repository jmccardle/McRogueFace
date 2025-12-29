"""
Enhanced Turn Orchestrator
==========================

Extends TurnOrchestrator with:
- Action economy (free actions vs turn-ending)
- Multi-tile path continuation
- FOV interrupt detection
- Enhanced logging for offline viewer replay
"""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Callable, Set
from datetime import datetime

from world_graph import WorldGraph, AgentInfo
from action_parser import Action, ActionType, parse_action
from action_executor import ActionResult
from action_economy import (
    TurnState, PathState, TurnCost, get_action_cost,
    PointOfInterestCollector, PointOfInterest
)
from enhanced_executor import EnhancedExecutor, LookResult, SpeechResult, Message, TakeResult


@dataclass
class FreeActionRecord:
    """Record of a free action taken during a turn."""
    action_type: str
    args: tuple
    result: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class EnhancedSimulationStep:
    """
    Enhanced simulation step for offline viewer replay.

    Contains all data needed to reconstruct the agent's perspective
    and decision-making for that turn.
    """
    # Turn identification
    turn: int
    agent_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Agent state at start of turn
    position_start: tuple = (0, 0)
    room: str = ""
    path_in_progress: bool = False

    # FOV and perception
    visible_entities: List[str] = field(default_factory=list)
    visible_tiles: int = 0  # Count of visible tiles
    points_of_interest: List[Dict] = field(default_factory=list)

    # Context provided to LLM
    location_description: str = ""
    available_actions: List[str] = field(default_factory=list)
    pending_messages: List[Dict] = field(default_factory=list)
    poi_prompt: str = ""

    # Screenshot path (for viewer to load)
    screenshot_path: str = ""

    # LLM interaction
    llm_prompt_system: str = ""
    llm_prompt_user: str = ""
    llm_response: str = ""
    llm_was_queried: bool = True  # False if path continuation

    # Conversation history (LLM queries within this turn)
    llm_exchanges: List[Dict] = field(default_factory=list)  # [{prompt, response, action, error}]
    action_retries: int = 0  # How many times we re-prompted due to errors

    # Free actions taken (LOOK, SPEAK)
    free_actions: List[Dict] = field(default_factory=list)

    # Turn-ending action
    final_action_type: str = ""
    final_action_args: tuple = ()
    final_action_success: bool = False
    final_action_message: str = ""

    # Movement result
    position_end: tuple = (0, 0)
    path_taken: List[tuple] = field(default_factory=list)
    path_remaining: int = 0  # Tiles left if multi-tile path


@dataclass
class EnhancedSimulationLog:
    """
    Complete simulation log for offline viewer.

    Designed to support:
    - Turn-by-turn replay
    - Per-agent perspective reconstruction
    - LLM chain-of-thought review
    - Speech history tracking
    """
    metadata: Dict[str, Any] = field(default_factory=dict)
    steps: List[EnhancedSimulationStep] = field(default_factory=list)
    speech_log: List[Dict] = field(default_factory=list)

    def save(self, path: str):
        """Save log to JSON file."""
        data = {
            "metadata": self.metadata,
            "steps": [asdict(s) for s in self.steps],
            "speech_log": self.speech_log
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Enhanced simulation log saved to: {path}")

    @classmethod
    def load(cls, path: str) -> 'EnhancedSimulationLog':
        """Load log from JSON file."""
        with open(path) as f:
            data = json.load(f)

        steps = []
        for s in data.get("steps", []):
            # Convert lists back to tuples where needed
            if isinstance(s.get("position_start"), list):
                s["position_start"] = tuple(s["position_start"])
            if isinstance(s.get("position_end"), list):
                s["position_end"] = tuple(s["position_end"])
            if isinstance(s.get("final_action_args"), list):
                s["final_action_args"] = tuple(s["final_action_args"])
            if s.get("path_taken"):
                s["path_taken"] = [tuple(p) for p in s["path_taken"]]
            steps.append(EnhancedSimulationStep(**s))

        return cls(
            metadata=data.get("metadata", {}),
            steps=steps,
            speech_log=data.get("speech_log", [])
        )

    def get_turn_summary(self, turn: int) -> str:
        """Get summary of a specific turn for display."""
        turn_steps = [s for s in self.steps if s.turn == turn]
        lines = [f"=== Turn {turn} ==="]

        for step in turn_steps:
            lines.append(f"\n{step.agent_id}:")
            lines.append(f"  Position: {step.position_start} -> {step.position_end}")

            if step.free_actions:
                lines.append(f"  Free actions: {len(step.free_actions)}")
                for fa in step.free_actions:
                    lines.append(f"    - {fa['action_type']}: {fa.get('result', {}).get('message', '')[:50]}")

            status = "OK" if step.final_action_success else "FAIL"
            lines.append(f"  Action: {step.final_action_type} {step.final_action_args} [{status}]")

            if not step.llm_was_queried:
                lines.append("  (Path continuation - no LLM query)")

        return "\n".join(lines)


class EnhancedOrchestrator:
    """
    Enhanced turn orchestrator with action economy and improved logging.
    """

    def __init__(self, grid, fov_layer, world: WorldGraph, agents: list,
                 screenshot_dir: str, llm_query_fn: Callable):
        """
        Initialize enhanced orchestrator.

        Args:
            grid: mcrfpy.Grid instance
            fov_layer: Color layer for FOV rendering
            world: WorldGraph instance
            agents: List of Agent objects
            screenshot_dir: Directory for screenshots
            llm_query_fn: Function(agent, screenshot_path, context) -> str
        """
        self.grid = grid
        self.fov_layer = fov_layer
        self.world = world
        self.agents = agents
        self.screenshot_dir = screenshot_dir
        self.llm_query_fn = llm_query_fn

        self.executor = EnhancedExecutor(grid, world)
        self.turn_number = 0
        self.steps: List[EnhancedSimulationStep] = []
        self.speech_log: List[Dict] = []

        os.makedirs(screenshot_dir, exist_ok=True)

    def run_simulation(self, max_turns: int = 10,
                       stop_condition: Callable = None) -> EnhancedSimulationLog:
        """
        Run complete simulation with enhanced logging.

        Args:
            max_turns: Maximum number of turns
            stop_condition: Optional callable(orchestrator) -> bool

        Returns:
            EnhancedSimulationLog for offline viewer
        """
        print(f"\nStarting enhanced simulation: max {max_turns} turns")
        print(f"Agents: {[a.name for a in self.agents]}")
        print("=" * 60)

        for turn in range(max_turns):
            self.run_turn()

            if stop_condition and stop_condition(self):
                print(f"\nStop condition met at turn {self.turn_number}")
                break

        # Build log
        log = EnhancedSimulationLog(
            metadata={
                "total_turns": self.turn_number,
                "num_agents": len(self.agents),
                "agent_names": [a.name for a in self.agents],
                "timestamp_start": self.steps[0].timestamp if self.steps else "",
                "timestamp_end": self.steps[-1].timestamp if self.steps else "",
                "world_rooms": list(self.world.rooms.keys()),
                "screenshot_dir": self.screenshot_dir,
            },
            steps=self.steps,
            speech_log=self.speech_log
        )

        return log

    def run_turn(self) -> List[EnhancedSimulationStep]:
        """Execute one full turn (all agents act once)."""
        import mcrfpy

        self.turn_number += 1
        turn_steps = []

        print(f"\n{'='*60}")
        print(f"TURN {self.turn_number}")
        print("=" * 60)

        for agent in self.agents:
            step = self._run_agent_turn(agent)
            turn_steps.append(step)
            self.steps.append(step)

        return turn_steps

    def _run_agent_turn(self, agent) -> EnhancedSimulationStep:
        """Execute one agent's turn with action economy."""
        import mcrfpy
        from mcrfpy import automation

        print(f"\n--- {agent.name}'s Turn ---")

        # Initialize step record
        step = EnhancedSimulationStep(
            turn=self.turn_number,
            agent_id=agent.name,
            position_start=agent.pos,
            room=agent.current_room
        )

        # Check for path continuation
        path_state = self.executor.get_path_state(agent.name)
        current_visible = self._get_visible_entity_ids(agent)

        if path_state.has_path:
            # Check for FOV interrupt
            if path_state.should_interrupt(current_visible):
                print(f"  Path interrupted: new entity in FOV")
                path_state.clear()
            else:
                # Continue path without LLM query
                result = self.executor.continue_path(agent, current_visible)
                if result and result.success:
                    step.llm_was_queried = False
                    step.path_in_progress = True
                    step.final_action_type = "GO"
                    step.final_action_args = ("CONTINUE",)
                    step.final_action_success = True
                    step.final_action_message = result.message
                    step.position_end = result.new_position or agent.pos
                    step.path_taken = result.path or []
                    step.path_remaining = self.executor.get_path_state(agent.name).remaining_tiles

                    print(f"  Path continuation: {result.message}")
                    return step

        # Need LLM query - set up perspective
        step.visible_entities = list(current_visible)
        self._switch_perspective(agent)
        mcrfpy.step(0.016)

        # Take screenshot
        screenshot_path = os.path.join(
            self.screenshot_dir,
            f"turn{self.turn_number}_{agent.name.lower()}.png"
        )
        automation.screenshot(screenshot_path)
        step.screenshot_path = screenshot_path

        # Collect points of interest
        poi_collector = PointOfInterestCollector(self.grid, agent.pos)
        pois = poi_collector.collect_from_fov(self.world)
        step.points_of_interest = [asdict(p) for p in pois]
        step.poi_prompt = poi_collector.format_for_prompt()

        # Get pending messages
        messages = self.executor.get_pending_messages(agent.name)
        step.pending_messages = [asdict(m) for m in messages]

        # Build context
        visible_agents = self._get_visible_agents(agent)
        context = agent.get_context(visible_agents + [agent])
        step.location_description = context["location"]
        step.available_actions = context["available_actions"]

        # Turn state for action economy
        turn_state = TurnState()

        # Error feedback for retry loop
        last_error = None
        MAX_RETRIES = 3

        # Action loop - handle free actions until turn-ending action
        while not turn_state.turn_ended:
            # Build prompt with current state (includes error feedback if any)
            prompt = self._build_prompt(agent, context, step.poi_prompt, messages, turn_state, last_error)
            step.llm_prompt_user = prompt  # Store last prompt

            # Query LLM
            print(f"  Querying LLM...")
            response = self.llm_query_fn(agent, screenshot_path, {
                **context,
                "poi_prompt": step.poi_prompt,
                "messages": [asdict(m) for m in messages],
                "has_spoken": turn_state.has_spoken,
                "last_error": last_error,
                "conversation_history": step.llm_exchanges  # Include past exchanges
            })
            step.llm_response = response
            print(f"  Response: {response[:200]}...")

            # Parse action
            action = parse_action(response)
            cost = get_action_cost(action)

            print(f"  Action: {action.type.value} {action.args} (cost: {cost.value})")

            # Track this exchange
            exchange = {
                "prompt": prompt[:500],  # Truncate for storage
                "response": response,
                "action_type": action.type.value,
                "action_args": action.args,
                "error": None
            }

            # Execute action based on type
            if action.type == ActionType.LOOK:
                result = self.executor.execute_look(agent, action)
                turn_state.record_free_action("LOOK", {
                    "target": result.target_name,
                    "description": result.description
                })
                step.free_actions.append({
                    "action_type": "LOOK",
                    "args": action.args,
                    "result": {"description": result.description}
                })
                # Provide result and continue loop for another action
                context["look_result"] = result.description
                last_error = None  # Clear error on success
                print(f"  LOOK result: {result.description[:100]}...")

            elif action.type in (ActionType.SPEAK, ActionType.ANNOUNCE):
                if not turn_state.can_speak():
                    print(f"  Already spoke this turn")
                    last_error = "You have already spoken this turn. Choose a different action."
                    exchange["error"] = last_error
                    step.action_retries += 1
                    if step.action_retries >= MAX_RETRIES:
                        # Force end turn
                        step.final_action_type = "WAIT"
                        step.final_action_args = ()
                        step.final_action_success = False
                        step.final_action_message = "Too many invalid actions - turn ended"
                        step.position_end = agent.pos
                        turn_state.end_turn()
                else:
                    result = self.executor.execute_speech(
                        agent, action, self.agents, self.turn_number
                    )
                    turn_state.record_speech()
                    turn_state.record_free_action(action.type.value, {
                        "content": result.content,
                        "recipients": result.recipients
                    })
                    step.free_actions.append({
                        "action_type": action.type.value,
                        "args": action.args,
                        "result": {
                            "content": result.content,
                            "recipients": result.recipients
                        }
                    })
                    # Record in speech log
                    self.speech_log.append({
                        "turn": self.turn_number,
                        "speaker": agent.name,
                        "type": result.speech_type,
                        "content": result.content,
                        "recipients": result.recipients
                    })
                    last_error = None
                    print(f"  {result.speech_type.upper()}: {result.content[:50]}... -> {result.recipients}")
                    # Continue loop for another action (can still move)

            elif action.type == ActionType.TAKE:
                result = self.executor.execute_take(agent, action)
                if result.success:
                    step.final_action_type = "TAKE"
                    step.final_action_args = action.args
                    step.final_action_success = True
                    step.final_action_message = result.message
                    step.position_end = agent.pos
                    last_error = None
                    turn_state.end_turn()
                    print(f"  TAKE: {result.message}")
                else:
                    # Failed - give error feedback and let LLM try again
                    last_error = result.message
                    exchange["error"] = last_error
                    step.action_retries += 1
                    print(f"  TAKE FAILED: {result.message}")
                    if step.action_retries >= MAX_RETRIES:
                        step.final_action_type = "TAKE"
                        step.final_action_args = action.args
                        step.final_action_success = False
                        step.final_action_message = result.message
                        step.position_end = agent.pos
                        turn_state.end_turn()

            elif action.type == ActionType.GO:
                result = self.executor.execute_move(agent, action)
                if result.success:
                    step.final_action_type = "GO"
                    step.final_action_args = action.args
                    step.final_action_success = True
                    step.final_action_message = result.message
                    step.position_end = result.new_position or agent.pos
                    step.path_taken = result.path or []
                    last_error = None
                    turn_state.end_turn()
                    print(f"  MOVE: {result.message}")
                else:
                    # Failed - give error feedback
                    last_error = result.message
                    exchange["error"] = last_error
                    step.action_retries += 1
                    print(f"  MOVE FAILED: {result.message}")
                    if step.action_retries >= MAX_RETRIES:
                        step.final_action_type = "GO"
                        step.final_action_args = action.args
                        step.final_action_success = False
                        step.final_action_message = result.message
                        step.position_end = agent.pos
                        turn_state.end_turn()

            elif action.type == ActionType.WAIT:
                result = self.executor.execute_wait(agent, action)
                step.final_action_type = "WAIT"
                step.final_action_args = ()
                step.final_action_success = True
                step.final_action_message = result.message
                step.position_end = agent.pos
                last_error = None
                turn_state.end_turn()
                print(f"  WAIT")

            elif action.type == ActionType.INVALID:
                # Could not parse action - give feedback
                last_error = f"Could not understand your action. Please use a valid action format like 'Action: GO EAST' or 'Action: TAKE key'."
                exchange["error"] = last_error
                step.action_retries += 1
                print(f"  INVALID ACTION: {action.args}")
                if step.action_retries >= MAX_RETRIES:
                    step.final_action_type = "INVALID"
                    step.final_action_args = action.args
                    step.final_action_success = False
                    step.final_action_message = "Could not parse action"
                    step.position_end = agent.pos
                    turn_state.end_turn()

            else:
                # Unimplemented action type - give feedback
                last_error = f"The action '{action.type.value}' is not yet supported. Try GO, TAKE, LOOK, SPEAK, or WAIT."
                exchange["error"] = last_error
                step.action_retries += 1
                print(f"  Unsupported: {action.type.value}")
                if step.action_retries >= MAX_RETRIES:
                    step.final_action_type = action.type.value
                    step.final_action_args = action.args
                    step.final_action_success = False
                    step.final_action_message = f"Unsupported action: {action.type.value}"
                    step.position_end = agent.pos
                    turn_state.end_turn()

            # Record exchange
            step.llm_exchanges.append(exchange)

        return step

    def _build_prompt(self, agent, context: dict, poi_prompt: str,
                      messages: List[Message], turn_state: TurnState,
                      last_error: Optional[str] = None) -> str:
        """Build LLM prompt with current state and error feedback."""
        parts = [context["location"]]

        # Add messages received
        if messages:
            parts.append("\nMessages received:")
            for msg in messages:
                if msg.speech_type == "announce":
                    parts.append(f'  {msg.sender} announces: "{msg.content}"')
                else:
                    parts.append(f'  {msg.sender} says: "{msg.content}"')

        # Add points of interest
        parts.append(f"\n{poi_prompt}")

        # Add available actions
        actions_str = ", ".join(context["available_actions"])
        parts.append(f"\nAvailable actions: {actions_str}")

        # Add LOOK result if we just looked
        if "look_result" in context:
            parts.append(f"\n[LOOK result: {context['look_result']}]")

        # Add constraints
        constraints = []
        if turn_state.has_spoken:
            constraints.append("You have already spoken this turn.")
        if constraints:
            parts.append(f"\nConstraints: {' '.join(constraints)}")

        # Add error feedback from last action attempt
        if last_error:
            parts.append(f"\n[ERROR: {last_error}]")
            parts.append("[Please try a different action.]")

        parts.append("\nWhat do you do? Brief reasoning, then Action: <action>")

        return "\n".join(parts)

    def _switch_perspective(self, agent):
        """Switch grid view to agent's perspective."""
        import mcrfpy

        self.fov_layer.fill(mcrfpy.Color(0, 0, 0, 255))
        self.fov_layer.apply_perspective(
            entity=agent.entity,
            visible=mcrfpy.Color(0, 0, 0, 0),
            discovered=mcrfpy.Color(40, 40, 60, 180),
            unknown=mcrfpy.Color(0, 0, 0, 255)
        )
        agent.entity.update_visibility()

        px, py = agent.pos
        self.grid.center = (px * 16 + 8, py * 16 + 8)

    def _get_visible_agents(self, observer) -> list:
        """Get agents visible to observer based on FOV."""
        visible = []
        for agent in self.agents:
            if agent.name == observer.name:
                continue
            ax, ay = agent.pos
            if self.grid.is_in_fov(ax, ay):
                visible.append(agent)
        return visible

    def _get_visible_entity_ids(self, agent) -> Set[str]:
        """Get set of entity IDs currently visible to agent."""
        visible = set()
        ax, ay = agent.pos

        for entity in self.grid.entities:
            if entity is agent.entity:
                continue
            ex, ey = int(entity.pos[0]), int(entity.pos[1])
            if self.grid.is_in_fov(ex, ey):
                entity_id = getattr(entity, 'id', None) or str(id(entity))
                visible.add(entity_id)

        return visible
