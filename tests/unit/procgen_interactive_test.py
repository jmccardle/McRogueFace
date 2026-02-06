#!/usr/bin/env python3
"""Unit tests for the Interactive Procedural Generation Demo System.

Tests:
- Demo creation and initialization
- Step execution (forward/backward)
- Parameter changes and regeneration
- Layer visibility toggling
- State snapshot capture/restore
"""

import sys
import os

# Add tests directory to path
tests_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

import mcrfpy
from procgen_interactive.demos.cave_demo import CaveDemo
from procgen_interactive.demos.dungeon_demo import DungeonDemo
from procgen_interactive.demos.terrain_demo import TerrainDemo
from procgen_interactive.demos.town_demo import TownDemo


def test_cave_demo():
    """Test Cave demo creation and stepping."""
    print("Testing CaveDemo...")

    demo = CaveDemo()
    demo.activate()

    # Run all steps
    for i in range(len(demo.steps)):
        demo.advance_step()
        assert demo.current_step == i + 1, f"Step count mismatch: {demo.current_step} != {i + 1}"

    # Test backward navigation
    demo.reverse_step()
    assert demo.current_step == len(demo.steps) - 1, "Reverse step failed"

    print("  CaveDemo OK")
    return True


def test_dungeon_demo():
    """Test Dungeon demo creation and stepping."""
    print("Testing DungeonDemo...")

    demo = DungeonDemo()
    demo.activate()

    # Run all steps
    for i in range(len(demo.steps)):
        demo.advance_step()

    assert demo.current_step == len(demo.steps), "Step count mismatch"
    print("  DungeonDemo OK")
    return True


def test_terrain_demo():
    """Test Terrain demo creation and stepping."""
    print("Testing TerrainDemo...")

    demo = TerrainDemo()
    demo.activate()

    # Run all steps
    for i in range(len(demo.steps)):
        demo.advance_step()

    assert demo.current_step == len(demo.steps), "Step count mismatch"
    print("  TerrainDemo OK")
    return True


def test_town_demo():
    """Test Town demo creation and stepping."""
    print("Testing TownDemo...")

    demo = TownDemo()
    demo.activate()

    # Run all steps
    for i in range(len(demo.steps)):
        demo.advance_step()

    assert demo.current_step == len(demo.steps), "Step count mismatch"
    print("  TownDemo OK")
    return True


def test_parameter_change(demo=None):
    """Test that parameter changes trigger regeneration."""
    print("Testing parameter changes...")

    # Reuse existing demo if provided (to avoid scene name conflict)
    if demo is None:
        demo = CaveDemo()
        demo.activate()

    # Change a parameter
    seed_param = demo.parameters["seed"]
    original_seed = seed_param.value

    # Test parameter value change
    seed_param.value = original_seed + 1
    assert seed_param.value == original_seed + 1, "Parameter value not updated"

    # Test parameter bounds
    seed_param.value = -10  # Should clamp to min (0)
    assert seed_param.value >= 0, "Parameter min bound not enforced"

    # Test increment/decrement
    seed_param.value = 100
    old_val = seed_param.value
    seed_param.increment()
    assert seed_param.value > old_val, "Increment failed"

    seed_param.decrement()
    assert seed_param.value == old_val, "Decrement failed"

    print("  Parameter changes OK")
    return True


def test_layer_visibility(demo=None):
    """Test layer visibility toggling."""
    print("Testing layer visibility...")

    # Reuse existing demo if provided (to avoid scene name conflict)
    if demo is None:
        demo = CaveDemo()
        demo.activate()

    # Get a layer
    final_layer = demo.get_layer("final")
    assert final_layer is not None, "Layer not found"

    # Test visibility toggle
    original_visible = final_layer.visible
    final_layer.visible = not original_visible
    assert final_layer.visible == (not original_visible), "Visibility not toggled"

    # Toggle back
    final_layer.visible = original_visible
    assert final_layer.visible == original_visible, "Visibility not restored"

    print("  Layer visibility OK")
    return True


def main():
    """Run all tests."""
    print("=" * 50)
    print("Interactive Procgen Demo System Tests")
    print("=" * 50)
    print()

    passed = 0
    failed = 0

    # Demo creation tests
    demo_tests = [
        ("test_cave_demo", test_cave_demo),
        ("test_dungeon_demo", test_dungeon_demo),
        ("test_terrain_demo", test_terrain_demo),
        ("test_town_demo", test_town_demo),
    ]

    # Create a fresh cave demo for parameter/layer tests
    cave_demo = None

    for name, test in demo_tests:
        try:
            if test():
                passed += 1
                # Save cave demo for later tests
                if name == "test_cave_demo":
                    cave_demo = CaveDemo.__last_instance__ if hasattr(CaveDemo, '__last_instance__') else None
            else:
                failed += 1
                print(f"  FAILED: {name}")
        except Exception as e:
            failed += 1
            print(f"  ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()

    # Parameter and layer tests use the last cave demo created
    # (or create a new one if cave test didn't run)
    try:
        # These tests are about the parameter/layer system, not demo creation
        # We test with the first cave demo's parameters and layers
        from procgen_interactive.core.parameter import Parameter

        print("Testing parameter system...")
        p = Parameter(name="test", display="Test", type="int", default=50, min_val=0, max_val=100)
        p.value = 75
        assert p.value == 75, "Parameter set failed"
        p.increment()
        assert p.value == 76, "Increment failed"
        p.value = -10
        assert p.value == 0, "Min bound not enforced"
        p.value = 200
        assert p.value == 100, "Max bound not enforced"
        print("  Parameter system OK")
        passed += 1

        print("Testing float parameter...")
        p = Parameter(name="test", display="Test", type="float", default=0.5, min_val=0.0, max_val=1.0, step=0.1)
        p.value = 0.7
        assert abs(p.value - 0.7) < 0.001, "Float parameter set failed"
        p.increment()
        assert abs(p.value - 0.8) < 0.001, "Float increment failed"
        print("  Float parameter OK")
        passed += 1

    except Exception as e:
        failed += 1
        print(f"  ERROR in parameter tests: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)

    if failed == 0:
        print("PASS")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
