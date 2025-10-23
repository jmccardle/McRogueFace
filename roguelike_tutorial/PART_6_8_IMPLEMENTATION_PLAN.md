# McRogueFace Tutorial Parts 6-8: Implementation Plan

**Date**: Monday, July 28, 2025  
**Target Delivery**: Tuesday, July 29, 2025  

## Executive Summary

This document outlines the implementation plan for Parts 6-8 of the McRogueFace roguelike tutorial, adapting the libtcod Python tutorial to McRogueFace's architecture. The key discovery is that Python classes can successfully inherit from `mcrfpy.Entity` and store custom attributes, enabling a clean, Pythonic implementation.

## Key Architectural Insights

### Entity Inheritance Works!
```python
class GameEntity(mcrfpy.Entity):
    def __init__(self, x, y, **kwargs):
        super().__init__(x=x, y=y, **kwargs)
        # Custom attributes work perfectly!
        self.hp = 10
        self.inventory = []
        self.any_attribute = "works"
```

This completely changes our approach from wrapper patterns to direct inheritance.

---

## Part 6: Doing (and Taking) Some Damage

### Overview
Implement a combat system with HP tracking, damage calculation, and death mechanics using entity inheritance.

### Core Components

#### 1. CombatEntity Base Class
```python
class CombatEntity(mcrfpy.Entity):
    """Base class for entities that can fight and take damage"""
    def __init__(self, x, y, hp=10, defense=0, power=1, **kwargs):
        super().__init__(x=x, y=y, **kwargs)
        # Combat stats as direct attributes
        self.hp = hp
        self.max_hp = hp
        self.defense = defense
        self.power = power
        self.is_alive = True
        self.blocks_movement = True
        
    def calculate_damage(self, attacker):
        """Simple damage formula: power - defense"""
        return max(0, attacker.power - self.defense)
        
    def take_damage(self, damage, attacker=None):
        """Apply damage and handle death"""
        self.hp = max(0, self.hp - damage)
        
        if self.hp == 0 and self.is_alive:
            self.is_alive = False
            self.on_death(attacker)
            
    def on_death(self, killer=None):
        """Handle death - override in subclasses"""
        self.sprite_index = self.sprite_index + 180  # Corpse offset
        self.blocks_movement = False
```

#### 2. Entity Types
```python
class PlayerEntity(CombatEntity):
    """Player: HP=30, Defense=2, Power=5"""
    def __init__(self, x, y, **kwargs):
        kwargs['sprite_index'] = 64  # Hero sprite
        super().__init__(x=x, y=y, hp=30, defense=2, power=5, **kwargs)
        self.entity_type = "player"

class OrcEntity(CombatEntity):
    """Orc: HP=10, Defense=0, Power=3"""
    def __init__(self, x, y, **kwargs):
        kwargs['sprite_index'] = 65  # Orc sprite
        super().__init__(x=x, y=y, hp=10, defense=0, power=3, **kwargs)
        self.entity_type = "orc"

class TrollEntity(CombatEntity):
    """Troll: HP=16, Defense=1, Power=4"""
    def __init__(self, x, y, **kwargs):
        kwargs['sprite_index'] = 66  # Troll sprite
        super().__init__(x=x, y=y, hp=16, defense=1, power=4, **kwargs)
        self.entity_type = "troll"
```

#### 3. Combat Integration
- Extend `on_bump()` from Part 5 to include combat
- Add attack animations (quick bump toward target)
- Console messages initially, UI messages in Part 7
- Death changes sprite and removes blocking

### Key Differences from Original Tutorial
- No Fighter component - stats are direct attributes
- No AI component - behavior in entity methods
- Integrated animations for visual feedback
- Simpler architecture overall

---

## Part 7: Creating the Interface

### Overview
Add visual UI elements including health bars, message logs, and colored feedback for combat events.

### Core Components

