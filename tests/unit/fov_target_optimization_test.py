"""Unit test for #303: FOV optimization for TARGET triggers in grid.step().

Tests the tiered optimization:
  Tier 1: O(1) label check - no target_label means no FOV
  Tier 2: O(bucket) spatial hash - only nearby entities checked
  Tier 3: O(radius^2) bounded FOV via TCOD radius param
  Tier 4: Per-entity FOV cache - skip recomputation when entity+map unchanged
"""
import mcrfpy
import sys

def make_grid(w=20, h=20):
    """Create a walkable, transparent grid."""
    scene = mcrfpy.Scene("test303")
    mcrfpy.current_scene = scene
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(w, h), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)
    for y in range(h):
        for x in range(w):
            pt = grid.at(x, y)
            pt.walkable = True
            pt.transparent = True
    return grid


def test_target_trigger_fires():
    """TARGET trigger fires when entity can see a labeled target."""
    grid = make_grid()
    triggered = []

    hunter = mcrfpy.Entity((5, 5), grid=grid)
    hunter.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=99)
    hunter.target_label = "prey"
    hunter.sight_radius = 10
    hunter.step = lambda t, d: triggered.append(("TARGET", d))

    prey = mcrfpy.Entity((7, 5), grid=grid)
    prey.labels = {"prey"}
    prey.turn_order = 0  # skip prey's own turn

    grid.step()
    assert len(triggered) == 1, f"TARGET should fire once, got {len(triggered)}"
    print("PASS: TARGET trigger fires on visible labeled entity")


def test_target_trigger_blocked_by_wall():
    """TARGET trigger does NOT fire when wall blocks line of sight."""
    grid = make_grid()
    triggered = []

    hunter = mcrfpy.Entity((5, 5), grid=grid)
    hunter.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=99)
    hunter.target_label = "prey"
    hunter.sight_radius = 10
    hunter.step = lambda t, d: triggered.append("TARGET")

    # Place wall between hunter and prey
    grid.at(6, 5).transparent = False

    prey = mcrfpy.Entity((8, 5), grid=grid)
    prey.labels = {"prey"}
    prey.turn_order = 0

    grid.step()
    assert len(triggered) == 0, f"TARGET should NOT fire through wall, got {len(triggered)}"
    print("PASS: TARGET blocked by opaque wall")


def test_target_trigger_out_of_range():
    """TARGET trigger does NOT fire when target is beyond sight_radius."""
    grid = make_grid()
    triggered = []

    hunter = mcrfpy.Entity((2, 2), grid=grid)
    hunter.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=99)
    hunter.target_label = "prey"
    hunter.sight_radius = 3
    hunter.step = lambda t, d: triggered.append("TARGET")

    prey = mcrfpy.Entity((15, 15), grid=grid)
    prey.labels = {"prey"}
    prey.turn_order = 0

    grid.step()
    assert len(triggered) == 0, f"TARGET should NOT fire beyond sight_radius, got {len(triggered)}"
    print("PASS: TARGET not fired beyond sight_radius")


def test_no_target_label_skips_fov():
    """Entity without target_label should not trigger TARGET (Tier 1 skip)."""
    grid = make_grid()
    triggered = []

    entity = mcrfpy.Entity((5, 5), grid=grid)
    entity.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=99)
    # No target_label set
    entity.step = lambda t, d: triggered.append(int(t))

    prey = mcrfpy.Entity((6, 5), grid=grid)
    prey.labels = {"prey"}
    prey.turn_order = 0

    grid.step()
    # Should get DONE eventually, but never TARGET
    target_triggers = [t for t in triggered if t == int(mcrfpy.Trigger.TARGET)]
    assert len(target_triggers) == 0, "No target_label = no TARGET trigger"
    print("PASS: no target_label skips TARGET check (Tier 1)")


def test_wrong_label_no_trigger():
    """TARGET trigger requires matching label."""
    grid = make_grid()
    triggered = []

    hunter = mcrfpy.Entity((5, 5), grid=grid)
    hunter.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=99)
    hunter.target_label = "prey"
    hunter.sight_radius = 10
    hunter.step = lambda t, d: triggered.append("TARGET")

    decoy = mcrfpy.Entity((6, 5), grid=grid)
    decoy.labels = {"friendly"}  # Wrong label
    decoy.turn_order = 0

    grid.step()
    assert len(triggered) == 0, "Wrong label should not trigger TARGET"
    print("PASS: wrong label does not trigger TARGET")


