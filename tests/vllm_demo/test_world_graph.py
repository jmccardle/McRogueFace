"""
Unit tests for WorldGraph
"""

from world_graph import (
    WorldGraph, Room, Door, WorldObject, Direction,
    AgentInfo, create_two_room_scenario, create_button_door_scenario
)

def test_room_contains():
    """Test room boundary checking."""
    room = Room("test", "test room", bounds=(5, 5, 10, 10))

    assert room.contains(5, 5) == True   # Top-left corner
    assert room.contains(14, 14) == True # Bottom-right (exclusive)
    assert room.contains(15, 15) == False # Outside
    assert room.contains(4, 5) == False  # Just outside left

    print("PASS: room_contains")

def test_room_at():
    """Test spatial room lookup."""
    world = create_two_room_scenario()

    # Guard room is at (1,1) with size (8,8)
    room = world.room_at(3, 3)
    assert room is not None
    assert room.name == "guard_room"

    # Armory is at (11,1) with size (8,8)
    room = world.room_at(13, 3)
    assert room is not None
    assert room.name == "armory"

    # Between rooms (the door area) - should return None
    room = world.room_at(9, 4)
    assert room is None

    print("PASS: room_at")

def test_describe_room_basic():
    """Test basic room description."""
    world = create_two_room_scenario()

    desc = world.describe_room("guard_room")

    assert "You are in the guard room" in desc
    assert "brass key" in desc
    assert "Exits:" in desc
    assert "east" in desc
    assert "armory" in desc

    print("PASS: describe_room_basic")
    print(f"  Output: {desc}")

def test_describe_room_with_agents():
    """Test room description with visible agents."""
    world = create_two_room_scenario()

    agents = [
        AgentInfo("Wizard", "a wizard", (3, 3)),
        AgentInfo("Knight", "a knight", (4, 4)),
    ]

    desc = world.describe_room("guard_room", visible_agents=agents, observer_name="Wizard")

    assert "knight" in desc.lower()
    assert "wizard" not in desc.lower()  # Observer excluded

    print("PASS: describe_room_with_agents")
    print(f"  Output: {desc}")

def test_describe_locked_door():
    """Test that locked doors are described correctly."""
    world = create_button_door_scenario()

    desc = world.describe_room("button_room")

    assert "locked" in desc.lower()

    print("PASS: describe_locked_door")
    print(f"  Output: {desc}")

def test_available_actions():
    """Test action enumeration."""
    world = create_two_room_scenario()

    actions = world.get_available_actions("guard_room")

    assert "GO EAST" in actions
    assert "TAKE brass_key" in actions
    assert "LOOK" in actions
    assert "WAIT" in actions

    print("PASS: available_actions")
    print(f"  Actions: {actions}")

def test_determinism():
    """Test that descriptions are deterministic."""
    world = create_two_room_scenario()

    desc1 = world.describe_room("guard_room")
    desc2 = world.describe_room("guard_room")
    desc3 = world.describe_room("guard_room")

    assert desc1 == desc2 == desc3, "Descriptions must be deterministic!"

    print("PASS: determinism")

def test_direction_opposites():
    """Test direction opposite calculation."""
    assert Direction.NORTH.opposite == Direction.SOUTH
    assert Direction.SOUTH.opposite == Direction.NORTH
    assert Direction.EAST.opposite == Direction.WEST
    assert Direction.WEST.opposite == Direction.EAST

    print("PASS: direction_opposites")

def run_all_tests():
    """Run all WorldGraph tests."""
    print("=" * 50)
    print("WorldGraph Unit Tests")
    print("=" * 50)

    test_room_contains()
    test_room_at()
    test_describe_room_basic()
    test_describe_room_with_agents()
    test_describe_locked_door()
    test_available_actions()
    test_determinism()
    test_direction_opposites()

    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)

if __name__ == "__main__":
    run_all_tests()
