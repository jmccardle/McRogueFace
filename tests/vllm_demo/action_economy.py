"""
Action Economy System
=====================

Defines which actions consume turns and which are free.
Manages multi-tile pathing with FOV interruption.

Action Categories:
- FREE: LOOK, SPEAK, ANNOUNCE (don't end turn)
- FULL: MOVE, WAIT (end turn)

Constraints:
- Only ONE speech action per turn
- LOOK provides description and prompts for another action
- Multi-tile paths continue without LLM until FOV changes
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set, Dict, Any
from enum import Enum

from action_parser import Action, ActionType


class TurnCost(Enum):
    """How much of a turn an action consumes."""
    FREE = "free"           # Doesn't end turn
    FULL = "full"           # Ends turn


# Action cost mapping
ACTION_COSTS = {
    ActionType.LOOK: TurnCost.FREE,
    ActionType.SPEAK: TurnCost.FREE,
    ActionType.ANNOUNCE: TurnCost.FREE,
    ActionType.GO: TurnCost.FULL,
    ActionType.WAIT: TurnCost.FULL,
    ActionType.TAKE: TurnCost.FULL,
    ActionType.DROP: TurnCost.FULL,
    ActionType.PUSH: TurnCost.FULL,
    ActionType.USE: TurnCost.FULL,
    ActionType.OPEN: TurnCost.FULL,
    ActionType.CLOSE: TurnCost.FULL,
    ActionType.INVALID: TurnCost.FULL,  # Invalid action ends turn
}


@dataclass
class TurnState:
    """
    Tracks state within a single turn.

    Used to enforce constraints like "only one speech per turn"
    and track free actions taken before turn-ending action.
    """
    has_spoken: bool = False
    free_actions: List[Dict[str, Any]] = field(default_factory=list)
    turn_ended: bool = False

    def can_speak(self) -> bool:
        """Check if agent can still speak this turn."""
        return not self.has_spoken

    def record_speech(self):
        """Record that agent has spoken this turn."""
        self.has_spoken = True

    def record_free_action(self, action_type: str, details: Dict[str, Any]):
        """Record a free action for logging."""
        self.free_actions.append({
            "type": action_type,
            **details
        })

    def end_turn(self):
        """Mark turn as ended."""
        self.turn_ended = True


@dataclass
class PathState:
    """
    Tracks multi-tile movement path for an agent.

    When an agent decides to move to a distant location,
    we store the path and continue moving without LLM calls
    until the path completes or FOV changes.
    """
    path: List[Tuple[int, int]] = field(default_factory=list)
    current_index: int = 0
    destination_description: str = ""  # "the armory", "the door"

    # FOV state when path was planned
    visible_entities_at_start: Set[str] = field(default_factory=set)

    @property
    def has_path(self) -> bool:
        """Check if there's an active path."""
        return len(self.path) > self.current_index

    @property
    def next_tile(self) -> Optional[Tuple[int, int]]:
        """Get next tile in path, or None if path complete."""
        if self.has_path:
            return self.path[self.current_index]
        return None

    @property
    def remaining_tiles(self) -> int:
        """Number of tiles left in path."""
        return max(0, len(self.path) - self.current_index)

    def advance(self):
        """Move to next tile in path."""
        if self.has_path:
            self.current_index += 1

    def clear(self):
        """Clear the current path."""
        self.path = []
        self.current_index = 0
        self.destination_description = ""
        self.visible_entities_at_start = set()

    def should_interrupt(self, current_visible_entities: Set[str]) -> bool:
        """
        Check if path should be interrupted due to FOV change.

        Returns True if a NEW entity has entered the agent's FOV
        since the path was planned.
        """
        new_entities = current_visible_entities - self.visible_entities_at_start
        return len(new_entities) > 0


@dataclass
class PointOfInterest:
    """
    A targetable object/location for LOOK/MOVE actions.

    Listed in LLM prompts to guide valid targeting.
    """
    name: str                       # Short name: "door", "rat", "button"
    display_name: str               # Full description: "a wooden door to the east"
    position: Tuple[int, int]       # Tile coordinates
    direction: str                  # Cardinal direction from agent: "north", "east"
    distance: int                   # Manhattan distance from agent
    can_look: bool = True           # Can be examined with LOOK
    can_move_to: bool = False       # Can be targeted with GO TO
    entity_id: Optional[str] = None # Entity ID if this is an entity


def get_action_cost(action: Action) -> TurnCost:
    """Get the turn cost for an action."""
    return ACTION_COSTS.get(action.type, TurnCost.FULL)


