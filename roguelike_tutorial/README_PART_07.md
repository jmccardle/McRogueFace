# Part 7: Creating the User Interface

## Overview

Part 7 significantly enhances the user interface, transforming our roguelike from a basic game into a more polished experience. We add mouse interaction, help displays, information panels, and better visual feedback systems.

## What's New in Part 7

### Mouse Interaction

#### Click-to-Inspect System
Since McRogueFace doesn't have mouse motion events, we use click events to show entity information:
```python
def grid_click_handler(pixel_x, pixel_y, button, state):
    # Convert pixel coordinates to grid coordinates
    grid_x = int(pixel_x / (self.tile_size * self.zoom))
    grid_y = int(pixel_y / (self.tile_size * self.zoom))
    
    # Update hover display for this position
    self.update_mouse_hover(grid_x, grid_y)
```

Click displays show:
- Entity names
- Current HP for living creatures
- Multiple entities if stacked (e.g., "Grave of Rat")

#### Mouse Handler Registration
The click handler is registered as a local function to avoid issues with bound methods:
```python
# Use a local function instead of a bound method
self.game_map.click = grid_click_handler
```

### Help System

#### Toggle Help Display
Press `?`, `H`, or `F1` to show/hide help:
```python
class HelpDisplay:
    def toggle(self) -> None:
        self.visible = not self.visible
        self.panel.frame.visible = self.visible
```

The help panel includes:
- Movement controls for all input methods
- Combat instructions
- Mouse usage tips
- Gameplay strategies

### Information Panels

#### Player Stats Panel
Always-visible panel showing:
- Player name
- Current/Max HP
- Power and Defense stats
- Current grid position

```python
class InfoPanel:
    def create_ui(self, title: str) -> List[mcrfpy.Drawable]:
        # Semi-transparent background frame
        self.frame = mcrfpy.Frame(pos=(x, y), size=(width, height))
        self.frame.fill_color = mcrfpy.Color(20, 20, 40, 200)
        
        # Title and content captions as children
        self.frame.children.append(self.title_caption)
        self.frame.children.append(self.content_caption)
```

#### Reusable Panel System
The `InfoPanel` class provides:
- Titled panels with borders
- Semi-transparent backgrounds
- Easy content updates
- Consistent visual style

### Enhanced UI Components

#### MouseHoverDisplay Class
Manages tooltip-style hover information:
- Follows mouse position
- Shows/hides automatically
- Offset to avoid cursor overlap
- Multiple entity support

#### UI Module Organization
Clean separation of UI components:
- `MessageLog`: Combat messages
- `HealthBar`: HP visualization
- `MouseHoverDisplay`: Entity inspection
- `InfoPanel`: Generic information display
- `HelpDisplay`: Keyboard controls

## Architecture Improvements

### UI Composition
Using McRogueFace's parent-child system:
```python
# Add caption as child of frame
self.frame.children.append(self.text_caption)
```

Benefits:
- Automatic relative positioning
- Group visibility control
- Clean hierarchy

### Event Handler Extensions
Input handler now manages:
- Keyboard input (existing)
- Mouse motion (new)
- Mouse clicks (prepared for future)
- UI toggles (help display)

### Dynamic Content Updates
All UI elements support real-time updates:
```python
def update_stats_panel(self) -> None:
    stats_text = f"""Name: {self.player.name}
HP: {self.player.hp}/{self.player.max_hp}
Power: {self.player.power}
Defense: {self.player.defense}"""
    self.stats_panel.update_content(stats_text)
```

## Key Implementation Details

### Mouse Coordinate Conversion
Pixel to grid conversion:
```python
grid_x = int(x / (self.engine.tile_size * self.engine.zoom))
grid_y = int(y / (self.engine.tile_size * self.engine.zoom))
```

### Visibility Management
UI elements can be toggled:
- Help panel starts hidden
- Mouse hover hides when not over entities
- Panels can be shown/hidden dynamically

### Color and Transparency
UI uses semi-transparent overlays:
- Panel backgrounds: `Color(20, 20, 40, 200)`
- Hover tooltips: `Color(255, 255, 200, 255)`
- Borders and outlines for readability

## Files Modified

- `game/ui.py`: Added MouseHoverDisplay, InfoPanel, HelpDisplay classes
- `game/engine.py`: Integrated new UI components, mouse hover handling
- `game/input_handlers.py`: Added mouse motion handling, help toggle
- `main.py`: Registered mouse handlers, updated part description

## What's Next

Part 8 will add items and inventory:
- Collectible items (potions, equipment)
- Inventory management UI
- Item usage mechanics
- Equipment system

## Learning Points

1. **UI Composition**: Use parent-child relationships for complex UI
2. **Event Delegation**: Separate input handling from UI updates
3. **Information Layers**: Multiple UI systems can coexist (hover, panels, help)
4. **Visual Polish**: Small touches like transparency and borders improve UX
5. **Reusable Components**: Generic panels can be specialized for different uses

## Running Part 7

```bash
cd simple_tcod_tutorial/build
./mcrogueface scripts/main.py
```

New features to try:
- Click on entities to see their details
- Press ? or H to toggle help display
- Watch the stats panel update as you take damage
- See entity HP in hover tooltips
- Notice the visual polish in UI panels

## UI Design Principles

### Consistency
- All panels use similar visual style
- Consistent color scheme
- Uniform text sizing

### Non-Intrusive
- Semi-transparent panels don't block view
- Hover info appears near cursor
- Help can be toggled off

### Information Hierarchy
- Critical info (health) always visible
- Contextual info (hover) on demand
- Help info toggleable

The UI now provides a professional feel while maintaining the roguelike aesthetic!