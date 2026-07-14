"""
Regression test for issue #341.

get_metrics() reported 0 for every render counter:

  * draw_calls / ui_elements / visible_elements WERE incremented -- but only inside
    render(), which runs after every Python callback, while the counters were zeroed
    at the top of the frame. Python was structurally unable to observe a nonzero
    value. Render counters are now published at the end of the render pass.

  * grid_cells_rendered / entities_rendered / total_entities / grid_render_time /
    entity_render_time were never incremented ANYWHERE -- dead code since the
    GridView refactor. Re-instrumented in UIGridView::render().

Also locks two riders: frame_time is milliseconds (the docstring claimed seconds),
and fps is no longer inflated by the zero-filled history buffer on early frames.

Model under test (#350): step() is the clock and never renders; rendering is
orthogonal and costs zero simulation time. So we drive time with step() and force a
render with a screenshot, then read the metrics that render published.
"""
import mcrfpy
from mcrfpy import automation
import sys
import os
import tempfile

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  PASS: {label}")
    else:
        print(f"  FAIL: {label} {detail}")
        failures.append(label)


scene = mcrfpy.Scene("issue341")
ui = scene.children

# A grid with a layer + entities, so the grid counters have something to count.
grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
layer = mcrfpy.TileLayer("ground", 0)
grid.add_layer(layer)
for x in range(20):
    for y in range(20):
        layer.set((x, y), 0)

for i in range(6):
    grid.entities.append(mcrfpy.Entity(grid_pos=(i, i)))

ui.append(grid)

# Plain UI elements, so ui_elements / draw_calls have something to count.
for i in range(4):
    ui.append(mcrfpy.Frame(pos=(400 + i * 20, 10), size=(15, 15)))
ui.append(mcrfpy.Caption(pos=(400, 200), text="metrics"))

mcrfpy.current_scene = scene

# Advance the clock a few times. step() must NOT render, so this alone must leave
# the render counters untouched.
for _ in range(5):
    mcrfpy.step(0.016)

print("1. step() advances the sim clock but renders nothing")
m = mcrfpy.get_metrics()
check("current_frame advanced under step()", m["current_frame"] >= 5,
      f"got {m['current_frame']}")
check("frame_time is set by step()", m["frame_time"] > 0, f"got {m['frame_time']}")
check("draw_calls still 0 (step does not render)", m["draw_calls"] == 0,
      f"got {m['draw_calls']}")

# Force a render. This costs zero simulation time and publishes the render counters.
shot = os.path.join(tempfile.gettempdir(), "issue341_metrics.png")
frame_before = mcrfpy.get_metrics()["current_frame"]
automation.screenshot(shot)
m = mcrfpy.get_metrics()

print("2. Rendering costs zero simulation time")
check("current_frame did not advance from rendering",
      m["current_frame"] == frame_before,
      f"{frame_before} -> {m['current_frame']}")

print("3. Render counters are observable from Python (were always 0)")
check("draw_calls > 0", m["draw_calls"] > 0, f"got {m['draw_calls']}")
check("ui_elements > 0", m["ui_elements"] > 0, f"got {m['ui_elements']}")
check("visible_elements > 0", m["visible_elements"] > 0, f"got {m['visible_elements']}")

print("4. Grid counters are re-instrumented (were dead code)")
check("grid_cells_rendered > 0", m["grid_cells_rendered"] > 0,
      f"got {m['grid_cells_rendered']}")
check("entities_rendered > 0", m["entities_rendered"] > 0,
      f"got {m['entities_rendered']}")
check("total_entities == 6", m["total_entities"] == 6, f"got {m['total_entities']}")
check("entities_rendered <= total_entities",
      m["entities_rendered"] <= m["total_entities"])
# A cell "render" is counted per cell per layer drawn: the 20x20 grid is fully on
# screen, so it is exactly 400 * (number of layers).
expected_cells = 400 * len(grid.layers)
check(f"grid_cells_rendered == 400 * {len(grid.layers)} layers",
      m["grid_cells_rendered"] == expected_cells,
      f"got {m['grid_cells_rendered']}, expected {expected_cells}")

print("5. frame_time is in milliseconds, not seconds")
ft = m["frame_time"]
# step(0.016) -> 16ms. In seconds this would read 0.016 and fail the lower bound.
check("frame_time ~= 16ms for step(0.016)", 10.0 <= ft <= 25.0, f"got {ft}")

print("6. fps is sane on early frames (was inflated by the zero-filled history)")
fps = m["fps"]
check("fps > 0", fps > 0, f"got {fps}")
# Pre-fix, dividing by a mostly-zero 60-slot buffer inflated this enormously.
# step(0.016) is 62.5 fps; allow slack but nothing absurd.
check("fps is not absurdly inflated", fps < 1000, f"got {fps}")

print("7. Timing breakdowns are present")
check("grid_render_time >= 0", m["grid_render_time"] >= 0.0)
check("entity_render_time >= 0", m["entity_render_time"] >= 0.0)

if os.path.exists(shot):
    os.remove(shot)

print()
if failures:
    print(f"FAIL - {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
