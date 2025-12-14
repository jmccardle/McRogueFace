"""
WorldGraph: Room-based World Representation
============================================

Provides dual-purpose data structures for:
1. Generating 2D tilemaps (visual representation)
2. Generating text descriptions (LLM context)

Ensures deterministic text output: same state = same description.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

    @property
    def opposite(self) -> 'Direction':
        opposites = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST,
        }
        return opposites[self]

    @property
    def vector(self) -> Tuple[int, int]:
        vectors = {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0),
        }
        return vectors[self]


@dataclass
class Room:
    """A room in the world graph."""
    name: str                           # Internal ID: "kitchen", "guard_room"
    display_name: str                   # Text output: "the kitchen", "a dimly lit guard room"
    bounds: Tuple[int, int, int, int]   # (x, y, width, height) in tile coords
    properties: Dict[str, Any] = field(default_factory=dict)  # {"lit": True, "temperature": "warm"}
    description_template: Optional[str] = None  # "A {temperature} room with {features}."

    @property
    def x(self) -> int:
        return self.bounds[0]

    @property
    def y(self) -> int:
        return self.bounds[1]

    @property
    def width(self) -> int:
        return self.bounds[2]

    @property
    def height(self) -> int:
        return self.bounds[3]

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains(self, x: int, y: int) -> bool:
        """Check if a tile coordinate is within this room."""
        return (self.x <= x < self.x + self.width and
                self.y <= y < self.y + self.height)


@dataclass
class Door:
    """A connection between two rooms."""
    room_a: str                     # Room name
    room_b: str                     # Room name
    position: Tuple[int, int]       # Tile position of the door
    direction_from_a: Direction     # Direction from room_a to reach room_b
    locked: bool = False
    key_id: Optional[str] = None    # Which key unlocks this door

    @property
    def direction_from_b(self) -> Direction:
        return self.direction_from_a.opposite


@dataclass
class WorldObject:
    """An interactable object in the world."""
    name: str                       # Internal ID: "brass_key"
    display_name: str               # Text output: "a brass key"
    room: str                       # Which room contains it
    position: Tuple[int, int]       # Tile position (or None if carried)
    affordances: List[str] = field(default_factory=list)  # ["takeable", "unlocks:pantry_door"]
    description: str = ""           # "A tarnished brass key with ornate handle."


@dataclass
class AgentInfo:
    """Information about an agent for description purposes."""
    name: str                       # "Wizard", "Knight"
    display_name: str               # "a wizard", "the knight"
    position: Tuple[int, int]       # Current tile position
    is_player: bool = False         # Is this the observing agent?


class WorldGraph:
    """
    Graph-based world representation.

    Provides:
    - Room/door/object storage
    - Deterministic text description generation
    - Spatial queries (what room is at x,y?)
    - Available action enumeration
    """

    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.doors: List[Door] = []
        self.objects: Dict[str, WorldObject] = {}

    # =========================================================================
    # Building the World
    # =========================================================================

    def add_room(self, room: Room) -> None:
        """Add a room to the world."""
        self.rooms[room.name] = room

    def add_door(self, door: Door) -> None:
        """Add a door connecting two rooms."""
        self.doors.append(door)

    def add_object(self, obj: WorldObject) -> None:
        """Add an object to the world."""
        self.objects[obj.name] = obj

    # =========================================================================
    # Spatial Queries
    # =========================================================================

    def room_at(self, x: int, y: int) -> Optional[Room]:
        """Get the room containing a tile coordinate."""
        for room in self.rooms.values():
            if room.contains(x, y):
                return room
        return None

    def get_exits(self, room_name: str) -> List[Door]:
        """Get all doors leading out of a room."""
        exits = []
        for door in self.doors:
            if door.room_a == room_name or door.room_b == room_name:
                exits.append(door)
        return exits

    def get_door_in_direction(self, room_name: str, direction: Direction) -> Optional[Door]:
        """Get the door in a specific direction from a room."""
        for door in self.doors:
            if door.room_a == room_name and door.direction_from_a == direction:
                return door
            if door.room_b == room_name and door.direction_from_b == direction:
                return door
        return None

    def get_objects_in_room(self, room_name: str) -> List[WorldObject]:
        """Get all objects in a room."""
        return [obj for obj in self.objects.values() if obj.room == room_name]

    # =========================================================================
    # Text Description Generation (Deterministic!)
    # =========================================================================

    def describe_room(self, room_name: str,
                      visible_agents: List[AgentInfo] = None,
                      observer_name: str = None) -> str:
        """
        Generate a complete room description.

        Args:
            room_name: The room to describe
            visible_agents: List of agents visible in the room
            observer_name: Name of the observing agent (excluded from description)

        Returns:
            Deterministic prose description of the room
        """
        room = self.rooms.get(room_name)
        if not room:
            return "You are in an unknown location."

        parts = []

        # Base location
        parts.append(f"You are in {room.display_name}.")

        # Room template description (if any)
        if room.description_template and room.properties:
            try:
                desc = room.description_template.format(**room.properties)
                parts.append(desc)
            except KeyError:
                pass

        # Visible agents
        if visible_agents:
            agent_desc = self._describe_agents(visible_agents, observer_name)
            if agent_desc:
                parts.append(agent_desc)

        # Objects on the ground
        objects = self.get_objects_in_room(room_name)
        if objects:
            obj_desc = self._describe_objects(objects)
            parts.append(obj_desc)

        # Exits
        exits = self.get_exits(room_name)
        parts.append(self._describe_exits(room_name, exits))

        return " ".join(parts)

    def _describe_agents(self, agents: List[AgentInfo], observer_name: str = None) -> str:
        """Describe visible agents (excluding observer)."""
        others = [a for a in agents if a.name != observer_name and not a.is_player]
        if not others:
            return ""

        if len(others) == 1:
            return f"You see {others[0].display_name} here."
        else:
            names = [a.display_name for a in others]
            formatted = ", ".join(names[:-1]) + f" and {names[-1]}"
            return f"You see {formatted} here."

    def _describe_objects(self, objects: List[WorldObject]) -> str:
        """Describe objects in the room."""
        if not objects:
            return ""

        # Group by affordance for natural description
        takeable = [o for o in objects if "takeable" in o.affordances]
        furniture = [o for o in objects if "takeable" not in o.affordances]

        parts = []
        if takeable:
            if len(takeable) == 1:
                parts.append(f"On the ground you see {takeable[0].display_name}.")
            else:
                names = [o.display_name for o in takeable]
                formatted = ", ".join(names[:-1]) + f" and {names[-1]}"
                parts.append(f"On the ground you see {formatted}.")

        if furniture:
            for obj in furniture:
                parts.append(f"There is {obj.display_name} here.")

        return " ".join(parts)

    def _describe_exits(self, room_name: str, exits: List[Door]) -> str:
        """Describe available exits."""
        if not exits:
            return "There are no visible exits."

        exit_parts = []
        for door in exits:
            # Determine direction and destination from this room's perspective
            if door.room_a == room_name:
                direction = door.direction_from_a.value
                dest_room = self.rooms.get(door.room_b)
            else:
                direction = door.direction_from_b.value
                dest_room = self.rooms.get(door.room_a)

            dest_name = dest_room.display_name if dest_room else "unknown"

            if door.locked:
                exit_parts.append(f"{direction} ({dest_name}, locked)")
            else:
                exit_parts.append(f"{direction} ({dest_name})")

        # Sort for deterministic output
        exit_parts.sort()

        return "Exits: " + ", ".join(exit_parts) + "."

    # =========================================================================
    # Action Enumeration
    # =========================================================================

    def get_available_actions(self, room_name: str,
                              can_speak: bool = True) -> List[str]:
        """
        Get list of available actions for an agent in a room.

        Returns list of action strings like:
        ["GO NORTH", "GO EAST", "TAKE brass_key", "WAIT", "LOOK"]
        """
        actions = ["LOOK", "WAIT"]

        # Movement actions
        for door in self.get_exits(room_name):
            if door.room_a == room_name:
                direction = door.direction_from_a.value.upper()
            else:
                direction = door.direction_from_b.value.upper()

            if not door.locked:
                actions.append(f"GO {direction}")
            else:
                # Could add UNLOCK action here if agent has key
                pass

        # Object interactions
        for obj in self.get_objects_in_room(room_name):
            if "takeable" in obj.affordances:
                actions.append(f"TAKE {obj.name}")
            if "pushable" in obj.affordances:
                actions.append(f"PUSH {obj.name} <direction>")
            if "openable" in obj.affordances:
                actions.append(f"OPEN {obj.name}")
            if "readable" in obj.affordances:
                actions.append(f"READ {obj.name}")

        # Speech actions
        if can_speak:
            actions.append("ANNOUNCE '<message>'")
            actions.append("SPEAK '<message>'")

        return sorted(actions)


# =============================================================================
# Factory Functions for Common Scenarios
# =============================================================================

def create_two_room_scenario() -> WorldGraph:
    """
    Create a simple two-room test scenario.

    Layout:
    +--------+   +--------+
    | Room A |===| Room B |
    | (west) |   | (east) |
    +--------+   +--------+

    Room A: "the guard room" - contains a brass key
    Room B: "the armory" - destination room
    Door: unlocked, between rooms
    """
    world = WorldGraph()

    # Room A (left side)
    room_a = Room(
        name="guard_room",
        display_name="the guard room",
        bounds=(1, 1, 8, 8),  # x, y, width, height
        properties={"lit": True, "atmosphere": "musty"},
        description_template="The air is {atmosphere}."
    )
    world.add_room(room_a)

    # Room B (right side)
    room_b = Room(
        name="armory",
        display_name="the armory",
        bounds=(11, 1, 8, 8),
        properties={"lit": True, "atmosphere": "cold"},
        description_template="Weapon racks line the walls."
    )
    world.add_room(room_b)

    # Door connecting them
    door = Door(
        room_a="guard_room",
        room_b="armory",
        position=(9, 4),  # Between the rooms
        direction_from_a=Direction.EAST,
        locked=False
    )
    world.add_door(door)

    # Object in Room A
    key = WorldObject(
        name="brass_key",
        display_name="a brass key",
        room="guard_room",
        position=(3, 3),
        affordances=["takeable", "unlocks:dungeon_door"],
        description="A tarnished brass key with an ornate handle."
    )
    world.add_object(key)

    return world


def create_button_door_scenario() -> WorldGraph:
    """
    Create the Phase 1 scenario from issue #154.

    Layout:
    +----------+   +----------+
    | Room A   |   | Room B   |
    | [Button] |===| [Goal]   |
    | Agent A  |   | Agent B  |
    +----------+   +----------+

    - Door starts locked
    - Button in Room A unlocks the door
    - Agent A can reach button; Agent B's goal is blocked by door
    - Success: Agents coordinate to solve puzzle
    """
    world = WorldGraph()

    # Room A (button room)
    room_a = Room(
        name="button_room",
        display_name="the button room",
        bounds=(1, 1, 8, 8),
        properties={"lit": True}
    )
    world.add_room(room_a)

    # Room B (goal room)
    room_b = Room(
        name="goal_room",
        display_name="the goal room",
        bounds=(11, 1, 8, 8),
        properties={"lit": True}
    )
    world.add_room(room_b)

    # Locked door
    door = Door(
        room_a="button_room",
        room_b="goal_room",
        position=(9, 4),
        direction_from_a=Direction.EAST,
        locked=True,
        key_id="button_mechanism"
    )
    world.add_door(door)

    # Button in Room A
    button = WorldObject(
        name="wall_button",
        display_name="a large button on the wall",
        room="button_room",
        position=(2, 4),
        affordances=["pressable", "activates:main_door"],
        description="A heavy stone button protrudes from the wall."
    )
    world.add_object(button)

    # Goal marker in Room B
    goal = WorldObject(
        name="goal_marker",
        display_name="a glowing rune on the floor",
        room="goal_room",
        position=(15, 4),
        affordances=["examinable"],
        description="An arcane symbol pulses with soft light."
    )
    world.add_object(goal)

    return world
