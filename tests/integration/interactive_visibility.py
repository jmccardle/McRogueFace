#!/usr/bin/env python3
"""
Interactive Visibility Test
===========================

Originally an interactive demo (WASD moves the player, arrows move the enemy,
Tab cycles perspective, Space recomputes visibility, R resets). Headless mode
never delivers real keystrokes, so the same key handler is now driven with
mcrfpy.automation.keyDown/keyUp and the resulting state is asserted.

Covers:
  - walls block movement (walkable) and sight (transparent)
  - Entity.update_visibility() / Entity.perspective_map (UNKNOWN/DISCOVERED/VISIBLE)
  - moving an entity discovers new cells and demotes VISIBLE -> DISCOVERED
  - Grid.perspective cycling (None -> player -> enemy -> None)

API notes (current contract):
  - grid.add_layer() takes a layer OBJECT, no kwargs; GridPoint has no .color,
    so cell coloring goes through a ColorLayer.
  - Grid.perspective is an Entity (or None), not an integer index.
"""

import mcrfpy
from mcrfpy import automation
import sys

GRID_W, GRID_H = 30, 20

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"FAIL: {msg}")
    return cond


# Create scene and grid
visibility_demo = mcrfpy.Scene("visibility_demo")
grid = mcrfpy.Grid(grid_size=(GRID_W, GRID_H), pos=(50, 100), size=(900, 600))
grid.fill_color = mcrfpy.Color(20, 20, 30)  # Dark background

# Add color layer for cell coloring (GridPoint.color no longer exists)
color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
grid.grid_data.add_layer(color_layer)

# Initialize grid - all walkable and transparent
for y in range(GRID_H):
    for x in range(GRID_W):
        cell = grid.at(x, y)
        cell.walkable = True
        cell.transparent = True
        color_layer.set((x, y), mcrfpy.Color(100, 100, 120))  # Floor color

# Create walls
walls = [
    # Central cross - a solid wall separating left half from right half
    [(15, y) for y in range(0, GRID_H)],

    # Rooms
    # Top-left room
    [(x, 5) for x in range(2, 8)] + [(8, y) for y in range(2, 6)],
    [(2, y) for y in range(2, 6)] + [(x, 2) for x in range(2, 8)],

    # Top-right room
    [(x, 5) for x in range(22, 28)] + [(22, y) for y in range(2, 6)],
    [(28, y) for y in range(2, 6)] + [(x, 2) for x in range(22, 28)],

    # Bottom-left room
    [(x, 15) for x in range(2, 8)] + [(8, y) for y in range(15, 18)],
    [(2, y) for y in range(15, 18)] + [(x, 18) for x in range(2, 8)],

    # Bottom-right room
    [(x, 15) for x in range(22, 28)] + [(22, y) for y in range(15, 18)],
    [(28, y) for y in range(15, 18)] + [(x, 18) for x in range(22, 28)],
]

wall_cells = set()
for wall_group in walls:
    for x, y in wall_group:
        if 0 <= x < GRID_W and 0 <= y < GRID_H:
            cell = grid.at(x, y)
            cell.walkable = False
            cell.transparent = False
            color_layer.set((x, y), mcrfpy.Color(40, 20, 20))  # Wall color
            wall_cells.add((x, y))

# Create entities
player = mcrfpy.Entity(grid_pos=(5, 10))
player.sprite_index = 64  # @
grid.grid_data.entities.append(player)
enemy = mcrfpy.Entity(grid_pos=(25, 10))
enemy.sprite_index = 69  # E
grid.grid_data.entities.append(enemy)

# Short FOV radius: the default (10) is wide enough that the player's start cell
# stays in FOV from the far side of the room, so cells could never demote from
# VISIBLE to DISCOVERED. update_visibility() reads GridData.fov_radius (Entity.
# sight_radius only feeds the TARGET trigger).
grid.grid_data.fov_radius = 4

# Update initial visibility
player.update_visibility()
enemy.update_visibility()

