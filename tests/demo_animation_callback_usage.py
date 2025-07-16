#!/usr/bin/env python3
"""
Demonstration of animation callbacks solving race conditions.
Shows how callbacks enable direct causality for game state changes.
"""

import mcrfpy

# Game state
player_moving = False
move_queue = []

def movement_complete(anim, target):
    """Called when player movement animation completes"""
    global player_moving, move_queue
    
    print("Movement animation completed!")
    player_moving = False
    
    # Process next move if queued
    if move_queue:
        next_pos = move_queue.pop(0)
        move_player_to(next_pos)
    else:
        print("Player is now idle and ready for input")

def move_player_to(new_pos):
    """Move player with animation and proper state management"""
    global player_moving
    
    if player_moving:
        print(f"Queueing move to {new_pos}")
        move_queue.append(new_pos)
        return
    
    player_moving = True
    print(f"Moving player to {new_pos}")
    
    # Get player entity (placeholder for demo)
    ui = mcrfpy.sceneUI("game")
    player = ui[0]  # Assume first element is player
    
    # Animate movement with callback
    x, y = new_pos
    anim_x = mcrfpy.Animation("x", float(x), 0.5, "easeInOutQuad", callback=movement_complete)
    anim_y = mcrfpy.Animation("y", float(y), 0.5, "easeInOutQuad")
    
    anim_x.start(player)
    anim_y.start(player)

def setup_demo():
    """Set up the demo scene"""
    # Create scene
    mcrfpy.createScene("game")
    mcrfpy.setScene("game")
    
    # Create player sprite
    player = mcrfpy.Frame((100, 100), (32, 32), fill_color=(0, 255, 0))
    ui = mcrfpy.sceneUI("game")
    ui.append(player)
    
    print("Demo: Animation callbacks for movement queue")
    print("=" * 40)
    
    # Simulate rapid movement commands
    mcrfpy.setTimer("move1", lambda r: move_player_to((200, 100)), 100)
    mcrfpy.setTimer("move2", lambda r: move_player_to((200, 200)), 200)  # Will be queued
    mcrfpy.setTimer("move3", lambda r: move_player_to((100, 200)), 300)  # Will be queued
    
    # Exit after demo
    mcrfpy.setTimer("exit", lambda r: exit_demo(), 3000)

def exit_demo():
    """Exit the demo"""
    print("\nDemo completed successfully!")
    print("Callbacks ensure proper movement sequencing without race conditions")
    import sys
    sys.exit(0)

# Run the demo
setup_demo()