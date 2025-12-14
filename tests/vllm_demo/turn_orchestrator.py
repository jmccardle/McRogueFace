"""
Turn Orchestrator
=================

Manages multi-turn simulation with logging for replay.
Coordinates perspective switching, LLM queries, and action execution.
"""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from world_graph import WorldGraph, AgentInfo
from action_parser import Action, ActionType, parse_action
from action_executor import ActionExecutor, ActionResult


@dataclass
class SimulationStep:
    """Record of one agent's turn."""
    turn: int
    agent_id: str
    agent_position: tuple
    room: str
    perception: Dict[str, Any]      # Context shown to LLM
    llm_response: str               # Raw LLM output
    parsed_action_type: str         # Action type as string
    parsed_action_args: tuple       # Action arguments
    result_success: bool
    result_message: str
    new_position: Optional[tuple] = None
    path: Optional[List[tuple]] = None  # For animation replay
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SimulationLog:
    """Complete simulation record for replay and analysis."""
    metadata: Dict[str, Any]
    steps: List[SimulationStep] = field(default_factory=list)

    def save(self, path: str):
        """Save log to JSON file."""
        data = {
            "metadata": self.metadata,
            "steps": [asdict(s) for s in self.steps]
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Simulation log saved to: {path}")

    @classmethod
    def load(cls, path: str) -> 'SimulationLog':
        """Load log from JSON file."""
        with open(path) as f:
            data = json.load(f)

        steps = []
        for s in data["steps"]:
            # Convert tuple strings back to tuples
            if isinstance(s.get("agent_position"), list):
                s["agent_position"] = tuple(s["agent_position"])
            if isinstance(s.get("new_position"), list):
                s["new_position"] = tuple(s["new_position"])
            if isinstance(s.get("parsed_action_args"), list):
                s["parsed_action_args"] = tuple(s["parsed_action_args"])
            if s.get("path"):
                s["path"] = [tuple(p) for p in s["path"]]
            steps.append(SimulationStep(**s))

        return cls(metadata=data["metadata"], steps=steps)

    def get_agent_steps(self, agent_name: str) -> List[SimulationStep]:
        """Get all steps for a specific agent."""
        return [s for s in self.steps if s.agent_id == agent_name]

    def get_turn_steps(self, turn: int) -> List[SimulationStep]:
        """Get all steps from a specific turn."""
        return [s for s in self.steps if s.turn == turn]

    def summary(self) -> str:
        """Generate a summary of the simulation."""
        lines = [
            f"Simulation Summary",
            f"==================",
            f"Total turns: {self.metadata.get('total_turns', 'unknown')}",
            f"Total steps: {len(self.steps)}",
            f"Agents: {', '.join(self.metadata.get('agent_names', []))}",
            f"",
        ]

        # Per-agent stats
        for agent_name in self.metadata.get('agent_names', []):
            agent_steps = self.get_agent_steps(agent_name)
            successes = sum(1 for s in agent_steps if s.result_success)
            lines.append(f"{agent_name}:")
            lines.append(f"  Actions: {len(agent_steps)}")
            lines.append(f"  Successful: {successes}")
            if agent_steps:
                final = agent_steps[-1]
                final_pos = final.new_position or final.agent_position
                lines.append(f"  Final position: {final_pos}")
                lines.append(f"  Final room: {final.room}")
            lines.append("")

        return "\n".join(lines)


class TurnOrchestrator:
    """
    Orchestrates multi-turn simulation.

    Handles:
    - Turn sequencing
    - Perspective switching
    - LLM queries
    - Action execution
    - Simulation logging
    """

    def __init__(self, grid, fov_layer, world: WorldGraph, agents: list,
                 screenshot_dir: str, llm_query_fn: Callable):
        """
        Initialize orchestrator.

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

        self.executor = ActionExecutor(grid)
        self.turn_number = 0
        self.steps: List[SimulationStep] = []

        os.makedirs(screenshot_dir, exist_ok=True)

    def run_turn(self) -> List[SimulationStep]:
        """
        Execute one full turn (all agents act once).

        Returns list of SimulationSteps for this turn.
        """
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

    def run_simulation(self, max_turns: int = 10,
                       stop_condition: Callable = None) -> SimulationLog:
        """
        Run complete simulation.

        Args:
            max_turns: Maximum number of turns to run
            stop_condition: Optional callable(orchestrator) -> bool
                           Returns True to stop simulation early

        Returns:
            SimulationLog with all steps
        """
        print(f"\nStarting simulation: max {max_turns} turns")
        print(f"Agents: {[a.name for a in self.agents]}")
        print("=" * 60)

        for turn in range(max_turns):
            self.run_turn()

            # Check stop condition
            if stop_condition and stop_condition(self):
                print(f"\nStop condition met at turn {self.turn_number}")
                break

        # Create log
        log = SimulationLog(
            metadata={
                "total_turns": self.turn_number,
                "num_agents": len(self.agents),
                "agent_names": [a.name for a in self.agents],
                "timestamp": datetime.now().isoformat(),
                "world_rooms": list(self.world.rooms.keys()),
                "screenshot_dir": self.screenshot_dir,
            },
            steps=self.steps
        )

        return log

    def _run_agent_turn(self, agent) -> SimulationStep:
        """Execute one agent's turn."""
        import mcrfpy
        from mcrfpy import automation

        print(f"\n--- {agent.name}'s Turn ---")
        print(f"Position: {agent.pos} | Room: {agent.current_room}")

        # Switch perspective
        self._switch_perspective(agent)
        mcrfpy.step(0.016)

        # Screenshot
        screenshot_path = os.path.join(
            self.screenshot_dir,
            f"turn{self.turn_number}_{agent.name.lower()}.png"
        )
        automation.screenshot(screenshot_path)

        # Build context
        visible_agents = self._get_visible_agents(agent)
        context = agent.get_context(visible_agents + [agent])

        # Query LLM
        llm_response = self.llm_query_fn(agent, screenshot_path, context)

        # Parse and execute
        action = parse_action(llm_response)
        result = self.executor.execute(agent, action)

        # Log output
        status = "SUCCESS" if result.success else "FAILED"
        print(f"  Action: {action.type.value} {action.args}")
        print(f"  Result: {status} - {result.message}")

        # Build step record
        step = SimulationStep(
            turn=self.turn_number,
            agent_id=agent.name,
            agent_position=agent.pos,
            room=agent.current_room,
            perception={
                "location": context["location"],
                "available_actions": context["available_actions"],
            },
            llm_response=llm_response,
            parsed_action_type=action.type.value,
            parsed_action_args=action.args,
            result_success=result.success,
            result_message=result.message,
            new_position=result.new_position,
            path=result.path
        )

        return step

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

    def get_agent_positions(self) -> Dict[str, tuple]:
        """Get current positions of all agents."""
        return {a.name: a.pos for a in self.agents}

    def agents_in_same_room(self) -> bool:
        """Check if all agents are in the same room."""
        rooms = [a.current_room for a in self.agents]
        return len(set(rooms)) == 1
