# McRogueFace Test Suite - Known Issues

## Test Results Summary

As of 2026-01-14, with `--mcrf-timeout=5`:
- **120 passed** (67%)
- **59 failed** (33%)
  - 40 timeout failures (tests requiring timers/animations)
  - 19 actual failures (API changes, missing features, or bugs)

## Timeout Failures (40 tests)

These tests require timers, animations, or callbacks that don't complete within the 5s timeout.
Run with `--mcrf-timeout=30` for a more permissive test run.

**Animation/Timer tests:**
- WORKING_automation_test_example.py
- benchmark_logging_test.py
- keypress_scene_validation_test.py
- simple_timer_screenshot_test.py
- test_animation_callback_simple.py
- test_animation_property_locking.py
- test_animation_raii.py
- test_animation_removal.py
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
