#!/usr/bin/env python3
"""
Test Animation Chaining
=======================

Demonstrates proper animation chaining to avoid glitches: an entity walks a path
one tile at a time, and each step's animation only starts after the previous
step's animation has completed (never two overlapping position animations).

Headless: mcrfpy.step(dt) is the clock -- it drives both timers and animations.
Animations are created with target.animate(...) (mcrfpy.Animation is no longer
constructible); chaining uses the completion callback instead of polling.
"""

import mcrfpy
import sys

failures = []

def check(name, condition, detail=""):
    if condition:
        print(f"  PASS: {name}")
    else:
        print(f"  FAIL: {name} {detail}")
        failures.append(name)

class PathAnimator:
    """Handles step-by-step path animation with proper chaining"""

    def __init__(self, entity, path, step_duration=0.3, on_complete=None):
        self.entity = entity
        self.path = path
        self.current_index = 0
        self.step_duration = step_duration
        self.on_complete = on_complete
        self.animating = False
        self.completed_steps = []   # (index, draw_pos) recorded as each step lands
        self.overlaps = 0           # times a new step started while one was in flight
        self.anim_x = None
        self.anim_y = None

    def start(self):
        """Start animating along the path"""
        if not self.path or self.animating:
            return

        self.current_index = 0
        self.animating = True
        self._animate_next_step()

    def _animate_next_step(self):
        """Animate to the next position in the path"""
        if self.current_index >= len(self.path):
            # Path complete
            self.animating = False
            if self.on_complete:
                self.on_complete()
            return

        # Detect a chaining violation: the previous step must be finished
        if self.anim_x is not None and not self.anim_x.is_complete:
            self.overlaps += 1
        if self.anim_y is not None and not self.anim_y.is_complete:
            self.overlaps += 1

        # Get target position
        target_x, target_y = self.path[self.current_index]

        # Create + start animations ('x'/'y' animate the entity's draw position,
        # in tile coordinates).  The x animation's callback chains the next step.
        self.anim_y = self.entity.animate("y", float(target_y), self.step_duration,
                                          mcrfpy.Easing.EASE_IN_OUT)
        self.anim_x = self.entity.animate("x", float(target_x), self.step_duration,
                                          mcrfpy.Easing.EASE_IN_OUT,
                                          callback=self._on_step_complete)

        # Update visibility if entity has this method
        if hasattr(self.entity, 'update_visibility'):
            self.entity.update_visibility()

    def _on_step_complete(self, target, prop, value):
        """Animation completion callback -- advance to the next path node"""
        self.completed_steps.append((self.current_index,
                                     (self.entity.draw_pos.x, self.entity.draw_pos.y)))
        self.current_index += 1
        self._animate_next_step()

# Create test scene
chain_test = mcrfpy.Scene("chain_test")

# Create grid
grid = mcrfpy.Grid(grid_size=(20, 15), pos=(100, 100), size=(600, 450))
grid.fill_color = mcrfpy.Color(20, 20, 30)

# Add a color layer for cell coloring (GridPoint has no .color any more)
color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
grid.add_layer(color_layer)

# Simple map
for y in range(15):
    for x in range(20):
        cell = grid.at(x, y)
        if x == 0 or x == 19 or y == 0 or y == 14:
            cell.walkable = False
            cell.transparent = False
            color_layer.set((x, y), mcrfpy.Color(60, 40, 40))
        else:
            cell.walkable = True
            cell.transparent = True
            color_layer.set((x, y), mcrfpy.Color(100, 100, 120))

# Create entities
player = mcrfpy.Entity(grid_pos=(2, 2))
player.sprite_index = 64  # @
grid.entities.append(player)

enemy = mcrfpy.Entity(grid_pos=(17, 12))
enemy.sprite_index = 69  # E
grid.entities.append(enemy)

# UI setup
ui = chain_test.children
ui.append(grid)

title = mcrfpy.Caption(pos=(300, 20), text="Animation Chaining Test")
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

info = mcrfpy.Caption(pos=(100, 70), text="Status: Ready")
info.fill_color = mcrfpy.Color(100, 255, 100)
ui.append(info)

# Path animators
player_animator = None
enemy_animator = None
player_done = False
enemy_done = False

PLAYER_PATH = [
    (2, 2), (3, 2), (4, 2), (5, 2), (6, 2),  # Right
    (6, 3), (6, 4), (6, 5), (6, 6),          # Down
    (7, 6), (8, 6), (9, 6), (10, 6),         # Right
    (10, 7), (10, 8), (10, 9),               # Down
]

ENEMY_PATH = [
    (17, 12), (16, 12), (15, 12), (14, 12),  # Left
    (14, 11), (14, 10), (14, 9),             # Up
    (13, 9), (12, 9), (11, 9), (10, 9),      # Left
    (10, 8), (10, 7), (10, 6),               # Up
]

