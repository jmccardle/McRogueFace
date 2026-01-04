#!/usr/bin/env python3
"""
Animation Debug Tool
====================

Helps diagnose animation timing issues.
"""

import mcrfpy
import sys

# Track all active animations
active_animations = {}
animation_log = []

class AnimationTracker:
    """Tracks animation lifecycle for debugging"""
    
    def __init__(self, name, target, property_name, target_value, duration):
        self.name = name
        self.target = target
        self.property_name = property_name
        self.target_value = target_value
        self.duration = duration
        self.start_time = None
        self.animation = None
        
    def start(self):
        """Start the animation with tracking"""
        # Log the start
        log_entry = f"START: {self.name} - {self.property_name} to {self.target_value} over {self.duration}s"
        animation_log.append(log_entry)
        print(log_entry)
        
        # Create and start animation
        self.animation = mcrfpy.Animation(self.property_name, self.target_value, self.duration, "linear")
        self.animation.start(self.target)
        
        # Track it
        active_animations[self.name] = self

        # Set timer to check completion
        check_interval = 100  # ms
        self._check_timer = mcrfpy.Timer(f"check_{self.name}", self._check_complete, check_interval)
        
    def _check_complete(self, timer, runtime):
        """Check if animation is complete"""
        if self.animation and hasattr(self.animation, 'is_complete') and self.animation.is_complete:
            # Log completion
            log_entry = f"COMPLETE: {self.name}"
            animation_log.append(log_entry)
            print(log_entry)

            # Remove from active
            if self.name in active_animations:
                del active_animations[self.name]

            # Stop checking
            timer.stop()

# Create test scene
anim_debug = mcrfpy.Scene("anim_debug")

# Simple grid
grid = mcrfpy.Grid(grid_x=15, grid_y=10)
color_layer = grid.add_layer("color", z_index=-1)
for y in range(10):
    for x in range(15):
        cell = grid.at(x, y)
        cell.walkable = True
        color_layer.set(x, y, mcrfpy.Color(100, 100, 120))

# Test entity
entity = mcrfpy.Entity((5, 5), grid=grid)
entity.sprite_index = 64

# UI
ui = anim_debug.children
ui.append(grid)
grid.position = (100, 150)
grid.size = (450, 300)

title = mcrfpy.Caption(pos=(250, 20), text="Animation Debug Tool")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

status = mcrfpy.Caption(pos=(100, 50), text="Press keys to test animations")
status.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(status)

pos_display = mcrfpy.Caption(pos=(100, 70), text="")
pos_display.fill_color = mcrfpy.Color(255, 255, 100)
ui.append(pos_display)

active_display = mcrfpy.Caption(pos=(100, 90), text="Active animations: 0")
active_display.fill_color = mcrfpy.Color(100, 255, 255)
ui.append(active_display)

# Test scenarios
def test_simultaneous():
    """Test multiple animations at once (causes issues)"""
    print("\n=== TEST: Simultaneous Animations ===")
    status.text = "Testing simultaneous X and Y animations"
    
    # Start both at once
    anim1 = AnimationTracker("sim_x", entity, "x", 10.0, 1.0)
    anim2 = AnimationTracker("sim_y", entity, "y", 8.0, 1.5)
    
    anim1.start()
    anim2.start()

def test_rapid_fire():
    """Test starting new animation before previous completes"""
    print("\n=== TEST: Rapid Fire Animations ===")
    status.text = "Testing rapid fire animations (overlapping)"
    
    # Start first animation
    anim1 = AnimationTracker("rapid_1", entity, "x", 8.0, 2.0)
    anim1.start()

    # Start another after 500ms (before first completes)
    def start_second(timer, runtime):
        anim2 = AnimationTracker("rapid_2", entity, "x", 12.0, 1.0)
        anim2.start()
        timer.stop()

    global rapid_timer
    rapid_timer = mcrfpy.Timer("rapid_timer", start_second, 500, once=True)

def test_sequential():
    """Test proper sequential animations"""
    print("\n=== TEST: Sequential Animations ===")
    status.text = "Testing proper sequential animations"
    
    sequence = [
        ("seq_1", "x", 8.0, 0.5),
        ("seq_2", "y", 7.0, 0.5),
        ("seq_3", "x", 6.0, 0.5),
        ("seq_4", "y", 5.0, 0.5),
    ]
    
    def run_sequence(index=0):
        if index >= len(sequence):
            print("Sequence complete!")
            return

        name, prop, value, duration = sequence[index]
        anim = AnimationTracker(name, entity, prop, value, duration)
        anim.start()

        # Schedule next
        delay = int(duration * 1000) + 100  # Add buffer
        mcrfpy.Timer(f"seq_timer_{index}", lambda t, r: run_sequence(index + 1), delay, once=True)
    
    run_sequence()

def test_conflicting():
    """Test conflicting animations on same property"""
    print("\n=== TEST: Conflicting Animations ===")
    status.text = "Testing conflicting animations (same property)"
    
    # Start animation to x=10
    anim1 = AnimationTracker("conflict_1", entity, "x", 10.0, 2.0)
    anim1.start()
    
    # After 1 second, start conflicting animation to x=2
    def start_conflict(timer, runtime):
        print("Starting conflicting animation!")
        anim2 = AnimationTracker("conflict_2", entity, "x", 2.0, 1.0)
        anim2.start()
        timer.stop()

    global conflict_timer
    conflict_timer = mcrfpy.Timer("conflict_timer", start_conflict, 1000, once=True)

# Update display
def update_display(timer, runtime):
    pos_display.text = f"Entity position: ({entity.x:.2f}, {entity.y:.2f})"
    active_display.text = f"Active animations: {len(active_animations)}"

    # Show active animation names
    if active_animations:
        names = ", ".join(active_animations.keys())
        active_display.text += f" [{names}]"

# Show log
def show_log():
    print("\n=== ANIMATION LOG ===")
    for entry in animation_log[-10:]:  # Last 10 entries
        print(entry)
    print("===================")

# Input handler
def handle_input(key, state):
    if state != "start":
        return
    
    key = key.lower()
    
    if key == "q":
        sys.exit(0)
    elif key == "num1":
        test_simultaneous()
    elif key == "num2":
        test_rapid_fire()
    elif key == "num3":
        test_sequential()
    elif key == "num4":
        test_conflicting()
    elif key == "l":
        show_log()
    elif key == "r":
        entity.x = 5
        entity.y = 5
        animation_log.clear()
        active_animations.clear()
        print("Reset entity and cleared log")

# Setup
anim_debug.activate()
anim_debug.on_key = handle_input
update_display_timer = mcrfpy.Timer("update", update_display, 100)

print("Animation Debug Tool")
print("====================")
print("This tool helps diagnose animation timing issues")
print()
print("Tests:")
print("  1 - Simultaneous X/Y (may cause issues)")
print("  2 - Rapid fire (overlapping animations)")
print("  3 - Sequential (proper chaining)")
print("  4 - Conflicting (same property)")
print()
print("Other keys:")
print("  L - Show animation log")
print("  R - Reset")
print("  Q - Quit")
print()
print("Watch the console for animation lifecycle events")