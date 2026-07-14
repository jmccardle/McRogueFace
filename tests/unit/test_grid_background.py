#!/usr/bin/env python3
"""Test Grid background color functionality

API notes (post-#313/#350):
  - Grid.background_color was renamed to Grid.fill_color ("Background fill color
    (Color). Drawn behind all tiles and entities."). Same property, new name.
  - grid.add_layer() takes a layer OBJECT and no keyword arguments; the layer's
    ctor takes the kwargs. ColorLayer.set() takes a (x, y) tuple.
  - Headless time only advances via mcrfpy.step(); timers never fire on their own.
"""

import mcrfpy
import sys

failures = []

def check(label, actual, expected):
    if actual == expected:
        print(f"+ {label}: {actual}")
    else:
        print(f"FAIL {label}: expected {expected}, got {actual}")
        failures.append(label)

def rgb(color):
    return (color.r, color.g, color.b)

def test_grid_background():
    """Test Grid background color property"""
    print("Testing Grid Background Color...")

    # Create a test scene
    test = mcrfpy.Scene("test")
    ui = test.children

    # Create a grid with default background
    grid = mcrfpy.Grid(pos=(50, 50), size=(400, 300), grid_size=(20, 15))
    ui.append(grid)

    # Add color layer for some tiles to see the background better
    color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
    grid.add_layer(color_layer)
    for x in range(5, 15):
        for y in range(5, 10):
            color_layer.set((x, y), mcrfpy.Color(100, 150, 100))

    # Add UI to show current background color
    info_frame = mcrfpy.Frame(pos=(500, 50), size=(200, 150),
                             fill_color=mcrfpy.Color(40, 40, 40),
                             outline_color=mcrfpy.Color(200, 200, 200),
                             outline=2)
    ui.append(info_frame)

    color_caption = mcrfpy.Caption(pos=(510, 60), text="Background Color:")
    color_caption.font_size = 14
    color_caption.fill_color = mcrfpy.Color(255, 255, 255)
    info_frame.children.append(color_caption)

    color_display = mcrfpy.Caption(pos=(510, 80), text="")
    color_display.font_size = 12
    color_display.fill_color = mcrfpy.Color(200, 200, 200)
    info_frame.children.append(color_display)

    # Activate the scene
    test.activate()

    # Track which timer stages actually ran
    stages = []

    def run_tests(timer, runtime):
        """Run background color tests"""
        timer.stop()
        stages.append("default")

        print("\nTest 1: Default background color")
        default_color = grid.fill_color
        print(f"Default: R={default_color.r}, G={default_color.g}, "
              f"B={default_color.b}, A={default_color.a}")
        color_display.text = f"R:{default_color.r} G:{default_color.g} B:{default_color.b}"

    def test_set_color(timer, runtime):
        timer.stop()
        stages.append("set")
        print("\nTest 2: Set background to blue")
        grid.fill_color = mcrfpy.Color(20, 40, 100)
        new_color = grid.fill_color
        check("set background to (20, 40, 100)", rgb(new_color), (20, 40, 100))
        color_display.text = f"R:{new_color.r} G:{new_color.g} B:{new_color.b}"

    colors = [
        mcrfpy.Color(200, 20, 20),   # Red
        mcrfpy.Color(20, 200, 20),   # Green
        mcrfpy.Color(20, 20, 200),   # Blue
    ]

    def test_animation(timer, runtime):
        timer.stop()
        stages.append("cycle")
        print("\nTest 3: Manual color cycling")

        def cycle_red(t, r):
            t.stop()
            grid.fill_color = colors[0]
            c = grid.fill_color
            color_display.text = f"R:{c.r} G:{c.g} B:{c.b}"
            check("cycle to Red", rgb(c), (200, 20, 20))

        def cycle_green(t, r):
            t.stop()
            grid.fill_color = colors[1]
            c = grid.fill_color
            color_display.text = f"R:{c.r} G:{c.g} B:{c.b}"
            check("cycle to Green", rgb(c), (20, 200, 20))

        def cycle_blue(t, r):
            t.stop()
            grid.fill_color = colors[2]
            c = grid.fill_color
            color_display.text = f"R:{c.r} G:{c.g} B:{c.b}"
            check("cycle to Blue", rgb(c), (20, 20, 200))

        # Cycle through colors
        mcrfpy.Timer("cycle_0", cycle_red, 100, once=True)
        mcrfpy.Timer("cycle_1", cycle_green, 400, once=True)
        mcrfpy.Timer("cycle_2", cycle_blue, 700, once=True)

    def test_complete(timer, runtime):
        timer.stop()
        stages.append("complete")
        print("\nTest 4: Final color check")
        final_color = grid.fill_color
        # The last color set by the cycle stage must have stuck.
        check("final color is Blue", rgb(final_color), (20, 20, 200))

    # Schedule tests
    mcrfpy.Timer("run_tests", run_tests, 100, once=True)
    mcrfpy.Timer("test_set", test_set_color, 1000, once=True)
    mcrfpy.Timer("test_anim", test_animation, 2000, once=True)
    mcrfpy.Timer("complete", test_complete, 4500, once=True)

    # Headless: mcrfpy.step() is the only clock. 5 simulated seconds at 50ms/step,
    # which covers the 4500ms 'complete' timer with margin.
    for _ in range(140):
        mcrfpy.step(0.05)

    # Force a render so the grid (with its fill_color) actually goes through the
    # render path -- the property is a render-time input, not just a stored value.
    mcrfpy.automation.screenshot("test_grid_background.png")

    for stage in ("default", "set", "cycle", "complete"):
        if stage not in stages:
            print(f"FAIL: timer stage '{stage}' never ran")
            failures.append(f"stage:{stage}")

    if failures:
        print(f"\nFAIL: {len(failures)} check(s) failed: {failures}")
        sys.exit(1)

    print("\n+ Grid background color tests completed!")
    print("- Default background color works")
    print("- Setting background color works")
    print("- Color cycling works")
    print("PASS")
    sys.exit(0)

if __name__ == "__main__":
    test_grid_background()
