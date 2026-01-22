# McRogueFace Test Suite

Automated tests for the McRogueFace game engine.

## Directory Structure

```
tests/
├── unit/           # Unit tests for individual components (155+ tests)
├── integration/    # Integration tests for system interactions
├── regression/     # Bug regression tests (issue_XX_*.py)
├── benchmarks/     # Performance benchmarks
├── demo/           # Interactive demo system
│   ├── demo_main.py    # Demo runner
│   └── screens/        # Per-feature demo screens
├── conftest.py     # Pytest configuration and fixtures
├── pytest.ini      # Pytest settings
├── run_tests.py    # Standalone test runner
└── KNOWN_ISSUES.md # Test status and mcrfpy.step() documentation
```

## Running Tests

### With pytest (recommended)

```bash
# Run all tests
pytest tests/ -v

# Run specific directory
pytest tests/unit/ -v

# Run tests matching a pattern
pytest tests/ -k "bsp" -v

# Quick run with short timeout (some timeouts expected)
pytest tests/ -q --mcrf-timeout=5

# Full run with longer timeout
pytest tests/ -q --mcrf-timeout=30

# Stop on first failure
pytest tests/ -x
```

### With run_tests.py

```bash
# Run all tests
python3 tests/run_tests.py

# Run specific category
python3 tests/run_tests.py unit
python3 tests/run_tests.py regression

# Verbose output
python3 tests/run_tests.py -v

# Quiet (no checksums)
python3 tests/run_tests.py -q

# Custom timeout
python3 tests/run_tests.py --timeout=30
```

### Running individual tests

```bash
cd build
./mcrogueface --headless --exec ../tests/unit/some_test.py
```

## Writing Tests

### Test Pattern: Synchronous with `mcrfpy.step()`

**Recommended:** Use `mcrfpy.step(t)` to advance simulation time synchronously.

```python
import mcrfpy
import sys

# Setup
scene = mcrfpy.Scene("test")
scene.activate()

# Create UI elements
frame = mcrfpy.Frame(pos=(100, 100), size=(50, 50))
scene.children.append(frame)

# Start animation
frame.animate("x", 500.0, 1.0, mcrfpy.Easing.LINEAR)

# Advance simulation synchronously
mcrfpy.step(1.5)

# Verify results
if abs(frame.x - 500.0) < 0.1:
    print("PASS")
    sys.exit(0)
else:
    print(f"FAIL: frame.x = {frame.x}, expected 500.0")
    sys.exit(1)
```

### Test Pattern: Timer-based (legacy)

For tests that need multiple timer callbacks or complex timing:

```python
import mcrfpy
import sys

def run_test(runtime):
    # Test code here
    print("PASS")
    sys.exit(0)

scene = mcrfpy.Scene("test")
scene.activate()

# Timer fires after 100ms
timer = mcrfpy.Timer("test", run_test, 100)
# Script ends, game loop runs timer
```

### Test Output

- Print `PASS` and `sys.exit(0)` for success
- Print `FAIL` with details and `sys.exit(1)` for failure
- Tests that timeout are marked as failures

## Test Categories

### Unit Tests (`unit/`)

Test individual components in isolation:
- `*_test.py` - Standard component tests
- `api_*_test.py` - Python API tests
- `automation_*_test.py` - Automation module tests

### Regression Tests (`regression/`)

Tests for specific bug fixes, named by issue number:
- `issue_XX_description_test.py`

### Integration Tests (`integration/`)

Tests for system interactions and complex scenarios.

### Benchmarks (`benchmarks/`)

Performance measurement tests.

### Demo (`demo/`)

Interactive demonstrations of features. Run with:
```bash
cd build
./mcrogueface ../tests/demo/demo_main.py
```

## Tips

- **Read tests as examples**: Tests show correct API usage
- **Use `mcrfpy.step()`**: Avoids timeout issues, makes tests deterministic
- **Check KNOWN_ISSUES.md**: Documents expected failures and workarounds
- **Screenshots**: Use `mcrfpy.automation.screenshot("name.png")` after `mcrfpy.step()`

## See Also

- `KNOWN_ISSUES.md` - Current test status and the `mcrfpy.step()` pattern
- `conftest.py` - Pytest fixtures and custom collector
- `demo/screens/` - Feature demonstrations (good API examples)