def test_fov_cache_reuse_stationary():
    """Per-entity FOV cache should allow repeated steps without recomputation
    when entity hasn't moved and map hasn't changed (Tier 4)."""
    grid = make_grid()
    trigger_count = []

    hunter = mcrfpy.Entity((5, 5), grid=grid)
    hunter.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=99)
    hunter.target_label = "prey"
    hunter.sight_radius = 10
    hunter.step = lambda t, d: trigger_count.append(1)

    prey = mcrfpy.Entity((7, 5), grid=grid)
    prey.labels = {"prey"}
    prey.turn_order = 0

    # Multiple steps - entity doesn't move, map doesn't change
    # The per-entity FOV cache should be reused after the first computation
    for _ in range(5):
        grid.step()

    assert len(trigger_count) == 5, (
        f"TARGET should fire every step (cached FOV reuse), got {len(trigger_count)}"
    )
    print("PASS: FOV cache reuse for stationary entity (Tier 4)")


def test_fov_cache_invalidated_on_transparency_change():
    """FOV cache should invalidate when a cell's transparency changes."""
    grid = make_grid()
    triggered = []

    hunter = mcrfpy.Entity((5, 5), grid=grid)
    hunter.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=99)
    hunter.target_label = "prey"
    hunter.sight_radius = 10
    hunter.step = lambda t, d: triggered.append(1)

    prey = mcrfpy.Entity((8, 5), grid=grid)
    prey.labels = {"prey"}
    prey.turn_order = 0

    # First step: visible, should trigger
    grid.step()
    assert len(triggered) == 1, "Should trigger on first step"

    # Block line of sight
    grid.at(6, 5).transparent = False
    grid.at(7, 5).transparent = False

    # Second step: cache should be invalidated, FOV recomputed, no trigger
    triggered.clear()
    grid.step()
    assert len(triggered) == 0, (
        f"Should NOT trigger after wall placed, got {len(triggered)}"
    )
    print("PASS: FOV cache invalidated on transparency change")


def test_multiple_hunters_independent_caches():
    """Multiple entities with target_label should have independent FOV caches."""
    grid = make_grid()
    results = {"a": [], "b": []}

    hunter_a = mcrfpy.Entity((3, 3), grid=grid)
    hunter_a.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=99)
    hunter_a.target_label = "prey"
    hunter_a.sight_radius = 5
    hunter_a.step = lambda t, d: results["a"].append(1)

    hunter_b = mcrfpy.Entity((17, 17), grid=grid)
    hunter_b.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=99)
    hunter_b.target_label = "prey"
    hunter_b.sight_radius = 5
    hunter_b.step = lambda t, d: results["b"].append(1)

    # Prey near hunter_a but far from hunter_b
    prey = mcrfpy.Entity((4, 3), grid=grid)
    prey.labels = {"prey"}
    prey.turn_order = 0

    grid.step()
    assert len(results["a"]) == 1, "Hunter A should see prey"
    assert len(results["b"]) == 0, "Hunter B should NOT see prey (out of range)"
    print("PASS: multiple hunters with independent FOV caches")


def test_target_trigger_n_rounds():
    """TARGET fires once per round in multi-round step (n>1)."""
    grid = make_grid()
    triggered = []

    hunter = mcrfpy.Entity((5, 5), grid=grid)
    hunter.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=99)
    hunter.target_label = "prey"
    hunter.sight_radius = 10
    hunter.step = lambda t, d: triggered.append(1)

    prey = mcrfpy.Entity((7, 5), grid=grid)
    prey.labels = {"prey"}
    prey.turn_order = 0

    grid.step(n=3)
    assert len(triggered) == 3, f"TARGET should fire 3 times for n=3, got {len(triggered)}"
    print("PASS: TARGET fires per round in multi-round step")


if __name__ == "__main__":
    test_target_trigger_fires()
    test_target_trigger_blocked_by_wall()
    test_target_trigger_out_of_range()
    test_no_target_label_skips_fov()
    test_wrong_label_no_trigger()
    test_fov_cache_reuse_stationary()
    test_fov_cache_invalidated_on_transparency_change()
    test_multiple_hunters_independent_caches()
    test_target_trigger_n_rounds()
    print("All #303 FOV optimization tests passed")
    sys.exit(0)