# Global state: perspective is now an Entity | None, not an int index
perspectives = [None, player, enemy]
perspective_names = ["Omniscient", "Player", "Enemy"]
current_perspective = 0

# UI Setup
ui = visibility_demo.children
ui.append(grid)

# Title
title = mcrfpy.Caption(pos=(350, 20), text="Interactive Visibility Demo")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Info displays
perspective_label = mcrfpy.Caption(pos=(50, 50), text="Perspective: Omniscient")
perspective_label.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(perspective_label)

player_info = mcrfpy.Caption(pos=(700, 50), text="Player: (5, 10)")
player_info.fill_color = mcrfpy.Color(100, 255, 100)
ui.append(player_info)

enemy_info = mcrfpy.Caption(pos=(700, 70), text="Enemy: (25, 10)")
enemy_info.fill_color = mcrfpy.Color(255, 100, 100)
ui.append(enemy_info)


# Helper functions
def move_entity(entity, dx, dy):
    """Move entity if target is walkable"""
    new_x = int(entity.grid_x + dx)
    new_y = int(entity.grid_y + dy)

    if 0 <= new_x < GRID_W and 0 <= new_y < GRID_H:
        cell = grid.at(new_x, new_y)
        if cell.walkable:
            entity.grid_pos = (new_x, new_y)
            entity.update_visibility()
            return True
    return False


def update_info():
    """Update info displays"""
    player_info.text = f"Player: ({player.grid_x}, {player.grid_y})"
    enemy_info.text = f"Enemy: ({enemy.grid_x}, {enemy.grid_y})"


def cycle_perspective():
    """Cycle through perspectives: Omniscient -> Player -> Enemy -> Omniscient"""
    global current_perspective
    current_perspective = (current_perspective + 1) % 3
    grid.perspective = perspectives[current_perspective]
    perspective_label.text = f"Perspective: {perspective_names[current_perspective]}"


# Key handlers
def handle_keys(key, state):
    """Handle keyboard input"""
    if state == mcrfpy.InputState.RELEASED:
        return
    # Player movement (WASD)
    if key == mcrfpy.Key.W:
        move_entity(player, 0, -1)
    elif key == mcrfpy.Key.S:
        move_entity(player, 0, 1)
    elif key == mcrfpy.Key.A:
        move_entity(player, -1, 0)
    elif key == mcrfpy.Key.D:
        move_entity(player, 1, 0)

    # Enemy movement (Arrows)
    elif key == mcrfpy.Key.UP:
        move_entity(enemy, 0, -1)
    elif key == mcrfpy.Key.DOWN:
        move_entity(enemy, 0, 1)
    elif key == mcrfpy.Key.LEFT:
        move_entity(enemy, -1, 0)
    elif key == mcrfpy.Key.RIGHT:
        move_entity(enemy, 1, 0)

    # Tab to cycle perspective
    elif key == mcrfpy.Key.TAB:
        cycle_perspective()

    # Space to update visibility
    elif key == mcrfpy.Key.SPACE:
        player.update_visibility()
        enemy.update_visibility()

    # R to reset
    elif key == mcrfpy.Key.R:
        player.grid_pos = (5, 10)
        enemy.grid_pos = (25, 10)
        player.update_visibility()
        enemy.update_visibility()

    update_info()


# Set scene first, then register key handler
visibility_demo.activate()
visibility_demo.on_key = handle_keys


def press(key):
    """Deliver a real key event to the scene handler."""
    automation.keyDown(key)
    automation.keyUp(key)


UNKNOWN = mcrfpy.Perspective.UNKNOWN
DISCOVERED = mcrfpy.Perspective.DISCOVERED
VISIBLE = mcrfpy.Perspective.VISIBLE


def seen(entity, x, y):
    return entity.perspective_map.get(x, y)


