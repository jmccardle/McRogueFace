# Offline Viewer Specification

**Status**: Planned (issue #154)
**Priority**: After core simulation features are stable

## Overview

The Offline Viewer allows users to replay stored simulation logs in McRogueFace, stepping through turn-by-turn to review:
- Each agent's perspective (FOV, camera position)
- LLM chain-of-thought reasoning
- Actions taken and their results
- Speech between agents

## Log Format

Simulation logs are stored as JSON with this structure:

```json
{
  "metadata": {
    "total_turns": 5,
    "num_agents": 2,
    "agent_names": ["Wizard", "Knight"],
    "timestamp_start": "2025-01-15T10:30:00",
    "timestamp_end": "2025-01-15T10:32:45",
    "world_rooms": ["guard_room", "armory"],
    "screenshot_dir": "/tmp/vllm_enhanced_demo"
  },
  "steps": [
    {
      "turn": 1,
      "agent_id": "Wizard",
      "timestamp": "2025-01-15T10:30:15",

      "position_start": [5, 4],
      "position_end": [6, 4],
      "room": "guard_room",

      "visible_entities": ["rat_123", "knight_456"],
      "visible_tiles": 42,
      "points_of_interest": [
        {"name": "door", "direction": "east", "distance": 4}
      ],

      "location_description": "You are in the guard room...",
      "available_actions": ["GO EAST", "LOOK", "WAIT"],
      "pending_messages": [],
      "poi_prompt": "Points of interest:\n  - a door to the armory (east)",

      "screenshot_path": "/tmp/.../turn1_wizard.png",

      "llm_prompt_system": "You are a wizard...",
      "llm_prompt_user": "You are in the guard room...",
      "llm_response": "I see a door to the east. I should explore. Action: GO EAST",
      "llm_was_queried": true,

      "free_actions": [
        {"action_type": "LOOK", "args": ["DOOR"], "result": {"description": "A wooden door..."}}
      ],

      "final_action_type": "GO",
      "final_action_args": ["EAST"],
      "final_action_success": true,
      "final_action_message": "Moved east to (6, 4)",

      "path_taken": [[5, 4], [6, 4]],
      "path_remaining": 0
    }
  ],
  "speech_log": [
    {
      "turn": 2,
      "speaker": "Wizard",
      "type": "announce",
      "content": "Hello, is anyone there?",
      "recipients": ["Knight"]
    }
  ]
}
```

## Viewer Features (Planned)

### Core Features

1. **Turn Navigation**
   - Step forward/backward through turns
   - Jump to specific turn number
   - Auto-play at configurable speed

2. **Agent Perspective**
   - Reconstruct agent's FOV from stored data
   - Center camera on current agent
   - Show visible entities and tiles

3. **LLM Review Panel**
   - Display system prompt
   - Display user prompt (context)
   - Display LLM response
   - Highlight parsed action

4. **Action Log**
   - Show free actions (LOOK, SPEAK)
   - Show final action and result
   - Color-code success/failure

5. **Speech History**
   - Timeline of all speech events
   - Filter by agent
   - Show recipients

### Implementation Notes

The viewer should:
- Load screenshots from `screenshot_path` (if available)
- OR reconstruct scene from WorldGraph + step data
- Support keyboard navigation (arrow keys)
- Display agent state in sidebar

### UI Layout (Suggested)

```
+----------------------------------+------------------+
|                                  |  Turn: 3/10      |
|     Main Viewport               |  Agent: Wizard   |
|     (Agent's Perspective)        |  Room: armory    |
|                                  +------------------+
|                                  |  LLM Response:   |
|                                  |  "I see a rat    |
|                                  |   to the east.   |
|                                  |   Action: LOOK   |
|                                  |   AT RAT"        |
+----------------------------------+------------------+
|  < Prev | Turn 3 | Next >        |  Actions:        |
|  [Agent: Wizard v]               |  - LOOK AT RAT   |
|                                  |  - GO EAST [OK]  |
+----------------------------------+------------------+
```

## Files

- `enhanced_orchestrator.py` - Generates `EnhancedSimulationLog`
- `4_enhanced_action_demo.py` - Demo with `--replay` mode for text preview
- Logs stored in `/tmp/vllm_enhanced_demo/simulation_log.json`

## Future Enhancements

- Animated path replay (smooth entity movement)
- Side-by-side multi-agent view
- Diff view comparing agent perceptions
- Export to video/GIF
- Integration with annotation tools for research
