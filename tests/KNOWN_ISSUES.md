# McRogueFace Test Suite - Known Issues

## Test Results Summary

As of 2026-01-14, with `--mcrf-timeout=5`:
- **120 passed** (67%)
- **59 failed** (33%)
  - 40 timeout failures (tests requiring timers/animations)
  - 19 actual failures (API changes, missing features, or bugs)

## Synchronous Testing with `mcrfpy.step()`

**RECOMMENDED:** Use `mcrfpy.step(t)` to advance simulation time synchronously instead of relying on Timer callbacks and the game loop. This eliminates timeout issues and makes tests deterministic.

### Old Pattern (Timer-based, async)

```python
# OLD: Requires game loop, subject to timeouts
def run_tests(timer, runtime):
    # tests here
    sys.exit(0)

mcrfpy.Timer("run", run_tests, 100, once=True)
# Script ends, game loop runs, timer eventually fires
```

### New Pattern (step-based, sync)

```python
# NEW: Synchronous, no timeouts
import mcrfpy
import sys

# Setup scene
scene = mcrfpy.Scene("test")
scene.activate()
mcrfpy.step(0.1)  # Initialize scene

# Run tests directly
frame = mcrfpy.Frame(pos=(100, 100), size=(100, 100))
scene.children.append(frame)

# Start animation
anim = mcrfpy.Animation("x", 500.0, 1.0, "linear")
anim.start(frame)

# Advance simulation to complete animation
mcrfpy.step(1.5)  # Advances 1.5 seconds synchronously

# Verify results
if frame.x == 500.0:
    print("PASS")
    sys.exit(0)
else:
    print("FAIL")
    sys.exit(1)
```

### Key Differences

| Aspect | Timer-based | step()-based |
|--------|-------------|--------------|
| Execution | Async (game loop) | Sync (immediate) |
| Timeout risk | High | None |
| Determinism | Variable | Consistent |
| Timer firing | Once per step() call | Per elapsed interval |

### Timer Behavior with `step()`

- Timers fire once per `step()` call if their interval has elapsed
- To fire a timer multiple times, call `step()` multiple times:

```python
# Timer fires every 100ms
timer = mcrfpy.Timer("tick", callback, 100)

# This fires the timer ~6 times
for i in range(6):
    mcrfpy.step(0.1)  # Each step processes timers once
```

## Refactored Tests

The following tests have been converted to use `mcrfpy.step()`:
- simple_timer_screenshot_test.py
- test_animation_callback_simple.py
- test_animation_property_locking.py
- test_animation_raii.py
- test_animation_removal.py
- test_timer_callback.py
- test_timer_once.py

## Remaining Timeout Failures

These tests still use Timer-based async patterns:
- WORKING_automation_test_example.py
- benchmark_logging_test.py
- keypress_scene_validation_test.py
- test_empty_animation_manager.py
- test_simple_callback.py

**Headless mode tests:**
- test_headless_detection.py
- test_headless_modes.py

**Other timing-dependent:**
- test_color_helpers.py
- test_frame_clipping.py
- test_frame_clipping_advanced.py
- test_grid_children.py
- test_no_arg_constructors.py
- test_properties_quick.py
- test_python_object_cache.py
- test_simple_drawable.py

## Running Tests

```bash
# Quick run (5s timeout, many timeouts expected)
pytest tests/ -q --mcrf-timeout=5

# Full run (30s timeout, should pass most timing tests)
pytest tests/ -q --mcrf-timeout=30

# Filter by pattern
pytest tests/ -k "bsp" -q

# Run original runner
python3 tests/run_tests.py -q
```

## Recommendations

1. **For CI:** Use `--mcrf-timeout=10` and accept ~30% timeout failures
2. **For local dev:** Use `--mcrf-timeout=30` for comprehensive testing
3. **For quick validation:** Use `-k "not animation and not timer"` to skip slow tests