def main():
    # --- Initial visibility: player sees its own cell, and cannot see through
    #     the solid wall at x=15 into the enemy's half of the map.
    check(seen(player, 5, 10) == VISIBLE, "player should see its own cell")
    check(seen(player, 25, 10) == UNKNOWN,
          f"player should not see across the wall; got {seen(player, 25, 10)}")
    check(seen(enemy, 25, 10) == VISIBLE, "enemy should see its own cell")
    check(seen(enemy, 5, 10) == UNKNOWN,
          f"enemy should not see across the wall; got {seen(enemy, 5, 10)}")
    check(player not in enemy.visible_entities(),
          "wall should hide the player from the enemy")

    # --- WASD moves the player; cells it leaves behind stay DISCOVERED.
    press('d')
    check((player.grid_x, player.grid_y) == (6, 10),
          f"'d' should move player right; got {(player.grid_x, player.grid_y)}")
    press('s')
    check((player.grid_x, player.grid_y) == (6, 11),
          f"'s' should move player down; got {(player.grid_x, player.grid_y)}")
    check(player_info.text == "Player: (6, 11)", f"caption not updated: {player_info.text}")

    # --- Walls block movement: walk the player into the central wall.
    while player.grid_x < 14:
        before = player.grid_x
        press('d')
        check(player.grid_x == before + 1, "player should walk freely up to the wall")
    check((player.grid_x, player.grid_y) == (14, 11), "player should be adjacent to the wall")
    press('d')
    check((player.grid_x, player.grid_y) == (14, 11),
          f"wall must block movement; player reached {(player.grid_x, player.grid_y)}")

    # --- Having walked across the room, previously-seen cells are remembered
    #     but no longer visible.
    check(seen(player, 5, 10) == DISCOVERED,
          f"start cell should be remembered, not visible; got {seen(player, 5, 10)}")
    check(seen(player, 14, 11) == VISIBLE, "player's current cell should be visible")
    check(seen(player, 25, 10) == UNKNOWN, "the wall still hides the enemy's half")

    # --- Arrow keys move the enemy.
    press('left')
    check((enemy.grid_x, enemy.grid_y) == (24, 10),
          f"left arrow should move enemy; got {(enemy.grid_x, enemy.grid_y)}")
    press('up')
    check((enemy.grid_x, enemy.grid_y) == (24, 9),
          f"up arrow should move enemy; got {(enemy.grid_x, enemy.grid_y)}")

    # --- Space recomputes visibility without moving anything.
    pos_before = (player.grid_x, player.grid_y, enemy.grid_x, enemy.grid_y)
    press('space')
    check((player.grid_x, player.grid_y, enemy.grid_x, enemy.grid_y) == pos_before,
          "space must not move entities")
    check(seen(player, 14, 11) == VISIBLE, "player still sees its own cell after space")

    # --- Tab cycles perspective: Omniscient -> Player -> Enemy -> Omniscient.
    check(grid.perspective is None, "grid starts omniscient")
    press('tab')
    check(grid.perspective is player, f"tab 1 -> player; got {grid.perspective}")
    check(perspective_label.text == "Perspective: Player", perspective_label.text)
    press('tab')
    check(grid.perspective is enemy, f"tab 2 -> enemy; got {grid.perspective}")
    press('tab')
    check(grid.perspective is None, f"tab 3 -> omniscient; got {grid.perspective}")
    check(perspective_label.text == "Perspective: Omniscient", perspective_label.text)

    # --- R resets positions and visibility.
    press('r')
    check((player.grid_x, player.grid_y) == (5, 10), "R resets the player")
    check((enemy.grid_x, enemy.grid_y) == (25, 10), "R resets the enemy")
    check(seen(player, 5, 10) == VISIBLE, "player sees its cell again after reset")
    check(seen(player, 14, 11) == DISCOVERED,
          f"cells left behind stay remembered after reset; got {seen(player, 14, 11)}")

    # --- Perspective rendering path must not crash.
    grid.perspective = player
    automation.screenshot("interactive_visibility.png")
    grid.perspective = None

    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