def get_direction_name(from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> str:
    """Get cardinal direction name from one position to another."""
    dx = to_pos[0] - from_pos[0]
    dy = to_pos[1] - from_pos[1]

    if abs(dx) > abs(dy):
        return "east" if dx > 0 else "west"
    elif abs(dy) > abs(dx):
        return "south" if dy > 0 else "north"
    else:
        # Diagonal
        ns = "south" if dy > 0 else "north"
        ew = "east" if dx > 0 else "west"
        return f"{ns}-{ew}"


def manhattan_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Calculate Manhattan distance between two points."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class PointOfInterestCollector:
    """
    Collects points of interest visible to an agent.

    Used to populate LLM prompts with valid LOOK/MOVE targets.
    """

    def __init__(self, grid, agent_pos: Tuple[int, int]):
        self.grid = grid
        self.agent_pos = agent_pos
        self.points: List[PointOfInterest] = []

    def collect_from_fov(self, world_graph=None) -> List[PointOfInterest]:
        """
        Collect all points of interest visible in current FOV.

        Examines:
        - Entities (other agents, NPCs, items)
        - Doors/exits
        - Interactive objects (buttons, chests)
        - Notable tiles (walls with features)
        """
        self.points = []

        # Collect entities
        for entity in self.grid.entities:
            ex, ey = int(entity.pos[0]), int(entity.pos[1])
            if (ex, ey) == self.agent_pos:
                continue  # Skip self

            if self.grid.is_in_fov(ex, ey):
                direction = get_direction_name(self.agent_pos, (ex, ey))
                distance = manhattan_distance(self.agent_pos, (ex, ey))

                # Try to get entity name/description
                entity_name = getattr(entity, 'name', None) or f"creature"
                entity_id = getattr(entity, 'id', None) or str(id(entity))

                self.points.append(PointOfInterest(
                    name=entity_name,
                    display_name=f"a {entity_name} to the {direction}",
                    position=(ex, ey),
                    direction=direction,
                    distance=distance,
                    can_look=True,
                    can_move_to=False,  # Can't move onto entities
                    entity_id=entity_id
                ))

        # Collect from WorldGraph if provided
        if world_graph:
            self._collect_from_world_graph(world_graph)

        # Sort by distance
        self.points.sort(key=lambda p: p.distance)

        return self.points

    def _collect_from_world_graph(self, world):
        """Collect doors and objects from WorldGraph."""
        agent_room = world.room_at(*self.agent_pos)
        if not agent_room:
            return

        # Doors
        for door in world.get_exits(agent_room.name):
            dx, dy = door.position
            if self.grid.is_in_fov(dx, dy):
                direction = get_direction_name(self.agent_pos, (dx, dy))
                distance = manhattan_distance(self.agent_pos, (dx, dy))

                # Get destination room name
                if door.room_a == agent_room.name:
                    dest = world.rooms.get(door.room_b)
                else:
                    dest = world.rooms.get(door.room_a)
                dest_name = dest.display_name if dest else "unknown"

                lock_str = " (locked)" if door.locked else ""

                self.points.append(PointOfInterest(
                    name="door",
                    display_name=f"a door to {dest_name}{lock_str} ({direction})",
                    position=(dx, dy),
                    direction=direction,
                    distance=distance,
                    can_look=True,
                    can_move_to=not door.locked
                ))

        # Objects in room
        for obj in world.get_objects_in_room(agent_room.name):
            ox, oy = obj.position
            if self.grid.is_in_fov(ox, oy):
                direction = get_direction_name(self.agent_pos, (ox, oy))
                distance = manhattan_distance(self.agent_pos, (ox, oy))

                self.points.append(PointOfInterest(
                    name=obj.name,
                    display_name=f"{obj.display_name} ({direction})",
                    position=(ox, oy),
                    direction=direction,
                    distance=distance,
                    can_look=True,
                    can_move_to="pressable" not in obj.affordances  # Can walk to items
                ))

    def format_for_prompt(self) -> str:
        """Format points of interest for inclusion in LLM prompt."""
        if not self.points:
            return "No notable objects in view."

        lines = ["Points of interest:"]
        for poi in self.points:
            actions = []
            if poi.can_look:
                actions.append(f"LOOK AT {poi.name.upper()}")
            if poi.can_move_to:
                actions.append(f"GO TO {poi.name.upper()}")

            action_str = ", ".join(actions) if actions else "observe only"
            lines.append(f"  - {poi.display_name}: {action_str}")

        return "\n".join(lines)
