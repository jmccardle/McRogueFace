"""
Action Executor for McRogueFace
===============================

Executes parsed actions in the game world.
Handles movement, collision detection, and action results.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
from action_parser import Action, ActionType


@dataclass
class ActionResult:
    success: bool
    message: str
    new_position: Optional[Tuple[int, int]] = None
    path: Optional[List[Tuple[int, int]]] = None  # For animation replay


class ActionExecutor:
    """Execute actions in the McRogueFace game world."""

    # Direction vectors
    DIRECTION_VECTORS = {
        'NORTH': (0, -1),
        'SOUTH': (0, 1),
        'EAST': (1, 0),
        'WEST': (-1, 0),
    }

    def __init__(self, grid):
        """
        Initialize executor with a grid reference.

        Args:
            grid: mcrfpy.Grid instance
        """
        self.grid = grid

    def execute(self, agent, action: Action) -> ActionResult:
        """
        Execute an action for an agent.

        Args:
            agent: Agent wrapper with .entity attribute
            action: Parsed Action to execute

        Returns:
            ActionResult with success status and message
        """
        handlers = {
            ActionType.GO: self._execute_go,
            ActionType.WAIT: self._execute_wait,
            ActionType.LOOK: self._execute_look,
            ActionType.TAKE: self._execute_take,
            ActionType.DROP: self._execute_drop,
            ActionType.INVALID: self._execute_invalid,
        }

        handler = handlers.get(action.type, self._execute_unimplemented)
        return handler(agent, action)

    def _execute_go(self, agent, action: Action) -> ActionResult:
        """Execute movement in a direction."""
        if not action.args or not action.args[0]:
            return ActionResult(False, "No direction specified")

        direction = action.args[0]
        if direction not in self.DIRECTION_VECTORS:
            return ActionResult(False, f"Invalid direction: {direction}")

        dx, dy = self.DIRECTION_VECTORS[direction]

        # Get current position
        current_x, current_y = int(agent.entity.pos[0]), int(agent.entity.pos[1])
        new_x, new_y = current_x + dx, current_y + dy

        # Check bounds
        grid_w, grid_h = self.grid.grid_size
        if not (0 <= new_x < grid_w and 0 <= new_y < grid_h):
            return ActionResult(False, f"Cannot go {direction} - edge of map")

        # Check walkability
        target_cell = self.grid.at(new_x, new_y)
        if not target_cell.walkable:
            return ActionResult(False, f"Cannot go {direction} - path blocked")

        # Check for entity collision (optional - depends on game rules)
        for entity in self.grid.entities:
            if entity is agent.entity:
                continue
            ex, ey = int(entity.pos[0]), int(entity.pos[1])
            if ex == new_x and ey == new_y:
                return ActionResult(False, f"Cannot go {direction} - someone is there")

        # Execute movement
        agent.entity.pos = (new_x, new_y)

        return ActionResult(
            success=True,
            message=f"Moved {direction.lower()} to ({new_x}, {new_y})",
            new_position=(new_x, new_y),
            path=[(current_x, current_y), (new_x, new_y)]
        )

    def _execute_wait(self, agent, action: Action) -> ActionResult:
        """Execute wait action (no-op)."""
        return ActionResult(True, "Waited and observed surroundings")

    def _execute_look(self, agent, action: Action) -> ActionResult:
        """Execute look action - returns enhanced observation."""
        target = action.args[0] if action.args else None
        if target:
            return ActionResult(True, f"Examined {target} closely")
        return ActionResult(True, "Looked around carefully")

    def _execute_take(self, agent, action: Action) -> ActionResult:
        """Execute take action (placeholder)."""
        item = action.args[0] if action.args else "unknown"
        # TODO: Implement inventory system
        return ActionResult(False, f"Cannot take {item} - not implemented yet")

    def _execute_drop(self, agent, action: Action) -> ActionResult:
        """Execute drop action (placeholder)."""
        item = action.args[0] if action.args else "unknown"
        return ActionResult(False, f"Cannot drop {item} - not implemented yet")

    def _execute_invalid(self, agent, action: Action) -> ActionResult:
        """Handle invalid/unparseable action."""
        return ActionResult(False, f"Could not understand action: {action.args[0]}")

    def _execute_unimplemented(self, agent, action: Action) -> ActionResult:
        """Handle unimplemented action types."""
        return ActionResult(False, f"Action {action.type.value} not yet implemented")
