"""
Enhanced Action Executor
========================

Extends ActionExecutor with:
- LOOK action with detailed descriptions
- SPEAK/ANNOUNCE execution with range checking
- Multi-tile path planning
- Free action vs turn-ending action handling
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any, Set
from action_parser import Action, ActionType
from action_executor import ActionResult
from action_economy import (
    TurnState, PathState, TurnCost, get_action_cost,
    manhattan_distance, get_direction_name
)


@dataclass
class TakeResult:
    """Result of a TAKE action."""
    success: bool
    message: str
    item_name: str
    item_position: Optional[Tuple[int, int]] = None


@dataclass
class LookResult:
    """Result of a LOOK action."""
    success: bool
    description: str
    target_name: str
    target_position: Optional[Tuple[int, int]] = None


@dataclass
class SpeechResult:
    """Result of a SPEAK/ANNOUNCE action."""
    success: bool
    message: str
    recipients: List[str]  # Names of agents who received the message
    speech_type: str  # "announce" or "speak"
    content: str  # What was said


@dataclass
class Message:
    """A message received by an agent."""
    sender: str
    content: str
    speech_type: str  # "announce" or "speak"
    turn: int
    distance: Optional[int] = None  # For SPEAK, how far away sender was


class EnhancedExecutor:
    """
    Enhanced action executor with LOOK, SPEAK, and multi-tile support.
    """

    # Direction vectors for movement
    DIRECTION_VECTORS = {
        'NORTH': (0, -1),
        'SOUTH': (0, 1),
        'EAST': (1, 0),
        'WEST': (-1, 0),
    }

    # SPEAK range (Manhattan distance)
    SPEAK_RANGE = 4

    def __init__(self, grid, world_graph=None):
        """
        Initialize executor.

        Args:
            grid: mcrfpy.Grid instance
            world_graph: Optional WorldGraph for detailed descriptions
        """
        self.grid = grid
        self.world = world_graph

        # Agent path states (agent_name -> PathState)
        self.path_states: Dict[str, PathState] = {}

        # Speech channel for message delivery
        self.pending_messages: Dict[str, List[Message]] = {}  # agent_name -> messages

    def get_path_state(self, agent_name: str) -> PathState:
        """Get or create path state for an agent."""
        if agent_name not in self.path_states:
            self.path_states[agent_name] = PathState()
        return self.path_states[agent_name]

    def get_pending_messages(self, agent_name: str) -> List[Message]:
        """Get and clear pending messages for an agent."""
        messages = self.pending_messages.get(agent_name, [])
        self.pending_messages[agent_name] = []
        return messages

    # =========================================================================
    # LOOK Action
    # =========================================================================

    def execute_look(self, agent, action: Action) -> LookResult:
        """
        Execute LOOK action - examine a tile or entity.

        Args:
            agent: Agent performing the look
            action: Parsed LOOK action with optional target

        Returns:
            LookResult with detailed description
        """
        target = action.args[0] if action.args and action.args[0] else None

        if target is None:
            # General look around
            return self._look_around(agent)
        else:
            # Look at specific target
            return self._look_at_target(agent, target.upper())

    def _look_around(self, agent) -> LookResult:
        """Describe the general surroundings."""
        ax, ay = int(agent.entity.pos[0]), int(agent.entity.pos[1])

        descriptions = []

        # Describe current room
        if self.world:
            room = self.world.room_at(ax, ay)
            if room:
                descriptions.append(f"You are in {room.display_name}.")
                if room.description_template and room.properties:
                    try:
                        desc = room.description_template.format(**room.properties)
                        descriptions.append(desc)
                    except KeyError:
                        pass

        # Count visible entities
        visible_count = 0
        for entity in self.grid.entities:
            ex, ey = int(entity.pos[0]), int(entity.pos[1])
            if (ex, ey) != (ax, ay) and self.grid.is_in_fov(ex, ey):
                visible_count += 1

        if visible_count > 0:
            descriptions.append(f"You can see {visible_count} other creature(s) nearby.")

        # Describe nearby walls/openings
        wall_dirs = []
        open_dirs = []
        for direction, (dx, dy) in self.DIRECTION_VECTORS.items():
            nx, ny = ax + dx, ay + dy
            if 0 <= nx < self.grid.grid_size[0] and 0 <= ny < self.grid.grid_size[1]:
                cell = self.grid.at(nx, ny)
                if cell.walkable:
                    open_dirs.append(direction.lower())
                else:
                    wall_dirs.append(direction.lower())

        if open_dirs:
            descriptions.append(f"Open passages: {', '.join(open_dirs)}.")
        if wall_dirs:
            descriptions.append(f"Walls to the: {', '.join(wall_dirs)}.")

        return LookResult(
            success=True,
            description=" ".join(descriptions),
            target_name="surroundings"
        )

    def _look_at_target(self, agent, target: str) -> LookResult:
        """Look at a specific target (direction, entity, or object name)."""
        ax, ay = int(agent.entity.pos[0]), int(agent.entity.pos[1])

        # Check if target is a direction
        if target in self.DIRECTION_VECTORS:
            return self._look_in_direction(agent, target)

        # Check if target matches an entity
        for entity in self.grid.entities:
            ex, ey = int(entity.pos[0]), int(entity.pos[1])
            if (ex, ey) == (ax, ay):
                continue

            entity_name = getattr(entity, 'name', '').upper()
            if target in entity_name or entity_name in target:
                if self.grid.is_in_fov(ex, ey):
                    return self._describe_entity(agent, entity)
                else:
                    return LookResult(
                        success=False,
                        description=f"You cannot see {target.lower()} from here.",
                        target_name=target.lower()
                    )

        # Check WorldGraph objects
        if self.world:
            room = self.world.room_at(ax, ay)
            if room:
                for obj in self.world.get_objects_in_room(room.name):
                    if target in obj.name.upper() or obj.name.upper() in target:
                        ox, oy = obj.position
                        if self.grid.is_in_fov(ox, oy):
                            return self._describe_object(agent, obj)

                # Check doors
                for door in self.world.get_exits(room.name):
                    if "DOOR" in target:
                        dx, dy = door.position
                        if self.grid.is_in_fov(dx, dy):
                            return self._describe_door(agent, door)

        return LookResult(
            success=False,
            description=f"You don't see anything called '{target.lower()}' nearby.",
            target_name=target.lower()
        )

    def _look_in_direction(self, agent, direction: str) -> LookResult:
        """Look in a cardinal direction."""
        ax, ay = int(agent.entity.pos[0]), int(agent.entity.pos[1])
        dx, dy = self.DIRECTION_VECTORS[direction]

        descriptions = []

        # Scan tiles in that direction
        for distance in range(1, 10):
            tx, ty = ax + dx * distance, ay + dy * distance

            if not (0 <= tx < self.grid.grid_size[0] and 0 <= ty < self.grid.grid_size[1]):
                descriptions.append(f"The edge of the known world lies {direction.lower()}.")
                break

            if not self.grid.is_in_fov(tx, ty):
                descriptions.append(f"Darkness obscures your vision beyond {distance} tiles.")
                break

            cell = self.grid.at(tx, ty)

            # Check for entity at this tile
            for entity in self.grid.entities:
                ex, ey = int(entity.pos[0]), int(entity.pos[1])
                if (ex, ey) == (tx, ty):
                    entity_name = getattr(entity, 'name', 'creature')
                    descriptions.append(f"A {entity_name} stands {distance} tile(s) to the {direction.lower()}.")

            # Check for wall
            if not cell.walkable:
                # Check if it's a door
                if self.world:
                    room = self.world.room_at(ax, ay)
                    if room:
                        for door in self.world.get_exits(room.name):
                            if door.position == (tx, ty):
                                dest = self.world.rooms.get(
                                    door.room_b if door.room_a == room.name else door.room_a
                                )
                                dest_name = dest.display_name if dest else "another area"
                                lock_str = " It is locked." if door.locked else ""
                                descriptions.append(
                                    f"A door to {dest_name} lies {distance} tile(s) {direction.lower()}.{lock_str}"
                                )
                                break
                        else:
                            descriptions.append(f"A wall blocks passage {distance} tile(s) to the {direction.lower()}.")
                    else:
                        descriptions.append(f"A wall blocks passage {distance} tile(s) to the {direction.lower()}.")
                else:
                    descriptions.append(f"A wall blocks passage {distance} tile(s) to the {direction.lower()}.")
                break

        if not descriptions:
            descriptions.append(f"Open floor extends to the {direction.lower()}.")

        return LookResult(
            success=True,
            description=" ".join(descriptions),
            target_name=direction.lower(),
            target_position=None
        )

    def _describe_entity(self, agent, entity) -> LookResult:
        """Generate detailed description of an entity."""
        ax, ay = int(agent.entity.pos[0]), int(agent.entity.pos[1])
        ex, ey = int(entity.pos[0]), int(entity.pos[1])

        entity_name = getattr(entity, 'name', 'creature')
        direction = get_direction_name((ax, ay), (ex, ey))
        distance = manhattan_distance((ax, ay), (ex, ey))

        descriptions = [
            f"You examine the {entity_name} carefully.",
            f"It stands {distance} tile(s) to the {direction}."
        ]

        # Add any entity-specific description
        if hasattr(entity, 'description'):
            descriptions.append(entity.description)

        # Add behavior hints if available
        if hasattr(entity, 'behavior'):
            descriptions.append(f"It appears to be {entity.behavior}.")

        return LookResult(
            success=True,
            description=" ".join(descriptions),
            target_name=entity_name,
            target_position=(ex, ey)
        )

    def _describe_object(self, agent, obj) -> LookResult:
        """Generate detailed description of a WorldGraph object."""
        ax, ay = int(agent.entity.pos[0]), int(agent.entity.pos[1])
        ox, oy = obj.position

        direction = get_direction_name((ax, ay), (ox, oy))
        distance = manhattan_distance((ax, ay), (ox, oy))

        descriptions = [
            f"You examine {obj.display_name}.",
            f"It is {distance} tile(s) to the {direction}."
        ]

        if obj.description:
            descriptions.append(obj.description)

        # Describe affordances
        if "takeable" in obj.affordances:
            descriptions.append("It looks small enough to pick up.")
        if "pressable" in obj.affordances:
            descriptions.append("It appears to be some kind of mechanism.")
        if "openable" in obj.affordances:
            descriptions.append("It can be opened.")
        if "readable" in obj.affordances:
            descriptions.append("There is writing on it.")

        return LookResult(
            success=True,
            description=" ".join(descriptions),
            target_name=obj.name,
            target_position=(ox, oy)
        )

    def _describe_door(self, agent, door) -> LookResult:
        """Generate detailed description of a door."""
        ax, ay = int(agent.entity.pos[0]), int(agent.entity.pos[1])
        dx, dy = door.position

        direction = get_direction_name((ax, ay), (dx, dy))
        distance = manhattan_distance((ax, ay), (dx, dy))

        # Get destination
        if self.world:
            current_room = self.world.room_at(ax, ay)
            if current_room:
                if door.room_a == current_room.name:
                    dest = self.world.rooms.get(door.room_b)
                else:
                    dest = self.world.rooms.get(door.room_a)
                dest_name = dest.display_name if dest else "another area"
            else:
                dest_name = "another area"
        else:
            dest_name = "another area"

        descriptions = [
            f"You examine the doorway to the {direction}.",
            f"It leads to {dest_name}, {distance} tile(s) away."
        ]

        if door.locked:
            descriptions.append("The door is locked. You'll need a key or mechanism to open it.")
        else:
            descriptions.append("The passage is open.")

        return LookResult(
            success=True,
            description=" ".join(descriptions),
            target_name="door",
            target_position=(dx, dy)
        )

    # =========================================================================
    # SPEAK/ANNOUNCE Actions
    # =========================================================================

    def execute_speech(self, agent, action: Action, all_agents: list,
                       turn_number: int) -> SpeechResult:
        """
        Execute SPEAK or ANNOUNCE action.

        ANNOUNCE: All agents in the same room hear the message
        SPEAK: Only agents within SPEAK_RANGE tiles hear the message
        """
        message_content = action.args[0] if action.args else ""

        if not message_content:
            return SpeechResult(
                success=False,
                message="Nothing to say.",
                recipients=[],
                speech_type=action.type.value.lower(),
                content=""
            )

        ax, ay = int(agent.entity.pos[0]), int(agent.entity.pos[1])
        recipients = []

        if action.type == ActionType.ANNOUNCE:
            # Room-wide broadcast
            recipients = self._get_agents_in_room(agent, all_agents)
            speech_type = "announce"
        else:
            # Proximity-based speech
            recipients = self._get_agents_in_range(agent, all_agents, self.SPEAK_RANGE)
            speech_type = "speak"

        # Deliver messages
        for recipient in recipients:
            if recipient.name not in self.pending_messages:
                self.pending_messages[recipient.name] = []

            distance = manhattan_distance(
                (ax, ay),
                (int(recipient.entity.pos[0]), int(recipient.entity.pos[1]))
            ) if speech_type == "speak" else None

            self.pending_messages[recipient.name].append(Message(
                sender=agent.name,
                content=message_content,
                speech_type=speech_type,
                turn=turn_number,
                distance=distance
            ))

        recipient_names = [r.name for r in recipients]

        if recipients:
            return SpeechResult(
                success=True,
                message=f"You {speech_type}: \"{message_content}\"",
                recipients=recipient_names,
                speech_type=speech_type,
                content=message_content
            )
        else:
            return SpeechResult(
                success=True,  # Still succeeds, just nobody heard
                message=f"You {speech_type} into the emptiness: \"{message_content}\"",
                recipients=[],
                speech_type=speech_type,
                content=message_content
            )

    def _get_agents_in_room(self, speaker, all_agents: list) -> list:
        """Get all agents in the same room as speaker (excluding speaker)."""
        if not self.world:
            # Fallback: use proximity
            return self._get_agents_in_range(speaker, all_agents, 20)

        ax, ay = int(speaker.entity.pos[0]), int(speaker.entity.pos[1])
        speaker_room = self.world.room_at(ax, ay)

        if not speaker_room:
            return []

        recipients = []
        for agent in all_agents:
            if agent.name == speaker.name:
                continue
            rx, ry = int(agent.entity.pos[0]), int(agent.entity.pos[1])
            agent_room = self.world.room_at(rx, ry)
            if agent_room and agent_room.name == speaker_room.name:
                recipients.append(agent)

        return recipients

    def _get_agents_in_range(self, speaker, all_agents: list, range_tiles: int) -> list:
        """Get all agents within Manhattan distance of speaker."""
        ax, ay = int(speaker.entity.pos[0]), int(speaker.entity.pos[1])

        recipients = []
        for agent in all_agents:
            if agent.name == speaker.name:
                continue
            rx, ry = int(agent.entity.pos[0]), int(agent.entity.pos[1])
            if manhattan_distance((ax, ay), (rx, ry)) <= range_tiles:
                recipients.append(agent)

        return recipients

    # =========================================================================
    # TAKE Action
    # =========================================================================

    def execute_take(self, agent, action: Action) -> TakeResult:
        """
        Execute TAKE action - pick up an item.

        Items must be:
        1. In the WorldGraph as a takeable object
        2. Within reach (adjacent tile or same tile, distance <= 1)
        3. Visible in FOV
        """
        item_name = action.args[0].lower() if action.args and action.args[0] else None

        if not item_name:
            return TakeResult(
                success=False,
                message="Take what? Specify an item name.",
                item_name=""
            )

        ax, ay = int(agent.entity.pos[0]), int(agent.entity.pos[1])

        # Search for the item in WorldGraph
        if not self.world:
            return TakeResult(
                success=False,
                message="No items exist in this world.",
                item_name=item_name
            )

        # Find matching object
        matching_obj = None
        for obj_name, obj in self.world.objects.items():
            if item_name in obj_name.lower() or obj_name.lower() in item_name:
                matching_obj = obj
                break

        if not matching_obj:
            return TakeResult(
                success=False,
                message=f"You don't see any '{item_name}' here.",
                item_name=item_name
            )

        # Check if takeable
        if "takeable" not in matching_obj.affordances:
            return TakeResult(
                success=False,
                message=f"The {matching_obj.display_name} cannot be picked up.",
                item_name=item_name,
                item_position=matching_obj.position
            )

        ox, oy = matching_obj.position

        # Check if visible in FOV
        if not self.grid.is_in_fov(ox, oy):
            return TakeResult(
                success=False,
                message=f"You can't see the {matching_obj.display_name} from here.",
                item_name=item_name,
                item_position=(ox, oy)
            )

        # Check distance (must be adjacent or same tile)
        distance = manhattan_distance((ax, ay), (ox, oy))
        if distance > 1:
            direction = get_direction_name((ax, ay), (ox, oy))
            # Use name for cleaner message (display_name often has article already)
            return TakeResult(
                success=False,
                message=f"The {matching_obj.name.replace('_', ' ')} is {distance} tiles away to the {direction}. Move closer to pick it up.",
                item_name=item_name,
                item_position=(ox, oy)
            )

        # Success! Remove from world (simplified - no inventory system yet)
        del self.world.objects[matching_obj.name]

        return TakeResult(
            success=True,
            message=f"You pick up {matching_obj.display_name}.",
            item_name=matching_obj.name,
            item_position=(ox, oy)
        )

    # =========================================================================
    # Movement (single tile, delegates to original executor)
    # =========================================================================

    def execute_move(self, agent, action: Action) -> ActionResult:
        """
        Execute single-tile movement.

        This is the per-turn movement. Multi-tile paths are handled
        at the orchestrator level.
        """
        if not action.args or not action.args[0]:
            return ActionResult(False, "No direction specified")

        direction = action.args[0]
        if direction not in self.DIRECTION_VECTORS:
            return ActionResult(False, f"Invalid direction: {direction}")

        dx, dy = self.DIRECTION_VECTORS[direction]
        current_x, current_y = int(agent.entity.pos[0]), int(agent.entity.pos[1])
        new_x, new_y = current_x + dx, current_y + dy

        # Bounds check
        grid_w, grid_h = self.grid.grid_size
        if not (0 <= new_x < grid_w and 0 <= new_y < grid_h):
            return ActionResult(False, f"Cannot go {direction} - edge of map")

        # Walkability check
        target_cell = self.grid.at(new_x, new_y)
        if not target_cell.walkable:
            return ActionResult(False, f"Cannot go {direction} - path blocked")

        # Entity collision check
        for entity in self.grid.entities:
            if entity is agent.entity:
                continue
            ex, ey = int(entity.pos[0]), int(entity.pos[1])
            if ex == new_x and ey == new_y:
                return ActionResult(False, f"Cannot go {direction} - occupied")

        # Execute movement
        agent.entity.pos = (new_x, new_y)

        return ActionResult(
            success=True,
            message=f"Moved {direction.lower()} to ({new_x}, {new_y})",
            new_position=(new_x, new_y),
            path=[(current_x, current_y), (new_x, new_y)]
        )

    def execute_wait(self, agent, action: Action) -> ActionResult:
        """Execute WAIT action."""
        return ActionResult(True, "Waited and observed surroundings")

    # =========================================================================
    # Multi-tile Pathfinding
    # =========================================================================

    def plan_path_to(self, agent, target_pos: Tuple[int, int],
                     visible_entities: Set[str]) -> Optional[List[Tuple[int, int]]]:
        """
        Plan a path to a target position.

        Uses A* via libtcod if available, otherwise simple pathfinding.
        Returns list of tiles from current position to target (excluding current).
        """
        try:
            from mcrfpy import libtcod
            ax, ay = int(agent.entity.pos[0]), int(agent.entity.pos[1])

            path = libtcod.find_path(self.grid, ax, ay, target_pos[0], target_pos[1])

            if path:
                # Store path state
                path_state = self.get_path_state(agent.name)
                path_state.path = path
                path_state.current_index = 0
                path_state.visible_entities_at_start = visible_entities.copy()

                return path
        except ImportError:
            pass

        return None

    def continue_path(self, agent, current_visible: Set[str]) -> Optional[ActionResult]:
        """
        Continue an existing multi-tile path.

        Returns ActionResult if moved, None if path complete or interrupted.
        """
        path_state = self.get_path_state(agent.name)

        if not path_state.has_path:
            return None

        # Check for FOV interrupt
        if path_state.should_interrupt(current_visible):
            path_state.clear()
            return None  # Signal that LLM should be queried

        # Get next tile
        next_tile = path_state.next_tile
        if not next_tile:
            path_state.clear()
            return None

        # Move to next tile
        current_x, current_y = int(agent.entity.pos[0]), int(agent.entity.pos[1])
        new_x, new_y = next_tile

        # Verify still walkable
        target_cell = self.grid.at(new_x, new_y)
        if not target_cell.walkable:
            path_state.clear()
            return ActionResult(False, "Path blocked - recalculating")

        # Check for entity collision
        for entity in self.grid.entities:
            if entity is agent.entity:
                continue
            ex, ey = int(entity.pos[0]), int(entity.pos[1])
            if ex == new_x and ey == new_y:
                path_state.clear()
                return ActionResult(False, "Path blocked by creature")

        # Execute movement
        agent.entity.pos = (new_x, new_y)
        path_state.advance()

        remaining = path_state.remaining_tiles
        if remaining > 0:
            msg = f"Continuing path ({remaining} tiles remaining)"
        else:
            msg = "Arrived at destination"
            path_state.clear()

        return ActionResult(
            success=True,
            message=msg,
            new_position=(new_x, new_y),
            path=[(current_x, current_y), (new_x, new_y)]
        )