#### 1. Health Bar
```python
class HealthBar:
    """Health bar that reads entity HP directly"""
    def __init__(self, entity, pos=(10, 740), size=(200, 20)):
        self.entity = entity  # Direct reference!
        
        # Background (dark red)
        self.bg = mcrfpy.Frame(pos=pos, size=size)
        self.bg.fill_color = mcrfpy.Color(64, 16, 16)
        
        # Foreground (green)
        self.fg = mcrfpy.Frame(pos=pos, size=size)
        self.fg.fill_color = mcrfpy.Color(0, 96, 0)
        
        # Text overlay
        self.text = mcrfpy.Caption(
            pos=(pos[0] + 5, pos[1] + 2),
            text=f"HP: {entity.hp}/{entity.max_hp}"
        )
        
    def update(self):
        """Update based on entity's current HP"""
        ratio = self.entity.hp / self.entity.max_hp
        self.fg.w = int(self.bg.w * ratio)
        self.text.text = f"HP: {self.entity.hp}/{self.entity.max_hp}"
        
        # Color changes at low health
        if ratio < 0.25:
            self.fg.fill_color = mcrfpy.Color(196, 16, 16)  # Red
        elif ratio < 0.5:
            self.fg.fill_color = mcrfpy.Color(196, 196, 16)  # Yellow
```

#### 2. Message Log
```python
class MessageLog:
    """Scrolling message log for combat feedback"""
    def __init__(self, pos=(10, 600), size=(400, 120), max_messages=6):
        self.frame = mcrfpy.Frame(pos=pos, size=size)
        self.messages = []  # List of (text, color) tuples
        self.captions = []  # Pre-allocated Caption pool
        
    def add_message(self, text, color=None):
        """Add message with optional color"""
        # Handle duplicate detection (x2, x3, etc.)
        # Update caption display
```

#### 3. Color System
```python
class Colors:
    # Combat colors
    PLAYER_ATTACK = mcrfpy.Color(224, 224, 224)
    ENEMY_ATTACK = mcrfpy.Color(255, 192, 192)
    PLAYER_DEATH = mcrfpy.Color(255, 48, 48)
    ENEMY_DEATH = mcrfpy.Color(255, 160, 48)
    HEALTH_RECOVERED = mcrfpy.Color(0, 255, 0)
```

### UI Layout
- Health bar at bottom of screen
- Message log above health bar
- Direct binding to entity attributes
- Real-time updates during gameplay

---

## Part 8: Items and Inventory

### Overview
Implement items as entities, inventory management, and a hotbar-style UI for item usage.

### Core Components

#### 1. Item Entities
```python
class ItemEntity(mcrfpy.Entity):
    """Base class for pickupable items"""
    def __init__(self, x, y, name, sprite, **kwargs):
        kwargs['sprite_index'] = sprite
        super().__init__(x=x, y=y, **kwargs)
        self.item_name = name
        self.blocks_movement = False
        self.item_type = "generic"

class HealingPotion(ItemEntity):
    """Consumable healing item"""
    def __init__(self, x, y, healing_amount=4):
        super().__init__(x, y, "Healing Potion", sprite=33)
        self.healing_amount = healing_amount
        self.item_type = "consumable"
        
    def use(self, user):
        """Use the potion - returns (success, message)"""
        if hasattr(user, 'hp'):
            healed = min(self.healing_amount, user.max_hp - user.hp)
            if healed > 0:
                user.hp += healed
                return True, f"You heal {healed} HP!"
```

#### 2. Inventory System
```python
class InventoryMixin:
    """Mixin for entities with inventory"""
    def __init__(self, *args, capacity=10, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory = []
        self.inventory_capacity = capacity
        
    def pickup_item(self, item):
        """Pick up an item entity"""
        if len(self.inventory) >= self.inventory_capacity:
            return False, "Inventory full!"
        self.inventory.append(item)
        item.die()  # Remove from grid
        return True, f"Picked up {item.item_name}."
```

#### 3. Inventory UI
```python
class InventoryDisplay:
    """Hotbar-style inventory display"""
    def __init__(self, entity, pos=(200, 700), slots=10):
        # Create slot frames and sprites
        # Number keys 1-9, 0 for slots
        # Highlight selected slot
        # Update based on entity.inventory
```

### Key Features
- Items exist as entities on the grid
- Direct inventory attribute on player
- Hotkey-based usage (1-9, 0)
- Visual hotbar display
- Item effects (healing, future: damage boost, etc.)

