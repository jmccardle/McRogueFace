"""Integration test for #301: grid.step() turn manager."""
import mcrfpy
import sys

def make_grid(w=20, h=20):
    """Create a walkable grid with walls on borders."""
    scene = mcrfpy.Scene("test301")
    mcrfpy.current_scene = scene
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(w, h), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)
    for y in range(h):
        for x in range(w):
            pt = grid.at(x, y)
            if x == 0 or x == w-1 or y == 0 or y == h-1:
                pt.walkable = False
                pt.transparent = False
            else:
                pt.walkable = True
                pt.transparent = True
    return grid

def test_step_basic():
    """grid.step() executes without error."""
    grid = make_grid()
    e = mcrfpy.Entity((5, 5), grid=grid)
    e.set_behavior(int(mcrfpy.Behavior.NOISE4))
    grid.step()  # Should not crash
    print("PASS: grid.step() basic execution")

def test_step_noise_movement():
    """NOISE4 entity moves to adjacent cell after step."""
    grid = make_grid()
    e = mcrfpy.Entity((10, 10), grid=grid)
    e.set_behavior(int(mcrfpy.Behavior.NOISE4))
    e.move_speed = 0  # Instant movement

    old_x, old_y = e.cell_x, e.cell_y
    grid.step()
    new_x, new_y = e.cell_x, e.cell_y

    # Should have moved to an adjacent cell (or stayed if all blocked, unlikely in open grid)
    dx = abs(new_x - old_x)
    dy = abs(new_y - old_y)
    assert dx + dy <= 1, f"NOISE4 should move at most 1 cell cardinal, moved ({dx}, {dy})"
    assert dx + dy == 1, f"NOISE4 should move exactly 1 cell in open grid, moved ({dx}, {dy})"
    print("PASS: NOISE4 moves to adjacent cell")

def test_step_idle_no_move():
    """IDLE entity does not move."""
    grid = make_grid()
    e = mcrfpy.Entity((10, 10), grid=grid)
    # Default behavior is IDLE
    grid.step()
    assert e.cell_x == 10 and e.cell_y == 10, "IDLE entity should not move"
    print("PASS: IDLE entity stays put")

def test_step_turn_order():
    """Entities process in turn_order order."""
    grid = make_grid()
    order_log = []

    e1 = mcrfpy.Entity((5, 5), grid=grid)
    e1.turn_order = 2
    e1.set_behavior(int(mcrfpy.Behavior.CUSTOM))
    e1.step = lambda t, d: order_log.append(2)

    e2 = mcrfpy.Entity((7, 7), grid=grid)
    e2.turn_order = 1
    e2.set_behavior(int(mcrfpy.Behavior.CUSTOM))
    e2.step = lambda t, d: order_log.append(1)

    # CUSTOM behavior fires NO_ACTION, so step callback won't fire via triggers
    # But we can verify turn_order sorting via a different approach
    # Let's use SLEEP with turns=1 which triggers DONE
    e1.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=1)
    e1.step = lambda t, d: order_log.append(2)
    e2.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=1)
    e2.step = lambda t, d: order_log.append(1)

    grid.step()
    assert order_log == [1, 2], f"Expected [1, 2] turn order, got {order_log}"
    print("PASS: turn_order sorting")

def test_step_turn_order_zero_skip():
    """turn_order=0 entities are skipped."""
    grid = make_grid()
    e = mcrfpy.Entity((10, 10), grid=grid)
    e.turn_order = 0
    e.set_behavior(int(mcrfpy.Behavior.NOISE4))
    e.move_speed = 0

    grid.step()
    assert e.cell_x == 10 and e.cell_y == 10, "turn_order=0 entity should be skipped"
    print("PASS: turn_order=0 skipped")

def test_step_done_trigger():
    """SLEEP behavior fires DONE trigger when turns exhausted."""
    grid = make_grid()
    triggered = []

    e = mcrfpy.Entity((5, 5), grid=grid)
    e.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=2)
    e.step = lambda t, d: triggered.append(int(t))

    grid.step()  # Sleep turns: 2 -> 1
    assert len(triggered) == 0, "Should not trigger DONE after first step"

    grid.step()  # Sleep turns: 1 -> 0 -> DONE
    assert len(triggered) == 1, f"Should trigger DONE, got {len(triggered)} triggers"
    assert triggered[0] == int(mcrfpy.Trigger.DONE), f"Should be DONE trigger, got {triggered[0]}"
    print("PASS: SLEEP DONE trigger")

def test_step_n_rounds():
    """grid.step(n=3) executes 3 rounds."""
    grid = make_grid()
    e = mcrfpy.Entity((10, 10), grid=grid)
    e.set_behavior(int(mcrfpy.Behavior.NOISE4))
    e.move_speed = 0

    grid.step(n=3)
    # After 3 steps of NOISE4, entity should have moved
    # Can't predict exact position due to randomness
    print("PASS: grid.step(n=3) executes without error")

def test_step_turn_order_filter():
    """grid.step(turn_order=1) only processes entities with that turn_order."""
    grid = make_grid()
    e1 = mcrfpy.Entity((5, 5), grid=grid)
    e1.turn_order = 1
    e1.set_behavior(int(mcrfpy.Behavior.NOISE4))
    e1.move_speed = 0

    e2 = mcrfpy.Entity((10, 10), grid=grid)
    e2.turn_order = 2
    e2.set_behavior(int(mcrfpy.Behavior.NOISE4))
    e2.move_speed = 0

    grid.step(turn_order=1)
    # e1 should have moved, e2 should not
    assert not (e1.cell_x == 5 and e1.cell_y == 5), "turn_order=1 entity should have moved"
    assert e2.cell_x == 10 and e2.cell_y == 10, "turn_order=2 entity should not have moved"
    print("PASS: turn_order filter")

if __name__ == "__main__":
    test_step_basic()
    test_step_noise_movement()
    test_step_idle_no_move()
    test_step_turn_order()
    test_step_turn_order_zero_skip()
    test_step_done_trigger()
    test_step_n_rounds()
    test_step_turn_order_filter()
    print("All #301 tests passed")
    sys.exit(0)