def animate_player():
    """Animate player along a path"""
    global player_animator

    def on_complete():
        global player_done
        player_done = True
        info.text = "Player animation complete!"

    player_animator = PathAnimator(player, PLAYER_PATH, step_duration=0.2,
                                   on_complete=on_complete)
    player_animator.start()
    info.text = "Animating player..."

def animate_enemy():
    """Animate enemy along a path"""
    global enemy_animator

    def on_complete():
        global enemy_done
        enemy_done = True
        info.text = "Enemy animation complete!"

    enemy_animator = PathAnimator(enemy, ENEMY_PATH, step_duration=0.25,
                                  on_complete=on_complete)
    enemy_animator.start()
    info.text = "Animating enemy..."

def animate_both():
    """Animate both entities simultaneously"""
    info.text = "Animating both entities..."
    animate_player()
    animate_enemy()

# Camera follow test
camera_follow = True
camera_updates = 0

def update_camera(timer, runtime):
    """Update camera to follow player if enabled"""
    global camera_updates
    if camera_follow and player_animator and player_animator.animating:
        # Smooth camera follow. grid.center is in pixels; entity.x/.y are the
        # entity's draw position in pixels (draw_pos is the same in tile coords).
        grid.animate("center", (player.x, player.y), 0.25, mcrfpy.Easing.LINEAR)
        camera_updates += 1

# Setup
chain_test.activate()
cam_update_timer = mcrfpy.Timer("cam_update", update_camera, 100)

print("Animation Chaining Test")
print("=======================")

# --- Drive the chained animations headlessly -------------------------------
animate_both()

check("player animator started", player_animator.animating)
check("enemy animator started", enemy_animator.animating)

# Path node 0 is the entity's starting cell, so the first 0.2s step is a no-op
# move.  Halfway through the *second* step the entity must be strictly between
# nodes 0 and 1 -- i.e. the animation is interpolating, one step at a time.
for _ in range(2):
    mcrfpy.step(0.1)   # completes step 0, chains step 1
check("first step completed before the next began",
      player_animator.current_index == 1 and len(player_animator.completed_steps) == 1,
      f"(index={player_animator.current_index})")

mcrfpy.step(0.1)       # halfway through step 1: (2,2) -> (3,2)
mid_x = player.draw_pos.x
check("player interpolates between tiles", 2.0 < mid_x < 3.0,
      f"(draw_x={mid_x})")
check("only one step in flight at a time (mid-step)",
      player_animator.current_index == 1,
      f"(index={player_animator.current_index})")

# Player: 16 nodes * 0.2s; enemy: 14 nodes * 0.25s -> 3.5s worst case.
elapsed = 0.3
while elapsed < 6.0 and not (player_done and enemy_done):
    mcrfpy.step(0.05)
    elapsed += 0.05

# --- Assertions ------------------------------------------------------------
check("player path completed", player_done)
check("enemy path completed", enemy_done)
check("player animator stopped", not player_animator.animating)
check("enemy animator stopped", not enemy_animator.animating)

check("no overlapping player animations", player_animator.overlaps == 0,
      f"(overlaps={player_animator.overlaps})")
check("no overlapping enemy animations", enemy_animator.overlaps == 0,
      f"(overlaps={enemy_animator.overlaps})")

check("player visited every path node",
      [i for i, _ in player_animator.completed_steps] == list(range(len(PLAYER_PATH))),
      f"({player_animator.completed_steps})")
check("enemy visited every path node",
      [i for i, _ in enemy_animator.completed_steps] == list(range(len(ENEMY_PATH))),
      f"({enemy_animator.completed_steps})")

# Each step landed exactly on its path node (chaining kept positions in sync)
player_landings_ok = all(pos == (float(px), float(py))
                         for (i, pos), (px, py)
                         in zip(player_animator.completed_steps, PLAYER_PATH))
check("each player step landed on its path node", player_landings_ok,
      f"({player_animator.completed_steps})")

enemy_landings_ok = all(pos == (float(px), float(py))
                        for (i, pos), (px, py)
                        in zip(enemy_animator.completed_steps, ENEMY_PATH))
check("each enemy step landed on its path node", enemy_landings_ok,
      f"({enemy_animator.completed_steps})")

check("player ended at final path node",
      (player.draw_pos.x, player.draw_pos.y) == (float(PLAYER_PATH[-1][0]),
                                                 float(PLAYER_PATH[-1][1])),
      f"({player.draw_pos})")
check("enemy ended at final path node",
      (enemy.draw_pos.x, enemy.draw_pos.y) == (float(ENEMY_PATH[-1][0]),
                                               float(ENEMY_PATH[-1][1])),
      f"({enemy.draw_pos})")

# Camera-follow timer ran while the player was animating
check("camera follow timer fired during animation", camera_updates > 0,
      f"(updates={camera_updates})")

if failures:
    print(f"FAIL: {len(failures)} check(s) failed: {failures}")
    sys.exit(1)

print("PASS")
sys.exit(0)
