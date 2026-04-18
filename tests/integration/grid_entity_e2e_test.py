"""Phase 5.1 (#36): End-to-end scenario test.

Exercises Grid + GridView + the full entity behavior system in one realistic
scenario over 100 turns:

  * Player  - turn_order=0 (skipped by step()), labeled "player", manually placed
  * Guard   - PATROL waypoints, target_label="player", switches to SEEK on TARGET
  * NPC     - NOISE8 random 8-directional wandering
  * Trap    - SLEEP for 10 turns, fires DONE callback then becomes IDLE

Verifies:
  - 100 calls to grid.step() complete with no crashes / Python exceptions
  - Guard either visited >=2 patrol waypoints OR switched to SEEK on player sight
  - NPC moved away from its starting cell at least once
  - Trap's DONE callback fired exactly once and its behavior reverted to IDLE
"""
import mcrfpy
import sys


WIDTH = 20
HEIGHT = 20


def make_walled_grid():
    scene = mcrfpy.Scene("e2e_phase5")
    mcrfpy.current_scene = scene
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(WIDTH, HEIGHT), texture=tex,
                       pos=(0, 0), size=(320, 320))
    scene.children.append(grid)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            cell = grid.at(x, y)
            wall = (x == 0 or y == 0 or x == WIDTH - 1 or y == HEIGHT - 1)
            cell.walkable = not wall
            cell.transparent = not wall
    return scene, grid


def attach_gridview(scene, grid):
    """Attach a GridView so the Grid+GridView pairing is exercised, not only the Grid alone."""
    view = mcrfpy.GridView(grid=grid, pos=(0, 0), size=(320, 320))
    scene.children.append(view)
    return view


