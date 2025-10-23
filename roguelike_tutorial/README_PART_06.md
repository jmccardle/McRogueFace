# Part 6: Doing (and Taking) Damage

## Overview

Part 6 transforms our basic combat into a complete gameplay loop with visual feedback, enemy AI, and win/lose conditions. We add a health bar, message log, enemy AI that pursues the player, and proper game over handling.

## What's New in Part 6

### User Interface Components

#### Health Bar
A visual representation of the player's current health:
```python
class HealthBar:
    def create_ui(self) -> List[mcrfpy.UIDrawable]:
        # Dark red background
        self.background = mcrfpy.Frame(pos=(x, y), size=(width, height))
        self.background.fill_color = mcrfpy.Color(100, 0, 0, 255)
        
        # Bright colored bar (green/yellow/red based on HP)
        self.bar = mcrfpy.Frame(pos=(x, y), size=(width, height))
        
        # Text overlay showing HP numbers
        self.text = mcrfpy.Caption(pos=(x+5, y+2), 
                                   text=f"HP: {hp}/{max_hp}")
```

The bar changes color based on health percentage:
- Green (>60% health)
- Yellow (30-60% health)  
- Red (<30% health)

#### Message Log
A scrolling combat log that replaces console print statements:
```python
class MessageLog:
    def __init__(self, max_messages: int = 5):
        self.messages: deque[str] = deque(maxlen=max_messages)
    
    def add_message(self, message: str) -> None:
        self.messages.append(message)
        self.update_display()
```

Messages include:
- Combat actions ("Rat attacks Player for 3 hit points.")
- Death notifications ("Spider is dead!")
- Game state changes ("You have died! Press Escape to quit.")

### Enemy AI System

#### Basic AI Component
Enemies now actively pursue and attack the player:
```python
class BasicAI:
    def take_turn(self, engine: Engine) -> None:
        distance = max(abs(dx), abs(dy))  # Chebyshev distance
        
        if distance <= 1:
            # Adjacent: Attack!
            MeleeAction(self.entity, attack_dx, attack_dy).perform(engine)
        elif distance <= 6:
            # Can see player: Move closer
            MovementAction(self.entity, move_dx, move_dy).perform(engine)
```

#### Turn-Based System
After each player action, all enemies take their turn:
```python
def handle_enemy_turns(self) -> None:
    for entity in self.game_map.entities:
        if isinstance(entity, Actor) and entity.ai and entity.is_alive:
            entity.ai.take_turn(self)
```

### Game Over Condition

When the player dies:
1. Game state flag is set (`engine.game_over = True`)
2. Player becomes a gravestone (sprite changes)
3. Input is restricted (only Escape works)
4. Death message appears in the message log

```python
def handle_player_death(self) -> None:
    self.game_over = True
    self.message_log.add_message("You have died! Press Escape to quit.")
```

## Architecture Improvements

### UI Module (`game/ui.py`)
Separates UI concerns from game logic:
- `MessageLog`: Manages combat messages
- `HealthBar`: Displays player health
- Clean interface for updating displays

### AI Module (`game/ai.py`)
Encapsulates enemy behavior:
- `BasicAI`: Simple pursue-and-attack behavior
- Extensible for different AI types
- Uses existing action system

### Turn Management
Player actions trigger enemy turns:
- Movement → Enemy turns
- Attack → Enemy turns
- Wait → Enemy turns
- Maintains turn-based feel

## Key Implementation Details

### UI Updates
Health bar updates occur:
- After player takes damage
- Automatically via `engine.update_ui()`
- Color changes based on HP percentage

### Message Flow
Combat messages follow this pattern:
1. Action generates message text
2. `engine.message_log.add_message(text)`
3. Message appears in UI Caption
4. Old messages scroll up

### AI Decision Making
Basic AI uses simple rules:
1. Check if player is adjacent → Attack
2. Check if player is visible (within 6 tiles) → Move toward
3. Otherwise → Do nothing

### Game State Management
The `game_over` flag prevents:
- Player movement
- Player attacks
- Player waiting
- But allows Escape to quit

## Files Modified

- `game/ui.py`: New module for UI components
- `game/ai.py`: New module for enemy AI
- `game/engine.py`: Added UI setup, enemy turns, game over handling
- `game/entity.py`: Added AI component to Actor
- `game/entity_factories.py`: Attached AI to enemies
- `game/actions.py`: Integrated message log, added enemy turn triggers
- `main.py`: Updated part description

## What's Next

Part 7 will expand the user interface further with:
- More detailed entity inspection
- Possibly inventory display
- Additional UI panels
- Mouse interaction

## Learning Points

1. **UI Separation**: Keep UI logic separate from game logic
2. **Component Systems**: AI as a component allows different behaviors
3. **Turn-Based Flow**: Player action → Enemy reactions creates tactical gameplay
4. **Visual Feedback**: Health bars and message logs improve player understanding
5. **State Management**: Game over flag controls available actions

## Running Part 6

```bash
cd simple_tcod_tutorial/build
./mcrogueface scripts/main.py
```

You'll now see:
- Health bar at the top showing your current HP
- Message log at the bottom showing combat events
- Enemies that chase you when you're nearby
- Enemies that attack when adjacent
- Death state when HP reaches 0

## Combat Strategy

With enemy AI active, combat becomes more tactical:
- Enemies pursue when they see you
- Fighting in corridors limits how many can attack
- Running away is sometimes the best option
- Health management becomes critical

The game now has a complete combat loop with clear win/lose conditions!