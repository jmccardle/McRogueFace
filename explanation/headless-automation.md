# Headless Mode and Automation

McRogueFace supports headless operation for automated testing, CI/CD pipelines, and programmatic control without a display.

## Running Headless

Launch with the `--headless` flag:

```bash
mcrogueface --headless --exec game.py
```

Or use xvfb for a virtual framebuffer (required for rendering):

```bash
xvfb-run -a -s "-screen 0 1024x768x24" mcrogueface --headless --exec game.py
```

## Time Control with mcrfpy.step()

In headless mode, you control time explicitly rather than waiting for real-time to pass. The `step()` function takes **seconds** as a float:

```python
import mcrfpy

# Advance simulation by 100ms
mcrfpy.step(0.1)

# Advance by 1 second
mcrfpy.step(1.0)

# Advance by 16ms (~60fps frame)
mcrfpy.step(0.016)
```

### Why This Matters

Traditional timer-based code waits for real time and the game loop:

```python
# OLD PATTERN - waits for game loop, subject to timeouts
def delayed_action(timer, runtime):
    print("Action!")
    sys.exit(0)

mcrfpy.Timer("delay", delayed_action, 500, once=True)
# Script ends, game loop runs, timer eventually fires
```

With `mcrfpy.step()`, you control the clock synchronously:

```python
# NEW PATTERN - instant, deterministic
mcrfpy.Timer("delay", delayed_action, 500, once=True)
mcrfpy.step(0.6)  # Advance 600ms - timer fires during this call
```

### Timer Behavior

- Timers fire **once per `step()` call** if their interval has elapsed
- To fire a timer multiple times, call `step()` multiple times:

```python
count = 0
def tick(timer, runtime):
    global count
    count += 1

timer = mcrfpy.Timer("tick", tick, 100)  # Fire every 100ms

# Each step() processes timers once
for i in range(5):
    mcrfpy.step(0.1)  # 100ms each

print(count)  # 5
```

## Screenshots

The `automation.screenshot()` function captures the current frame:

```python
from mcrfpy import automation

# Capture screenshot (synchronous in headless mode)
result = automation.screenshot("output.png")
print(f"Screenshot saved: {result}")
```

**Key insight:** In headless mode, `screenshot()` is synchronous - no timer dance needed.

## Testing Patterns

### Synchronous Test Structure

```python
#!/usr/bin/env python3
import mcrfpy
import sys

# Setup scene
scene = mcrfpy.Scene("test")
scene.activate()
mcrfpy.step(0.1)  # Initialize scene

# Create test objects
frame = mcrfpy.Frame(pos=(100, 100), size=(50, 50))
scene.children.append(frame)

# Verify state
if frame.x != 100:
    print("FAIL: frame.x should be 100")
    sys.exit(1)

print("PASS")
sys.exit(0)
```

### Testing Animations

```python
# Create frame and start animation
frame = mcrfpy.Frame(pos=(100, 100), size=(50, 50))
scene.children.append(frame)

anim = mcrfpy.Animation("x", 200.0, 1.0, "linear")  # 1 second duration
anim.start(frame)

# Advance to midpoint (0.5 seconds)
mcrfpy.step(0.5)
# frame.x should be ~150 (halfway between 100 and 200)

# Advance to completion
mcrfpy.step(0.6)  # Past the 1.0s duration
# frame.x should be 200

if frame.x == 200.0:
    print("PASS: Animation completed")
    sys.exit(0)
```

### Testing Timers

```python
callback_count = 0

def on_timer(timer, runtime):
    """Timer callbacks receive (timer_object, runtime_ms)"""
    global callback_count
    callback_count += 1
    print(f"Timer fired! Count: {callback_count}, runtime: {runtime}ms")

# Create timer that fires every 100ms
timer = mcrfpy.Timer("test", on_timer, 100)

# Advance time - each step() can fire the timer once
mcrfpy.step(0.15)  # First fire at ~100ms
mcrfpy.step(0.15)  # Second fire at ~200ms

if callback_count >= 2:
    print("PASS")
    sys.exit(0)
```

### Testing with once=True Timers

```python
fired = False

def one_shot(timer, runtime):
    global fired
    fired = True
    print(f"One-shot timer fired! once={timer.once}")

# Create one-shot timer
timer = mcrfpy.Timer("oneshot", one_shot, 100, once=True)

mcrfpy.step(0.15)  # Should fire
mcrfpy.step(0.15)  # Should NOT fire again

if fired:
    print("PASS: One-shot timer worked")
```

## Pattern Comparison

| Aspect | Timer-based (old) | step()-based (new) |
|--------|-------------------|-------------------|
| Execution | Async (game loop) | Sync (immediate) |
| Timeout risk | High | None |
| Determinism | Variable | Consistent |
| Script flow | Callbacks | Linear |

## LLM Agent Integration

Headless mode enables AI agents to interact with McRogueFace programmatically:

1. **Observe**: Capture screenshots, read game state
2. **Decide**: Process with vision models or state analysis
3. **Act**: Send input commands, modify game state
4. **Verify**: Check results, capture new state

```python
from mcrfpy import automation

# Agent loop
while not game_over:
    automation.screenshot("state.png")
    action = agent.decide("state.png")
    execute_action(action)
    mcrfpy.step(0.1)  # Let action take effect
```

## Best Practices

1. **Use `mcrfpy.step()`** instead of real-time waiting for all headless tests
2. **Initialize scenes** with a brief `step(0.1)` after `activate()`
3. **Be deterministic** - same inputs should produce same outputs
4. **Test incrementally** - advance time in small steps to catch intermediate states
5. **Use `sys.exit(0/1)`** for clear pass/fail signals to test runners
6. **Multiple `step()` calls** to fire repeating timers multiple times

## Running the Test Suite

```bash
# Quick run with pytest wrapper
pytest tests/ -q --mcrf-timeout=5

# Using the original runner with xvfb
xvfb-run -a python3 tests/run_tests.py -q

# Run specific test directly
xvfb-run -a mcrogueface --headless --exec tests/unit/test_animation.py
```

## Related Topics

- [Animation System](animation.md) - How animations work
- [Scene API](scene-api.md) - Managing scenes
- [Timer API](timer-api.md) - Timer details