def main():
    scene, grid = make_walled_grid()
    attach_gridview(scene, grid)

    # ---- Player: manually placed, skipped by step() -------------------------
    # Placed near (15,15) waypoint so the Guard hits PATROL phase first and
    # then triggers TARGET once it reaches that corner of its route.
    player = mcrfpy.Entity((17, 17), grid=grid, labels=["player"])
    player.turn_order = 0  # excluded from step()
    player_start = (player.cell_x, player.cell_y)

    # ---- Guard: PATROL with TARGET->SEEK switch -----------------------------
    guard_state = {"seek_engaged": False, "target_seen_at": None,
                   "target_trigger_count": 0}
    waypoints = [(5, 5), (15, 5), (15, 15), (5, 15)]
    visited_waypoints = set()

    guard = mcrfpy.Entity((5, 5), grid=grid, labels=["guard"])
    guard.turn_order = 1
    guard.move_speed = 0  # snap movement so we can verify positions per step
    guard.target_label = "player"
    guard.sight_radius = 5
    guard.set_behavior(int(mcrfpy.Behavior.PATROL), waypoints=waypoints)

    def guard_step(trigger, data):
        # Only TARGET should reach us in this scenario; PATROL never returns DONE.
        if trigger == mcrfpy.Trigger.TARGET:
            guard_state["target_trigger_count"] += 1
            if not guard_state["seek_engaged"]:
                target_pos = (data.cell_x, data.cell_y) if data is not None else None
                guard_state["target_seen_at"] = target_pos
                guard_state["seek_engaged"] = True
                # Switch to SEEK using the player as a static target (Player
                # never moves, so a TargetProvider is sufficient).
                if target_pos is not None:
                    guard.set_behavior(int(mcrfpy.Behavior.SEEK),
                                       pathfinder=target_pos)
    guard.step = guard_step

    # ---- NPC: NOISE8 random 8-directional wandering -------------------------
    npc = mcrfpy.Entity((3, 17), grid=grid, labels=["npc"])
    npc.turn_order = 2
    npc.move_speed = 0
    npc.set_behavior(int(mcrfpy.Behavior.NOISE8))
    npc_start = (npc.cell_x, npc.cell_y)
    npc_visited = {npc_start}

    # ---- Trap: SLEEP -> DONE -> IDLE ---------------------------------------
    SLEEP_TURNS = 10
    trap_state = {"done_count": 0, "done_at_step": None}

    trap = mcrfpy.Entity((17, 3), grid=grid, labels=["trap"])
    trap.turn_order = 3
    trap.move_speed = 0
    trap.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=SLEEP_TURNS)
    # default_behavior is IDLE (0) - executed after DONE per UIGridPyMethods.cpp:854

    def trap_step(trigger, data):
        if trigger == mcrfpy.Trigger.DONE:
            trap_state["done_count"] += 1
            trap_state["done_at_step"] = current_step["i"]
    trap.step = trap_step

    current_step = {"i": 0}

    # ---- Run 100 turns ------------------------------------------------------
    for i in range(1, 101):
        current_step["i"] = i
        grid.step()

        # Snapshot per-step Guard / NPC positions for behaviour assertions.
        gx, gy = guard.cell_x, guard.cell_y
        if (gx, gy) in waypoints:
            visited_waypoints.add((gx, gy))
        npc_visited.add((npc.cell_x, npc.cell_y))

    # ---- Assertions ---------------------------------------------------------
    failures = []

    # Player must not have moved (turn_order=0).
    if (player.cell_x, player.cell_y) != player_start:
        failures.append(f"Player moved despite turn_order=0: "
                        f"{player_start} -> ({player.cell_x},{player.cell_y})")

    # Guard: with player at (17,17) and sight_radius=5, the guard's PATROL
    # route (5,5)->(15,5)->(15,15)->(5,15) means TARGET only fires around the
    # (15,15) corner.  We expect to see BOTH at least one patrol waypoint
    # visited AND SEEK engaged by turn 100.
    if len(visited_waypoints) < 1:
        failures.append(
            f"Guard visited no patrol waypoints (visited={visited_waypoints})")
    if not guard_state["seek_engaged"]:
        failures.append(
            f"Guard never engaged SEEK despite player at {player_start} "
            f"(waypoints visited: {visited_waypoints})"
        )

    # If SEEK engaged, the trigger must have fired at least once and we should
    # have moved closer to the player by the end of the run (TargetProvider
    # walks straight toward the goal).
    if guard_state["seek_engaged"]:
        if guard_state["target_trigger_count"] < 1:
            failures.append("seek_engaged set but target_trigger_count==0")
        # We can't guarantee adjacency by turn 100 (path can be long), but the
        # guard must not still be parked on its starting waypoint.
        if (guard.cell_x, guard.cell_y) == (5, 5):
            failures.append("Guard engaged SEEK but never left starting cell")

    # NPC: NOISE8 in an open grid must move at least once over 100 steps.
    if (npc.cell_x, npc.cell_y) == npc_start and len(npc_visited) == 1:
        failures.append(f"NPC NOISE8 never moved from {npc_start}")

    # Trap: DONE must fire exactly once after SLEEP_TURNS, then revert to IDLE.
    if trap_state["done_count"] != 1:
        failures.append(
            f"Trap DONE fired {trap_state['done_count']} times, expected 1")
    elif trap_state["done_at_step"] != SLEEP_TURNS:
        failures.append(
            f"Trap DONE fired at step {trap_state['done_at_step']}, "
            f"expected step {SLEEP_TURNS}")
    if trap.behavior_type != int(mcrfpy.Behavior.IDLE):
        failures.append(
            f"Trap behavior_type={trap.behavior_type} after DONE, "
            f"expected IDLE ({int(mcrfpy.Behavior.IDLE)})")

    # ---- Report -------------------------------------------------------------
    print(f"Player: stayed at {player_start} (turn_order=0): "
          f"{'OK' if (player.cell_x, player.cell_y) == player_start else 'FAIL'}")
    print(f"Guard: visited waypoints {sorted(visited_waypoints)}, "
          f"seek_engaged={guard_state['seek_engaged']}, "
          f"target_triggers={guard_state['target_trigger_count']}, "
          f"final={(guard.cell_x, guard.cell_y)}")
    print(f"NPC: visited {len(npc_visited)} unique cells, "
          f"final={(npc.cell_x, npc.cell_y)}")
    print(f"Trap: DONE fired {trap_state['done_count']}x at step "
          f"{trap_state['done_at_step']}, behavior_type={trap.behavior_type}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print("FAIL")
        sys.exit(1)

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
