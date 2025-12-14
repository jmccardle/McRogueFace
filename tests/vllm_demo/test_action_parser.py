#!/usr/bin/env python3
"""
Unit tests for action_parser.py
===============================

Tests the ActionParser's ability to extract structured actions
from various LLM response formats.
"""

import sys
from action_parser import parse_action, ActionType


def test_explicit_go_directions():
    """Test explicit 'Action: GO <direction>' format."""
    # Cardinal directions
    assert parse_action("Action: GO NORTH").type == ActionType.GO
    assert parse_action("Action: GO NORTH").args == ("NORTH",)

    assert parse_action("Action: GO SOUTH").type == ActionType.GO
    assert parse_action("Action: GO SOUTH").args == ("SOUTH",)

    assert parse_action("Action: GO EAST").type == ActionType.GO
    assert parse_action("Action: GO EAST").args == ("EAST",)

    assert parse_action("Action: GO WEST").type == ActionType.GO
    assert parse_action("Action: GO WEST").args == ("WEST",)

    print("  [PASS] Explicit GO directions")


def test_short_directions():
    """Test short direction abbreviations (N, S, E, W)."""
    assert parse_action("Action: GO N").args == ("NORTH",)
    assert parse_action("Action: GO S").args == ("SOUTH",)
    assert parse_action("Action: GO E").args == ("EAST",)
    assert parse_action("Action: GO W").args == ("WEST",)

    print("  [PASS] Short direction abbreviations")


def test_case_insensitivity():
    """Test that parsing is case-insensitive."""
    assert parse_action("action: go south").type == ActionType.GO
    assert parse_action("ACTION: GO SOUTH").type == ActionType.GO
    assert parse_action("Action: Go South").type == ActionType.GO
    assert parse_action("action: GO south").type == ActionType.GO

    print("  [PASS] Case insensitivity")


def test_fallback_patterns():
    """Test fallback patterns without 'Action:' prefix."""
    # Natural language variations
    assert parse_action("I think I'll GO WEST to explore").type == ActionType.GO
    assert parse_action("I'll GO NORTH").type == ActionType.GO
    assert parse_action("Let me GO EAST").type == ActionType.GO

    # Move variations
    assert parse_action("I should move NORTH").type == ActionType.GO
    assert parse_action("Let me head SOUTH").type == ActionType.GO

    print("  [PASS] Fallback patterns")


def test_wait_action():
    """Test WAIT action parsing."""
    assert parse_action("Action: WAIT").type == ActionType.WAIT
    assert parse_action("I'll WAIT here").type == ActionType.WAIT
    assert parse_action("Let me WAIT and see").type == ActionType.WAIT

    print("  [PASS] WAIT action")


def test_look_action():
    """Test LOOK action parsing."""
    assert parse_action("Action: LOOK").type == ActionType.LOOK
    assert parse_action("Action: LOOK AT door").type == ActionType.LOOK
    assert parse_action("Action: LOOK AT door").args == ("DOOR",)

    print("  [PASS] LOOK action")


def test_invalid_actions():
    """Test that invalid actions are properly flagged."""
    result = parse_action("I'm not sure what to do")
    assert result.type == ActionType.INVALID

    result = parse_action("Let me think about this...")
    assert result.type == ActionType.INVALID

    result = parse_action("The weather is nice today")
    assert result.type == ActionType.INVALID

    print("  [PASS] Invalid action detection")


def test_raw_match_capture():
    """Test that raw_match captures the matched text."""
    result = parse_action("After thinking, Action: GO NORTH is best")
    assert "GO NORTH" in result.raw_match

    print("  [PASS] Raw match capture")


def test_embedded_actions():
    """Test extraction of actions embedded in longer text."""
    long_response = """
    Looking at the screenshot, I can see I'm in a dungeon corridor.
    There's a rat to the east and a wall to the north.
    The path south appears clear.

    I think the best course of action is to investigate the rat.

    Action: GO EAST
    """

    result = parse_action(long_response)
    assert result.type == ActionType.GO
    assert result.args == ("EAST",)

    print("  [PASS] Embedded action extraction")


def test_complex_actions():
    """Test more complex action types."""
    # TAKE action
    assert parse_action("Action: TAKE sword").type == ActionType.TAKE
    assert parse_action("Action: TAKE sword").args == ("SWORD",)

    # DROP action
    assert parse_action("Action: DROP shield").type == ActionType.DROP

    # USE action
    assert parse_action("Action: USE key").type == ActionType.USE
    assert parse_action("Action: USE key ON door").type == ActionType.USE

    # OPEN/CLOSE
    assert parse_action("Action: OPEN chest").type == ActionType.OPEN
    assert parse_action("Action: CLOSE door").type == ActionType.CLOSE

    print("  [PASS] Complex action types")


def test_push_action():
    """Test PUSH action with direction."""
    result = parse_action("Action: PUSH boulder NORTH")
    assert result.type == ActionType.PUSH
    assert result.args == ("BOULDER", "NORTH")

    result = parse_action("Action: PUSH box E")
    assert result.type == ActionType.PUSH
    assert result.args == ("BOX", "EAST")

    print("  [PASS] PUSH action")


def test_speak_announce_actions():
    """Test SPEAK and ANNOUNCE with quoted strings."""
    result = parse_action('Action: SPEAK "Hello there!"')
    assert result.type == ActionType.SPEAK
    assert result.args[0] == "HELLO THERE!"  # Uppercase due to text normalization

    result = parse_action("Action: ANNOUNCE 'Watch out!'")
    assert result.type == ActionType.ANNOUNCE

    print("  [PASS] SPEAK/ANNOUNCE actions")


def run_all_tests():
    """Run all parser tests."""
    print("=" * 60)
    print("Action Parser Tests")
    print("=" * 60)

    tests = [
        test_explicit_go_directions,
        test_short_directions,
        test_case_insensitivity,
        test_fallback_patterns,
        test_wait_action,
        test_look_action,
        test_invalid_actions,
        test_raw_match_capture,
        test_embedded_actions,
        test_complex_actions,
        test_push_action,
        test_speak_announce_actions,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {test.__name__}: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
