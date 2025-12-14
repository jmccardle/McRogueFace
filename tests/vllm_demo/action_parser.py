"""
Action Parser for LLM Agent Responses
=====================================

Extracts structured actions from free-form LLM text responses.
Handles variations like "Action: GO EAST", "I'll go east", "GO E", etc.
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple, Any
from enum import Enum


class ActionType(Enum):
    GO = "GO"
    WAIT = "WAIT"
    LOOK = "LOOK"
    TAKE = "TAKE"
    DROP = "DROP"
    PUSH = "PUSH"
    USE = "USE"
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    ANNOUNCE = "ANNOUNCE"
    SPEAK = "SPEAK"
    INVALID = "INVALID"


@dataclass
class Action:
    type: ActionType
    args: Tuple[Any, ...] = ()
    raw_match: str = ""


class ActionParser:
    """Parse LLM responses into structured actions."""

    # Direction normalization
    DIRECTIONS = {
        'N': 'NORTH', 'S': 'SOUTH', 'E': 'EAST', 'W': 'WEST',
        'NORTH': 'NORTH', 'SOUTH': 'SOUTH', 'EAST': 'EAST', 'WEST': 'WEST',
        'UP': 'NORTH', 'DOWN': 'SOUTH', 'LEFT': 'WEST', 'RIGHT': 'EAST',
    }

    # Patterns ordered by specificity (most specific first)
    PATTERNS = [
        # Explicit "Action: X" format (preferred)
        (ActionType.GO, r'Action:\s*GO\s+(NORTH|SOUTH|EAST|WEST|N|S|E|W)\b', 1),
        (ActionType.WAIT, r'Action:\s*WAIT\b', 0),
        (ActionType.LOOK, r'Action:\s*LOOK(?:\s+AT\s+(\w+))?\b', 1),
        (ActionType.TAKE, r'Action:\s*TAKE\s+(\w+)', 1),
        (ActionType.DROP, r'Action:\s*DROP\s+(\w+)', 1),
        (ActionType.PUSH, r'Action:\s*PUSH\s+(\w+)\s+(NORTH|SOUTH|EAST|WEST|N|S|E|W)', 2),
        (ActionType.USE, r'Action:\s*USE\s+(\w+)(?:\s+ON\s+(\w+))?', 2),
        (ActionType.OPEN, r'Action:\s*OPEN\s+(\w+)', 1),
        (ActionType.CLOSE, r'Action:\s*CLOSE\s+(\w+)', 1),
        (ActionType.ANNOUNCE, r'Action:\s*ANNOUNCE\s+["\'](.+?)["\']', 1),
        (ActionType.SPEAK, r'Action:\s*SPEAK\s+["\'](.+?)["\']', 1),

        # Fallback patterns (less strict)
        (ActionType.GO, r'\bGO\s+(NORTH|SOUTH|EAST|WEST|N|S|E|W)\b', 1),
        (ActionType.GO, r'\bmove\s+(NORTH|SOUTH|EAST|WEST|N|S|E|W)\b', 1),
        (ActionType.GO, r'\bhead\s+(NORTH|SOUTH|EAST|WEST|N|S|E|W)\b', 1),
        (ActionType.WAIT, r'\bWAIT\b', 0),
        (ActionType.LOOK, r'\bLOOK\b', 0),
    ]

    def parse(self, llm_response: str) -> Action:
        """
        Parse an LLM response and extract the action.

        Returns Action with type=INVALID if no valid action found.
        """
        # Normalize to uppercase for matching
        text = llm_response.upper()

        for action_type, pattern, num_groups in self.PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                args = self._extract_args(match, num_groups, action_type)
                return Action(
                    type=action_type,
                    args=args,
                    raw_match=match.group(0)
                )

        # No valid action found
        return Action(
            type=ActionType.INVALID,
            args=(llm_response[:100],),  # First 100 chars for debugging
            raw_match=""
        )

    def _extract_args(self, match, num_groups: int, action_type: ActionType) -> tuple:
        """Extract and normalize arguments from regex match."""
        if num_groups == 0:
            return ()

        args = []
        for i in range(1, num_groups + 1):
            group = match.group(i)
            if group:
                # Normalize directions
                if action_type == ActionType.GO or (action_type == ActionType.PUSH and i == 2):
                    group = self.DIRECTIONS.get(group.upper(), group.upper())
                args.append(group)
            else:
                args.append(None)

        return tuple(args)


# Convenience function
def parse_action(llm_response: str) -> Action:
    """Parse an LLM response into an Action."""
    return ActionParser().parse(llm_response)