---

## Implementation Timeline

### Tuesday Morning (Priority 1: Core Systems)
1. **8:00-9:30**: Implement CombatEntity and entity types
2. **9:30-10:30**: Add combat to bump interactions
3. **10:30-11:30**: Basic health display (text or simple bar)
4. **11:30-12:00**: ItemEntity and pickup system

### Tuesday Afternoon (Priority 2: Integration)
1. **1:00-2:00**: Message log implementation
2. **2:00-3:00**: Full health bar with colors
3. **3:00-4:00**: Inventory UI (hotbar)
4. **4:00-5:00**: Testing and bug fixes

### Tuesday Evening (Priority 3: Polish)
1. **5:00-6:00**: Combat animations and effects
2. **6:00-7:00**: Sound integration (use CoS splat sounds)
3. **7:00-8:00**: Additional item types
4. **8:00-9:00**: Documentation and cleanup

---

## Testing Strategy

### Automated Tests
```python
# tests/test_part6_combat.py
- Test damage calculation
- Test death mechanics
- Test combat messages

# tests/test_part7_ui.py
- Test health bar updates
- Test message log scrolling
- Test color system

# tests/test_part8_inventory.py
- Test item pickup/drop
- Test inventory capacity
- Test item usage
```

### Visual Tests
- Screenshot combat states
- Verify UI element positioning
- Check animation smoothness

---

## File Structure
```
roguelike_tutorial/
├── part_6.py          # Combat implementation
├── part_7.py          # UI enhancements
├── part_8.py          # Inventory system
├── combat.py          # Shared combat utilities
├── ui_components.py   # Reusable UI classes
├── colors.py          # Color definitions
└── items.py           # Item definitions
```

---

## Risk Mitigation

### Potential Issues
1. **Performance**: Many UI updates per frame
   - Solution: Update only on state changes
   
2. **Entity Collection Bugs**: Known segfault issues
   - Solution: Use index-based access when needed
   
3. **Animation Timing**: Complex with turn-based combat
   - Solution: Queue animations, process sequentially

### Fallback Options
1. Start with console messages, add UI later
2. Simple health numbers before bars
3. Basic inventory list before hotbar

---

## Success Criteria

### Part 6
- [x] Entities can have HP and take damage
- [x] Death changes sprite and walkability
- [x] Combat messages appear
- [x] Player can kill enemies

### Part 7
- [x] Health bar shows current/max HP
- [x] Messages appear in scrolling log
- [x] Colors differentiate message types
- [x] UI updates in real-time

### Part 8
- [x] Items can be picked up
- [x] Inventory has capacity limit
- [x] Items can be used/consumed
- [x] Hotbar shows inventory items

---

## Notes for Implementation

1. **Keep It Simple**: Start with minimum viable features
2. **Build Incrementally**: Test each component before integrating
3. **Use Part 5**: Leverage existing entity interaction system
4. **Document Well**: Clear comments for tutorial purposes
5. **Visual Feedback**: McRogueFace excels at animations - use them!

---

## Comparison with Original Tutorial

### What We Keep
- Same combat formula (power - defense)
- Same entity stats (Player, Orc, Troll)
- Same item types (healing potions to start)
- Same UI elements (health bar, message log)

### What's Different
- Direct inheritance instead of components
- Integrated animations and visual effects
- Hotbar inventory instead of menu
- Built-in sound support
- Cleaner architecture overall

### What's Better
- More Pythonic with real inheritance
- Better visual feedback
- Smoother animations
- Simpler to understand
- Leverages McRogueFace's strengths

---

## Conclusion

This implementation plan leverages McRogueFace's support for Python entity inheritance to create a clean, intuitive tutorial series. By using direct attributes instead of components, we simplify the architecture while maintaining all the functionality of the original tutorial. The addition of animations, sound effects, and rich UI elements showcases McRogueFace's capabilities while keeping the code beginner-friendly.

The Tuesday delivery timeline is aggressive but achievable by focusing on core functionality first, then integration, then polish. The modular design allows for easy testing and incremental development.