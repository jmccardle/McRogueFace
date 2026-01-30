# McRogueFace Game-to-API Bridge

A general-purpose API layer that exposes any McRogueFace game to external clients (LLMs, accessibility tools, Twitch integrations, testing harnesses).

## Quick Start

```python
# In your game script
import sys
sys.path.insert(0, '../src/scripts')
from api import start_server

# Start the API server
server = start_server(8765)
```

The API will be available at `http://localhost:8765`.

## API Endpoints

### GET /health
Health check endpoint.

```bash
curl http://localhost:8765/health
```

### GET /scene
Returns the current scene graph with all UI elements.

```bash
curl http://localhost:8765/scene
```

Response includes:
- Scene name
- Viewport dimensions
- All UI elements with type, bounds, visibility, interactivity
- Nested children
- Type-specific properties (text for Caption, grid_size for Grid, etc.)

### GET /affordances
Returns only interactive elements with semantic labels.

```bash
curl http://localhost:8765/affordances
```

Response includes:
- List of clickable elements with:
  - `id`: Unique affordance ID (for click_affordance)
  - `label`: Human-readable label (button text or element name)
  - `type`: Affordance type (button, text_button, icon_button, interactive_grid)
  - `bounds`: Position and size
  - `actions`: Available actions (click, hover, grid_cell_click)
  - `hint`: Developer label if different from display label
- Default keyboard hints

### GET /screenshot
Returns a screenshot of the current game state.

```bash
# Binary PNG
curl http://localhost:8765/screenshot -o screenshot.png

# Base64 JSON
curl "http://localhost:8765/screenshot?format=base64"
```

### GET /metadata
Returns game metadata for LLM context.

```bash
curl http://localhost:8765/metadata
```

### POST /input
Inject keyboard or mouse input.

```bash
# Click at coordinates
curl -X POST -H "Content-Type: application/json" \
  -d '{"action":"click","x":150,"y":100}' \
  http://localhost:8765/input

# Click affordance by label (fuzzy match)
curl -X POST -H "Content-Type: application/json" \
  -d '{"action":"click_affordance","label":"Play"}' \
  http://localhost:8765/input

# Press a key
curl -X POST -H "Content-Type: application/json" \
  -d '{"action":"key","key":"W"}' \
  http://localhost:8765/input

# Type text
curl -X POST -H "Content-Type: application/json" \
  -d '{"action":"type","text":"Hello"}' \
  http://localhost:8765/input

# Key combination
curl -X POST -H "Content-Type: application/json" \
  -d '{"action":"hotkey","keys":["ctrl","s"]}' \
  http://localhost:8765/input
```

### GET /wait
Long-poll endpoint that returns when scene state changes.

```bash
curl "http://localhost:8765/wait?timeout=30&scene_hash=abc123"
```

## Customizing Game Metadata

Games can provide rich metadata for external clients:

```python
from api.metadata import (
    set_game_info,
    set_controls,
    set_keyboard_hints,
    set_custom_hints,
)

set_game_info(
    name="My Game",
    version="1.0.0",
    description="A puzzle roguelike"
)

set_controls({
    "movement": "W/A/S/D",
    "attack": "Space",
})

set_keyboard_hints([
    {"key": "W", "action": "Move up"},
    {"key": "Space", "action": "Attack"},
])

set_custom_hints("""
Strategy tips:
- Always check corners
- Save potions for boss fights
""")
```

## Affordance Detection

The API automatically detects interactive elements:

1. **Buttons**: Frame with on_click + Caption child
2. **Icon Buttons**: Frame with on_click + Sprite child
3. **Interactive Grids**: Grid with on_cell_click
4. **Text Buttons**: Caption with on_click

Labels are extracted from:
1. Caption text inside the element
2. Element's `name` property (developer hint)

Set meaningful `name` properties on your interactive elements for best results:

```python
button = mcrfpy.Frame(...)
button.name = "attack_button"  # Will show in affordances
```

## Use Cases

- **LLM Co-Play**: AI analyzes game state via /scene and /affordances, sends moves via /input
- **Accessibility**: Screen readers can get semantic labels from /affordances
- **Twitch Plays**: Aggregate chat votes and inject via /input
- **Automated Testing**: Query state, inject inputs, verify outcomes

## Architecture

```
┌─────────────────────────────────┐
│     McRogueFace Game Loop       │
│  (Main Thread - renders game)   │
└────────────────┬────────────────┘
                 │
┌────────────────┴────────────────┐
│   API Server (Background Thread)│
│  - Introspects scene graph      │
│  - Injects input via automation │
└────────────────┬────────────────┘
                 │ HTTP :8765
                 ▼
┌─────────────────────────────────┐
│       External Clients          │
│  (LLMs, tests, accessibility)   │
└─────────────────────────────────┘
```

The API server runs in a daemon thread and uses `mcrfpy.lock()` for thread-safe access to the scene graph.
